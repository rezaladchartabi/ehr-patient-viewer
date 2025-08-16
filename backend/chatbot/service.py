"""
Chatbot Service

Main service that coordinates NLP processing, data retrieval, and response generation.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

from .nlp_processor import MedicalNLPProcessor
from .response_generator import MedicalResponseGenerator
from data_sources import OpenEvidenceSource, RxNormSource, KnowledgeBase

logger = logging.getLogger(__name__)

class ChatbotService:
    """Main chatbot service for medical queries"""
    
    def __init__(self):
        self.nlp_processor = MedicalNLPProcessor()
        self.response_generator = MedicalResponseGenerator()
        self.knowledge_base = KnowledgeBase()
        
        # Initialize data sources (with mock implementations for now)
        self.openevidence = OpenEvidenceSource()
        self.rxnorm = RxNormSource()
        
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
            
            # 3. Gather relevant evidence and knowledge
            evidence_data = await self._gather_evidence(entities, intent, patient_data)
            
            # 4. Generate response
            response = await self.response_generator.generate_response(
                query=message,
                intent=intent,
                entities=entities,
                patient_data=patient_data,
                evidence=evidence_data
            )
            
            # 5. Store in knowledge base for future reference
            await self._store_conversation_context(
                conversation_id, patient_id, message, response, entities, intent
            )
            
            return {
                "response": response["text"],
                "evidence": response.get("evidence", []),
                "sources": response.get("sources", []),
                "confidence": response.get("confidence", 0.8),
                "conversation_id": conversation_id,
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "intent": intent,
                    "entities": entities,
                    "patient_id": patient_id
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                "response": "I apologize, but I encountered an error while processing your request. Please try again or rephrase your question.",
                "evidence": [],
                "sources": [],
                "confidence": 0.0,
                "conversation_id": conversation_id,
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
    
    async def _get_patient_data(self, patient_id: str) -> Dict[str, Any]:
        """Get comprehensive patient data"""
        if patient_id in self.patient_cache:
            return self.patient_cache[patient_id]
        
        # This would integrate with your existing patient data endpoints
        # For now, return a mock structure
        patient_data = {
            "id": patient_id,
            "conditions": [],
            "medications": [],
            "allergies": [],
            "observations": [],
            "encounters": []
        }
        
        # Cache the data
        self.patient_cache[patient_id] = patient_data
        return patient_data
    
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
