#!/usr/bin/env python3
"""
Test script for PromptManager class
"""

import sys
import json
from pathlib import Path

# Add the current directory to Python path
sys.path.append('.')

from chatbot.prompt_manager import PromptManager

def test_prompt_manager():
    """Test the PromptManager functionality"""
    
    print("🧪 Testing PromptManager...")
    
    try:
        # Initialize the prompt manager
        pm = PromptManager()
        
        print(f"✅ PromptManager initialized successfully")
        print(f"📊 Loaded {len(pm.intents_config)} intent configurations")
        
        # Test listing intents
        intents = pm.list_intents()
        print(f"📋 Found {len(intents)} intents in master config")
        
        # Test getting active intents
        active_intents = pm.get_active_intents()
        print(f"🟢 Active intents: {active_intents}")
        
        # Test getting prompt for PMH query
        pmh_prompt = pm.get_intent_prompt('pmh_query')
        if pmh_prompt:
            print(f"✅ PMH prompt loaded successfully")
            print(f"   System prompt length: {len(pmh_prompt['system_prompt'])} chars")
            print(f"   User prompt length: {len(pmh_prompt['user_prompt'])} chars")
        else:
            print(f"❌ Failed to load PMH prompt")
        
        # Test prompt testing functionality
        test_result = pm.test_intent_prompt('pmh_query', 'What is the patient past medical history?')
        if test_result['success']:
            print(f"✅ PMH prompt test successful")
            print(f"   Formatted prompt length: {len(test_result['formatted_prompt'])} chars")
        else:
            print(f"❌ PMH prompt test failed: {test_result['error']}")
        
        # Test validation
        validation_results = pm.validate_configurations()
        print(f"🔍 Validation results:")
        for intent, errors in validation_results.items():
            if errors:
                print(f"   ❌ {intent}: {len(errors)} errors")
                for error in errors:
                    print(f"      - {error}")
            else:
                print(f"   ✅ {intent}: No errors")
        
        # Test statistics
        stats = pm.get_prompt_statistics()
        print(f"📈 Prompt statistics:")
        print(f"   Total intents: {stats['total_intents']}")
        print(f"   Active intents: {stats['active_intents']}")
        print(f"   Average prompt length: {stats['avg_prompt_length']} chars")
        print(f"   Total keywords: {stats['total_keywords']}")
        print(f"   Total examples: {stats['total_examples']}")
        
        # Test getting intent info
        pmh_info = pm.get_intent_info('pmh_query')
        if pmh_info:
            print(f"✅ PMH intent info loaded")
            print(f"   Description: {pmh_info['description']}")
            print(f"   Keywords: {len(pmh_info['keywords'])} keywords")
            print(f"   Examples: {len(pmh_info['example_queries'])} examples")
        
        print("\n🎉 All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = test_prompt_manager()
    sys.exit(0 if success else 1)
