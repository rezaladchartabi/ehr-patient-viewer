import { useState, useCallback, useEffect } from 'react';
import { Message } from '../components/ChatInterface';
import { chatbotApi, ChatbotRequest, ChatbotResponse } from '../services/chatbotApi';

interface UseChatbotProps {
  patientId?: string;
  patientName?: string;
}

interface UseChatbotReturn {
  messages: Message[];
  isLoading: boolean;
  sendMessage: (text: string) => Promise<void>;
  clearConversation: () => void;
  conversationId: string;
  error: string | null;
  clearError: () => void;
}

export const useChatbot = ({ patientId, patientName }: UseChatbotProps): UseChatbotReturn => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string>('');
  const [error, setError] = useState<string | null>(null);

  // Initialize conversation when patient changes
  useEffect(() => {
    if (patientId) {
      const newConversationId = `conv_${patientId}_${Date.now()}`;
      setConversationId(newConversationId);
      
      // Add welcome message
      const welcomeMessage: Message = {
        id: `welcome_${Date.now()}`,
        text: `Hello! I'm your AI medical assistant. I can help you with questions about ${patientName || 'this patient'}, including their conditions, medications, allergies, and provide evidence-based clinical insights. What would you like to know?`,
        sender: 'bot',
        timestamp: new Date(),
        status: 'sent',
        metadata: {
          confidence: 1.0
        }
      };
      
      setMessages([welcomeMessage]);
      setError(null);
    } else {
      setMessages([]);
      setConversationId('');
    }
  }, [patientId, patientName]);

  const sendMessage = useCallback(async (text: string) => {
    if (!text.trim() || !patientId) return;

    const userMessage: Message = {
      id: `user_${Date.now()}`,
      text: text.trim(),
      sender: 'user',
      timestamp: new Date(),
      status: 'sending'
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);

    try {
      const request: ChatbotRequest = {
        message: text.trim(),
        patientId,
        conversationId,
        timestamp: new Date().toISOString()
      };

      const response: ChatbotResponse = await chatbotApi.sendMessage(request);
      
      // Update user message status
      setMessages(prev => prev.map(msg => 
        msg.id === userMessage.id 
          ? { ...msg, status: 'sent' as const }
          : msg
      ));

      // Add bot response
      const botMessage: Message = {
        id: `bot_${Date.now()}`,
        text: response.response,
        sender: 'bot',
        timestamp: new Date(),
        status: 'sent',
        metadata: {
          evidence: response.evidence,
          sources: response.sources,
          confidence: response.confidence
        }
      };

      setMessages(prev => [...prev, botMessage]);

    } catch (err) {
      console.error('Error sending message:', err);
      
      // Update user message status to error
      setMessages(prev => prev.map(msg => 
        msg.id === userMessage.id 
          ? { ...msg, status: 'error' as const }
          : msg
      ));

      // Add error message
      const errorMessage: Message = {
        id: `error_${Date.now()}`,
        text: 'Sorry, I encountered an error while processing your request. Please try again.',
        sender: 'bot',
        timestamp: new Date(),
        status: 'sent'
      };

      setMessages(prev => [...prev, errorMessage]);
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
    } finally {
      setIsLoading(false);
    }
  }, [patientId, conversationId]);

  const clearConversation = useCallback(() => {
    setMessages([]);
    if (patientId) {
      const newConversationId = `conv_${patientId}_${Date.now()}`;
      setConversationId(newConversationId);
      
      // Add new welcome message
      const welcomeMessage: Message = {
        id: `welcome_${Date.now()}`,
        text: `Hello! I'm your AI medical assistant. I can help you with questions about ${patientName || 'this patient'}, including their conditions, medications, allergies, and provide evidence-based clinical insights. What would you like to know?`,
        sender: 'bot',
        timestamp: new Date(),
        status: 'sent',
        metadata: {
          confidence: 1.0
        }
      };
      
      setMessages([welcomeMessage]);
    }
    setError(null);
  }, [patientId, patientName]);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    messages,
    isLoading,
    sendMessage,
    clearConversation,
    conversationId,
    error,
    clearError
  };
};
