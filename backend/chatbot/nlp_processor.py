"""
Medical NLP Processor

Natural language processing for medical queries, including entity extraction
and intent classification.
"""

import re
import logging
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class MedicalNLPProcessor:
    """NLP processor for medical queries"""
    
    def __init__(self):
        # Medical entity patterns
        self.medical_patterns = {
            'medications': [
                r'\b(medication|med|drug|prescription|pill|tablet|capsule|injection)\b',
                r'\b(aspirin|ibuprofen|acetaminophen|lisinopril|metformin|atorvastatin)\b',
                r'\b(antibiotic|antihypertensive|antidiabetic|statin|beta.?blocker)\b'
            ],
            'conditions': [
                r'\b(hypertension|diabetes|heart.?disease|asthma|arthritis|depression)\b',
                r'\b(condition|diagnosis|disease|illness|symptom)\b',
                r'\b(high.?blood.?pressure|type.?2.?diabetes|coronary.?artery.?disease)\b'
            ],
            'allergies': [
                r'\b(allergy|allergic|reaction|intolerance|sensitivity)\b',
                r'\b(penicillin|sulfa|latex|peanut|shellfish|egg|milk)\b'
            ],
            'procedures': [
                r'\b(procedure|surgery|operation|test|scan|examination)\b',
                r'\b(blood.?test|x.?ray|mri|ct.?scan|ultrasound|biopsy)\b'
            ],
            'vitals': [
                r'\b(blood.?pressure|heart.?rate|temperature|weight|height|bmi)\b',
                r'\b(vital|sign|reading|measurement)\b'
            ]
        }
        
        # Intent patterns
        self.intent_patterns = {
            'medication_query': [
                r'\b(what|which|show|list|current|taking)\b.*\b(medication|med|drug|prescription)\b',
                r'\b(medication|med|drug).*\b(taking|current|prescribed|on)\b',
                r'\b(dosage|dose|frequency|how.?much|how.?often)\b'
            ],
            'condition_query': [
                r'\b(what|which|show|list|diagnosed).*\b(condition|disease|diagnosis)\b',
                r'\b(condition|diagnosis|disease).*\b(has|have|diagnosed)\b',
                r'\b(medical.?history|past.?medical|pmh)\b'
            ],
            'observation_query': [
                r'\b(what|which|show|list).*\b(observation|vital|sign|reading|measurement)\b',
                r'\b(observation|vital|sign|reading|measurement).*\b(has|have)\b',
                r'\b(blood.?pressure|heart.?rate|temperature|weight|height|bmi|lab|test)\b',
                r'\b(vital|sign|reading|measurement|result|value)\b'
            ],
            'encounter_query': [
                r'\b(what|which|show|list).*\b(encounter|visit|appointment|admission)\b',
                r'\b(encounter|visit|appointment|admission|hospitalization).*\b(has|have)\b',
                r'\b(when|date|time).*\b(visit|appointment|admission)\b'
            ],
            'procedure_query': [
                r'\b(what|which|show|list).*\b(procedure|surgery|operation|test|scan)\b',
                r'\b(procedure|surgery|operation|test|scan|examination)\b',
                r'\b(blood.?test|x.?ray|mri|ct.?scan|ultrasound|biopsy)\b'
            ],
            'specimen_query': [
                r'\b(what|which|show|list).*\b(specimen|sample|lab|test|collection)\b',
                r'\b(specimen|sample|lab|test|collection|blood|urine|tissue).*\b(has|have)\b',
                r'\b(lab.?work|laboratory|pathology)\b'
            ],
            'allergy_query': [
                r'\b(allergy|allergic|reaction|intolerance)\b',
                r'\b(what|which|show|list).*\b(allergy|allergic)\b',
                r'\b(known.?allergies|allergy.?list)\b'
            ],
            'interaction_query': [
                r'\b(interaction|interact|conflict|contraindication)\b',
                r'\b(drug.?interaction|medication.?interaction)\b',
                r'\b(safe|unsafe|compatible|incompatible)\b'
            ],
            'evidence_query': [
                r'\b(evidence|study|trial|research|guideline)\b',
                r'\b(latest|recent|new).*\b(treatment|evidence|study)\b',
                r'\b(clinical.?trial|systematic.?review|meta.?analysis)\b'
            ],
            'alert_query': [
                r'\b(alert|warning|caution|risk|danger)\b',
                r'\b(clinical.?alert|medical.?alert)\b',
                r'\b(problem|issue|concern|adverse)\b'
            ],
            'general_query': [
                r'\b(what|how|when|where|why)\b',
                r'\b(help|assist|explain|describe)\b',
                r'\b(information|details|summary)\b'
            ]
        }
        
        # Compile patterns for efficiency
        self.compiled_medical_patterns = {
            category: [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
            for category, patterns in self.medical_patterns.items()
        }
        
        self.compiled_intent_patterns = {
            intent: [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
            for intent, patterns in self.intent_patterns.items()
        }
    
    async def extract_entities(self, text: str) -> List[str]:
        """Extract medical entities from text"""
        entities = []
        text_lower = text.lower()
        
        for category, patterns in self.compiled_medical_patterns.items():
            for pattern in patterns:
                matches = pattern.findall(text_lower)
                entities.extend(matches)
        
        # Remove duplicates and clean up
        entities = list(set(entities))
        entities = [entity.strip() for entity in entities if len(entity.strip()) > 2]
        
        logger.info(f"Extracted entities: {entities}")
        return entities
    
    async def classify_intent(self, text: str) -> str:
        """Classify the intent of the query"""
        text_lower = text.lower()
        intent_scores = {}
        
        for intent, patterns in self.compiled_intent_patterns.items():
            score = 0
            for pattern in patterns:
                if pattern.search(text_lower):
                    score += 1
            intent_scores[intent] = score
        
        # Find the intent with the highest score
        if intent_scores:
            best_intent = max(intent_scores, key=intent_scores.get)
            if intent_scores[best_intent] > 0:
                logger.info(f"Classified intent: {best_intent} (score: {intent_scores[best_intent]})")
                return best_intent
        
        # Default to general query if no specific intent is detected
        logger.info("No specific intent detected, using general_query")
        return "general_query"
    
    async def extract_patient_context(self, text: str) -> Dict[str, Any]:
        """Extract patient-specific context from query"""
        context = {
            "time_reference": None,
            "severity": None,
            "urgency": None,
            "comparison": None
        }
        
        # Time references
        time_patterns = {
            "current": r'\b(current|now|present|today)\b',
            "recent": r'\b(recent|latest|new|last)\b',
            "past": r'\b(past|previous|history|before)\b',
            "future": r'\b(future|upcoming|next|planned)\b'
        }
        
        for time_ref, pattern in time_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                context["time_reference"] = time_ref
                break
        
        # Severity indicators
        severity_patterns = {
            "mild": r'\b(mild|minor|slight|low)\b',
            "moderate": r'\b(moderate|medium|modest)\b',
            "severe": r'\b(severe|serious|critical|high|acute)\b'
        }
        
        for severity, pattern in severity_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                context["severity"] = severity
                break
        
        # Urgency indicators
        urgency_patterns = {
            "urgent": r'\b(urgent|emergency|immediate|asap|stat)\b',
            "routine": r'\b(routine|regular|scheduled|planned)\b'
        }
        
        for urgency, pattern in urgency_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                context["urgency"] = urgency
                break
        
        return context
    
    async def normalize_medical_terms(self, text: str) -> str:
        """Normalize medical terminology"""
        # Common medical abbreviations and their full forms
        medical_abbreviations = {
            'bp': 'blood pressure',
            'hr': 'heart rate',
            'temp': 'temperature',
            'wt': 'weight',
            'ht': 'height',
            'med': 'medication',
            'rx': 'prescription',
            'dx': 'diagnosis',
            'hx': 'history',
            'pmh': 'past medical history',
            'dm': 'diabetes mellitus',
            'htn': 'hypertension',
            'cad': 'coronary artery disease',
            'chf': 'congestive heart failure',
            'copd': 'chronic obstructive pulmonary disease'
        }
        
        normalized_text = text.lower()
        
        for abbrev, full_form in medical_abbreviations.items():
            # Replace abbreviations with full forms
            normalized_text = re.sub(r'\b' + abbrev + r'\b', full_form, normalized_text)
        
        return normalized_text
    
    async def extract_medication_dosage(self, text: str) -> Dict[str, Any]:
        """Extract medication dosage information"""
        dosage_info = {
            "amount": None,
            "unit": None,
            "frequency": None,
            "route": None,
            "duration": None
        }
        
        # Dosage amount patterns
        amount_pattern = r'\b(\d+(?:\.\d+)?)\s*(mg|mcg|g|ml|units?|tablets?|capsules?|pills?)\b'
        amount_match = re.search(amount_pattern, text, re.IGNORECASE)
        if amount_match:
            dosage_info["amount"] = float(amount_match.group(1))
            dosage_info["unit"] = amount_match.group(2)
        
        # Frequency patterns
        frequency_patterns = {
            "daily": r'\b(daily|once.?a.?day|qd|q24h)\b',
            "twice_daily": r'\b(twice.?daily|bid|q12h|every.?12.?hours)\b',
            "three_times_daily": r'\b(three.?times.?daily|tid|q8h|every.?8.?hours)\b',
            "four_times_daily": r'\b(four.?times.?daily|qid|q6h|every.?6.?hours)\b',
            "weekly": r'\b(weekly|once.?a.?week|qw)\b',
            "monthly": r'\b(monthly|once.?a.?month)\b'
        }
        
        for freq, pattern in frequency_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                dosage_info["frequency"] = freq
                break
        
        # Route patterns
        route_patterns = {
            "oral": r'\b(oral|by.?mouth|po|tablet|capsule|pill)\b',
            "intravenous": r'\b(iv|intravenous|injection)\b',
            "subcutaneous": r'\b(subcutaneous|subq|sc|injection)\b',
            "topical": r'\b(topical|cream|ointment|gel|patch)\b',
            "inhalation": r'\b(inhalation|inhaler|nebulizer)\b'
        }
        
        for route, pattern in route_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                dosage_info["route"] = route
                break
        
        return dosage_info
    
    async def is_medical_query(self, text: str) -> bool:
        """Determine if the query is medical in nature"""
        medical_keywords = [
            'patient', 'medication', 'condition', 'allergy', 'symptom',
            'diagnosis', 'treatment', 'prescription', 'drug', 'disease',
            'health', 'medical', 'clinical', 'doctor', 'nurse', 'hospital'
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in medical_keywords)
    
    async def get_query_complexity(self, text: str) -> str:
        """Determine the complexity of the query"""
        word_count = len(text.split())
        entity_count = len(await self.extract_entities(text))
        
        if word_count > 20 or entity_count > 3:
            return "complex"
        elif word_count > 10 or entity_count > 1:
            return "moderate"
        else:
            return "simple"
