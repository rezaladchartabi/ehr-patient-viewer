"""
Ollama-based Medical NLP Processor

Natural language processing for medical queries using local LLMs via Ollama.
No API keys required - runs completely locally.
"""

import re
import logging
import json
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import httpx
from .prompt_manager import PromptManager

logger = logging.getLogger(__name__)

class OllamaMedicalNLPProcessor:
    """Ollama-based NLP processor for medical queries using local LLMs"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama2"):
        self.base_url = base_url
        self.model = model
        self.client = httpx.AsyncClient(timeout=30.0)
        
        # Initialize PromptManager for intent-specific prompts
        try:
            self.prompt_manager = PromptManager()
            logger.info("PromptManager initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize PromptManager: {e}")
            self.prompt_manager = None
        
        # Intent categories for medical queries
        self.intent_categories = [
            'medication_query',
            'pmh_query',
            'condition_query', 
            'observation_query',
            'encounter_query',
            'procedure_query',
            'specimen_query',
            'allergy_query',
            'interaction_query',
            'evidence_query',
            'alert_query',
            'general_query'
        ]
        
        # Medical entity types
        self.entity_types = [
            'medication',
            'condition',
            'allergy',
            'procedure',
            'vital_sign',
            'lab_test',
            'symptom',
            'body_part',
            'medical_device'
        ]
    
    async def _call_ollama(self, prompt: str, system_prompt: str = None) -> str:
        """Make a call to Ollama API"""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9,
                    "max_tokens": 200
                }
            }
            
            if system_prompt:
                payload["system"] = system_prompt
            
            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "").strip()
            
        except Exception as e:
            logger.error(f"Error calling Ollama: {e}")
            raise
    
    async def extract_entities(self, text: str) -> List[str]:
        """Extract medical entities from text using local LLM"""
        try:
            system_prompt = "You are a medical entity extraction system. Return ONLY a JSON array of entity names, nothing else."
            
            prompt = f"""
Extract medical entities from this text and return ONLY a JSON array:

Text: "{text}"

Return format: ["entity1", "entity2", "entity3"]
"""

            response = await self._call_ollama(prompt, system_prompt)
            
            # Try to parse JSON response
            try:
                # Clean up the response to extract JSON
                json_start = response.find('[')
                json_end = response.rfind(']') + 1
                
                if json_start != -1 and json_end != 0:
                    json_str = response[json_start:json_end]
                    entities = json.loads(json_str)
                    
                    if isinstance(entities, list):
                        # Clean up entities
                        entities = [entity.strip() for entity in entities if entity.strip() and len(entity.strip()) > 2]
                        logger.info(f"Extracted entities: {entities}")
                        return entities
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse JSON response: {response}")
            
            # Fallback to regex extraction if JSON parsing fails
            return await self._fallback_entity_extraction(text)
            
        except Exception as e:
            logger.error(f"Error extracting entities with Ollama: {e}")
            return await self._fallback_entity_extraction(text)
    
    async def classify_intent(self, text: str) -> str:
        """Classify the intent of the query using local LLM with intent-specific prompts"""
        try:
            # Try to use intent-specific prompt if PromptManager is available
            if self.prompt_manager:
                # Use a generic prompt that includes all intents for classification
                # We'll use the PMH prompt as a template since it has all intents listed
                pmh_prompt = self.prompt_manager.get_intent_prompt('pmh_query')
                if pmh_prompt:
                    system_prompt = pmh_prompt['system_prompt']
                    user_prompt = pmh_prompt['user_prompt'].format(query=text)
                    
                    response = await self._call_ollama(user_prompt, system_prompt)
                    
                    # Clean up the response
                    intent = response.strip().lower()
                    
                    # Validate intent against all available intents
                    available_intents = self.prompt_manager.get_active_intents()
                    if intent in available_intents:
                        logger.info(f"Classified intent using PromptManager: {intent}")
                        return intent
                    else:
                        logger.warning(f"Invalid intent returned: {intent}, using general_query")
                        return "general_query"
            
            # Fallback to hardcoded prompt if PromptManager is not available
            system_prompt = "You are a medical intent classification system. Return ONLY the intent name, nothing else."
            
            prompt = f"""
Classify the intent of this medical query:

Available intents:
- medication_query: Questions about medications, drugs, prescriptions
- pmh_query: Questions about past medical history, PMH, medical history
- condition_query: Questions about medical conditions, diagnoses, diseases
- observation_query: Questions about vital signs, lab results, measurements, observations
- encounter_query: Questions about hospital visits, appointments, encounters
- procedure_query: Questions about medical procedures, surgeries, tests
- specimen_query: Questions about lab samples, specimens, collections
- allergy_query: Questions about allergies, allergic reactions
- interaction_query: Questions about drug interactions, contraindications
- evidence_query: Questions about clinical evidence, studies, guidelines
- alert_query: Questions about clinical alerts, warnings, risks
- general_query: General medical questions or unclear intent

Query: "{text}"

Return ONLY the intent name.
"""

            response = await self._call_ollama(prompt, system_prompt)
            
            # Clean up the response
            intent = response.strip().lower()
            
            # Validate intent
            if intent in self.intent_categories:
                logger.info(f"Classified intent using fallback: {intent}")
                return intent
            else:
                logger.warning(f"Invalid intent returned: {intent}, using general_query")
                return "general_query"
                
        except Exception as e:
            logger.error(f"Error classifying intent with Ollama: {e}")
            return await self._fallback_intent_classification(text)
    
    async def extract_patient_context(self, text: str) -> Dict[str, Any]:
        """Extract patient-specific context from query using local LLM"""
        try:
            system_prompt = "You are a medical context extraction system. Return ONLY a JSON object, nothing else."
            
            prompt = f"""
Extract context from this medical query and return a JSON object:

Query: "{text}"

Return a JSON object with these fields:
- time_reference: "current", "recent", "past", "future", or null
- severity: "mild", "moderate", "severe", or null  
- urgency: "urgent", "routine", or null
- comparison: "trend", "baseline", "normal", or null

Return format: {{"time_reference": "...", "severity": "...", "urgency": "...", "comparison": "..."}}
"""

            response = await self._call_ollama(prompt, system_prompt)
            
            try:
                # Clean up the response to extract JSON
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                
                if json_start != -1 and json_end != 0:
                    json_str = response[json_start:json_end]
                    context = json.loads(json_str)
                    return context
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse context JSON: {response}")
            
            return self._get_default_context()
                
        except Exception as e:
            logger.error(f"Error extracting context with Ollama: {e}")
            return self._get_default_context()
    
    async def analyze_query_complexity(self, text: str) -> Dict[str, Any]:
        """Analyze the complexity of a medical query using local LLM"""
        try:
            system_prompt = "You are a medical query complexity analyzer. Return ONLY a JSON object, nothing else."
            
            prompt = f"""
Analyze the complexity of this medical query:

"{text}"

Return a JSON object with:
- complexity_level: "simple", "moderate", or "complex"
- requires_context: true/false
- multi_intent: true/false
- medical_terminology_density: "low", "medium", or "high"

Return format: {{"complexity_level": "...", "requires_context": true/false, "multi_intent": true/false, "medical_terminology_density": "..."}}
"""

            response = await self._call_ollama(prompt, system_prompt)
            
            try:
                # Clean up the response to extract JSON
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                
                if json_start != -1 and json_end != 0:
                    json_str = response[json_start:json_end]
                    analysis = json.loads(json_str)
                    return analysis
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse complexity analysis JSON: {response}")
            
            return {
                "complexity_level": "moderate",
                "requires_context": False,
                "multi_intent": False,
                "medical_terminology_density": "medium"
            }
                
        except Exception as e:
            logger.error(f"Error analyzing query complexity: {e}")
            return {
                "complexity_level": "moderate",
                "requires_context": False,
                "multi_intent": False,
                "medical_terminology_density": "medium"
            }
    
    async def _fallback_entity_extraction(self, text: str) -> List[str]:
        """Fallback entity extraction using regex patterns"""
        entities = []
        text_lower = text.lower()
        
        # Basic medical term patterns
        medical_patterns = [
            r'\b(medication|med|drug|prescription|pill|tablet|capsule|injection)\b',
            r'\b(condition|diagnosis|disease|illness|symptom)\b',
            r'\b(allergy|allergic|reaction|intolerance)\b',
            r'\b(procedure|surgery|operation|test|scan)\b',
            r'\b(blood.?pressure|heart.?rate|temperature|weight|height|bmi)\b',
            r'\b(observation|vital|sign|reading|measurement)\b',
            r'\b(encounter|visit|appointment|admission)\b',
            r'\b(specimen|sample|lab|collection)\b'
        ]
        
        for pattern in medical_patterns:
            matches = re.findall(pattern, text_lower)
            entities.extend(matches)
        
        # Remove duplicates and clean up
        entities = list(set(entities))
        entities = [entity.strip() for entity in entities if len(entity.strip()) > 2]
        
        logger.info(f"Fallback extracted entities: {entities}")
        return entities
    
    async def _fallback_intent_classification(self, text: str) -> str:
        """Fallback intent classification using regex patterns"""
        text_lower = text.lower()
        
        # Simple pattern matching as fallback - order matters for specificity
        if any(word in text_lower for word in ['pmh', 'medical history', 'past medical']):
            return 'pmh_query'
        elif any(word in text_lower for word in ['allergy', 'allergies', 'allergic', 'reaction']):
            return 'allergy_query'
        elif any(word in text_lower for word in ['medication', 'med', 'drug', 'prescription']):
            return 'medication_query'
        elif any(word in text_lower for word in ['condition', 'diagnosis', 'disease']):
            return 'condition_query'
        elif any(word in text_lower for word in ['observation', 'vital', 'sign', 'lab']):
            return 'observation_query'
        elif any(word in text_lower for word in ['encounter', 'visit', 'appointment']):
            return 'encounter_query'
        elif any(word in text_lower for word in ['procedure', 'surgery', 'operation']):
            return 'procedure_query'
        elif any(word in text_lower for word in ['specimen', 'sample', 'collection']):
            return 'specimen_query'
        elif any(word in text_lower for word in ['interaction', 'interact', 'conflict']):
            return 'interaction_query'
        elif any(word in text_lower for word in ['evidence', 'study', 'trial']):
            return 'evidence_query'
        elif any(word in text_lower for word in ['alert', 'warning', 'risk']):
            return 'alert_query'
        else:
            return 'general_query'
    
    def _get_default_context(self) -> Dict[str, Any]:
        """Get default context structure"""
        return {
            "time_reference": None,
            "severity": None,
            "urgency": None,
            "comparison": None
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check if Ollama is available and working"""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            
            models = response.json().get("models", [])
            available_models = [model["name"] for model in models]
            
            return {
                "status": "healthy",
                "available_models": available_models,
                "current_model": self.model,
                "model_available": self.model in available_models
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "message": "Ollama server not available"
            }
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
