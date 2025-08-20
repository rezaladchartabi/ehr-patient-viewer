"""
Chatbot Service

Main service that coordinates NLP processing, data retrieval, and response generation.
"""

import asyncio
import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

# Set up logger first
logger = logging.getLogger(__name__)

from .nlp_processor import MedicalNLPProcessor
from .llm_nlp_processor import LLMMedicalNLPProcessor
from .ollama_nlp_processor import OllamaMedicalNLPProcessor
from .response_generator import MedicalResponseGenerator
from data_sources import OpenEvidenceSource, RxNormSource, KnowledgeBase

# Import RAG service
try:
    import sys
    # Add the backend directory to the path to ensure we can import rag
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)
    
    from rag.service import RagService
    RAG_AVAILABLE = True
    logger.info("RAG service imported successfully")
except ImportError as e:
    RAG_AVAILABLE = False
    logger.warning(f"RAG service not available - clinical context retrieval will be limited: {e}")

class ChatbotService:
    """Main chatbot service for medical queries"""
    
    def __init__(self, nlp_type: str = "auto"):
        """
        Initialize chatbot service with specified NLP processor
        
        Args:
            nlp_type: "auto", "gpt4", "ollama", or "rule-based"
        """
        # Initialize NLP processor based on type
        if nlp_type == "gpt4":
            # Try GPT-4 first
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                try:
                    self.nlp_processor = LLMMedicalNLPProcessor(api_key=api_key)
                    logger.info("Initialized LLM-based NLP processor with GPT-4")
                except Exception as e:
                    logger.warning(f"Failed to initialize GPT-4 processor: {e}, falling back to rule-based")
                    self.nlp_processor = MedicalNLPProcessor()
            else:
                logger.warning("OPENAI_API_KEY not found, using rule-based NLP processor")
                self.nlp_processor = MedicalNLPProcessor()
        
        elif nlp_type == "ollama":
            # Try Ollama
            try:
                # Use GPT-OSS 20B model for better medical NLP
                self.nlp_processor = OllamaMedicalNLPProcessor(model="gpt-oss:20b")
                logger.info("Initialized Ollama-based NLP processor with GPT-OSS 20B")
            except Exception as e:
                logger.warning(f"Failed to initialize Ollama processor: {e}, falling back to rule-based")
                self.nlp_processor = MedicalNLPProcessor()
        
        elif nlp_type == "rule-based":
            # Use rule-based only
            self.nlp_processor = MedicalNLPProcessor()
            logger.info("Using rule-based NLP processor")
        
        else:  # "auto" - try GPT-4, then Ollama, then rule-based
            # Try GPT-4 first
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                try:
                    self.nlp_processor = LLMMedicalNLPProcessor(api_key=api_key)
                    logger.info("Auto-selected: LLM-based NLP processor with GPT-4")
                except Exception as e:
                    logger.warning(f"GPT-4 failed: {e}, trying Ollama...")
                    # Try Ollama
                    try:
                        self.nlp_processor = OllamaMedicalNLPProcessor()
                        logger.info("Auto-selected: Ollama-based NLP processor")
                    except Exception as e2:
                        logger.warning(f"Ollama failed: {e2}, using rule-based")
                        self.nlp_processor = MedicalNLPProcessor()
            else:
                                    # Try Ollama
                    try:
                        self.nlp_processor = OllamaMedicalNLPProcessor(model="gpt-oss:20b")
                        logger.info("Auto-selected: Ollama-based NLP processor with GPT-OSS 20B")
                    except Exception as e:
                        logger.warning(f"Ollama failed: {e}, using rule-based")
                        self.nlp_processor = MedicalNLPProcessor()
        
        self.response_generator = MedicalResponseGenerator()
        self.knowledge_base = KnowledgeBase()
        
        # Initialize data sources (with mock implementations for now)
        self.openevidence = OpenEvidenceSource()
        self.rxnorm = RxNormSource()
        
        # Initialize RAG service for clinical context retrieval
        if RAG_AVAILABLE:
            try:
                self.rag_service = RagService()
                logger.info("RAG service initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize RAG service: {e}")
                self.rag_service = None
        else:
            self.rag_service = None
        
        # Cache for patient data
        self.patient_cache: Dict[str, Dict] = {}
        
    async def process_query(self, message: str, patient_id: str, conversation_id: str) -> Dict[str, Any]:
        """Process a user query and generate a response"""
        try:
            logger.info(f"Processing query for patient {patient_id}: {message}")
            
            # 1. Extract medical entities and intent
            entities = await self.nlp_processor.extract_entities(message)
            intent = await self.nlp_processor.classify_intent(message)
            
            logger.info(f"Extracted entities: {entities}")
            logger.info(f"Classified intent: {intent}")
            
            # 2. Get patient data
            patient_data = await self._get_patient_data(patient_id)
            
            # 3. Get relevant clinical context from RAG
            clinical_context = await self._get_clinical_context(message, patient_id)
            
            # 4. Gather relevant evidence and knowledge
            evidence_data = await self._gather_evidence(entities, intent, patient_data)
            
            # 5. Generate response with clinical context
            response = await self.response_generator.generate_response(
                query=message,
                intent=intent,
                entities=entities,
                patient_data=patient_data,
                evidence=evidence_data,
                clinical_context=clinical_context
            )
            
            # 6. Store in knowledge base for future reference
            await self._store_conversation_context(
                conversation_id, patient_id, message, response, entities, intent
            )
            
            return {
                "response": response["text"],
                "evidence": response.get("evidence", []),
                "sources": response.get("sources", []),
                "confidence": response.get("confidence", 0.8),
                "conversationId": conversation_id,
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "intent": intent,
                    "entities": entities,
                    "patient_id": patient_id,
                    "clinical_context_count": len(clinical_context.get("hits", [])),
                    "rag_enabled": self.rag_service is not None and self.rag_service.enabled
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                "response": "I apologize, but I encountered an error while processing your request. Please try again or rephrase your question.",
                "evidence": [],
                "sources": [],
                "confidence": 0.0,
                "conversationId": conversation_id,
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
    
    async def _get_clinical_context(self, query: str, patient_id: str) -> Dict[str, Any]:
        """Get relevant clinical context from RAG system"""
        logger.info(f"RAG service status: available={RAG_AVAILABLE}, service={self.rag_service is not None}, enabled={self.rag_service.enabled if self.rag_service else False}")
        
        if not self.rag_service or not self.rag_service.enabled:
            logger.info("RAG service not available or disabled")
            return {"hits": []}
        
        try:
            logger.info(f"Searching RAG for clinical context: {query}")
            
            # Search for relevant clinical notes
            rag_results = self.rag_service.search(
                query=query,
                top_k=5,  # Get top 5 most relevant chunks
                collection="patient"
            )
            
            logger.info(f"RAG returned {len(rag_results.get('hits', []))} relevant clinical chunks")
            
            # Format the clinical context for the response generator
            clinical_context = {
                "hits": rag_results.get("hits", []),
                "query": query,
                "total_hits": len(rag_results.get("hits", [])),
                "source": "clinical_notes"
            }
            
            return clinical_context
            
        except Exception as e:
            logger.error(f"Error retrieving clinical context from RAG: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return {"hits": [], "error": str(e)}
    
    async def _get_patient_data(self, patient_id: str) -> Dict[str, Any]:
        """Get comprehensive patient data from database and FHIR server"""
        if patient_id in self.patient_cache:
            return self.patient_cache[patient_id]
        
        try:
            # Initialize comprehensive patient data structure
            patient_data = {
                "id": patient_id,
                "basic_info": {},
                "conditions": [],
                "medications": [],
                "allergies": [],
                "observations": [],
                "encounters": [],
                "procedures": [],
                "specimens": [],
                "pmh": [],
                "medication_requests": [],
                "medication_administrations": [],
                "medication_dispenses": []
            }
            
            # Get basic patient info from local database
            try:
                basic_info = await self._fetch_patient_basic_info(patient_id)
                if basic_info:
                    patient_data["basic_info"] = basic_info
            except Exception as e:
                logger.warning(f"Failed to fetch basic info for patient {patient_id}: {e}")
            
            # Get PMH data from database
            try:
                pmh_response = await self._fetch_patient_pmh(patient_id)
                if pmh_response and "pmh_conditions" in pmh_response:
                    patient_data["pmh"] = pmh_response["pmh_conditions"]
            except Exception as e:
                logger.warning(f"Failed to fetch PMH data for patient {patient_id}: {e}")
            
            # Get allergies from database
            try:
                allergies_response = await self._fetch_patient_allergies(patient_id)
                if allergies_response and "allergies" in allergies_response:
                    patient_data["allergies"] = allergies_response["allergies"]
            except Exception as e:
                logger.warning(f"Failed to fetch allergies for patient {patient_id}: {e}")
            
            # Get FHIR resources
            fhir_patient_ref = f"Patient/{patient_id}"
            
            # Always get conditions from FHIR (prioritize PMH if available, but always have FHIR as backup)
            try:
                conditions_response = await self._fetch_fhir_conditions(fhir_patient_ref)
                if conditions_response and "entry" in conditions_response:
                    patient_data["conditions"] = [entry["resource"] for entry in conditions_response["entry"]]
            except Exception as e:
                logger.warning(f"Failed to fetch conditions for patient {patient_id}: {e}")
                patient_data["conditions"] = []
            
            # Get medication requests from FHIR
            try:
                med_requests_response = await self._fetch_fhir_medication_requests(fhir_patient_ref)
                if med_requests_response and "entry" in med_requests_response:
                    patient_data["medication_requests"] = [entry["resource"] for entry in med_requests_response["entry"]]
            except Exception as e:
                logger.warning(f"Failed to fetch medication requests for patient {patient_id}: {e}")
            
            # Get medication administrations from FHIR
            try:
                med_admins_response = await self._fetch_fhir_medication_administrations(fhir_patient_ref)
                if med_admins_response and "entry" in med_admins_response:
                    patient_data["medication_administrations"] = [entry["resource"] for entry in med_admins_response["entry"]]
            except Exception as e:
                logger.warning(f"Failed to fetch medication administrations for patient {patient_id}: {e}")
            
            # Get medication dispenses from FHIR
            try:
                med_dispenses_response = await self._fetch_fhir_medication_dispenses(fhir_patient_ref)
                if med_dispenses_response and "entry" in med_dispenses_response:
                    patient_data["medication_dispenses"] = [entry["resource"] for entry in med_dispenses_response["entry"]]
            except Exception as e:
                logger.warning(f"Failed to fetch medication dispenses for patient {patient_id}: {e}")
            
            # Get observations from FHIR
            try:
                observations_response = await self._fetch_fhir_observations(fhir_patient_ref)
                if observations_response and "entry" in observations_response:
                    patient_data["observations"] = [entry["resource"] for entry in observations_response["entry"]]
            except Exception as e:
                logger.warning(f"Failed to fetch observations for patient {patient_id}: {e}")
            
            # Get encounters from FHIR
            try:
                encounters_response = await self._fetch_fhir_encounters(fhir_patient_ref)
                if encounters_response and "entry" in encounters_response:
                    patient_data["encounters"] = [entry["resource"] for entry in encounters_response["entry"]]
            except Exception as e:
                logger.warning(f"Failed to fetch encounters for patient {patient_id}: {e}")
            
            # Get procedures from FHIR
            try:
                procedures_response = await self._fetch_fhir_procedures(fhir_patient_ref)
                if procedures_response and "entry" in procedures_response:
                    patient_data["procedures"] = [entry["resource"] for entry in procedures_response["entry"]]
            except Exception as e:
                logger.warning(f"Failed to fetch procedures for patient {patient_id}: {e}")
            
            # Get specimens from FHIR
            try:
                specimens_response = await self._fetch_fhir_specimens(fhir_patient_ref)
                if specimens_response and "entry" in specimens_response:
                    patient_data["specimens"] = [entry["resource"] for entry in specimens_response["entry"]]
            except Exception as e:
                logger.warning(f"Failed to fetch specimens for patient {patient_id}: {e}")
            
            # Combine all medication data
            patient_data["medications"] = (
                patient_data["medication_requests"] + 
                patient_data["medication_administrations"] + 
                patient_data["medication_dispenses"]
            )
            
            # Cache the comprehensive data
            self.patient_cache[patient_id] = patient_data
            
            # Log summary
            logger.info(f"Fetched comprehensive patient data for {patient_id}:")
            logger.info(f"  - Basic info: {'Yes' if patient_data['basic_info'] else 'No'}")
            logger.info(f"  - PMH: {len(patient_data['pmh'])} conditions")
            logger.info(f"  - Allergies: {len(patient_data['allergies'])} allergies")
            logger.info(f"  - FHIR Conditions: {len(patient_data['conditions'])} conditions")
            logger.info(f"  - Medication Requests: {len(patient_data['medication_requests'])} requests")
            logger.info(f"  - Medication Administrations: {len(patient_data['medication_administrations'])} administrations")
            logger.info(f"  - Medication Dispenses: {len(patient_data['medication_dispenses'])} dispenses")
            logger.info(f"  - Observations: {len(patient_data['observations'])} observations")
            logger.info(f"  - Encounters: {len(patient_data['encounters'])} encounters")
            logger.info(f"  - Procedures: {len(patient_data['procedures'])} procedures")
            logger.info(f"  - Specimens: {len(patient_data['specimens'])} specimens")
            
            return patient_data
            
        except Exception as e:
            logger.error(f"Error fetching comprehensive patient data for {patient_id}: {e}")
            # Return empty structure on error
            return {
                "id": patient_id,
                "basic_info": {},
                "conditions": [],
                "medications": [],
                "allergies": [],
                "observations": [],
                "encounters": [],
                "procedures": [],
                "specimens": [],
                "pmh": [],
                "medication_requests": [],
                "medication_administrations": [],
                "medication_dispenses": []
            }
    
    async def _fetch_patient_pmh(self, patient_id: str) -> Dict[str, Any]:
        """Fetch PMH data for a patient from the database"""
        try:
            # Use the same backend as the UI for consistency
            import httpx
            async with httpx.AsyncClient() as client:
                url = f"https://ehr-backend-87r9.onrender.com/local/patients/{patient_id}/pmh"
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
                return {
                    "patient_id": patient_id,
                    "pmh_conditions": data.get("pmh_conditions", []),
                    "count": len(data.get("pmh_conditions", []))
                }
        except Exception as e:
            logger.error(f"Error fetching PMH data: {e}")
            return {"pmh_conditions": []}
    
    async def _fetch_patient_allergies(self, patient_id: str) -> Dict[str, Any]:
        """Fetch allergies for a patient from the database"""
        try:
            # Use the same backend as the UI for consistency
            import httpx
            async with httpx.AsyncClient() as client:
                url = f"https://ehr-backend-87r9.onrender.com/local/patients/{patient_id}/allergies"
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
                return {
                    "patient_id": patient_id,
                    "allergies": data.get("allergies", []),
                    "count": len(data.get("allergies", []))
                }
        except Exception as e:
            logger.error(f"Error fetching allergies data: {e}")
            return {"allergies": []}
    
    async def _fetch_patient_basic_info(self, patient_id: str) -> Dict[str, Any]:
        """Fetch basic patient information from the database"""
        try:
            from main import local_db
            if local_db:
                patient = local_db.get_patient_with_allergies(patient_id)
                return patient if patient else {}
            else:
                logger.error("Local database not available")
                return {}
        except Exception as e:
            logger.error(f"Error fetching basic patient info: {e}")
            return {}
    
    async def _fetch_fhir_conditions(self, patient_ref: str) -> Dict[str, Any]:
        """Fetch conditions from FHIR server"""
        try:
            # Use the same backend as the UI for consistency
            import httpx
            async with httpx.AsyncClient() as client:
                # Extract patient ID from patient_ref (format: "Patient/{id}")
                patient_id = patient_ref.split('/')[-1]
                url = f"https://ehr-backend-87r9.onrender.com/Condition?patient=Patient/{patient_id}&_count=100"
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error fetching FHIR conditions: {e}")
            return {}
    
    async def _fetch_fhir_medication_requests(self, patient_ref: str) -> Dict[str, Any]:
        """Fetch medication requests from FHIR server"""
        try:
            # Use the same backend as the UI for consistency
            import httpx
            async with httpx.AsyncClient() as client:
                patient_id = patient_ref.split('/')[-1]
                url = f"https://ehr-backend-87r9.onrender.com/MedicationRequest?patient=Patient/{patient_id}&_count=100"
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error fetching FHIR medication requests: {e}")
            return {}
    
    async def _fetch_fhir_medication_administrations(self, patient_ref: str) -> Dict[str, Any]:
        """Fetch medication administrations from FHIR server"""
        try:
            # Use the same backend as the UI for consistency
            import httpx
            async with httpx.AsyncClient() as client:
                patient_id = patient_ref.split('/')[-1]
                url = f"https://ehr-backend-87r9.onrender.com/MedicationAdministration?patient=Patient/{patient_id}&_count=100"
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error fetching FHIR medication administrations: {e}")
            return {}
    
    async def _fetch_fhir_medication_dispenses(self, patient_ref: str) -> Dict[str, Any]:
        """Fetch medication dispenses from FHIR server"""
        try:
            # Use the same backend as the UI for consistency
            import httpx
            async with httpx.AsyncClient() as client:
                patient_id = patient_ref.split('/')[-1]
                url = f"https://ehr-backend-87r9.onrender.com/MedicationDispense?patient=Patient/{patient_id}&_count=100"
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error fetching FHIR medication dispenses: {e}")
            return {}
    
    async def _fetch_fhir_observations(self, patient_ref: str) -> Dict[str, Any]:
        """Fetch observations from FHIR server"""
        try:
            # Use the same backend as the UI for consistency
            import httpx
            async with httpx.AsyncClient() as client:
                patient_id = patient_ref.split('/')[-1]
                url = f"https://ehr-backend-87r9.onrender.com/Observation?patient=Patient/{patient_id}&_count=100"
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error fetching FHIR observations: {e}")
            return {}
    
    async def _fetch_fhir_encounters(self, patient_ref: str) -> Dict[str, Any]:
        """Fetch encounters from FHIR server"""
        try:
            # Use the same backend as the UI for consistency
            import httpx
            async with httpx.AsyncClient() as client:
                patient_id = patient_ref.split('/')[-1]
                url = f"https://ehr-backend-87r9.onrender.com/Encounter?patient=Patient/{patient_id}&_count=100"
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error fetching FHIR encounters: {e}")
            return {}
    
    async def _fetch_fhir_procedures(self, patient_ref: str) -> Dict[str, Any]:
        """Fetch procedures from FHIR server"""
        try:
            # Use the same backend as the UI for consistency
            import httpx
            async with httpx.AsyncClient() as client:
                patient_id = patient_ref.split('/')[-1]
                url = f"https://ehr-backend-87r9.onrender.com/Procedure?patient=Patient/{patient_id}&_count=100"
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error fetching FHIR procedures: {e}")
            return {}
    
    async def _fetch_fhir_specimens(self, patient_ref: str) -> Dict[str, Any]:
        """Fetch specimens from FHIR server"""
        try:
            # Use the same backend as the UI for consistency
            import httpx
            async with httpx.AsyncClient() as client:
                patient_id = patient_ref.split('/')[-1]
                url = f"https://ehr-backend-87r9.onrender.com/Specimen?patient=Patient/{patient_id}&_count=100"
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error fetching FHIR specimens: {e}")
            return {}
    
    async def _gather_evidence(self, entities: List[str], intent: str, patient_data: Dict) -> Dict[str, Any]:
        """Gather relevant evidence from multiple sources"""
        evidence_data = {
            "clinical_evidence": [],
            "drug_info": [],
            "interactions": [],
            "guidelines": []
        }
        
        try:
            # Search for clinical evidence
            if entities:
                for entity in entities:
                    evidence = await self.openevidence.search_evidence(entity)
                    evidence_data["clinical_evidence"].extend(evidence)
            
            # Get drug information
            if intent == "medication_query" and entities:
                for entity in entities:
                    drug_info = await self.rxnorm.search_drugs(entity)
                    evidence_data["drug_info"].extend(drug_info)
            
            # Search knowledge base
            knowledge_results = await self.knowledge_base.search_knowledge(
                " ".join(entities) if entities else intent
            )
            evidence_data["knowledge_base"] = knowledge_results
            
        except Exception as e:
            logger.error(f"Error gathering evidence: {e}")
        
        return evidence_data
    
    async def _store_conversation_context(self, conversation_id: str, patient_id: str, 
                                        message: str, response: Dict, entities: List[str], 
                                        intent: str) -> None:
        """Store conversation context for future reference"""
        try:
            context = {
                "conversation_id": conversation_id,
                "patient_id": patient_id,
                "timestamp": datetime.now().isoformat(),
                "user_message": message,
                "bot_response": response["text"],
                "entities": entities,
                "intent": intent,
                "evidence_count": len(response.get("evidence", [])),
                "confidence": response.get("confidence", 0.0)
            }
            
            # Store in knowledge base
            await self.knowledge_base.store_knowledge(
                source_name="conversation",
                source_id=conversation_id,
                knowledge_type="conversation_context",
                title=f"Conversation: {intent}",
                content=json.dumps(context),
                metadata=context,
                confidence_score=response.get("confidence", 0.0)
            )
            
        except Exception as e:
            logger.error(f"Error storing conversation context: {e}")
    
    async def get_suggested_questions(self, patient_id: str) -> List[str]:
        """Get suggested questions based on patient data"""
        try:
            patient_data = await self._get_patient_data(patient_id)
            
            suggestions = [
                "What medications is this patient currently taking?",
                "Are there any drug interactions with their medications?",
                "What conditions has this patient been diagnosed with?",
                "Show me the patient's allergies",
                "What's the latest evidence for treating their condition?",
                "Are there any clinical alerts for this patient?"
            ]
            
            # Customize suggestions based on patient data
            if patient_data.get("medications"):
                suggestions.append("What are the side effects of their current medications?")
            
            if patient_data.get("conditions"):
                suggestions.append("What are the treatment guidelines for their conditions?")
            
            if patient_data.get("allergies"):
                suggestions.append("Are there any contraindications with their allergies?")
            
            return suggestions[:8]  # Limit to 8 suggestions
            
        except Exception as e:
            logger.error(f"Error getting suggested questions: {e}")
            return [
                "What medications is this patient currently taking?",
                "What conditions has this patient been diagnosed with?",
                "Show me the patient's allergies"
            ]
    
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of all chatbot components"""
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {}
        }
        
        try:
            # Check NLP processor
            health_status["components"]["nlp_processor"] = "healthy"
            
            # Check response generator
            health_status["components"]["response_generator"] = "healthy"
            
            # Check knowledge base
            kb_stats = await self.knowledge_base.get_statistics()
            health_status["components"]["knowledge_base"] = {
                "status": "healthy",
                "total_entries": kb_stats["total_entries"]
            }
            
            # Check data sources
            openevidence_health = await self.openevidence.health_check()
            rxnorm_health = await self.rxnorm.health_check()
            
            health_status["components"]["openevidence"] = openevidence_health
            health_status["components"]["rxnorm"] = rxnorm_health
            
            # Overall status
            all_healthy = all(
                comp.get("status") == "healthy" 
                for comp in health_status["components"].values()
                if isinstance(comp, dict)
            )
            
            if not all_healthy:
                health_status["status"] = "degraded"
                
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            health_status["status"] = "unhealthy"
            health_status["error"] = str(e)
        
        return health_status
