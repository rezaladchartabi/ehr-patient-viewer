"""
Past Medical History (PMH) Extractor for Clinical Notes
Extracts patient medical history from clinical note text using only standard library
"""

import re
from typing import List, Optional, Dict
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PMHExtractor:
    """Extract Past Medical History from clinical note text"""
    
    def __init__(self):
        # PMH section patterns
        self.pmh_section_patterns = [
            r'Past Medical History:\s*\n([^\n]*(?:\n(?!\s*\n)[^\n]*)*)',
            r'PAST MEDICAL HISTORY:\s*\n([^\n]*(?:\n(?!\s*\n)[^\n]*)*)',
            r'Medical History:\s*\n([^\n]*(?:\n(?!\s*\n)[^\n]*)*)',
            r'MEDICAL HISTORY:\s*\n([^\n]*(?:\n(?!\s*\n)[^\n]*)*)',
        ]
        
        # Inline PMH patterns (in History of Present Illness)
        self.pmh_inline_patterns = [
            r'w/\s*PMH\s+([^.]*(?:\.|presents|who))',
            r'with\s+(?:a\s+)?PMH\s+(?:of\s+)?([^.]*(?:\.|presents|who))',
            r'PMH\s+(?:of\s+)?([^.]*(?:\.|presents|who))',
            r'(?:patient|pt)\s+(?:with|w/)\s+(?:a\s+)?(?:history\s+of|PMH\s+of|PMH)\s+([^.]*(?:\.|presents|who))',
        ]
        
        # List-style PMH patterns
        self.pmh_list_patterns = [
            r'Past Medical History:\s*\n((?:\s*[-•*]\s*[^\n]+\n?)+)',
            r'PAST MEDICAL HISTORY:\s*\n((?:\s*[-•*]\s*[^\n]+\n?)+)',
            r'PMH:\s*\n((?:\s*[-•*]\s*[^\n]+\n?)+)',
        ]
        
        # Common non-PMH terms to filter out
        self.exclusion_terms = {
            'none', 'unknown', 'unable to obtain', 'patient unable to provide',
            'see below', 'as noted', 'per patient', 'per family', 'non-contributory',
            'presents', 'presenting', 'presentation', 'history of present illness',
            'chief complaint', 'review of systems'
        }
        
        # Common medical condition abbreviations
        self.condition_expansions = {
            'HTN': 'Hypertension',
            'DM': 'Diabetes Mellitus',
            'CAD': 'Coronary Artery Disease',
            'CHF': 'Congestive Heart Failure',
            'COPD': 'Chronic Obstructive Pulmonary Disease',
            'CVA': 'Cerebrovascular Accident',
            'MI': 'Myocardial Infarction',
            'A-fib': 'Atrial Fibrillation',
            'AFib': 'Atrial Fibrillation',
            'CKD': 'Chronic Kidney Disease',
            'ESRD': 'End Stage Renal Disease',
            'OSA': 'Obstructive Sleep Apnea',
            'GERD': 'Gastroesophageal Reflux Disease',
            'DVT': 'Deep Vein Thrombosis',
            'PE': 'Pulmonary Embolism',
            'BPH': 'Benign Prostatic Hyperplasia'
        }
    
    def extract_pmh_from_text(self, text: str) -> List[str]:
        """Extract Past Medical History from clinical note text"""
        if not text:
            return []
        
        pmh_conditions = []
        
        # Try section-based patterns first
        section_conditions = self._extract_from_sections(text)
        pmh_conditions.extend(section_conditions)
        
        # Try inline patterns if section-based didn't find much
        if len(section_conditions) < 3:  # If we found few conditions, try inline
            inline_conditions = self._extract_from_inline(text)
            pmh_conditions.extend(inline_conditions)
        
        # Try list-style patterns
        list_conditions = self._extract_from_lists(text)
        pmh_conditions.extend(list_conditions)
        
        # Remove duplicates and filter
        unique_conditions = list(set(pmh_conditions))
        filtered_conditions = self._filter_conditions(unique_conditions)
        
        return filtered_conditions
    
    def _extract_from_sections(self, text: str) -> List[str]:
        """Extract PMH from dedicated sections"""
        conditions = []
        
        for pattern in self.pmh_section_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                pmh_section = match.group(1).strip()
                parsed_conditions = self._parse_pmh_section(pmh_section)
                conditions.extend(parsed_conditions)
                
                if conditions:  # If we found conditions, use first successful pattern
                    break
        
        return conditions
    
    def _extract_from_inline(self, text: str) -> List[str]:
        """Extract PMH from inline mentions (e.g., in HPI)"""
        conditions = []
        
        for pattern in self.pmh_inline_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # Clean up the match
                cleaned = re.sub(r'(presents|presenting|who|that)', '', match, flags=re.IGNORECASE)
                parsed_conditions = self._parse_pmh_section(cleaned)
                conditions.extend(parsed_conditions)
        
        return conditions
    
    def _extract_from_lists(self, text: str) -> List[str]:
        """Extract PMH from list-style formatting"""
        conditions = []
        
        for pattern in self.pmh_list_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                list_section = match.group(1).strip()
                # Split by lines and extract each item
                lines = list_section.split('\n')
                for line in lines:
                    # Remove bullet points and clean
                    cleaned = re.sub(r'^\s*[-•*]\s*', '', line.strip())
                    if cleaned and len(cleaned) > 2:
                        conditions.append(cleaned)
        
        return conditions
    
    def _parse_pmh_section(self, pmh_section: str) -> List[str]:
        """Parse PMH section text to extract individual conditions"""
        if not pmh_section:
            return []
        
        conditions = []
        
        # Handle list-style format (with dashes/bullets)
        if re.search(r'^\s*[-•*]', pmh_section, re.MULTILINE):
            lines = pmh_section.split('\n')
            for line in lines:
                # Extract condition from each line
                cleaned = re.sub(r'^\s*[-•*]\s*', '', line.strip())
                cleaned = re.sub(r';.*$', '', cleaned)  # Remove everything after semicolon
                cleaned = re.sub(r'\s*\([^)]*\)', '', cleaned)  # Remove parenthetical notes
                cleaned = cleaned.strip()
                
                if cleaned and len(cleaned) > 3 and not any(term in cleaned.lower() for term in self.exclusion_terms):
                    conditions.append(cleaned)
        else:
            # Handle comma-separated format
            potential_conditions = re.split(r'[,;]|(?:\s+and\s+)', pmh_section)
            
            for condition in potential_conditions:
                cleaned = condition.strip()
                if cleaned and len(cleaned) > 3:
                    # Remove common prefixes/suffixes
                    cleaned = re.sub(r'^\d+\.?\s*', '', cleaned)  # Remove numbering
                    cleaned = re.sub(r'^[-*•]\s*', '', cleaned)   # Remove bullet points
                    cleaned = re.sub(r'\s*\([^)]*\)', '', cleaned)  # Remove parenthetical notes
                    
                    # Stop at certain keywords that indicate end of condition
                    cleaned = re.sub(r'\s+(presents?|presenting|who|that|with).*$', '', cleaned, flags=re.IGNORECASE)
                    cleaned = cleaned.strip()
                    
                    if cleaned and len(cleaned) > 3:
                        conditions.append(cleaned)
        
        return conditions
    
    def _filter_conditions(self, conditions: List[str]) -> List[str]:
        """Filter out non-condition terms and clean up condition names"""
        filtered = []
        
        for condition in conditions:
            # Convert to lowercase for comparison
            condition_lower = condition.lower().strip()
            
            # Skip if it's an exclusion term
            if any(term in condition_lower for term in self.exclusion_terms):
                continue
            
            # Skip if it's too short or contains only special characters
            if len(condition_lower) < 3 or not re.search(r'[a-zA-Z]', condition_lower):
                continue
            
            # Skip if it looks like a sentence fragment
            if condition_lower.startswith(('with', 'who', 'that', 'presents', 'presenting')):
                continue
            
            # Clean up the condition name
            cleaned = self._clean_condition_name(condition)
            if cleaned:
                filtered.append(cleaned)
        
        return filtered
    
    def _clean_condition_name(self, condition: str) -> Optional[str]:
        """Clean up condition name formatting"""
        # Remove extra whitespace
        cleaned = ' '.join(condition.split())
        
        # Expand common abbreviations
        words = cleaned.split()
        expanded_words = []
        for word in words:
            # Check if word (without punctuation) is an abbreviation
            word_clean = re.sub(r'[^\w]', '', word)
            if word_clean.upper() in self.condition_expansions:
                expanded_words.append(self.condition_expansions[word_clean.upper()])
            else:
                expanded_words.append(word)
        
        cleaned = ' '.join(expanded_words)
        
        # Capitalize appropriately
        # Keep abbreviations uppercase, capitalize first letter of words
        words = cleaned.split()
        formatted_words = []
        for word in words:
            if word.upper() in self.condition_expansions.values():
                formatted_words.append(word)  # Keep medical terms as-is
            elif len(word) <= 4 and word.isupper():
                formatted_words.append(word)  # Keep short abbreviations uppercase
            else:
                formatted_words.append(word.capitalize())
        
        return ' '.join(formatted_words) if formatted_words else None
    
    def process_patient_pmh(self, notes_data: List[Dict]) -> Dict[str, List[Dict]]:
        """Process multiple notes for a patient and extract PMH"""
        patient_pmh = {}
        
        for note_data in notes_data:
            subject_id = str(note_data['subject_id'])
            note_text = note_data['text']
            note_id = note_data['note_id']
            charttime = note_data.get('charttime')
            
            # Extract PMH from this note
            conditions = self.extract_pmh_from_text(note_text)
            
            if conditions:
                # Initialize patient record if not exists
                if subject_id not in patient_pmh:
                    patient_pmh[subject_id] = []
                
                # Add conditions for this patient
                for condition in conditions:
                    pmh_record = {
                        'condition_name': condition,
                        'source_note_id': note_id,
                        'chart_time': charttime,
                        'extracted_at': datetime.now().isoformat()
                    }
                    patient_pmh[subject_id].append(pmh_record)
        
        # Remove duplicate conditions per patient
        for subject_id in patient_pmh:
            patient_pmh[subject_id] = self._deduplicate_patient_pmh(
                patient_pmh[subject_id]
            )
        
        return patient_pmh
    
    def _deduplicate_patient_pmh(self, conditions: List[Dict]) -> List[Dict]:
        """Remove duplicate conditions for a patient, keeping the most recent"""
        seen_conditions = {}
        
        for condition in conditions:
            condition_name = condition['condition_name'].lower()
            chart_time = condition['chart_time']
            
            # Keep the most recent entry for each condition
            if (condition_name not in seen_conditions or 
                (chart_time and chart_time > seen_conditions[condition_name].get('chart_time', ''))):
                seen_conditions[condition_name] = condition
        
        return list(seen_conditions.values())

# Example usage and testing
if __name__ == "__main__":
    extractor = PMHExtractor()
    
    # Test with sample text
    sample_text = """
    History of Present Illness:
    ___ w/ PMH advanced Alzheimer's, chronic HCV, autoimmune 
    hepatitis presents following witnessed period of 15min 
    unresponsiveness and myoclonic jerking.
    
    Past Medical History:
    - Alzheimer's; ADL impaired in preparing food, remembering to 
    bathe, recalling faces.  Lives at home but with extensive ___ 
    and family support.  
    - HCV, chronic, low viral load (last in OMR ___, 15 million 
    copies)  
    - Autoimmune hepatitis  
    - HTN
    """
    
    conditions = extractor.extract_pmh_from_text(sample_text)
    print(f"Extracted PMH conditions: {conditions}")
