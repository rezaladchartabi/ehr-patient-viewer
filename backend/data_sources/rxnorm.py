"""
RxNorm Data Source

Integration with RxNorm API for drug information, including drug names,
ingredients, and relationships between different drug concepts.
"""

from typing import Dict, List, Optional, Any
import logging
from datetime import datetime
from .base_source import BaseDataSource

logger = logging.getLogger(__name__)

class RxNormSource(BaseDataSource):
    """RxNorm API integration for drug information"""
    
    def __init__(self, api_key: str = "", base_url: str = "https://rxnav.nlm.nih.gov/REST"):
        super().__init__(
            name="rxnorm",
            api_key=api_key,
            base_url=base_url,
            cache_ttl=7200  # 2 hour cache for drug data
        )
    
    async def search_drugs(self, query: str, max_results: int = 20) -> List[Dict]:
        """Search for drugs by name"""
        try:
            result = await self._cached_request(
                method="GET",
                endpoint="/drugs.json",
                params={
                    "name": query,
                    "allsrc": 1,
                    "maxEntries": max_results
                }
            )
            
            drugs = []
            if 'drugGroup' in result and 'conceptGroup' in result['drugGroup']:
                for group in result['drugGroup']['conceptGroup']:
                    if 'conceptProperties' in group:
                        for concept in group['conceptProperties']:
                            drug = {
                                "rxcui": concept.get('rxcui', ''),
                                "name": concept.get('name', ''),
                                "synonym": concept.get('synonym', ''),
                                "tty": concept.get('tty', ''),
                                "language": concept.get('language', ''),
                                "suppress": concept.get('suppress', ''),
                                "umlscui": concept.get('umlscui', '')
                            }
                            drugs.append(drug)
            
            return drugs
            
        except Exception as e:
            logger.error(f"Error searching RxNorm drugs: {e}")
            return []
    
    async def get_drug_info(self, rxcui: str) -> Optional[Dict]:
        """Get detailed information about a drug by RxCUI"""
        try:
            result = await self._cached_request(
                method="GET",
                endpoint=f"/rxcui/{rxcui}/allrelated.json"
            )
            
            if 'allRelatedGroup' in result:
                return {
                    "rxcui": rxcui,
                    "concept_group": result['allRelatedGroup'].get('conceptGroup', []),
                    "timestamp": datetime.now().isoformat()
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting drug info for RxCUI {rxcui}: {e}")
            return None
    
    async def get_drug_ingredients(self, rxcui: str) -> List[Dict]:
        """Get ingredients for a drug"""
        try:
            result = await self._cached_request(
                method="GET",
                endpoint=f"/rxcui/{rxcui}/related.json",
                params={"tty": "IN"}
            )
            
            ingredients = []
            if 'relatedGroup' in result and 'conceptGroup' in result['relatedGroup']:
                for group in result['relatedGroup']['conceptGroup']:
                    if 'conceptProperties' in group:
                        for concept in group['conceptProperties']:
                            ingredient = {
                                "rxcui": concept.get('rxcui', ''),
                                "name": concept.get('name', ''),
                                "synonym": concept.get('synonym', ''),
                                "tty": concept.get('tty', ''),
                                "relationship": concept.get('relationship', '')
                            }
                            ingredients.append(ingredient)
            
            return ingredients
            
        except Exception as e:
            logger.error(f"Error getting ingredients for RxCUI {rxcui}: {e}")
            return []
    
    async def get_drug_brands(self, rxcui: str) -> List[Dict]:
        """Get brand names for a drug"""
        try:
            result = await self._cached_request(
                method="GET",
                endpoint=f"/rxcui/{rxcui}/related.json",
                params={"tty": "BN"}
            )
            
            brands = []
            if 'relatedGroup' in result and 'conceptGroup' in result['relatedGroup']:
                for group in result['relatedGroup']['conceptGroup']:
                    if 'conceptProperties' in group:
                        for concept in group['conceptProperties']:
                            brand = {
                                "rxcui": concept.get('rxcui', ''),
                                "name": concept.get('name', ''),
                                "synonym": concept.get('synonym', ''),
                                "tty": concept.get('tty', ''),
                                "relationship": concept.get('relationship', '')
                            }
                            brands.append(brand)
            
            return brands
            
        except Exception as e:
            logger.error(f"Error getting brands for RxCUI {rxcui}: {e}")
            return []
    
    async def get_drug_interactions(self, rxcui: str) -> List[Dict]:
        """Get drug interactions (Note: RxNorm doesn't provide interactions directly)"""
        # This would need to be integrated with other sources like DrugBank
        logger.warning("RxNorm doesn't provide drug interactions directly")
        return []
    
    async def get_drug_approximate_match(self, query: str) -> List[Dict]:
        """Get approximate matches for drug names"""
        try:
            result = await self._cached_request(
                method="GET",
                endpoint="/approximateTerm.json",
                params={
                    "term": query,
                    "maxEntries": 20,
                    "option": 1
                }
            )
            
            matches = []
            if 'approximateGroup' in result and 'candidate' in result['approximateGroup']:
                for candidate in result['approximateGroup']['candidate']:
                    match = {
                        "rxcui": candidate.get('rxcui', ''),
                        "name": candidate.get('name', ''),
                        "synonym": candidate.get('synonym', ''),
                        "score": candidate.get('score', 0),
                        "source": candidate.get('source', '')
                    }
                    matches.append(match)
            
            return matches
            
        except Exception as e:
            logger.error(f"Error getting approximate matches for {query}: {e}")
            return []
    
    async def get_drug_classes(self, rxcui: str) -> List[Dict]:
        """Get drug classes for a drug"""
        try:
            result = await self._cached_request(
                method="GET",
                endpoint=f"/rxcui/{rxcui}/allrelated.json",
                params={"tty": "VA"}
            )
            
            classes = []
            if 'allRelatedGroup' in result and 'conceptGroup' in result['allRelatedGroup']:
                for group in result['allRelatedGroup']['conceptGroup']:
                    if 'conceptProperties' in group:
                        for concept in group['conceptProperties']:
                            if concept.get('tty') == 'VA':
                                drug_class = {
                                    "rxcui": concept.get('rxcui', ''),
                                    "name": concept.get('name', ''),
                                    "synonym": concept.get('synonym', ''),
                                    "tty": concept.get('tty', '')
                                }
                                classes.append(drug_class)
            
            return classes
            
        except Exception as e:
            logger.error(f"Error getting drug classes for RxCUI {rxcui}: {e}")
            return []
    
    async def search(self, query: str, filters: Dict = None) -> List[Dict]:
        """Generic search method"""
        return await self.search_drugs(query)
    
    async def get_by_id(self, id: str) -> Optional[Dict]:
        """Get drug by RxCUI"""
        return await self.get_drug_info(id)
    
    async def get_metadata(self) -> Dict:
        """Get RxNorm API metadata"""
        return {
            "source": "rxnorm",
            "name": "RxNorm",
            "description": "Normalized Names for Clinical Drugs",
            "version": "2024",
            "base_url": self.base_url,
            "capabilities": [
                "drug_search",
                "drug_info",
                "ingredients",
                "brand_names",
                "approximate_matching",
                "drug_classes"
            ],
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_drug_summary(self, drug_name: str) -> Dict:
        """Get comprehensive drug summary including ingredients, brands, and classes"""
        # First search for the drug
        drugs = await self.search_drugs(drug_name, max_results=1)
        
        if not drugs:
            return {"error": f"Drug '{drug_name}' not found"}
        
        drug = drugs[0]
        rxcui = drug['rxcui']
        
        # Get additional information
        ingredients = await self.get_drug_ingredients(rxcui)
        brands = await self.get_drug_brands(rxcui)
        classes = await self.get_drug_classes(rxcui)
        
        return {
            "basic_info": drug,
            "ingredients": ingredients,
            "brand_names": brands,
            "drug_classes": classes,
            "timestamp": datetime.now().isoformat()
        }
