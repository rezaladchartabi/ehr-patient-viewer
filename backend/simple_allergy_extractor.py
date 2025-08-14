"""
Simple Allergy Extractor for Clinical Notes (no pandas dependency)
Extracts patient allergies from clinical note text using only standard library
"""

import re
from typing import List, Optional

class SimpleAllergyExtractor:
    """Extract allergies from clinical note text without external dependencies"""
    
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
    
    def extract_allergies_from_text(self, text: str) -> List[str]:
        """Extract allergies from clinical note text"""
        if not text:
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
