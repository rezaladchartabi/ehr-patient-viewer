"""
Allergy Processor for Clinical Notes Data
Extracts patient allergies from XLSX clinical notes and integrates with FHIR data
"""

import pandas as pd
import re
from typing import List, Dict, Optional, Tuple
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AllergyProcessor:
    """Process clinical notes to extract patient allergy information"""
    
    def __init__(self):
        self.allergy_patterns = [
            # Standard "Allergies:" section
            r'Allergies:\s*\n([^\n]*(?:\n(?!\s*\n)[^\n]*)*)',
            # Alternative patterns
            r'ALLERGIES:\s*\n([^\n]*(?:\n(?!\s*\n)[^\n]*)*)',
            r'Drug Allergies:\s*\n([^\n]*(?:\n(?!\s*\n)[^\n]*)*)',
            r'DRUG ALLERGIES:\s*\n([^\n]*(?:\n(?!\s*\n)[^\n]*)*)',
        ]
        
        # Common non-allergy terms to filter out
        self.exclusion_terms = {
            'none', 'nka', 'nkda', 'no known allergies', 'no known drug allergies',
            'unknown', 'unable to obtain', 'patient unable to provide', 'see below',
            'as noted', 'per patient', 'per family', 'unable to assess',
            'nkda to environmental allergens', 'no known food allergies'
        }
    
    def load_xlsx_data(self, file_path: str) -> pd.DataFrame:
        """Load clinical notes data from XLSX file"""
        try:
            logger.info(f"Loading XLSX file: {file_path}")
            df = pd.read_excel(file_path)
            logger.info(f"Loaded {len(df)} records from XLSX file")
            return df
        except Exception as e:
            logger.error(f"Error loading XLSX file: {e}")
            raise
    
    def extract_allergies_from_text(self, text: str) -> List[str]:
        """Extract allergies from clinical note text"""
        if not text or pd.isna(text):
            return []
        
        allergies = []
        
        # Try each allergy pattern
        for pattern in self.allergy_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                allergy_section = match.group(1).strip()
                
                # Parse the allergy section
                parsed_allergies = self._parse_allergy_section(allergy_section)
                allergies.extend(parsed_allergies)
                
                # If we found allergies, break (use first successful pattern)
                if allergies:
                    break
        
        # Remove duplicates and filter
        unique_allergies = list(set(allergies))
        filtered_allergies = self._filter_allergies(unique_allergies)
        
        return filtered_allergies
    
    def _parse_allergy_section(self, allergy_section: str) -> List[str]:
        """Parse the allergies section text to extract individual allergies"""
        if not allergy_section:
            return []
        
        allergies = []
        
        # Split by common delimiters
        potential_allergies = re.split(r'[,;\n]|(?:\s+and\s+)', allergy_section)
        
        for allergy in potential_allergies:
            cleaned = allergy.strip()
            if cleaned and len(cleaned) > 1:  # Avoid single characters
                # Remove common prefixes/suffixes
                cleaned = re.sub(r'^\d+\.?\s*', '', cleaned)  # Remove numbering
                cleaned = re.sub(r'^[-*•]\s*', '', cleaned)   # Remove bullet points
                cleaned = cleaned.strip()
                
                if cleaned:
                    allergies.append(cleaned)
        
        return allergies
    
    def _filter_allergies(self, allergies: List[str]) -> List[str]:
        """Filter out non-allergy terms and clean up allergy names"""
        filtered = []
        
        for allergy in allergies:
            # Convert to lowercase for comparison
            allergy_lower = allergy.lower().strip()
            
            # Skip if it's an exclusion term
            if allergy_lower in self.exclusion_terms:
                continue
            
            # Skip if it's too short or contains only special characters
            if len(allergy_lower) < 2 or not re.search(r'[a-zA-Z]', allergy_lower):
                continue
            
            # Clean up the allergy name
            cleaned = self._clean_allergy_name(allergy)
            if cleaned:
                filtered.append(cleaned)
        
        return filtered
    
    def _clean_allergy_name(self, allergy: str) -> Optional[str]:
        """Clean up allergy name formatting"""
        # Remove extra whitespace
        cleaned = ' '.join(allergy.split())
        
        # Capitalize first letter of each word
        cleaned = ' '.join(word.capitalize() for word in cleaned.split())
        
        # Handle common abbreviations
        abbreviation_map = {
            'Pcn': 'Penicillin',
            'Asa': 'Aspirin',
            'Nkda': None,  # Will be filtered out
            'Nka': None,   # Will be filtered out
        }
        
        for abbrev, full_name in abbreviation_map.items():
            if cleaned.lower() == abbrev.lower():
                return full_name
        
        return cleaned if cleaned else None
    
    def process_patient_allergies(self, df: pd.DataFrame) -> Dict[str, List[Dict]]:
        """Process all patients and extract their allergies"""
        logger.info("Processing patient allergies from clinical notes...")
        
        patient_allergies = {}
        processed_count = 0
        allergy_found_count = 0
        
        for _, row in df.iterrows():
            subject_id = str(row['subject_id'])
            note_text = row['text']
            note_id = row['note_id']
            charttime = row['charttime']
            
            # Extract allergies from this note
            allergies = self.extract_allergies_from_text(note_text)
            
            if allergies:
                allergy_found_count += 1
                
                # Initialize patient record if not exists
                if subject_id not in patient_allergies:
                    patient_allergies[subject_id] = []
                
                # Add allergies for this patient
                for allergy in allergies:
                    allergy_record = {
                        'allergy_name': allergy,
                        'source_note_id': note_id,
                        'chart_time': charttime,
                        'extracted_at': datetime.now().isoformat()
                    }
                    patient_allergies[subject_id].append(allergy_record)
            
            processed_count += 1
            
            # Log progress every 1000 records
            if processed_count % 1000 == 0:
                logger.info(f"Processed {processed_count} records, found allergies in {allergy_found_count} notes")
        
        logger.info(f"Completed processing {processed_count} records")
        logger.info(f"Found allergies in {allergy_found_count} notes")
        logger.info(f"Total patients with allergies: {len(patient_allergies)}")
        
        # Remove duplicate allergies per patient
        for subject_id in patient_allergies:
            patient_allergies[subject_id] = self._deduplicate_patient_allergies(
                patient_allergies[subject_id]
            )
        
        return patient_allergies
    
    def _deduplicate_patient_allergies(self, allergies: List[Dict]) -> List[Dict]:
        """Remove duplicate allergies for a patient, keeping the most recent"""
        seen_allergies = {}
        
        for allergy in allergies:
            allergy_name = allergy['allergy_name'].lower()
            chart_time = allergy['chart_time']
            
            # Keep the most recent entry for each allergy
            if (allergy_name not in seen_allergies or 
                chart_time > seen_allergies[allergy_name]['chart_time']):
                seen_allergies[allergy_name] = allergy
        
        return list(seen_allergies.values())
    
    def generate_allergy_summary(self, patient_allergies: Dict[str, List[Dict]]) -> Dict:
        """Generate summary statistics about extracted allergies"""
        total_patients = len(patient_allergies)
        total_allergies = sum(len(allergies) for allergies in patient_allergies.values())
        
        # Count most common allergies
        allergy_counts = {}
        for allergies in patient_allergies.values():
            for allergy in allergies:
                name = allergy['allergy_name']
                allergy_counts[name] = allergy_counts.get(name, 0) + 1
        
        # Sort by frequency
        common_allergies = sorted(allergy_counts.items(), key=lambda x: x[1], reverse=True)
        
        return {
            'total_patients_with_allergies': total_patients,
            'total_allergy_entries': total_allergies,
            'average_allergies_per_patient': total_allergies / total_patients if total_patients > 0 else 0,
            'most_common_allergies': common_allergies[:20],  # Top 20
            'unique_allergies': len(allergy_counts)
        }

# Example usage and testing
if __name__ == "__main__":
    processor = AllergyProcessor()
    
    # Test with sample text
    sample_text = """
    Name:  ___                    Unit No:   ___
     
    Admission Date:  ___              Discharge Date:   ___
     
    Date of Birth:  ___             Sex:   F
     
    Service: MEDICINE
     
    Allergies: 
    Codeine
     
    Attending: ___.
    """
    
    allergies = processor.extract_allergies_from_text(sample_text)
    print(f"Extracted allergies: {allergies}")
