"""
Prompt Manager for Intent-Specific Prompt Management System

This module provides a centralized way to manage and optimize prompts for each intent type.
"""

import json
import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class PromptManager:
    """Manages intent-specific prompts and configurations"""
    
    def __init__(self, config_dir: str = "chatbot/intent_configs"):
        """
        Initialize the Prompt Manager
        
        Args:
            config_dir: Directory containing intent configuration files
        """
        self.config_dir = Path(config_dir)
        self.intents_config = {}
        self.master_config = {}
        self._load_configurations()
    
    def _load_configurations(self):
        """Load all intent configurations and master config"""
        try:
            # Load master configuration
            master_config_path = self.config_dir / "intents.json"
            if master_config_path.exists():
                with open(master_config_path, 'r') as f:
                    self.master_config = json.load(f)
                logger.info(f"Loaded master configuration with {len(self.master_config.get('intents', []))} intents")
            
            # Load individual intent configurations
            for intent_info in self.master_config.get('intents', []):
                intent_name = intent_info['intent']
                config_file = intent_info['config_file']
                config_path = self.config_dir / config_file
                
                if config_path.exists():
                    with open(config_path, 'r') as f:
                        self.intents_config[intent_name] = json.load(f)
                    logger.info(f"Loaded configuration for intent: {intent_name}")
                else:
                    logger.warning(f"Configuration file not found for intent {intent_name}: {config_path}")
                    
        except Exception as e:
            logger.error(f"Error loading configurations: {e}")
            raise
    
    def get_intent_prompt(self, intent: str) -> Optional[Dict[str, str]]:
        """
        Get the prompt template for a specific intent
        
        Args:
            intent: The intent name (e.g., 'pmh_query', 'condition_query')
            
        Returns:
            Dictionary with 'system_prompt' and 'user_prompt' keys, or None if not found
        """
        if intent not in self.intents_config:
            logger.warning(f"Intent configuration not found: {intent}")
            return None
        
        config = self.intents_config[intent]
        prompt_template = config.get('prompt_template', {})
        
        return {
            'system_prompt': prompt_template.get('system_prompt', ''),
            'user_prompt': prompt_template.get('user_prompt', '')
        }
    
    def get_intent_info(self, intent: str) -> Optional[Dict[str, Any]]:
        """
        Get complete information for a specific intent
        
        Args:
            intent: The intent name
            
        Returns:
            Complete intent configuration dictionary, or None if not found
        """
        return self.intents_config.get(intent)
    
    def list_intents(self) -> List[Dict[str, Any]]:
        """
        List all available intents with their metadata
        
        Returns:
            List of intent information dictionaries
        """
        return self.master_config.get('intents', [])
    
    def get_active_intents(self) -> List[str]:
        """
        Get list of active intent names
        
        Returns:
            List of active intent names
        """
        return [
            intent_info['intent'] 
            for intent_info in self.master_config.get('intents', [])
            if intent_info.get('status') == 'active'
        ]
    
    def test_intent_prompt(self, intent: str, test_query: str) -> Dict[str, Any]:
        """
        Test a prompt with a sample query
        
        Args:
            intent: The intent name
            test_query: The query to test
            
        Returns:
            Dictionary with test results
        """
        prompt = self.get_intent_prompt(intent)
        if not prompt:
            return {
                'success': False,
                'error': f'Intent configuration not found: {intent}'
            }
        
        # Format the prompt with the test query
        formatted_prompt = prompt['user_prompt'].format(query=test_query)
        
        return {
            'success': True,
            'intent': intent,
            'test_query': test_query,
            'system_prompt': prompt['system_prompt'],
            'formatted_prompt': formatted_prompt,
            'config': self.get_intent_info(intent)
        }
    
    def update_performance_metrics(self, intent: str, metrics: Dict[str, float]):
        """
        Update performance metrics for an intent
        
        Args:
            intent: The intent name
            metrics: Dictionary with performance metrics
        """
        if intent not in self.intents_config:
            logger.warning(f"Cannot update metrics for unknown intent: {intent}")
            return
        
        config = self.intents_config[intent]
        config['performance_metrics'].update(metrics)
        config['performance_metrics']['last_tested'] = datetime.now().isoformat()
        config['performance_metrics']['test_count'] += 1
        
        # Save updated configuration
        self._save_intent_config(intent, config)
        logger.info(f"Updated performance metrics for intent: {intent}")
    
    def add_optimization_note(self, intent: str, note: str):
        """
        Add an optimization note to an intent
        
        Args:
            intent: The intent name
            note: The optimization note
        """
        if intent not in self.intents_config:
            logger.warning(f"Cannot add note for unknown intent: {intent}")
            return
        
        config = self.intents_config[intent]
        config['optimization_notes'] = note
        config['last_updated'] = datetime.now().strftime('%Y-%m-%d')
        
        # Save updated configuration
        self._save_intent_config(intent, config)
        logger.info(f"Added optimization note for intent: {intent}")
    
    def add_optimization_history(self, intent: str, change: str, reason: str, result: str):
        """
        Add an entry to the optimization history
        
        Args:
            intent: The intent name
            change: Description of the change made
            reason: Reason for the change
            result: Result of the change
        """
        if intent not in self.intents_config:
            logger.warning(f"Cannot add history for unknown intent: {intent}")
            return
        
        config = self.intents_config[intent]
        history_entry = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'change': change,
            'reason': reason,
            'result': result
        }
        
        config['optimization_history'].append(history_entry)
        config['last_updated'] = datetime.now().strftime('%Y-%m-%d')
        
        # Save updated configuration
        self._save_intent_config(intent, config)
        logger.info(f"Added optimization history for intent: {intent}")
    
    def _save_intent_config(self, intent: str, config: Dict[str, Any]):
        """
        Save an intent configuration back to file
        
        Args:
            intent: The intent name
            config: The configuration to save
        """
        try:
            intent_info = next(
                (info for info in self.master_config.get('intents', []) 
                 if info['intent'] == intent), 
                None
            )
            
            if not intent_info:
                logger.error(f"Intent not found in master config: {intent}")
                return
            
            config_file = intent_info['config_file']
            config_path = self.config_dir / config_file
            
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
                
            logger.info(f"Saved configuration for intent: {intent}")
            
        except Exception as e:
            logger.error(f"Error saving configuration for intent {intent}: {e}")
    
    def validate_configurations(self) -> Dict[str, List[str]]:
        """
        Validate all intent configurations
        
        Returns:
            Dictionary with validation results for each intent
        """
        validation_results = {}
        
        for intent_name, config in self.intents_config.items():
            errors = []
            
            # Check required fields
            required_fields = ['intent', 'description', 'prompt_template']
            for field in required_fields:
                if field not in config:
                    errors.append(f"Missing required field: {field}")
            
            # Check prompt template structure
            if 'prompt_template' in config:
                prompt_template = config['prompt_template']
                if 'system_prompt' not in prompt_template:
                    errors.append("Missing system_prompt in prompt_template")
                if 'user_prompt' not in prompt_template:
                    errors.append("Missing user_prompt in prompt_template")
            
            # Check performance metrics structure
            if 'performance_metrics' in config:
                metrics = config['performance_metrics']
                required_metrics = ['accuracy', 'precision', 'recall', 'f1_score', 'test_count']
                for metric in required_metrics:
                    if metric not in metrics:
                        errors.append(f"Missing performance metric: {metric}")
            
            validation_results[intent_name] = errors
        
        return validation_results
    
    def get_prompt_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about all prompts
        
        Returns:
            Dictionary with prompt statistics
        """
        stats = {
            'total_intents': len(self.intents_config),
            'active_intents': len(self.get_active_intents()),
            'intents_by_priority': {'high': 0, 'medium': 0, 'low': 0},
            'intents_by_status': {'active': 0, 'pending': 0},
            'avg_prompt_length': 0,
            'total_keywords': 0,
            'total_examples': 0
        }
        
        total_prompt_length = 0
        total_keywords = 0
        total_examples = 0
        
        for intent_info in self.master_config.get('intents', []):
            priority = intent_info.get('priority', 'low')
            status = intent_info.get('status', 'pending')
            
            stats['intents_by_priority'][priority] += 1
            stats['intents_by_status'][status] += 1
            
            intent_name = intent_info['intent']
            if intent_name in self.intents_config:
                config = self.intents_config[intent_name]
                
                # Calculate prompt length
                prompt = self.get_intent_prompt(intent_name)
                if prompt:
                    total_prompt_length += len(prompt['system_prompt']) + len(prompt['user_prompt'])
                
                # Count keywords and examples
                total_keywords += len(config.get('keywords', []))
                total_examples += len(config.get('example_queries', []))
        
        if stats['total_intents'] > 0:
            stats['avg_prompt_length'] = total_prompt_length // stats['total_intents']
            stats['total_keywords'] = total_keywords
            stats['total_examples'] = total_examples
        
        return stats
