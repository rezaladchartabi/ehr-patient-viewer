"""
Medical Response Generator

Generates evidence-based responses for medical queries using patient data
and external medical knowledge sources.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class MedicalResponseGenerator:
    """Generates medical responses based on queries and evidence"""
    
    def __init__(self):
        # Response templates for different intents
        self.response_templates = {
            'medication_query': {
                'found': "Based on the patient's records, they are currently taking the following medications:\n{medications}\n\n{additional_info}",
                'not_found': "I don't see any current medications recorded for this patient. Would you like me to check for past medication history or help you add new medications?",
                'no_data': "I don't have access to the patient's medication records at the moment. Please ensure the patient data is loaded."
            },
            'condition_query': {
                'found': "The patient has been diagnosed with the following conditions:\n{conditions}\n\n{additional_info}",
                'not_found': "I don't see any recorded conditions for this patient. Would you like me to check their medical history or help you add new conditions?",
                'no_data': "I don't have access to the patient's condition records at the moment. Please ensure the patient data is loaded."
            },
            'allergy_query': {
                'found': "The patient has the following known allergies:\n{allergies}\n\n{additional_info}",
                'not_found': "No known allergies are recorded for this patient. Would you like me to check for any adverse reactions or help you add allergy information?",
                'no_data': "I don't have access to the patient's allergy records at the moment. Please ensure the patient data is loaded."
            },
            'interaction_query': {
                'found': "I found the following potential drug interactions:\n{interactions}\n\n{recommendations}",
                'not_found': "No significant drug interactions were found with the current medications. However, it's always good practice to monitor for any adverse effects.",
                'no_data': "I don't have enough medication data to check for interactions. Please ensure the patient's medications are loaded."
            },
            'evidence_query': {
                'found': "Here's the latest clinical evidence for {condition}:\n{evidence}\n\n{recommendations}",
                'not_found': "I couldn't find specific clinical evidence for that query. Would you like me to search for related conditions or treatments?",
                'no_data': "I don't have access to clinical evidence databases at the moment. Please try again later."
            },
            'alert_query': {
                'found': "I found the following clinical alerts for this patient:\n{alerts}\n\n{recommendations}",
                'not_found': "No active clinical alerts were found for this patient at this time.",
                'no_data': "I don't have access to clinical alert systems at the moment. Please check with your clinical team."
            },
            'general_query': {
                'default': "I can help you with information about the patient's medications, conditions, allergies, drug interactions, and clinical evidence. What specific information would you like to know?"
            }
        }
        
        # Evidence formatting templates
        self.evidence_templates = {
            'clinical_trial': "📊 Clinical Trial: {title}\n📅 Published: {date}\n📝 {summary}\n🎯 Evidence Level: {level}",
            'systematic_review': "📚 Systematic Review: {title}\n📅 Published: {date}\n📝 {summary}\n🎯 Evidence Level: {level}",
            'guideline': "📋 Clinical Guideline: {title}\n📅 Published: {date}\n📝 {summary}\n🎯 Evidence Level: {level}",
            'drug_info': "💊 Drug Information: {name}\n📝 {description}\n⚠️ Side Effects: {side_effects}",
            'interaction': "⚠️ Drug Interaction: {drug1} + {drug2}\n📝 {description}\n🎯 Severity: {severity}"
        }
    
    async def generate_response(self, query: str, intent: str, entities: List[str], 
                              patient_data: Dict[str, Any], evidence: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a comprehensive response based on the query and available data"""
        try:
            logger.info(f"Generating response for intent: {intent}")
            
            # Generate base response
            response_text = await self._generate_base_response(intent, entities, patient_data, evidence)
            
            # Add evidence citations
            evidence_list = await self._format_evidence(evidence)
            
            # Add sources
            sources = await self._extract_sources(evidence)
            
            # Calculate confidence
            confidence = await self._calculate_confidence(intent, entities, patient_data, evidence)
            
            # Add recommendations
            recommendations = await self._generate_recommendations(intent, entities, patient_data, evidence)
            
            if recommendations:
                response_text += f"\n\n💡 Recommendations:\n{recommendations}"
            
            return {
                "text": response_text,
                "evidence": evidence_list,
                "sources": sources,
                "confidence": confidence,
                "intent": intent,
                "entities": entities,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {
                "text": "I apologize, but I encountered an error while generating a response. Please try rephrasing your question.",
                "evidence": [],
                "sources": [],
                "confidence": 0.0,
                "error": str(e)
            }
    
    async def _generate_base_response(self, intent: str, entities: List[str], 
                                    patient_data: Dict[str, Any], evidence: Dict[str, Any]) -> str:
        """Generate the base response text"""
        templates = self.response_templates.get(intent, self.response_templates['general_query'])
        
        if intent == 'medication_query':
            medications = patient_data.get('medications', [])
            if medications:
                med_list = self._format_medication_list(medications)
                additional_info = self._get_medication_additional_info(medications, evidence)
                return templates['found'].format(medications=med_list, additional_info=additional_info)
            else:
                return templates['not_found']
        
        elif intent == 'condition_query':
            conditions = patient_data.get('conditions', [])
            if conditions:
                condition_list = self._format_condition_list(conditions)
                additional_info = self._get_condition_additional_info(conditions, evidence)
                return templates['found'].format(conditions=condition_list, additional_info=additional_info)
            else:
                return templates['not_found']
        
        elif intent == 'allergy_query':
            allergies = patient_data.get('allergies', [])
            if allergies:
                allergy_list = self._format_allergy_list(allergies)
                additional_info = self._get_allergy_additional_info(allergies, evidence)
                return templates['found'].format(allergies=allergy_list, additional_info=additional_info)
            else:
                return templates['not_found']
        
        elif intent == 'interaction_query':
            interactions = evidence.get('interactions', [])
            if interactions:
                interaction_list = self._format_interaction_list(interactions)
                recommendations = self._get_interaction_recommendations(interactions)
                return templates['found'].format(interactions=interaction_list, recommendations=recommendations)
            else:
                return templates['not_found']
        
        elif intent == 'evidence_query':
            clinical_evidence = evidence.get('clinical_evidence', [])
            if clinical_evidence:
                evidence_text = self._format_evidence_list(clinical_evidence)
                recommendations = self._get_evidence_recommendations(clinical_evidence)
                return templates['found'].format(condition=entities[0] if entities else "the condition", 
                                               evidence=evidence_text, recommendations=recommendations)
            else:
                return templates['not_found']
        
        elif intent == 'alert_query':
            alerts = evidence.get('alerts', [])
            if alerts:
                alert_list = self._format_alert_list(alerts)
                recommendations = self._get_alert_recommendations(alerts)
                return templates['found'].format(alerts=alert_list, recommendations=recommendations)
            else:
                return templates['not_found']
        
        else:
            return templates.get('default', "I can help you with medical information. What would you like to know?")
    
    async def _format_evidence(self, evidence: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Format evidence for display"""
        formatted_evidence = []
        
        # Format clinical evidence
        for item in evidence.get('clinical_evidence', []):
            formatted_evidence.append({
                "type": "clinical_evidence",
                "title": item.get('title', 'Clinical Evidence'),
                "abstract": item.get('abstract', ''),
                "journal": item.get('journal', ''),
                "evidence_level": item.get('evidence_level', ''),
                "relevance_score": item.get('relevance_score', 0.0)
            })
        
        # Format drug information
        for item in evidence.get('drug_info', []):
            formatted_evidence.append({
                "type": "drug_info",
                "title": f"Drug Information: {item.get('name', 'Unknown')}",
                "abstract": item.get('description', ''),
                "journal": "RxNorm Database",
                "evidence_level": "Standard Reference",
                "relevance_score": 0.9
            })
        
        return formatted_evidence
    
    async def _extract_sources(self, evidence: Dict[str, Any]) -> List[str]:
        """Extract source information from evidence"""
        sources = []
        
        # Add evidence sources
        for item in evidence.get('clinical_evidence', []):
            if item.get('journal'):
                sources.append(item['journal'])
        
        # Add knowledge base sources
        knowledge_results = evidence.get('knowledge_base', [])
        for item in knowledge_results:
            if item.get('source_name'):
                sources.append(item['source_name'])
        
        # Remove duplicates
        return list(set(sources))
    
    async def _calculate_confidence(self, intent: str, entities: List[str], 
                                  patient_data: Dict[str, Any], evidence: Dict[str, Any]) -> float:
        """Calculate confidence score for the response"""
        confidence = 0.5  # Base confidence
        
        # Increase confidence based on available data
        if patient_data:
            confidence += 0.2
        
        if entities:
            confidence += 0.1
        
        if evidence.get('clinical_evidence'):
            confidence += 0.1
        
        if evidence.get('drug_info'):
            confidence += 0.1
        
        # Decrease confidence for complex queries
        if len(entities) > 3:
            confidence -= 0.1
        
        # Cap confidence at 1.0
        return min(confidence, 1.0)
    
    async def _generate_recommendations(self, intent: str, entities: List[str], 
                                      patient_data: Dict[str, Any], evidence: Dict[str, Any]) -> str:
        """Generate clinical recommendations"""
        recommendations = []
        
        if intent == 'medication_query':
            recommendations.append("• Monitor for medication adherence and side effects")
            recommendations.append("• Review medication list regularly for potential interactions")
            recommendations.append("• Consider medication reconciliation at each visit")
        
        elif intent == 'interaction_query':
            recommendations.append("• Monitor patient for signs of interaction")
            recommendations.append("• Consider alternative medications if needed")
            recommendations.append("• Document any adverse effects")
        
        elif intent == 'evidence_query':
            recommendations.append("• Consider the latest clinical guidelines")
            recommendations.append("• Individualize treatment based on patient factors")
            recommendations.append("• Monitor patient response to treatment")
        
        return "\n".join(recommendations)
    
    def _format_medication_list(self, medications: List[Dict]) -> str:
        """Format medication list for display"""
        if not medications:
            return "No medications found"
        
        formatted = []
        for med in medications:
            name = med.get('name', 'Unknown medication')
            dosage = med.get('dosage', '')
            frequency = med.get('frequency', '')
            
            med_text = f"• {name}"
            if dosage:
                med_text += f" - {dosage}"
            if frequency:
                med_text += f" {frequency}"
            
            formatted.append(med_text)
        
        return "\n".join(formatted)
    
    def _format_condition_list(self, conditions: List[Dict]) -> str:
        """Format condition list for display"""
        if not conditions:
            return "No conditions found"
        
        formatted = []
        for condition in conditions:
            name = condition.get('name', 'Unknown condition')
            status = condition.get('status', '')
            date = condition.get('date', '')
            
            condition_text = f"• {name}"
            if status:
                condition_text += f" ({status})"
            if date:
                condition_text += f" - {date}"
            
            formatted.append(condition_text)
        
        return "\n".join(formatted)
    
    def _format_allergy_list(self, allergies: List[Dict]) -> str:
        """Format allergy list for display"""
        if not allergies:
            return "No allergies found"
        
        formatted = []
        for allergy in allergies:
            name = allergy.get('name', 'Unknown allergy')
            severity = allergy.get('severity', '')
            reaction = allergy.get('reaction', '')
            
            allergy_text = f"• {name}"
            if severity:
                allergy_text += f" ({severity})"
            if reaction:
                allergy_text += f" - {reaction}"
            
            formatted.append(allergy_text)
        
        return "\n".join(formatted)
    
    def _get_medication_additional_info(self, medications: List[Dict], evidence: Dict[str, Any]) -> str:
        """Get additional medication information"""
        info = []
        
        if evidence.get('drug_info'):
            info.append("📊 Drug information available from RxNorm database")
        
        if evidence.get('interactions'):
            info.append("⚠️ Drug interaction analysis completed")
        
        return "\n".join(info) if info else ""
    
    def _get_condition_additional_info(self, conditions: List[Dict], evidence: Dict[str, Any]) -> str:
        """Get additional condition information"""
        info = []
        
        if evidence.get('clinical_evidence'):
            info.append("📚 Clinical evidence available for treatment options")
        
        return "\n".join(info) if info else ""
    
    def _get_allergy_additional_info(self, allergies: List[Dict], evidence: Dict[str, Any]) -> str:
        """Get additional allergy information"""
        info = []
        
        if evidence.get('interactions'):
            info.append("⚠️ Allergy contraindication analysis completed")
        
        return "\n".join(info) if info else ""
    
    def _format_interaction_list(self, interactions: List[Dict]) -> str:
        """Format interaction list for display"""
        if not interactions:
            return "No interactions found"
        
        formatted = []
        for interaction in interactions:
            drugs = interaction.get('drugs', [])
            severity = interaction.get('severity', 'Unknown')
            description = interaction.get('description', '')
            
            interaction_text = f"• {' + '.join(drugs)} ({severity})"
            if description:
                interaction_text += f": {description}"
            
            formatted.append(interaction_text)
        
        return "\n".join(formatted)
    
    def _get_interaction_recommendations(self, interactions: List[Dict]) -> str:
        """Get interaction recommendations"""
        return "• Monitor for signs of interaction\n• Consider alternative medications\n• Document any adverse effects"
    
    def _format_evidence_list(self, evidence: List[Dict]) -> str:
        """Format evidence list for display"""
        if not evidence:
            return "No evidence found"
        
        formatted = []
        for item in evidence[:3]:  # Limit to 3 items
            title = item.get('title', 'Unknown')
            level = item.get('evidence_level', 'Unknown')
            formatted.append(f"• {title} (Level: {level})")
        
        return "\n".join(formatted)
    
    def _get_evidence_recommendations(self, evidence: List[Dict]) -> str:
        """Get evidence-based recommendations"""
        return "• Consider the latest clinical guidelines\n• Individualize treatment based on patient factors"
    
    def _format_alert_list(self, alerts: List[Dict]) -> str:
        """Format alert list for display"""
        if not alerts:
            return "No alerts found"
        
        formatted = []
        for alert in alerts:
            type_alert = alert.get('type', 'Unknown')
            message = alert.get('message', '')
            severity = alert.get('severity', 'Unknown')
            
            alert_text = f"• {type_alert} ({severity})"
            if message:
                alert_text += f": {message}"
            
            formatted.append(alert_text)
        
        return "\n".join(formatted)
    
    def _get_alert_recommendations(self, alerts: List[Dict]) -> str:
        """Get alert recommendations"""
        return "• Review alerts immediately\n• Take appropriate clinical action\n• Document response to alerts"
