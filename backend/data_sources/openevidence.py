"""
OpenEvidence Data Source

Integration with OpenEvidence API for clinical evidence and medical knowledge.
Provides access to clinical trials, treatment guidelines, and evidence-based medicine data.
"""

from typing import Dict, List, Optional, Any
import logging
from datetime import datetime
from .base_source import BaseDataSource

logger = logging.getLogger(__name__)

class OpenEvidenceSource(BaseDataSource):
    """OpenEvidence API integration for clinical evidence data"""
    
    def __init__(self, api_key: str = "", base_url: str = "https://api.openevidence.com"):
        super().__init__(
            name="openevidence",
            api_key=api_key,
            base_url=base_url,
            cache_ttl=3600  # 1 hour cache
        )
        
    async def _get_headers(self) -> Dict[str, str]:
        """Get headers for OpenEvidence API requests"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        return headers
    
    async def search_evidence(self, query: str, filters: Dict = None) -> List[Dict]:
        """Search for clinical evidence"""
        params = {
            "q": query,
            "limit": 20,
            "offset": 0
        }
        
        if filters:
            params.update(filters)
        
        try:
            headers = await self._get_headers()
            result = await self._cached_request(
                method="GET",
                endpoint="/v1/evidence/search",
                params=params,
                headers=headers
            )
            
            return result.get('results', [])
            
        except Exception as e:
            logger.error(f"Error searching OpenEvidence: {e}")
            return []
    
    async def get_drug_evidence(self, drug_name: str) -> List[Dict]:
        """Get evidence for specific drug"""
        return await self.search_evidence(
            query=drug_name,
            filters={"type": "drug", "category": "clinical_trials"}
        )
    
    async def get_condition_evidence(self, condition: str) -> List[Dict]:
        """Get evidence for specific condition"""
        return await self.search_evidence(
            query=condition,
            filters={"type": "condition", "category": "treatment_guidelines"}
        )
    
    async def get_treatment_evidence(self, condition: str, treatment: str) -> Dict:
        """Get evidence for treatment of condition"""
        query = f"{condition} AND {treatment}"
        results = await self.search_evidence(
            query=query,
            filters={"type": "treatment", "category": "clinical_trials"}
        )
        
        if results:
            return results[0]  # Return most relevant result
        return {}
    
    async def get_clinical_trials(self, query: str, phase: str = None) -> List[Dict]:
        """Get clinical trial data"""
        filters = {"type": "clinical_trial"}
        if phase:
            filters["phase"] = phase
            
        return await self.search_evidence(query, filters)
    
    async def get_treatment_guidelines(self, condition: str) -> List[Dict]:
        """Get treatment guidelines for condition"""
        return await self.search_evidence(
            query=condition,
            filters={"type": "guideline", "category": "treatment"}
        )
    
    async def get_systematic_reviews(self, query: str) -> List[Dict]:
        """Get systematic reviews and meta-analyses"""
        return await self.search_evidence(
            query=query,
            filters={"type": "systematic_review"}
        )
    
    async def search(self, query: str, filters: Dict = None) -> List[Dict]:
        """Generic search method"""
        return await self.search_evidence(query, filters)
    
    async def get_by_id(self, id: str) -> Optional[Dict]:
        """Get specific evidence by ID"""
        try:
            headers = await self._get_headers()
            result = await self._cached_request(
                method="GET",
                endpoint=f"/v1/evidence/{id}",
                headers=headers
            )
            return result
        except Exception as e:
            logger.error(f"Error getting evidence by ID {id}: {e}")
            return None
    
    async def get_metadata(self) -> Dict:
        """Get OpenEvidence API metadata and capabilities"""
        try:
            headers = await self._get_headers()
            result = await self._cached_request(
                method="GET",
                endpoint="/v1/metadata",
                headers=headers
            )
            return result
        except Exception as e:
            logger.error(f"Error getting OpenEvidence metadata: {e}")
            return {
                "source": "openevidence",
                "status": "error",
                "error": str(e)
            }
    
    async def get_evidence_summary(self, evidence_ids: List[str]) -> Dict:
        """Get summary of multiple evidence items"""
        summaries = []
        
        for evidence_id in evidence_ids:
            evidence = await self.get_by_id(evidence_id)
            if evidence:
                summary = {
                    "id": evidence_id,
                    "title": evidence.get("title", ""),
                    "type": evidence.get("type", ""),
                    "publication_date": evidence.get("publication_date", ""),
                    "journal": evidence.get("journal", ""),
                    "authors": evidence.get("authors", []),
                    "abstract": evidence.get("abstract", ""),
                    "conclusions": evidence.get("conclusions", ""),
                    "evidence_level": evidence.get("evidence_level", ""),
                    "relevance_score": evidence.get("relevance_score", 0.0)
                }
                summaries.append(summary)
        
        return {
            "total_count": len(summaries),
            "summaries": summaries,
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_drug_interactions(self, drug_name: str) -> List[Dict]:
        """Get drug interaction data"""
        return await self.search_evidence(
            query=f"{drug_name} interactions",
            filters={"type": "drug_interaction"}
        )
    
    async def get_adverse_events(self, drug_name: str) -> List[Dict]:
        """Get adverse event data for drug"""
        return await self.search_evidence(
            query=f"{drug_name} adverse events",
            filters={"type": "adverse_event"}
        )
