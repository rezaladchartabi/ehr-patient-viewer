#!/usr/bin/env python3
"""
Debug script for allergy intent classification
"""

import sys
import asyncio

# Add the current directory to Python path
sys.path.append('.')

from chatbot.ollama_nlp_processor import OllamaMedicalNLPProcessor

async def debug_allergy_classification():
    """Debug the allergy intent classification"""
    
    print("🔍 Debugging Allergy Intent Classification...")
    
    # Initialize NLP processor
    nlp = OllamaMedicalNLPProcessor()
    
    # Test query
    test_query = "What allergies does this patient have?"
    print(f"📝 Test query: '{test_query}'")
    
    # Test fallback classification directly
    print(f"\n🔧 Testing fallback classification...")
    fallback_result = await nlp._fallback_intent_classification(test_query)
    print(f"   Fallback result: {fallback_result}")
    
    # Test full classification
    print(f"\n🔧 Testing full classification...")
    full_result = await nlp.classify_intent(test_query)
    print(f"   Full result: {full_result}")
    
    # Debug the text processing
    text_lower = test_query.lower()
    print(f"\n🔧 Text processing debug:")
    print(f"   Original: '{test_query}'")
    print(f"   Lowercase: '{text_lower}'")
    
    # Check each keyword
    allergy_keywords = ['allergy', 'allergies', 'allergic', 'reaction', 'intolerance', 'known allergies', 'allergy list', 'drug allergy', 'food allergy', 'patient allergies', 'what allergies']
    print(f"\n🔧 Checking allergy keywords:")
    for keyword in allergy_keywords:
        if keyword in text_lower:
            print(f"   ✅ '{keyword}' found in text")
        else:
            print(f"   ❌ '{keyword}' NOT found in text")
    
    # Check other keywords that might interfere
    other_keywords = ['condition', 'conditions', 'medication', 'med', 'drug', 'prescription']
    print(f"\n🔧 Checking other keywords:")
    for keyword in other_keywords:
        if keyword in text_lower:
            print(f"   ⚠️  '{keyword}' found in text (might interfere)")
        else:
            print(f"   ✅ '{keyword}' NOT found in text")

if __name__ == "__main__":
    asyncio.run(debug_allergy_classification())
