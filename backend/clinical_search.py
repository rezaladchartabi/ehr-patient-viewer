#!/usr/bin/env python3
"""
Clinical Search Service
Provides comprehensive search functionality across medications, diagnoses, and clinical notes
"""

import re
import sqlite3
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import logging
from notes_processor import get_all_notes, get_notes_for_patient

logger = logging.getLogger(__name__)

class ClinicalSearchService:
    def __init__(self, search_db_path: str = "search_index.sqlite3"):
        self.search_db_path = search_db_path
        
        # Clinical terminology mappings for search expansion
        self.medication_synonyms = {
            # VTE/DVT/PE treatments
            'vte': ['heparin', 'enoxaparin', 'dalteparin', 'warfarin', 'rivaroxaban', 'apixaban', 'dabigatran'],
            'dvt': ['heparin', 'enoxaparin', 'dalteparin', 'warfarin', 'rivaroxaban', 'apixaban', 'dabigatran'],
            'pe': ['heparin', 'enoxaparin', 'dalteparin', 'warfarin', 'rivaroxaban', 'apixaban', 'dabigatran'],
            'pulmonary embolism': ['heparin', 'enoxaparin', 'dalteparin', 'warfarin', 'rivaroxaban', 'apixaban', 'dabigatran'],
            'deep vein thrombosis': ['heparin', 'enoxaparin', 'dalteparin', 'warfarin', 'rivaroxaban', 'apixaban', 'dabigatran'],
            'venous thromboembolism': ['heparin', 'enoxaparin', 'dalteparin', 'warfarin', 'rivaroxaban', 'apixaban', 'dabigatran'],
            
            # Common medication classes
            'statin': ['atorvastatin', 'simvastatin', 'rosuvastatin', 'pravastatin', 'lovastatin', 'fluvastatin', 'pitavastatin'],
            'beta blocker': ['metoprolol', 'atenolol', 'propranolol', 'carvedilol', 'bisoprolol', 'nebivolol'],
            'ace inhibitor': ['lisinopril', 'enalapril', 'ramipril', 'quinapril', 'benazepril', 'fosinopril'],
            'diuretic': ['furosemide', 'hydrochlorothiazide', 'spironolactone', 'torsemide', 'bumetanide'],
            'insulin': ['insulin', 'humulin', 'novolin', 'lantus', 'levemir', 'novolog', 'humalog'],
            
            # Brand names to generics
            'coumadin': ['warfarin'],
            'lovenox': ['enoxaparin'],
            'xarelto': ['rivaroxaban'],
            'eliquis': ['apixaban'],
            'pradaxa': ['dabigatran'],
            'lipitor': ['atorvastatin'],
            'zocor': ['simvastatin'],
            'crestor': ['rosuvastatin'],
            'toprol': ['metoprolol'],
            'tenormin': ['atenolol'],
            'zestril': ['lisinopril'],
            'lasix': ['furosemide'],
            'aldactone': ['spironolactone'],
        }
        
        # Diagnosis synonyms
        self.diagnosis_synonyms = {
            'vte': ['venous thromboembolism', 'deep vein thrombosis', 'dvt', 'pulmonary embolism', 'pe'],
            'dvt': ['deep vein thrombosis', 'venous thromboembolism', 'vte'],
            'pe': ['pulmonary embolism', 'venous thromboembolism', 'vte'],
            'pulmonary embolism': ['pe', 'venous thromboembolism', 'vte'],
            'deep vein thrombosis': ['dvt', 'venous thromboembolism', 'vte'],
            'venous thromboembolism': ['vte', 'deep vein thrombosis', 'dvt', 'pulmonary embolism', 'pe'],
            
            # Common conditions
            'chf': ['congestive heart failure', 'heart failure'],
            'mi': ['myocardial infarction', 'heart attack'],
            'cva': ['cerebrovascular accident', 'stroke'],
            'copd': ['chronic obstructive pulmonary disease'],
            'dm': ['diabetes mellitus', 'diabetes'],
            'htn': ['hypertension', 'high blood pressure'],
            'cad': ['coronary artery disease'],
            'aki': ['acute kidney injury'],
            'ckd': ['chronic kidney disease'],
        }
        
        # Initialize search database
        self._init_search_db()
    
    def _init_search_db(self):
        """Initialize the search database with clinical search tables"""
        conn = sqlite3.connect(self.search_db_path)
        cur = conn.cursor()
        
        # Create clinical search table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS clinical_search (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id TEXT NOT NULL,
                resource_type TEXT NOT NULL,
                resource_id TEXT NOT NULL,
                content TEXT NOT NULL,
                search_text TEXT NOT NULL,
                timestamp TEXT,
                note_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create full-text search index
        cur.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS clinical_search_fts USING fts5(
                content,
                search_text,
                patient_id,
                resource_type,
                tokenize='unicode61 remove_diacritics 2'
            )
        """)
        
        # Create indexes for better performance
        cur.execute("CREATE INDEX IF NOT EXISTS idx_clinical_search_patient ON clinical_search(patient_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_clinical_search_type ON clinical_search(resource_type)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_clinical_search_timestamp ON clinical_search(timestamp)")
        
        conn.commit()
        conn.close()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.search_db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def expand_search_terms(self, query: str) -> List[str]:
        """Expand search query with clinical synonyms"""
        query_lower = query.lower().strip()
        expanded_terms = [query_lower]
        
        # Check medication synonyms
        for term, synonyms in self.medication_synonyms.items():
            if term in query_lower:
                expanded_terms.extend(synonyms)
        
        # Check diagnosis synonyms
        for term, synonyms in self.diagnosis_synonyms.items():
            if term in query_lower:
                expanded_terms.extend(synonyms)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_terms = []
        for term in expanded_terms:
            if term not in seen:
                seen.add(term)
                unique_terms.append(term)
        
        return unique_terms
    
    def index_notes_data(self, patient_id: Optional[str] = None):
        """Index clinical notes data for search"""
        conn = self._get_connection()
        cur = conn.cursor()
        
        try:
            # Clear existing notes data
            if patient_id:
                cur.execute("DELETE FROM clinical_search WHERE patient_id = ? AND resource_type = 'note'", (patient_id,))
                cur.execute("DELETE FROM clinical_search_fts WHERE patient_id = ? AND resource_type = 'note'", (patient_id,))
            else:
                cur.execute("DELETE FROM clinical_search WHERE resource_type = 'note'")
                cur.execute("DELETE FROM clinical_search_fts WHERE resource_type = 'note'")
            
            # Get notes data
            if patient_id:
                notes = get_notes_for_patient(patient_id)
            else:
                notes = get_all_notes()
            
            # Index each note
            for note in notes:
                note_patient_id = note.get('subject_id', '')
                note_id = note.get('note_id', '')
                note_text = note.get('text', '')
                charttime = note.get('charttime', '')
                
                if note_text:
                    # Create searchable text (remove common medical abbreviations and normalize)
                    search_text = self._normalize_text_for_search(note_text)
                    
                    # Insert into main table
                    cur.execute("""
                        INSERT INTO clinical_search 
                        (patient_id, resource_type, resource_id, content, search_text, timestamp, note_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (note_patient_id, 'note', note_id, note_text, search_text, charttime, note_id))
                    
                    # Insert into FTS table
                    cur.execute("""
                        INSERT INTO clinical_search_fts 
                        (content, search_text, patient_id, resource_type)
                        VALUES (?, ?, ?, ?)
                    """, (note_text, search_text, note_patient_id, 'note'))
            
            conn.commit()
            logger.info(f"Indexed {len(notes)} notes for search")
            
        except Exception as e:
            logger.error(f"Error indexing notes: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def _normalize_text_for_search(self, text: str) -> str:
        """Normalize text for better search matching"""
        # Convert to lowercase
        text = text.lower()
        
        # Remove common medical abbreviations that might interfere with search
        abbreviations = {
            'pt': 'patient',
            'hx': 'history',
            'dx': 'diagnosis',
            'tx': 'treatment',
            'rx': 'prescription',
            'vs': 'vital signs',
            'w/': 'with',
            'w/o': 'without',
            'b/l': 'bilateral',
            'r/o': 'rule out',
            'c/o': 'complains of',
            's/p': 'status post',
            'h/o': 'history of',
        }
        
        for abbr, full in abbreviations.items():
            text = re.sub(r'\b' + abbr + r'\b', full, text)
        
        return text
    
    def search_clinical_data(self, query: str, patient_id: Optional[str] = None, 
                           resource_types: Optional[List[str]] = None, 
                           limit: int = 50) -> Dict[str, Any]:
        """Search across clinical data including notes, medications, and diagnoses"""
        
        # Expand search terms
        search_terms = self.expand_search_terms(query)
        
        conn = self._get_connection()
        cur = conn.cursor()
        
        try:
            results = []
            
            # For now, use substring search directly since FTS is having issues
            logger.info(f"Using substring search for terms: {search_terms}")
            results = self._fallback_substring_search(query, patient_id, resource_types, limit)
            
            return {
                'query': query,
                'expanded_terms': search_terms,
                'results': results,
                'total_count': len(results)
            }
            
        except Exception as e:
            logger.error(f"Error in clinical search: {e}")
            return {
                'query': query,
                'expanded_terms': search_terms,
                'results': [],
                'total_count': 0,
                'error': str(e)
            }
        finally:
            conn.close()
    
    def _fallback_substring_search(self, query: str, patient_id: Optional[str] = None,
                                  resource_types: Optional[List[str]] = None, 
                                  limit: int = 50) -> List[Dict[str, Any]]:
        """Fallback to substring search if FTS doesn't find results"""
        conn = self._get_connection()
        cur = conn.cursor()
        
        try:
            sql = """
                SELECT DISTINCT 
                    patient_id,
                    resource_type,
                    resource_id,
                    content,
                    timestamp,
                    note_id
                FROM clinical_search
                WHERE (LOWER(content) LIKE ? OR LOWER(search_text) LIKE ?)
            """
            
            params = [f'%{query.lower()}%', f'%{query.lower()}%']
            
            if patient_id:
                sql += " AND patient_id = ?"
                params.append(patient_id)
            
            if resource_types:
                placeholders = ','.join(['?' for _ in resource_types])
                sql += f" AND resource_type IN ({placeholders})"
                params.extend(resource_types)
            
            sql += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cur.execute(sql, params)
            rows = cur.fetchall()
            
            results = []
            for row in rows:
                result = {
                    'patient_id': row['patient_id'],
                    'resource_type': row['resource_type'],
                    'resource_id': row['resource_id'],
                    'content': row['content'],
                    'timestamp': row['timestamp'],
                    'note_id': row['note_id'],
                    'rank': 0,
                    'matched_terms': [query.lower()]
                }
                results.append(result)
            
            return results
            
        finally:
            conn.close()
    
    def _find_matched_terms(self, content: str, search_terms: List[str]) -> List[str]:
        """Find which search terms matched in the content"""
        content_lower = content.lower()
        matched = []
        for term in search_terms:
            if term in content_lower:
                matched.append(term)
        return matched
    
    def get_search_suggestions(self, partial_query: str, limit: int = 10) -> List[str]:
        """Get search suggestions based on partial query"""
        if len(partial_query) < 2:
            return []
        
        conn = self._get_connection()
        cur = conn.cursor()
        
        try:
            # Search in medication synonyms
            suggestions = []
            
            # Check medication synonyms
            for term, synonyms in self.medication_synonyms.items():
                if partial_query.lower() in term.lower():
                    suggestions.append(term)
                    suggestions.extend(synonyms[:3])  # Limit synonyms
            
            # Check diagnosis synonyms
            for term, synonyms in self.diagnosis_synonyms.items():
                if partial_query.lower() in term.lower():
                    suggestions.append(term)
                    suggestions.extend(synonyms[:3])  # Limit synonyms
            
            # Remove duplicates and limit results
            unique_suggestions = list(dict.fromkeys(suggestions))  # Preserve order
            return unique_suggestions[:limit]
            
        finally:
            conn.close()

# Global instance
clinical_search_service = ClinicalSearchService()
