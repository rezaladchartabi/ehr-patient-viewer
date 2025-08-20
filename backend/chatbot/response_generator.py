"""
Medical Response Generator

Generates evidence-based responses for medical queries using patient data
and external medical knowledge sources.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class MedicalResponseGenerator:
    """Generates medical responses based on queries and evidence"""
    
    def __init__(self):
        # Response templates for different intents
        self.response_templates = {
            'medication_query': {
                'found': "Based on the patient's records, they are currently taking the following medications:\n{medications}\n\n{additional_info}",
                'not_found': "I don't see any current medications recorded for this patient. Would you like me to check for past medication history or help you add new medications?",
                'no_data': "I don't have access to the patient's medication records at the moment. Please ensure the patient data is loaded."
            },
            'condition_query': {
                'found': "The patient has been diagnosed with the following conditions:\n{conditions}\n\n{additional_info}",
                'not_found': "I don't see any recorded conditions for this patient. Would you like me to check their medical history or help you add new conditions?",
                'no_data': "I don't have access to the patient's condition records at the moment. Please ensure the patient data is loaded."
            },
            'allergy_query': {
                'found': "The patient has the following known allergies:\n{allergies}\n\n{additional_info}",
                'not_found': "No known allergies are recorded for this patient. Would you like me to check for any adverse reactions or help you add allergy information?",
                'no_data': "I don't have access to the patient's allergy records at the moment. Please ensure the patient data is loaded."
            },
            'pmh_query': {
                'found': "The patient has the following past medical history:\n{conditions}\n\n{additional_info}",
                'not_found': "No past medical history is recorded for this patient. Would you like me to check for current conditions?",
                'no_data': "I don't have access to the patient's past medical history at the moment. Please ensure the patient data is loaded."
            },
            'interaction_query': {
                'found': "I found the following potential drug interactions:\n{interactions}\n\n{recommendations}",
                'not_found': "No significant drug interactions were found with the current medications. However, it's always good practice to monitor for any adverse effects.",
                'no_data': "I don't have enough medication data to check for interactions. Please ensure the patient's medications are loaded."
            },
            'evidence_query': {
                'found': "Here's the latest clinical evidence for {condition}:\n{evidence}\n\n{recommendations}",
                'not_found': "I couldn't find specific clinical evidence for that query. Would you like me to search for related conditions or treatments?",
                'no_data': "I don't have access to clinical evidence databases at the moment. Please try again later."
            },
            'alert_query': {
                'found': "I found the following clinical alerts for this patient:\n{alerts}\n\n{recommendations}",
                'not_found': "No active clinical alerts were found for this patient at this time.",
                'no_data': "I don't have access to clinical alert systems at the moment. Please check with your clinical team."
            },
            'observation_query': {
                'found': "The patient has the following observations and vital signs:\n{observations}\n\n{additional_info}",
                'not_found': "No observations or vital signs are recorded for this patient. Would you like me to check for lab results or other measurements?",
                'no_data': "I don't have access to the patient's observation records at the moment. Please ensure the patient data is loaded."
            },
            'encounter_query': {
                'found': "The patient has the following encounters and visits:\n{encounters}\n\n{additional_info}",
                'not_found': "No encounters or visits are recorded for this patient. Would you like me to check for appointments or hospitalizations?",
                'no_data': "I don't have access to the patient's encounter records at the moment. Please ensure the patient data is loaded."
            },
            'procedure_query': {
                'found': "The patient has undergone the following procedures:\n{procedures}\n\n{additional_info}",
                'not_found': "No procedures are recorded for this patient. Would you like me to check for surgeries or tests?",
                'no_data': "I don't have access to the patient's procedure records at the moment. Please ensure the patient data is loaded."
            },
            'specimen_query': {
                'found': "The patient has the following specimens and lab samples:\n{specimens}\n\n{additional_info}",
                'not_found': "No specimens or lab samples are recorded for this patient. Would you like me to check for lab work or collections?",
                'no_data': "I don't have access to the patient's specimen records at the moment. Please ensure the patient data is loaded."
            },
            'general_query': {
                'default': "I can help you with information about the patient's medications, conditions, allergies, observations, encounters, procedures, specimens, drug interactions, and clinical evidence. What specific information would you like to know?"
            }
        }
        
        # Evidence formatting templates
        self.evidence_templates = {
            'clinical_trial': "📊 Clinical Trial: {title}\n📅 Published: {date}\n📝 {summary}\n🎯 Evidence Level: {level}",
            'systematic_review': "📚 Systematic Review: {title}\n📅 Published: {date}\n📝 {summary}\n🎯 Evidence Level: {level}",
            'guideline': "📋 Clinical Guideline: {title}\n📅 Published: {date}\n📝 {summary}\n🎯 Evidence Level: {level}",
            'drug_info': "💊 Drug Information: {name}\n📝 {description}\n⚠️ Side Effects: {side_effects}",
            'interaction': "⚠️ Drug Interaction: {drug1} + {drug2}\n📝 {description}\n🎯 Severity: {severity}"
        }
    
    async def generate_response(self, query: str, intent: str, entities: List[str], 
                              patient_data: Dict[str, Any], evidence: Dict[str, Any], 
                              clinical_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate a comprehensive response based on the query and available data"""
        try:
            logger.info(f"Generating response for intent: {intent}")
            
            # Generate base response
            response_text = await self._generate_base_response(intent, entities, patient_data, evidence, clinical_context)
            
            # Add evidence citations
            evidence_list = await self._format_evidence(evidence)
            
            # Add clinical context if available
            if clinical_context and clinical_context.get("hits"):
                clinical_evidence = await self._format_clinical_context(clinical_context)
                evidence_list.extend(clinical_evidence)
            
            # Add sources
            sources = await self._extract_sources(evidence)
            
            # Calculate confidence
            confidence = await self._calculate_confidence(intent, entities, patient_data, evidence, clinical_context)
            
            # Add recommendations
            recommendations = await self._generate_recommendations(intent, entities, patient_data, evidence, clinical_context)
            
            if recommendations:
                response_text += f"\n\n💡 Recommendations:\n{recommendations}"
            
            return {
                "text": response_text,
                "evidence": evidence_list,
                "sources": sources,
                "confidence": confidence,
                "intent": intent,
                "entities": entities,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {
                "text": "I apologize, but I encountered an error while generating a response. Please try rephrasing your question.",
                "evidence": [],
                "sources": [],
                "confidence": 0.0,
                "error": str(e)
            }
    
    async def _generate_base_response(self, intent: str, entities: List[str], 
                                    patient_data: Dict[str, Any], evidence: Dict[str, Any], 
                                    clinical_context: Optional[Dict[str, Any]] = None) -> str:
        """Generate the base response text"""
        templates = self.response_templates.get(intent, self.response_templates['general_query'])
        
        if intent == 'medication_query':
            # Check all medication types
            med_requests = patient_data.get('medication_requests', [])
            med_admins = patient_data.get('medication_administrations', [])
            med_dispenses = patient_data.get('medication_dispenses', [])
            all_medications = med_requests + med_admins + med_dispenses
            
            if all_medications:
                med_list = self._format_comprehensive_medication_list(med_requests, med_admins, med_dispenses)
                additional_info = self._get_medication_additional_info(all_medications, evidence)
                return templates['found'].format(medications=med_list, additional_info=additional_info)
            else:
                return templates['not_found']
        
        elif intent == 'condition_query':
            # Use FHIR conditions (which should always be available)
            fhir_conditions = patient_data.get('conditions', [])
            
            if fhir_conditions:
                condition_list = self._format_condition_list(fhir_conditions)
                additional_info = self._get_condition_additional_info(fhir_conditions, evidence)
                return templates['found'].format(conditions=condition_list, additional_info=additional_info)
            else:
                return templates['not_found']
        
        elif intent == 'pmh_query':
            # Use PMH data from local database
            pmh_conditions = patient_data.get('pmh', [])
            print(f"DEBUG: PMH query - found {len(pmh_conditions)} PMH conditions")
            print(f"DEBUG: PMH data keys: {list(patient_data.keys())}")
            print(f"DEBUG: PMH conditions sample: {pmh_conditions[:2] if pmh_conditions else 'None'}")
            if pmh_conditions:
                pmh_list = self._format_pmh_list(pmh_conditions)
                additional_info = self._get_pmh_additional_info(pmh_conditions, evidence)
                return templates['found'].format(conditions=pmh_list, additional_info=additional_info)
            else:
                return templates['not_found']
        
        elif intent == 'allergy_query':
            allergies = patient_data.get('allergies', [])
            if allergies:
                allergy_list = self._format_allergy_list(allergies)
                additional_info = self._get_allergy_additional_info(allergies, evidence)
                return templates['found'].format(allergies=allergy_list, additional_info=additional_info)
            else:
                return templates['not_found']
        
        elif intent == 'interaction_query':
            interactions = evidence.get('interactions', [])
            if interactions:
                interaction_list = self._format_interaction_list(interactions)
                recommendations = self._get_interaction_recommendations(interactions)
                return templates['found'].format(interactions=interaction_list, recommendations=recommendations)
            else:
                return templates['not_found']
        
        elif intent == 'evidence_query':
            clinical_evidence = evidence.get('clinical_evidence', [])
            if clinical_evidence:
                evidence_text = self._format_evidence_list(clinical_evidence)
                recommendations = self._get_evidence_recommendations(clinical_evidence)
                return templates['found'].format(condition=entities[0] if entities else "the condition", 
                                               evidence=evidence_text, recommendations=recommendations)
            else:
                return templates['not_found']
        
        elif intent == 'alert_query':
            alerts = evidence.get('alerts', [])
            if alerts:
                alert_list = self._format_alert_list(alerts)
                recommendations = self._get_alert_recommendations(alerts)
                return templates['found'].format(alerts=alert_list, recommendations=recommendations)
            else:
                return templates['not_found']
        
        elif intent == 'observation_query':
            observations = patient_data.get('observations', [])
            if observations:
                observation_list = self._format_observation_list(observations)
                additional_info = self._get_observation_additional_info(observations, evidence)
                return templates['found'].format(observations=observation_list, additional_info=additional_info)
            else:
                return templates['not_found']
        
        elif intent == 'encounter_query':
            encounters = patient_data.get('encounters', [])
            if encounters:
                encounter_list = self._format_encounter_list(encounters)
                additional_info = self._get_encounter_additional_info(encounters, evidence)
                return templates['found'].format(encounters=encounter_list, additional_info=additional_info)
            else:
                return templates['not_found']
        
        elif intent == 'procedure_query':
            procedures = patient_data.get('procedures', [])
            if procedures:
                procedure_list = self._format_procedure_list(procedures)
                additional_info = self._get_procedure_additional_info(procedures, evidence)
                return templates['found'].format(procedures=procedure_list, additional_info=additional_info)
            else:
                return templates['not_found']
        
        elif intent == 'specimen_query':
            specimens = patient_data.get('specimens', [])
            if specimens:
                specimen_list = self._format_specimen_list(specimens)
                additional_info = self._get_specimen_additional_info(specimens, evidence)
                return templates['found'].format(specimens=specimen_list, additional_info=additional_info)
            else:
                return templates['not_found']
        
        else:
            base_response = templates.get('default', "I can help you with medical information. What would you like to know?")
        
        # Add clinical context if available
        if clinical_context and clinical_context.get("hits"):
            clinical_context_text = self._format_clinical_context_for_response(clinical_context)
            if clinical_context_text:
                base_response += f"\n\n📋 **Relevant Clinical Context:**\n{clinical_context_text}"
        
        return base_response
    
    async def _format_evidence(self, evidence: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Format evidence for display"""
        formatted_evidence = []
        
        # Format clinical evidence
        for item in evidence.get('clinical_evidence', []):
            formatted_evidence.append({
                "type": "clinical_evidence",
                "title": item.get('title', 'Clinical Evidence'),
                "abstract": item.get('abstract', ''),
                "journal": item.get('journal', ''),
                "evidence_level": item.get('evidence_level', ''),
                "relevance_score": item.get('relevance_score', 0.0)
            })
        
        # Format drug information
        for item in evidence.get('drug_info', []):
            formatted_evidence.append({
                "type": "drug_info",
                "title": f"Drug Information: {item.get('name', 'Unknown')}",
                "abstract": item.get('description', ''),
                "journal": "RxNorm Database",
                "evidence_level": "Standard Reference",
                "relevance_score": 0.9
            })
        
        return formatted_evidence
    
    async def _format_clinical_context(self, clinical_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Format clinical context from RAG for display"""
        formatted_context = []
        
        hits = clinical_context.get("hits", [])
        for hit in hits:
            # Extract relevant information from the clinical note chunk
            text = hit.get("text", "")
            metadata = hit.get("metadata", {})
            score = hit.get("score", 0.0)
            
            # Create a summary of the clinical context
            note_id = metadata.get("note_id", "Unknown")
            section = metadata.get("section", "General")
            chart_time = metadata.get("chart_time", "")
            
            # Truncate text for display (keep first 200 characters)
            display_text = text[:200] + "..." if len(text) > 200 else text
            
            formatted_context.append({
                "type": "clinical_context",
                "title": f"Clinical Note: {note_id} - {section}",
                "abstract": display_text,
                "journal": f"Discharge Summary - {chart_time}",
                "evidence_level": "Patient Record",
                "relevance_score": score,
                "metadata": {
                    "note_id": note_id,
                    "section": section,
                    "chart_time": chart_time,
                    "full_text": text
                }
            })
        
        return formatted_context
    
    def _format_clinical_context_for_response(self, clinical_context: Dict[str, Any]) -> str:
        """Format clinical context for inclusion in the main response text"""
        hits = clinical_context.get("hits", [])
        if not hits:
            return ""
        
        context_parts = []
        
        # Include top 2 most relevant clinical notes
        for i, hit in enumerate(hits[:2]):
            text = hit.get("text", "")
            metadata = hit.get("metadata", {})
            score = hit.get("score", 0.0)
            
            note_id = metadata.get("note_id", "Unknown")
            section = metadata.get("section", "General")
            
            # Truncate text for readability (keep first 150 characters)
            display_text = text[:150] + "..." if len(text) > 150 else text
            
            # Format as a bullet point
            context_parts.append(f"• **{note_id} - {section}** (relevance: {score:.2f})\n  {display_text}")
        
        return "\n\n".join(context_parts)
    
    async def _extract_sources(self, evidence: Dict[str, Any]) -> List[str]:
        """Extract source information from evidence"""
        sources = []
        
        # Add evidence sources
        for item in evidence.get('clinical_evidence', []):
            if item.get('journal'):
                sources.append(item['journal'])
        
        # Add knowledge base sources
        knowledge_results = evidence.get('knowledge_base', [])
        for item in knowledge_results:
            if item.get('source_name'):
                sources.append(item['source_name'])
        
        # Remove duplicates
        return list(set(sources))
    
    async def _calculate_confidence(self, intent: str, entities: List[str], 
                                  patient_data: Dict[str, Any], evidence: Dict[str, Any], 
                                  clinical_context: Optional[Dict[str, Any]] = None) -> float:
        """Calculate confidence score for the response"""
        confidence = 0.5  # Base confidence
        
        # Increase confidence based on available data
        if patient_data:
            confidence += 0.2
        
        if entities:
            confidence += 0.1
        
        if evidence.get('clinical_evidence'):
            confidence += 0.1
        
        if evidence.get('drug_info'):
            confidence += 0.1
        
        # Increase confidence if we have relevant clinical context
        if clinical_context and clinical_context.get("hits"):
            confidence += 0.15
        
        # Decrease confidence for complex queries
        if len(entities) > 3:
            confidence -= 0.1
        
        # Cap confidence at 1.0
        return min(confidence, 1.0)
    
    async def _generate_recommendations(self, intent: str, entities: List[str], 
                                      patient_data: Dict[str, Any], evidence: Dict[str, Any], 
                                      clinical_context: Optional[Dict[str, Any]] = None) -> str:
        """Generate clinical recommendations"""
        recommendations = []
        
        if intent == 'medication_query':
            recommendations.append("• Monitor for medication adherence and side effects")
            recommendations.append("• Review medication list regularly for potential interactions")
            recommendations.append("• Consider medication reconciliation at each visit")
        
        elif intent == 'interaction_query':
            recommendations.append("• Monitor patient for signs of interaction")
            recommendations.append("• Consider alternative medications if needed")
            recommendations.append("• Document any adverse effects")
        
        elif intent == 'evidence_query':
            recommendations.append("• Consider the latest clinical guidelines")
            recommendations.append("• Individualize treatment based on patient factors")
            recommendations.append("• Monitor patient response to treatment")
        
        return "\n".join(recommendations)
    
    def _format_medication_list(self, medications: List[Dict]) -> str:
        """Format medication list for display"""
        if not medications:
            return "No medications found"
        
        formatted = []
        for med in medications:
            name = med.get('name', 'Unknown medication')
            dosage = med.get('dosage', '')
            frequency = med.get('frequency', '')
            
            med_text = f"• {name}"
            if dosage:
                med_text += f" - {dosage}"
            if frequency:
                med_text += f" {frequency}"
            
            formatted.append(med_text)
        
        return "\n".join(formatted)
    
    def _format_comprehensive_medication_list(self, med_requests: List[Dict], med_admins: List[Dict], med_dispenses: List[Dict]) -> str:
        """Format comprehensive medication list including all types"""
        sections = []
        
        # Medication Requests
        if med_requests:
            request_items = []
            for med in med_requests:
                name = med.get('medicationCodeableConcept', {}).get('text') or med.get('medicationCodeableConcept', {}).get('coding', [{}])[0].get('display', 'Unknown')
                status = med.get('status', '')
                intent = med.get('intent', '')
                date = med.get('authoredOn', '')
                
                # Skip UUIDs (medication names that look like UUIDs)
                if name and len(name) == 36 and '-' in name:
                    continue
                
                # Skip if no meaningful name
                if not name or name == 'Unknown' or len(name) < 3:
                    continue
                
                med_text = f"• {name}"
                if status and status != 'unknown':
                    med_text += f" ({status})"
                if intent and intent != 'unknown':
                    med_text += f" - {intent}"
                if date:
                    try:
                        date_obj = datetime.fromisoformat(date.replace('Z', '+00:00'))
                        formatted_date = date_obj.strftime('%m/%d/%Y')
                        med_text += f" - {formatted_date}"
                    except:
                        med_text += f" - {date}"
                
                request_items.append(med_text)
            
            if request_items:
                sections.append("📋 **Medication Requests:**\n" + "\n".join(request_items))
        
        # Medication Administrations
        if med_admins:
            admin_items = []
            for med in med_admins:
                name = med.get('medicationCodeableConcept', {}).get('text') or med.get('medicationCodeableConcept', {}).get('coding', [{}])[0].get('display', 'Unknown')
                status = med.get('status', '')
                date = med.get('effectiveDateTime', '')
                
                # Skip if no meaningful name
                if not name or name == 'Unknown' or len(name) < 3:
                    continue
                
                med_text = f"• {name}"
                if status and status != 'unknown':
                    med_text += f" ({status})"
                if date:
                    try:
                        date_obj = datetime.fromisoformat(date.replace('Z', '+00:00'))
                        formatted_date = date_obj.strftime('%m/%d/%Y')
                        med_text += f" - {formatted_date}"
                    except:
                        med_text += f" - {date}"
                
                admin_items.append(med_text)
            
            if admin_items:
                sections.append("💊 **Medication Administrations:**\n" + "\n".join(admin_items))
        
        # Medication Dispenses
        if med_dispenses:
            dispense_items = []
            for med in med_dispenses:
                coding = med.get('medicationCodeableConcept', {}).get('coding', [{}])[0]
                name = med.get('medicationCodeableConcept', {}).get('text') or coding.get('display') or coding.get('code', 'Unknown')
                status = med.get('status', '')
                date = med.get('whenHandedOver', '')
                
                # Skip if no meaningful name
                if not name or name == 'Unknown' or len(name) < 3:
                    continue
                
                med_text = f"• {name}"
                if status and status != 'unknown':
                    med_text += f" ({status})"
                if date:
                    try:
                        date_obj = datetime.fromisoformat(date.replace('Z', '+00:00'))
                        formatted_date = date_obj.strftime('%m/%d/%Y')
                        med_text += f" - {formatted_date}"
                    except:
                        med_text += f" - {date}"
                
                dispense_items.append(med_text)
            
            if dispense_items:
                sections.append("🏥 **Medication Dispenses:**\n" + "\n".join(dispense_items))
        
        if not sections:
            return "No medications found"
        
        return "\n".join(sections)
    
    def _format_observation_list(self, observations: List[Dict]) -> str:
        """Format observation list for display"""
        if not observations:
            return "No observations found"
        
        formatted = []
        for obs in observations:
            # Extract observation name from code
            code = obs.get('code', {})
            name = code.get('text') or (code.get('coding', [{}])[0].get('display') if code.get('coding') else 'Unknown observation')
            value = obs.get('valueQuantity', {}).get('value') if obs.get('valueQuantity') else obs.get('valueString', 'No value')
            unit = obs.get('valueQuantity', {}).get('unit', '') if obs.get('valueQuantity') else ''
            date = obs.get('effectiveDateTime', '')
            status = obs.get('status', '')
            
            # Skip if no meaningful name
            if not name or name == 'Unknown observation' or len(name) < 3:
                continue
            
            obs_text = f"• {name}"
            if value and value != 'No value':
                obs_text += f": {value}"
                if unit:
                    obs_text += f" {unit}"
            if status and status != 'unknown':
                obs_text += f" ({status})"
            if date:
                try:
                    date_obj = datetime.fromisoformat(date.replace('Z', '+00:00'))
                    formatted_date = date_obj.strftime('%m/%d/%Y')
                    obs_text += f" - {formatted_date}"
                except:
                    obs_text += f" - {date}"
            
            formatted.append(obs_text)
        
        return "\n".join(formatted)
    
    def _format_encounter_list(self, encounters: List[Dict]) -> str:
        """Format encounter list for display"""
        if not encounters:
            return "No encounters found"
        
        formatted = []
        for enc in encounters:
            # Extract encounter type
            type_coding = enc.get('type', [{}])[0].get('coding', [{}])[0] if enc.get('type') else {}
            name = type_coding.get('display') or 'Unknown encounter type'
            status = enc.get('status', '')
            date = enc.get('period', {}).get('start', '')
            
            enc_text = f"• {name}"
            if status:
                enc_text += f" ({status})"
            if date:
                try:
                    date_obj = datetime.fromisoformat(date.replace('Z', '+00:00'))
                    formatted_date = date_obj.strftime('%m/%d/%Y')
                    enc_text += f" - {formatted_date}"
                except:
                    enc_text += f" - {date}"
            
            formatted.append(enc_text)
        
        return "\n".join(formatted)
    
    def _format_procedure_list(self, procedures: List[Dict]) -> str:
        """Format procedure list for display"""
        if not procedures:
            return "No procedures found"
        
        formatted = []
        for proc in procedures:
            # Extract procedure name from code
            code = proc.get('code', {})
            name = code.get('text') or (code.get('coding', [{}])[0].get('display') if code.get('coding') else 'Unknown procedure')
            status = proc.get('status', '')
            date = proc.get('performedDateTime', '')
            
            proc_text = f"• {name}"
            if status:
                proc_text += f" ({status})"
            if date:
                try:
                    date_obj = datetime.fromisoformat(date.replace('Z', '+00:00'))
                    formatted_date = date_obj.strftime('%m/%d/%Y')
                    proc_text += f" - {formatted_date}"
                except:
                    proc_text += f" - {date}"
            
            formatted.append(proc_text)
        
        return "\n".join(formatted)
    
    def _format_specimen_list(self, specimens: List[Dict]) -> str:
        """Format specimen list for display"""
        if not specimens:
            return "No specimens found"
        
        formatted = []
        for spec in specimens:
            # Extract specimen type
            type_coding = spec.get('type', {}).get('coding', [{}])[0] if spec.get('type') else {}
            name = type_coding.get('display') or 'Unknown specimen type'
            status = spec.get('status', '')
            date = spec.get('collection', {}).get('collectedDateTime', '')
            
            spec_text = f"• {name}"
            if status:
                spec_text += f" ({status})"
            if date:
                try:
                    date_obj = datetime.fromisoformat(date.replace('Z', '+00:00'))
                    formatted_date = date_obj.strftime('%m/%d/%Y')
                    spec_text += f" - {formatted_date}"
                except:
                    spec_text += f" - {date}"
            
            formatted.append(spec_text)
        
        return "\n".join(formatted)
    
    def _format_condition_list(self, conditions: List[Dict]) -> str:
        """Format condition list for display"""
        if not conditions:
            return "No conditions found"
        
        # Process all conditions (don't deduplicate - show timeline)
        valid_conditions = []
        
        for condition in conditions:
            # Extract condition name
            name = condition.get('name') or condition.get('condition_name', '')
            
            # If no name from regular fields, try to extract from FHIR code structure
            if not name:
                code = condition.get('code', {})
                if code:
                    coding = code.get('coding', [])
                    if coding:
                        name = coding[0].get('display') or coding[0].get('code', '')
                    else:
                        name = code.get('text', '')
            
            # Skip if no meaningful name
            if not name or name == 'Unknown condition' or len(name) < 3:
                continue
            
            # Skip non-medical entries like "And Family Support"
            if isinstance(name, str):
                if any(skip_word in name.lower() for skip_word in ['family support', 'and family', 'support']):
                    continue
                # Remove any JSON-like structures
                if '[[' in name or ']]' in name or '{' in name:
                    continue
                # Clean up the name
                name = name.strip()
                if len(name) < 3:  # Skip very short names
                    continue
                
                # Skip entries that are just fragments
                if name.endswith(')') or name.endswith('___') or 'OMR' in name:
                    continue
            
            valid_conditions.append(condition)
        
        formatted = []
        for condition in valid_conditions:
            # Extract condition details (name already extracted and validated above)
            name = condition.get('name') or condition.get('condition_name', '')
            if not name:
                code = condition.get('code', {})
                if code:
                    coding = code.get('coding', [])
                    if coding:
                        name = coding[0].get('display') or coding[0].get('code', '')
                    else:
                        name = code.get('text', '')
            
            status = condition.get('status', '')
            date = condition.get('date') or condition.get('chart_time', '')
            category = condition.get('category', '')
            
            condition_text = f"• {name}"
            if status and status != 'unknown':
                condition_text += f" ({status})"
            
            # Handle category properly (avoid raw JSON)
            if category:
                if isinstance(category, list) and len(category) > 0:
                    # Extract category from FHIR structure
                    cat_coding = category[0].get('coding', [])
                    if cat_coding:
                        cat_display = cat_coding[0].get('display', '')
                        if cat_display and cat_display not in ['Encounter Diagnosis', 'medical-history']:
                            condition_text += f" [{cat_display}]"
                elif isinstance(category, str) and category not in ['medical-history', 'encounter-diagnosis']:
                    condition_text += f" [{category}]"
            
            # Add encounter information if available
            encounter = condition.get('encounter', {})
            if encounter and isinstance(encounter, dict) and encounter.get('reference'):
                encounter_id = encounter['reference'].split('/')[-1]
                condition_text += f" [Encounter: {encounter_id[:8]}...]"
            
            if date:
                try:
                    # Format the date nicely
                    date_obj = datetime.fromisoformat(date.replace('Z', '+00:00'))
                    formatted_date = date_obj.strftime('%m/%d/%Y')
                    condition_text += f" - {formatted_date}"
                except:
                    condition_text += f" - {date}"
            
            formatted.append(condition_text)
        
        return "\n".join(formatted)
    
    def _format_pmh_list(self, pmh_conditions: List[Dict]) -> str:
        """Format PMH list for display"""
        if not pmh_conditions:
            return "No PMH found"
        
        formatted = []
        for condition in pmh_conditions:
            name = condition.get('condition_name', 'Unknown condition')
            category = condition.get('category', '')
            chart_time = condition.get('chart_time', '')
            
            # Skip non-medical entries
            if not name or len(name) < 3 or 'family support' in name.lower():
                continue
            
            pmh_text = f"• {name}"
            if category and category != 'medical-history':
                pmh_text += f" [{category}]"
            
            if chart_time:
                try:
                    # Format the date nicely
                    date_obj = datetime.fromisoformat(chart_time.replace('Z', '+00:00'))
                    formatted_date = date_obj.strftime('%m/%d/%Y')
                    pmh_text += f" - {formatted_date}"
                except:
                    pmh_text += f" - {chart_time}"
            
            formatted.append(pmh_text)
        
        if not formatted:
            return "No specific PMH conditions found"
        
        return "\n".join(formatted)
    
    def _format_allergy_list(self, allergies: List[Dict]) -> str:
        """Format allergy list for display"""
        if not allergies:
            return "No allergies found"
        
        formatted = []
        for allergy in allergies:
            name = allergy.get('name') or allergy.get('allergy_name', 'Unknown allergy')
            severity = allergy.get('severity', '')
            reaction = allergy.get('reaction', '')
            
            # Skip unknown or empty allergies
            if not name or name == 'Unknown allergy' or len(name) < 3:
                continue
            
            allergy_text = f"• {name}"
            if severity and severity != 'unknown':
                allergy_text += f" ({severity})"
            if reaction:
                allergy_text += f" - {reaction}"
            
            formatted.append(allergy_text)
        
        if not formatted:
            return "No specific allergies found"
        
        return "\n".join(formatted)
    
    def _get_medication_additional_info(self, medications: List[Dict], evidence: Dict[str, Any]) -> str:
        """Get additional medication information"""
        info = []
        
        if evidence.get('drug_info'):
            info.append("📊 Drug information available from RxNorm database")
        
        if evidence.get('interactions'):
            info.append("⚠️ Drug interaction analysis completed")
        
        return "\n".join(info) if info else ""
    
    def _get_condition_additional_info(self, conditions: List[Dict], evidence: Dict[str, Any]) -> str:
        """Get additional condition information"""
        info = []
        
        if evidence.get('clinical_evidence'):
            info.append("📚 Clinical evidence available for treatment options")
        
        return "\n".join(info) if info else ""
    
    def _get_pmh_additional_info(self, pmh_conditions: List[Dict], evidence: Dict[str, Any]) -> str:
        """Get additional PMH information"""
        info = []
        
        if evidence.get('clinical_evidence'):
            info.append("📚 Clinical evidence available for PMH conditions")
        
        return "\n".join(info) if info else ""
    
    def _get_allergy_additional_info(self, allergies: List[Dict], evidence: Dict[str, Any]) -> str:
        """Get additional allergy information"""
        info = []
        
        if evidence.get('interactions'):
            info.append("⚠️ Allergy contraindication analysis completed")
        
        return "\n".join(info) if info else ""
    
    def _get_observation_additional_info(self, observations: List[Dict], evidence: Dict[str, Any]) -> str:
        """Get additional observation information"""
        info = []
        
        if len(observations) > 10:
            info.append(f"📊 Total observations: {len(observations)}")
        
        return "\n".join(info) if info else ""
    
    def _get_encounter_additional_info(self, encounters: List[Dict], evidence: Dict[str, Any]) -> str:
        """Get additional encounter information"""
        info = []
        
        if len(encounters) > 5:
            info.append(f"🏥 Total encounters: {len(encounters)}")
        
        return "\n".join(info) if info else ""
    
    def _get_procedure_additional_info(self, procedures: List[Dict], evidence: Dict[str, Any]) -> str:
        """Get additional procedure information"""
        info = []
        
        if len(procedures) > 5:
            info.append(f"🔬 Total procedures: {len(procedures)}")
        
        return "\n".join(info) if info else ""
    
    def _get_specimen_additional_info(self, specimens: List[Dict], evidence: Dict[str, Any]) -> str:
        """Get additional specimen information"""
        info = []
        
        if len(specimens) > 5:
            info.append(f"🧪 Total specimens: {len(specimens)}")
        
        return "\n".join(info) if info else ""
    
    def _format_interaction_list(self, interactions: List[Dict]) -> str:
        """Format interaction list for display"""
        if not interactions:
            return "No interactions found"
        
        formatted = []
        for interaction in interactions:
            drugs = interaction.get('drugs', [])
            severity = interaction.get('severity', 'Unknown')
            description = interaction.get('description', '')
            
            interaction_text = f"• {' + '.join(drugs)} ({severity})"
            if description:
                interaction_text += f": {description}"
            
            formatted.append(interaction_text)
        
        return "\n".join(formatted)
    
    def _get_interaction_recommendations(self, interactions: List[Dict]) -> str:
        """Get interaction recommendations"""
        return "• Monitor for signs of interaction\n• Consider alternative medications\n• Document any adverse effects"
    
    def _format_evidence_list(self, evidence: List[Dict]) -> str:
        """Format evidence list for display"""
        if not evidence:
            return "No evidence found"
        
        formatted = []
        for item in evidence[:3]:  # Limit to 3 items
            title = item.get('title', 'Unknown')
            level = item.get('evidence_level', 'Unknown')
            formatted.append(f"• {title} (Level: {level})")
        
        return "\n".join(formatted)
    
    def _get_evidence_recommendations(self, evidence: List[Dict]) -> str:
        """Get evidence-based recommendations"""
        return "• Consider the latest clinical guidelines\n• Individualize treatment based on patient factors"
    
    def _format_alert_list(self, alerts: List[Dict]) -> str:
        """Format alert list for display"""
        if not alerts:
            return "No alerts found"
        
        formatted = []
        for alert in alerts:
            type_alert = alert.get('type', 'Unknown')
            message = alert.get('message', '')
            severity = alert.get('severity', 'Unknown')
            
            alert_text = f"• {type_alert} ({severity})"
            if message:
                alert_text += f": {message}"
            
            formatted.append(alert_text)
        
        return "\n".join(formatted)
    
    def _get_alert_recommendations(self, alerts: List[Dict]) -> str:
        """Get alert recommendations"""
        return "• Review alerts immediately\n• Take appropriate clinical action\n• Document response to alerts"
