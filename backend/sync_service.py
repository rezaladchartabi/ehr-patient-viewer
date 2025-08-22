import asyncio
import httpx
import time
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging
import os
try:
    from local_db import LocalDatabase
except ImportError:
    # When imported as a package (e.g., uvicorn backend.main:app)
    from backend.local_db import LocalDatabase

logger = logging.getLogger(__name__)

class SyncService:
    def __init__(self, fhir_base_url: str, local_db: LocalDatabase, fetch_from_fhir_func=None):
        self.fhir_base_url = fhir_base_url or os.getenv("FHIR_BASE_URL", "http://localhost:8080/")
        self.local_db = local_db
        self.fetch_from_fhir = fetch_from_fhir_func
        self.sync_interval = 300  # 5 minutes
        self.max_retries = 3
        self.retry_delay = 5  # seconds
    
    async def sync_all_resources(self) -> Dict[str, Any]:
        """Sync all resource types from FHIR server"""
        sync_results = {}
        
        # Define resource types to sync
        resource_types = [
            'Patient',
            'AllergyIntolerance', 
            'Condition',
            'Encounter',
            'MedicationRequest',
            'MedicationAdministration',
            'MedicationDispense',
            'Observation',
            'Procedure',
            'Specimen'
        ]
        
        for resource_type in resource_types:
            try:
                result = await self.sync_resource_type(resource_type)
                sync_results[resource_type] = result
                logger.info(f"Synced {resource_type}: {result}")
            except Exception as e:
                logger.error(f"Failed to sync {resource_type}: {e}")
                sync_results[resource_type] = {'error': str(e)}
        
        return sync_results
    
    async def sync_resource_type(self, resource_type: str) -> Dict[str, Any]:
        """Sync a specific resource type with change detection"""
        last_sync_info = self.local_db.get_last_sync_info(resource_type)
        
        # Get current data from FHIR server
        fhir_data = await self._fetch_fhir_resource(resource_type)
        
        if not fhir_data or 'entry' not in fhir_data:
            return {'status': 'no_data', 'changes': 0}
        
        changes = 0
        total_count = len(fhir_data['entry'])
        
        # Process each resource
        for entry in fhir_data['entry']:
            resource = entry['resource']
            processed_data = self._process_resource(resource_type, resource)
            
            if processed_data:
                # Use appropriate upsert method based on resource type
                if resource_type == 'Patient':
                    changed = self.local_db.upsert_patient(processed_data)
                elif resource_type == 'AllergyIntolerance':
                    changed = self.local_db.upsert_allergy(processed_data)
                elif resource_type == 'MedicationDispense':
                    changed = self.local_db.upsert_medication_dispense(processed_data)
                # Add other resource types as needed
                else:
                    changed = False  # Placeholder for other resource types
                
                if changed:
                    changes += 1
        
        # Update sync metadata
        sync_info = {
            'last_sync_time': datetime.now().isoformat(),
            'last_version_id': fhir_data.get('meta', {}).get('versionId'),
            'total_count': total_count,
            'last_hash': self._calculate_bundle_hash(fhir_data)
        }
        self.local_db.update_sync_metadata(resource_type, sync_info)
        
        return {
            'status': 'success',
            'total_count': total_count,
            'changes': changes,
            'last_sync': sync_info['last_sync_time']
        }
    
    async def _fetch_fhir_resource(self, resource_type: str, params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Fetch resource data from FHIR server with retry logic"""
        if params is None:
            params = {'_count': 1000}  # Get more records per request
        
        url = f"{self.fhir_base_url}fhir/{resource_type}"
        
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    logger.info(f"Fetching {resource_type} from {url} with params: {params}")
                    response = await client.get(url, params=params)
                    response.raise_for_status()
                    data = response.json()
                    
                    # Log response info
                    if 'entry' in data:
                        logger.info(f"Received {len(data['entry'])} entries for {resource_type}")
                    else:
                        logger.warning(f"No 'entry' field in response for {resource_type}: {data}")
                    
                    return data
            except httpx.HTTPStatusError as e:
                logger.warning(f"HTTP error for {resource_type} (attempt {attempt + 1}): {e.response.status_code} - {e.response.text}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                else:
                    raise e
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed for {resource_type}: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                else:
                    raise e
        
        return None
    
    def _process_resource(self, resource_type: str, resource: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process FHIR resource into local database format"""
        if resource_type == 'Patient':
            return self._process_patient(resource)
        elif resource_type == 'AllergyIntolerance':
            return self._process_allergy(resource)
        elif resource_type == 'Condition':
            return self._process_condition(resource)
        elif resource_type == 'Encounter':
            return self._process_encounter(resource)
        elif resource_type == 'MedicationDispense':
            return self._process_medication_dispense(resource)
        # Add other resource processors as needed
        return None
    
    def _process_patient(self, resource: Dict[str, Any]) -> Dict[str, Any]:
        """Process Patient resource"""
        return {
            'id': resource.get('id'),
            'family_name': resource.get('name', [{}])[0].get('family') if resource.get('name') else None,
            'gender': resource.get('gender'),
            'birth_date': resource.get('birthDate'),
            'race': self._extract_extension_value(resource, 'us-core-race', 'text'),
            'ethnicity': self._extract_extension_value(resource, 'us-core-ethnicity', 'text'),
            'birth_sex': self._extract_extension_value(resource, 'us-core-birthsex'),
            'identifier': resource.get('identifier', [{}])[0].get('value') if resource.get('identifier') else None,
            'marital_status': resource.get('maritalStatus', {}).get('coding', [{}])[0].get('code') if resource.get('maritalStatus') else None,
            'deceased_date': resource.get('deceasedDateTime'),
            'managing_organization': resource.get('managingOrganization', {}).get('reference') if resource.get('managingOrganization') else None,
            'last_updated': resource.get('meta', {}).get('lastUpdated'),
            'version_id': resource.get('meta', {}).get('versionId')
        }
    
    def _process_allergy(self, resource: Dict[str, Any]) -> Dict[str, Any]:
        """Process AllergyIntolerance resource"""
        return {
            'id': resource.get('id'),
            'patient_id': resource.get('patient', {}).get('reference', '').split('/')[-1] if resource.get('patient') else None,
            'code': resource.get('code', {}).get('coding', [{}])[0].get('code') if resource.get('code') else None,
            'code_display': resource.get('code', {}).get('text') or resource.get('code', {}).get('coding', [{}])[0].get('display') if resource.get('code') else None,
            'code_system': resource.get('code', {}).get('coding', [{}])[0].get('system') if resource.get('code') else None,
            'category': resource.get('category', [{}])[0].get('coding', [{}])[0].get('display') if resource.get('category') else None,
            'clinical_status': resource.get('clinicalStatus', {}).get('coding', [{}])[0].get('code') if resource.get('clinicalStatus') else None,
            'verification_status': resource.get('verificationStatus', {}).get('coding', [{}])[0].get('code') if resource.get('verificationStatus') else None,
            'type': resource.get('type', [{}])[0].get('coding', [{}])[0].get('display') if resource.get('type') else None,
            'criticality': resource.get('criticality'),
            'onset_date': resource.get('onsetDateTime'),
            'recorded_date': resource.get('recordedDate'),
            'recorder': resource.get('recorder', {}).get('display') if resource.get('recorder') else None,
            'asserter': resource.get('asserter', {}).get('display') if resource.get('asserter') else None,
            'last_occurrence': resource.get('lastOccurrence'),
            'note': resource.get('note', [{}])[0].get('text') if resource.get('note') else None,
            'last_updated': resource.get('meta', {}).get('lastUpdated'),
            'version_id': resource.get('meta', {}).get('versionId')
        }
    
    def _process_condition(self, resource: Dict[str, Any]) -> Dict[str, Any]:
        """Process Condition resource"""
        return {
            'id': resource.get('id'),
            'patient_id': resource.get('subject', {}).get('reference', '').split('/')[-1] if resource.get('subject') else None,
            'code': resource.get('code', {}).get('coding', [{}])[0].get('code') if resource.get('code') else None,
            'code_display': resource.get('code', {}).get('text') or resource.get('code', {}).get('coding', [{}])[0].get('display') if resource.get('code') else None,
            'code_system': resource.get('code', {}).get('coding', [{}])[0].get('system') if resource.get('code') else None,
            'category': resource.get('category', [{}])[0].get('coding', [{}])[0].get('display') if resource.get('category') else None,
            'clinical_status': resource.get('clinicalStatus', {}).get('coding', [{}])[0].get('code') if resource.get('clinicalStatus') else None,
            'verification_status': resource.get('verificationStatus', {}).get('coding', [{}])[0].get('code') if resource.get('verificationStatus') else None,
            'severity': resource.get('severity', {}).get('coding', [{}])[0].get('display') if resource.get('severity') else None,
            'onset_date': resource.get('onsetDateTime') or resource.get('onsetString'),
            'recorded_date': resource.get('recordedDate'),
            'recorder': resource.get('recorder', {}).get('display') if resource.get('recorder') else None,
            'asserter': resource.get('asserter', {}).get('display') if resource.get('asserter') else None,
            'note': resource.get('note', [{}])[0].get('text') if resource.get('note') else None,
            'last_updated': resource.get('meta', {}).get('lastUpdated'),
            'version_id': resource.get('meta', {}).get('versionId')
        }
    
    def _process_encounter(self, resource: Dict[str, Any]) -> Dict[str, Any]:
        """Process Encounter resource"""
        return {
            'id': resource.get('id'),
            'patient_id': resource.get('subject', {}).get('reference', '').split('/')[-1] if resource.get('subject') else None,
            'status': resource.get('status'),
            'class': resource.get('class', {}).get('code') if resource.get('class') else None,
            'type': resource.get('type', [{}])[0].get('coding', [{}])[0].get('display') if resource.get('type') else None,
            'subject': resource.get('subject', {}).get('reference') if resource.get('subject') else None,
            'start_date': resource.get('period', {}).get('start') if resource.get('period') else None,
            'end_date': resource.get('period', {}).get('end') if resource.get('period') else None,
            'location': resource.get('location', [{}])[0].get('location', {}).get('display') if resource.get('location') else None,
            'service_provider': resource.get('serviceProvider', {}).get('display') if resource.get('serviceProvider') else None,
            'last_updated': resource.get('meta', {}).get('lastUpdated'),
            'version_id': resource.get('meta', {}).get('versionId')
        }
    
    def _process_medication_dispense(self, resource: Dict[str, Any]) -> Dict[str, Any]:
        """Process MedicationDispense resource"""
        # Extract encounter reference
        encounter_id = None
        if resource.get('context', {}).get('reference'):
            encounter_id = resource['context']['reference'].split('/')[-1]
        
        # Extract medication information
        medication_code = None
        medication_display = None
        medication_system = None
        
        if resource.get('medicationCodeableConcept'):
            med_concept = resource['medicationCodeableConcept']
            if med_concept.get('coding') and len(med_concept['coding']) > 0:
                coding = med_concept['coding'][0]
                medication_code = coding.get('code')
                medication_display = coding.get('display')
                medication_system = coding.get('system')
            if not medication_display:
                medication_display = med_concept.get('text')
        
        # Extract quantity information
        quantity_value = None
        quantity_unit = None
        quantity_system = None
        if resource.get('quantity'):
            quantity_value = resource['quantity'].get('value')
            quantity_unit = resource['quantity'].get('unit')
            quantity_system = resource['quantity'].get('system')
        
        # Extract days supply
        days_supply_value = None
        days_supply_unit = None
        if resource.get('daysSupply'):
            days_supply_value = resource['daysSupply'].get('value')
            days_supply_unit = resource['daysSupply'].get('unit')
        
        # Extract performer information
        performer_actor_display = None
        performer_actor_reference = None
        if resource.get('performer') and len(resource['performer']) > 0:
            performer = resource['performer'][0]
            if performer.get('actor'):
                performer_actor_display = performer['actor'].get('display')
                performer_actor_reference = performer['actor'].get('reference')
        
        # Extract location
        location_display = None
        location_reference = None
        if resource.get('location'):
            location_display = resource['location'].get('display')
            location_reference = resource['location'].get('reference')
        
        # Extract dosage instructions
        dosage_instruction = None
        if resource.get('dosageInstruction') and len(resource['dosageInstruction']) > 0:
            dosage_instruction = resource['dosageInstruction'][0].get('text')
        
        # Extract substitution information
        substitution_was_substituted = None
        substitution_type_code = None
        substitution_type_display = None
        substitution_reason_code = None
        substitution_reason_display = None
        
        if resource.get('substitution'):
            substitution = resource['substitution']
            substitution_was_substituted = substitution.get('wasSubstituted')
            
            if substitution.get('type', {}).get('coding') and len(substitution['type']['coding']) > 0:
                type_coding = substitution['type']['coding'][0]
                substitution_type_code = type_coding.get('code')
                substitution_type_display = type_coding.get('display')
            
            if substitution.get('reason') and len(substitution['reason']) > 0:
                reason = substitution['reason'][0]
                if reason.get('coding') and len(reason['coding']) > 0:
                    reason_coding = reason['coding'][0]
                    substitution_reason_code = reason_coding.get('code')
                    substitution_reason_display = reason_coding.get('display')
        
        return {
            'id': resource.get('id'),
            'patient_id': resource.get('subject', {}).get('reference', '').split('/')[-1] if resource.get('subject') else None,
            'encounter_id': encounter_id,
            'medication_code': medication_code,
            'medication_display': medication_display,
            'medication_system': medication_system,
            'status': resource.get('status'),
            'quantity_value': quantity_value,
            'quantity_unit': quantity_unit,
            'quantity_system': quantity_system,
            'days_supply_value': days_supply_value,
            'days_supply_unit': days_supply_unit,
            'when_prepared': resource.get('whenPrepared'),
            'when_handed_over': resource.get('whenHandedOver'),
            'destination': resource.get('destination', {}).get('display') if resource.get('destination') else None,
            'performer_actor_display': performer_actor_display,
            'performer_actor_reference': performer_actor_reference,
            'location_display': location_display,
            'location_reference': location_reference,
            'dosage_instruction': dosage_instruction,
            'substitution_was_substituted': substitution_was_substituted,
            'substitution_type_code': substitution_type_code,
            'substitution_type_display': substitution_type_display,
            'substitution_reason_code': substitution_reason_code,
            'substitution_reason_display': substitution_reason_display,
            'last_updated': resource.get('meta', {}).get('lastUpdated'),
            'version_id': resource.get('meta', {}).get('versionId')
        }
    
    def _extract_extension_value(self, resource: Dict[str, Any], extension_name: str, sub_field: str = None) -> Optional[str]:
        """Extract value from FHIR extension"""
        if not resource.get('extension'):
            return None
        
        for ext in resource['extension']:
            if extension_name in ext.get('url', ''):
                if sub_field and ext.get('extension'):
                    for sub_ext in ext['extension']:
                        if sub_ext.get('url') == sub_field:
                            return sub_ext.get('valueString')
                else:
                    return ext.get('valueCode') or ext.get('valueString')
        return None
    
    def _calculate_bundle_hash(self, bundle: Dict[str, Any]) -> str:
        """Calculate hash of entire bundle for change detection"""
        import hashlib
        import json
        
        # Create a simplified version for hashing
        hash_data = {
            'total': bundle.get('total'),
            'entry_count': len(bundle.get('entry', [])),
            'last_updated': bundle.get('meta', {}).get('lastUpdated')
        }
        
        return hashlib.md5(json.dumps(hash_data, sort_keys=True).encode()).hexdigest()
    
    async def start_periodic_sync(self):
        """Start periodic synchronization"""
        logger.info("Starting periodic sync service")
        
        while True:
            try:
                logger.info("Starting sync cycle")
                results = await self.sync_all_resources()
                
                # Log summary
                total_changes = sum(r.get('changes', 0) for r in results.values() if isinstance(r, dict))
                logger.info(f"Sync cycle completed. Total changes: {total_changes}")
                
            except Exception as e:
                logger.error(f"Sync cycle failed: {e}")
            
            # Wait for next sync cycle
            await asyncio.sleep(self.sync_interval)
    
    async def sync_specific_patients(self, patient_ids: List[str]) -> Dict[str, Any]:
        """Sync data for specific patients only"""
        results = {}
        
        for patient_id in patient_ids:
            try:
                # Fetch Patient by _id (standard FHIR)
                if self.fetch_from_fhir:
                    patient_data = await self.fetch_from_fhir("/Patient", {'_id': patient_id, '_count': 1})
                else:
                    async with httpx.AsyncClient(timeout=30.0) as client:
                        url = f"{self.fhir_base_url}fhir/Patient"
                        response = await client.get(url, params={"_id": patient_id, "_count": 1})
                        response.raise_for_status()
                        patient_data = response.json()
                
                if patient_data and 'entry' in patient_data and len(patient_data['entry']) > 0:
                    patient_resource = patient_data['entry'][0]['resource']
                    processed_patient = self._process_patient(patient_resource)
                    self.local_db.upsert_patient(processed_patient)
                else:
                    results[patient_id] = {'status': 'error', 'error': 'Patient not found in FHIR server'}
                    continue
                
                # Sync related resources for this patient
                related_resources = ['AllergyIntolerance', 'Condition', 'Encounter']
                for resource_type in related_resources:
                    try:
                        if self.fetch_from_fhir:
                            resource_data = await self.fetch_from_fhir(f"/{resource_type}", {'patient': f'Patient/{patient_id}'})
                        else:
                            # Fallback to direct HTTP call
                            async with httpx.AsyncClient(timeout=30.0) as client:
                                url = f"{self.fhir_base_url}fhir/{resource_type}?patient=Patient/{patient_id}&_count=100"
                                response = await client.get(url)
                                response.raise_for_status()
                                resource_data = response.json()
                        
                        if resource_data and 'entry' in resource_data:
                            for entry in resource_data['entry']:
                                processed_resource = self._process_resource(resource_type, entry['resource'])
                                if processed_resource:
                                    if resource_type == 'AllergyIntolerance':
                                        self.local_db.upsert_allergy(processed_resource)
                                    elif resource_type == 'Condition':
                                        self.local_db.upsert_condition(processed_resource)
                                    elif resource_type == 'Encounter':
                                        self.local_db.upsert_encounter(processed_resource)
                                    elif resource_type == 'MedicationDispense':
                                        self.local_db.upsert_medication_dispense(processed_resource)
                                    # Add other resource types as needed
                    except Exception as resource_error:
                        # Log but don't fail the entire sync for resource errors
                        logger.warning(f"Failed to sync {resource_type} for patient {patient_id}: {resource_error}")
                
                results[patient_id] = {'status': 'success'}
                
            except Exception as e:
                results[patient_id] = {'status': 'error', 'error': str(e)}
        
        return results
