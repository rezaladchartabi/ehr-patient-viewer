#!/usr/bin/env python3
"""
CLI Management Tool for Intent-Specific Prompts

Interactive command-line interface for managing and optimizing
intent-specific prompts in the medical chatbot system.
"""

import sys
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add the current directory to Python path
sys.path.append('.')

from chatbot.prompt_manager import PromptManager
from chatbot.ollama_nlp_processor import OllamaMedicalNLPProcessor

class PromptCLI:
    """Interactive CLI for managing intent-specific prompts"""
    
    def __init__(self):
        self.pm = PromptManager()
        self.nlp = OllamaMedicalNLPProcessor()
        self.running = True
    
    def print_header(self):
        """Print the CLI header"""
        print("\n" + "="*60)
        print("🔧 MEDICAL CHATBOT PROMPT MANAGEMENT CLI")
        print("="*60)
        print("Interactive tool for managing and optimizing intent-specific prompts")
        print("="*60)
    
    def print_menu(self):
        """Print the main menu"""
        print("\n📋 MAIN MENU:")
        print("1. 📊 View Intent Statistics")
        print("2. 🔍 List All Intents")
        print("3. 📝 View Intent Configuration")
        print("4. ✏️  Edit Intent Prompt")
        print("5. 🧪 Test Intent Classification")
        print("6. 📈 View Performance Metrics")
        print("7. 🔧 Add Optimization Note")
        print("8. 📋 Validate All Configurations")
        print("9. 🚀 Test with Sample Queries")
        print("0. ❌ Exit")
        print("-" * 40)
    
    def get_user_choice(self, max_choice: int) -> int:
        """Get user choice with validation"""
        while True:
            try:
                choice = input(f"Enter your choice (0-{max_choice}): ").strip()
                choice_int = int(choice)
                if 0 <= choice_int <= max_choice:
                    return choice_int
                else:
                    print(f"❌ Please enter a number between 0 and {max_choice}")
            except ValueError:
                print("❌ Please enter a valid number")
    
    def view_intent_statistics(self):
        """View intent statistics"""
        print("\n📊 INTENT STATISTICS:")
        print("-" * 40)
        
        stats = self.pm.get_prompt_statistics()
        print(f"Total Intents: {stats['total_intents']}")
        print(f"Active Intents: {stats['active_intents']}")
        print(f"Average Prompt Length: {stats['avg_prompt_length']} characters")
        print(f"Total Prompt Length: {stats['total_prompt_length']} characters")
        
        print(f"\n📋 Intent Distribution:")
        for intent, count in stats['intent_distribution'].items():
            print(f"  {intent}: {count} configs")
    
    def list_all_intents(self):
        """List all intents with details"""
        print("\n🔍 ALL INTENTS:")
        print("-" * 60)
        
        intents = self.pm.list_intents()
        for i, intent in enumerate(intents, 1):
            status_icon = "✅" if intent['status'] == 'active' else "⏳"
            priority_icon = "🔥" if intent['priority'] == 'high' else "⚡" if intent['priority'] == 'medium' else "💤"
            
            print(f"{i}. {status_icon} {priority_icon} {intent['intent']}")
            print(f"   Description: {intent['description']}")
            print(f"   Config File: {intent['config_file']}")
            print(f"   Status: {intent['status']} | Priority: {intent['priority']}")
            print()
    
    def view_intent_configuration(self):
        """View detailed configuration for a specific intent"""
        print("\n📝 VIEW INTENT CONFIGURATION:")
        print("-" * 40)
        
        # List available intents
        intents = self.pm.get_active_intents()
        print("Available intents:")
        for i, intent in enumerate(intents, 1):
            print(f"{i}. {intent}")
        
        choice = self.get_user_choice(len(intents))
        selected_intent = intents[choice - 1]
        
        # Get intent info
        intent_info = self.pm.get_intent_info(selected_intent)
        if not intent_info:
            print(f"❌ No configuration found for intent: {selected_intent}")
            return
        
        print(f"\n📋 Configuration for '{selected_intent}':")
        print("=" * 50)
        print(f"Description: {intent_info['description']}")
        print(f"Version: {intent_info['version']}")
        print(f"Created: {intent_info['created']}")
        print(f"Last Updated: {intent_info['last_updated']}")
        print(f"Optimization Notes: {intent_info['optimization_notes']}")
        
        print(f"\n🔑 Keywords:")
        for keyword in intent_info['keywords']:
            print(f"  • {keyword}")
        
        print(f"\n📝 Example Queries:")
        for query in intent_info['example_queries']:
            print(f"  • {query}")
        
        print(f"\n📊 Performance Metrics:")
        metrics = intent_info['performance_metrics']
        print(f"  Accuracy: {metrics['accuracy']:.2f}")
        print(f"  Precision: {metrics['precision']:.2f}")
        print(f"  Recall: {metrics['recall']:.2f}")
        print(f"  F1 Score: {metrics['f1_score']:.2f}")
        print(f"  Test Count: {metrics['test_count']}")
        
        print(f"\n📚 Data Source:")
        data_source = intent_info['data_source']
        print(f"  Primary: {data_source['primary']}")
        print(f"  Endpoint: {data_source['endpoint']}")
        print(f"  Description: {data_source['description']}")
    
    def edit_intent_prompt(self):
        """Edit prompt for a specific intent"""
        print("\n✏️  EDIT INTENT PROMPT:")
        print("-" * 40)
        
        # List available intents
        intents = self.pm.get_active_intents()
        print("Available intents:")
        for i, intent in enumerate(intents, 1):
            print(f"{i}. {intent}")
        
        choice = self.get_user_choice(len(intents))
        selected_intent = intents[choice - 1]
        
        # Get current prompt
        current_prompt = self.pm.get_intent_prompt(selected_intent)
        if not current_prompt:
            print(f"❌ No prompt found for intent: {selected_intent}")
            return
        
        print(f"\n📝 Current prompt for '{selected_intent}':")
        print("=" * 50)
        print(f"System Prompt:\n{current_prompt['system_prompt']}")
        print(f"\nUser Prompt:\n{current_prompt['user_prompt']}")
        
        print(f"\n🔧 Edit Options:")
        print("1. Edit System Prompt")
        print("2. Edit User Prompt")
        print("3. Edit Keywords")
        print("4. Add Example Query")
        print("5. Cancel")
        
        edit_choice = self.get_user_choice(5)
        
        if edit_choice == 1:
            print(f"\n✏️  Edit System Prompt:")
            print("Current system prompt:")
            print(current_prompt['system_prompt'])
            new_system = input("\nEnter new system prompt (or press Enter to keep current): ").strip()
            if new_system:
                # Update the prompt
                self._update_prompt_field(selected_intent, 'system_prompt', new_system)
                print("✅ System prompt updated!")
        
        elif edit_choice == 2:
            print(f"\n✏️  Edit User Prompt:")
            print("Current user prompt:")
            print(current_prompt['user_prompt'])
            new_user = input("\nEnter new user prompt (or press Enter to keep current): ").strip()
            if new_user:
                # Update the prompt
                self._update_prompt_field(selected_intent, 'user_prompt', new_user)
                print("✅ User prompt updated!")
        
        elif edit_choice == 3:
            self._edit_keywords(selected_intent)
        
        elif edit_choice == 4:
            self._add_example_query(selected_intent)
    
    def _update_prompt_field(self, intent: str, field: str, value: str):
        """Update a specific field in the prompt configuration"""
        intent_info = self.pm.get_intent_info(intent)
        if intent_info:
            intent_info['prompt_template'][field] = value
            intent_info['last_updated'] = datetime.now().strftime('%Y-%m-%d')
            self.pm._save_intent_config(intent, intent_info)
    
    def _edit_keywords(self, intent: str):
        """Edit keywords for an intent"""
        intent_info = self.pm.get_intent_info(intent)
        if not intent_info:
            return
        
        print(f"\n🔑 Current keywords for '{intent}':")
        for i, keyword in enumerate(intent_info['keywords'], 1):
            print(f"{i}. {keyword}")
        
        print(f"\nOptions:")
        print("1. Add keyword")
        print("2. Remove keyword")
        print("3. Cancel")
        
        choice = self.get_user_choice(3)
        
        if choice == 1:
            new_keyword = input("Enter new keyword: ").strip()
            if new_keyword:
                intent_info['keywords'].append(new_keyword)
                intent_info['last_updated'] = datetime.now().strftime('%Y-%m-%d')
                self.pm._save_intent_config(intent, intent_info)
                print("✅ Keyword added!")
        
        elif choice == 2:
            if intent_info['keywords']:
                remove_choice = self.get_user_choice(len(intent_info['keywords']))
                removed = intent_info['keywords'].pop(remove_choice - 1)
                intent_info['last_updated'] = datetime.now().strftime('%Y-%m-%d')
                self.pm._save_intent_config(intent, intent_info)
                print(f"✅ Removed keyword: {removed}")
    
    def _add_example_query(self, intent: str):
        """Add example query for an intent"""
        intent_info = self.pm.get_intent_info(intent)
        if not intent_info:
            return
        
        new_query = input("Enter new example query: ").strip()
        if new_query:
            intent_info['example_queries'].append(new_query)
            intent_info['last_updated'] = datetime.now().strftime('%Y-%m-%d')
            self.pm._save_intent_config(intent, intent_info)
            print("✅ Example query added!")
    
    async def test_intent_classification(self):
        """Test intent classification with a custom query"""
        print("\n🧪 TEST INTENT CLASSIFICATION:")
        print("-" * 40)
        
        query = input("Enter a test query: ").strip()
        if not query:
            print("❌ No query entered")
            return
        
        print(f"\n🔍 Testing query: '{query}'")
        print("-" * 30)
        
        try:
            # Test classification
            intent = await self.nlp.classify_intent(query)
            print(f"✅ Classified intent: {intent}")
            
            # Get prompt for the classified intent
            prompt = self.pm.get_intent_prompt(intent)
            if prompt:
                print(f"📋 Retrieved prompt for {intent}")
                print(f"   System prompt: {len(prompt['system_prompt'])} chars")
                print(f"   User prompt: {len(prompt['user_prompt'])} chars")
            else:
                print(f"⚠️  No prompt found for intent: {intent}")
                
        except Exception as e:
            print(f"❌ Error testing classification: {e}")
    
    def view_performance_metrics(self):
        """View performance metrics for all intents"""
        print("\n📈 PERFORMANCE METRICS:")
        print("-" * 60)
        
        intents = self.pm.get_active_intents()
        for intent in intents:
            intent_info = self.pm.get_intent_info(intent)
            if intent_info:
                metrics = intent_info['performance_metrics']
                print(f"\n📊 {intent}:")
                print(f"  Accuracy: {metrics['accuracy']:.2f}")
                print(f"  Precision: {metrics['precision']:.2f}")
                print(f"  Recall: {metrics['recall']:.2f}")
                print(f"  F1 Score: {metrics['f1_score']:.2f}")
                print(f"  Test Count: {metrics['test_count']}")
                if metrics['last_tested']:
                    print(f"  Last Tested: {metrics['last_tested']}")
    
    def add_optimization_note(self):
        """Add optimization note to an intent"""
        print("\n🔧 ADD OPTIMIZATION NOTE:")
        print("-" * 40)
        
        # List available intents
        intents = self.pm.get_active_intents()
        print("Available intents:")
        for i, intent in enumerate(intents, 1):
            print(f"{i}. {intent}")
        
        choice = self.get_user_choice(len(intents))
        selected_intent = intents[choice - 1]
        
        note = input(f"Enter optimization note for '{selected_intent}': ").strip()
        if note:
            self.pm.add_optimization_note(selected_intent, note)
            print("✅ Optimization note added!")
    
    def validate_all_configurations(self):
        """Validate all intent configurations"""
        print("\n📋 VALIDATION RESULTS:")
        print("-" * 40)
        
        validation_results = self.pm.validate_configurations()
        all_valid = True
        
        for intent, errors in validation_results.items():
            if errors:
                print(f"❌ {intent}: {len(errors)} errors")
                for error in errors:
                    print(f"   - {error}")
                all_valid = False
            else:
                print(f"✅ {intent}: Valid")
        
        if all_valid:
            print(f"\n🎉 All configurations are valid!")
        else:
            print(f"\n⚠️  Some configurations have errors that need to be fixed.")
    
    async def test_with_sample_queries(self):
        """Test with predefined sample queries"""
        print("\n🚀 TEST WITH SAMPLE QUERIES:")
        print("-" * 40)
        
        sample_queries = [
            ("What is the patient's past medical history?", "pmh_query"),
            ("What conditions does this patient have?", "condition_query"),
            ("What allergies does this patient have?", "allergy_query"),
            ("What medications is the patient taking?", "medication_query"),
            ("Show me the patient's vital signs", "observation_query"),
            ("What procedures has the patient had?", "procedure_query"),
        ]
        
        print("Testing sample queries...")
        print("-" * 30)
        
        correct = 0
        total = len(sample_queries)
        
        for query, expected_intent in sample_queries:
            print(f"\n📝 Query: '{query}'")
            print(f"   Expected: {expected_intent}")
            
            try:
                intent = await self.nlp.classify_intent(query)
                print(f"   Result: {intent}")
                
                if intent == expected_intent:
                    print(f"   ✅ CORRECT!")
                    correct += 1
                else:
                    print(f"   ❌ INCORRECT")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        accuracy = (correct / total) * 100
        print(f"\n📊 Test Results:")
        print(f"   Correct: {correct}/{total}")
        print(f"   Accuracy: {accuracy:.1f}%")
        
        if accuracy == 100:
            print(f"   🎉 Perfect classification!")
        elif accuracy >= 80:
            print(f"   ✅ Good classification!")
        else:
            print(f"   ⚠️  Needs optimization")
    
    async def run(self):
        """Run the CLI main loop"""
        self.print_header()
        
        while self.running:
            self.print_menu()
            choice = self.get_user_choice(9)
            
            try:
                if choice == 0:
                    print("\n👋 Goodbye!")
                    self.running = False
                elif choice == 1:
                    self.view_intent_statistics()
                elif choice == 2:
                    self.list_all_intents()
                elif choice == 3:
                    self.view_intent_configuration()
                elif choice == 4:
                    self.edit_intent_prompt()
                elif choice == 5:
                    await self.test_intent_classification()
                elif choice == 6:
                    self.view_performance_metrics()
                elif choice == 7:
                    self.add_optimization_note()
                elif choice == 8:
                    self.validate_all_configurations()
                elif choice == 9:
                    await self.test_with_sample_queries()
                
                if self.running:
                    input("\nPress Enter to continue...")
                    
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                self.running = False
            except Exception as e:
                print(f"\n❌ Error: {e}")
                input("Press Enter to continue...")

async def main():
    """Main entry point"""
    cli = PromptCLI()
    await cli.run()

if __name__ == "__main__":
    asyncio.run(main())
