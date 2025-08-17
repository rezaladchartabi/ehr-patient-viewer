#!/usr/bin/env python3
"""
Test script for Ollama-based NLP processor
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chatbot.ollama_nlp_processor import OllamaMedicalNLPProcessor

async def test_ollama_nlp():
    """Test the Ollama-based NLP processor"""
    
    try:
        # Initialize the Ollama processor
        print("🤖 Initializing Ollama-based NLP processor...")
        nlp_processor = OllamaMedicalNLPProcessor(model="gpt-oss:20b")
        print("✅ Ollama processor initialized successfully")
        
        # Check health
        print("\n🏥 Checking Ollama health...")
        health = await nlp_processor.health_check()
        print(f"Health status: {health}")
        
        if health["status"] != "healthy":
            print("❌ Ollama is not available. Please install and start Ollama:")
            print("1. Install Ollama: https://ollama.ai")
            print("2. Start Ollama: ollama serve")
            print("3. Pull a model: ollama pull llama2")
            return False
        
        # Test queries
        test_queries = [
            "What medications is this patient taking?",
            "Show me the patient's conditions",
            "What observations does this patient have?",
            "Tell me about the patient's allergies",
            "What encounters has this patient had?",
            "Show me the lab specimens",
            "Are there any drug interactions?",
            "What's the latest evidence for diabetes treatment?",
            "Are there any clinical alerts for this patient?",
            "How is the patient doing overall?"
        ]
        
        print("\n🧪 Testing intent classification and entity extraction...")
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n--- Test {i}: {query} ---")
            
            # Test intent classification
            intent = await nlp_processor.classify_intent(query)
            print(f"Intent: {intent}")
            
            # Test entity extraction
            entities = await nlp_processor.extract_entities(query)
            print(f"Entities: {entities}")
            
            # Test context extraction
            context = await nlp_processor.extract_patient_context(query)
            print(f"Context: {context}")
            
            # Test complexity analysis
            complexity = await nlp_processor.analyze_query_complexity(query)
            print(f"Complexity: {complexity}")
            
            # Small delay to avoid overwhelming the local model
            await asyncio.sleep(0.5)
        
        # Close the client
        await nlp_processor.close()
        
        print("\n✅ All tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_ollama_nlp())
    sys.exit(0 if success else 1)
