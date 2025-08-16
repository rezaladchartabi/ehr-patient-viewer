#!/usr/bin/env python3
"""
Test script for data source integrations

This script tests the data source framework and integrations
without requiring actual API keys or external services.
"""

import asyncio
import logging
from typing import Dict, List
from data_sources import OpenEvidenceSource, RxNormSource, KnowledgeBase

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockOpenEvidenceSource(OpenEvidenceSource):
    """Mock OpenEvidence source for testing"""
    
    def __init__(self):
        super().__init__(api_key="test_key", base_url="https://mock.openevidence.com")
    
    async def search_evidence(self, query: str, filters: Dict = None) -> List[Dict]:
        """Mock evidence search"""
        logger.info(f"Mock OpenEvidence search: {query}")
        
        # Return mock evidence data
        return [
            {
                "id": "mock_evidence_1",
                "title": f"Clinical trial for {query}",
                "type": "clinical_trial",
                "publication_date": "2024-01-15",
                "journal": "Mock Medical Journal",
                "authors": ["Dr. Test Author"],
                "abstract": f"This is a mock clinical trial about {query}",
                "conclusions": f"{query} shows promising results in clinical trials",
                "evidence_level": "Level 1",
                "relevance_score": 0.85
            },
            {
                "id": "mock_evidence_2", 
                "title": f"Systematic review of {query}",
                "type": "systematic_review",
                "publication_date": "2024-02-20",
                "journal": "Mock Review Journal",
                "authors": ["Dr. Review Author"],
                "abstract": f"A comprehensive review of {query} evidence",
                "conclusions": f"Strong evidence supports the use of {query}",
                "evidence_level": "Level 1",
                "relevance_score": 0.92
            }
        ]
    
    async def get_metadata(self) -> Dict:
        """Mock metadata"""
        return {
            "source": "openevidence",
            "name": "Mock OpenEvidence",
            "version": "1.0",
            "status": "mock_mode"
        }

class MockRxNormSource(RxNormSource):
    """Mock RxNorm source for testing"""
    
    def __init__(self):
        super().__init__(api_key="test_key", base_url="https://mock.rxnorm.com")
    
    async def search_drugs(self, query: str, max_results: int = 20) -> List[Dict]:
        """Mock drug search"""
        logger.info(f"Mock RxNorm search: {query}")
        
        # Return mock drug data
        return [
            {
                "rxcui": "mock_rxcui_1",
                "name": query,
                "synonym": f"Generic {query}",
                "tty": "BN",
                "language": "ENG",
                "suppress": "N",
                "umlscui": "mock_umls_1"
            },
            {
                "rxcui": "mock_rxcui_2",
                "name": f"{query} Extended Release",
                "synonym": f"ER {query}",
                "tty": "BN",
                "language": "ENG", 
                "suppress": "N",
                "umlscui": "mock_umls_2"
            }
        ]
    
    async def get_metadata(self) -> Dict:
        """Mock metadata"""
        return {
            "source": "rxnorm",
            "name": "Mock RxNorm",
            "description": "Mock Normalized Names for Clinical Drugs",
            "version": "2024",
            "status": "mock_mode"
        }

async def test_data_sources():
    """Test the data source integrations"""
    logger.info("Starting data source tests...")
    
    # Initialize mock sources
    openevidence = MockOpenEvidenceSource()
    rxnorm = MockRxNormSource()
    knowledge_base = KnowledgeBase("test_knowledge.db")
    
    try:
        # Test OpenEvidence
        logger.info("Testing OpenEvidence integration...")
        evidence = await openevidence.search_evidence("hypertension")
        logger.info(f"Found {len(evidence)} evidence items")
        
        # Test RxNorm
        logger.info("Testing RxNorm integration...")
        drugs = await rxnorm.search_drugs("lisinopril")
        logger.info(f"Found {len(drugs)} drug entries")
        
        # Test Knowledge Base
        logger.info("Testing Knowledge Base...")
        
        # Store some test knowledge
        for evidence_item in evidence:
            knowledge_id = await knowledge_base.store_knowledge(
                source_name="openevidence",
                source_id=evidence_item["id"],
                knowledge_type="clinical_evidence",
                title=evidence_item["title"],
                content=evidence_item["abstract"],
                metadata={
                    "journal": evidence_item["journal"],
                    "authors": evidence_item["authors"],
                    "evidence_level": evidence_item["evidence_level"]
                },
                confidence_score=evidence_item["relevance_score"],
                relevance_score=evidence_item["relevance_score"]
            )
            logger.info(f"Stored knowledge: {knowledge_id}")
        
        # Search knowledge base
        search_results = await knowledge_base.search_knowledge("hypertension")
        logger.info(f"Knowledge base search found {len(search_results)} results")
        
        # Get statistics
        stats = await knowledge_base.get_statistics()
        logger.info(f"Knowledge base statistics: {stats}")
        
        # Test health checks
        openevidence_health = await openevidence.health_check()
        rxnorm_health = await rxnorm.health_check()
        
        logger.info(f"OpenEvidence health: {openevidence_health['status']}")
        logger.info(f"RxNorm health: {rxnorm_health['status']}")
        
        logger.info("All tests completed successfully!")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise
    finally:
        # Cleanup
        await openevidence.close()
        await rxnorm.close()

async def test_integration_scenario():
    """Test a realistic integration scenario"""
    logger.info("Testing integration scenario...")
    
    openevidence = MockOpenEvidenceSource()
    rxnorm = MockRxNormSource()
    knowledge_base = KnowledgeBase("test_knowledge.db")
    
    try:
        # Scenario: User asks about hypertension treatment
        query = "hypertension treatment"
        
        # 1. Search for clinical evidence
        evidence = await openevidence.search_evidence(query)
        
        # 2. Search for relevant drugs
        drugs = await rxnorm.search_drugs("lisinopril")
        
        # 3. Store evidence in knowledge base
        for evidence_item in evidence:
            await knowledge_base.store_knowledge(
                source_name="openevidence",
                source_id=evidence_item["id"],
                knowledge_type="treatment_evidence",
                title=evidence_item["title"],
                content=evidence_item["abstract"],
                metadata={"query": query},
                confidence_score=evidence_item["relevance_score"]
            )
        
        # 4. Search knowledge base for comprehensive answer
        knowledge_results = await knowledge_base.search_knowledge(query)
        
        # 5. Generate response
        response = {
            "query": query,
            "evidence_count": len(evidence),
            "drug_count": len(drugs),
            "knowledge_results": len(knowledge_results),
            "summary": f"Found {len(evidence)} clinical evidence items and {len(drugs)} drug options for {query}"
        }
        
        logger.info(f"Integration scenario result: {response}")
        
    except Exception as e:
        logger.error(f"Integration test failed: {e}")
        raise
    finally:
        await openevidence.close()
        await rxnorm.close()

if __name__ == "__main__":
    # Run tests
    asyncio.run(test_data_sources())
    asyncio.run(test_integration_scenario())
