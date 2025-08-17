#!/usr/bin/env python3
"""
Test script for NLP processor integration with PromptManager
"""

import sys
import asyncio
from pathlib import Path

# Add the current directory to Python path
sys.path.append('.')

from chatbot.ollama_nlp_processor import OllamaMedicalNLPProcessor
from chatbot.prompt_manager import PromptManager

async def test_nlp_integration():
    """Test the NLP processor integration with PromptManager"""
    
    print("🧪 Testing NLP Integration with PromptManager...")
    
    try:
        # Initialize PromptManager
        pm = PromptManager()
        print(f"✅ PromptManager initialized")
        
        # Initialize Ollama NLP processor
        nlp = OllamaMedicalNLPProcessor()
        print(f"✅ Ollama NLP processor initialized")
        
        # Test queries for different intents
        test_queries = [
            ("What is the patient past medical history?", "pmh_query"),
            ("What conditions does this patient have?", "condition_query"),
            ("What allergies does this patient have?", "allergy_query"),
            ("What medications is the patient taking?", "medication_query"),
        ]
        
        print(f"\n🔍 Testing intent classification with PromptManager...")
        
        for query, expected_intent in test_queries:
            print(f"\n📝 Testing query: '{query}'")
            print(f"   Expected intent: {expected_intent}")
            
            # Test intent classification
            try:
                intent = await nlp.classify_intent(query)
                print(f"   ✅ Classified intent: {intent}")
                
                if intent == expected_intent:
                    print(f"   🎯 CORRECT classification!")
                else:
                    print(f"   ❌ INCORRECT classification (expected: {expected_intent})")
                
                # Test prompt retrieval
                prompt = pm.get_intent_prompt(intent)
                if prompt:
                    print(f"   📋 Retrieved prompt for {intent}")
                    print(f"      System prompt: {len(prompt['system_prompt'])} chars")
                    print(f"      User prompt: {len(prompt['user_prompt'])} chars")
                else:
                    print(f"   ⚠️  No prompt found for intent: {intent}")
                    
            except Exception as e:
                print(f"   ❌ Error testing query: {e}")
        
        # Test PromptManager functionality
        print(f"\n📊 PromptManager Statistics:")
        stats = pm.get_prompt_statistics()
        print(f"   Total intents: {stats['total_intents']}")
        print(f"   Active intents: {stats['active_intents']}")
        print(f"   Average prompt length: {stats['avg_prompt_length']} chars")
        
        # Test validation
        print(f"\n🔍 Configuration Validation:")
        validation_results = pm.validate_configurations()
        for intent, errors in validation_results.items():
            if errors:
                print(f"   ❌ {intent}: {len(errors)} errors")
            else:
                print(f"   ✅ {intent}: Valid")
        
        print(f"\n🎉 NLP Integration test completed!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_nlp_integration())
    sys.exit(0 if success else 1)
