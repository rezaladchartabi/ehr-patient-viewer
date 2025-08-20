import { Message } from '../components/ChatInterface';

export interface ChatbotRequest {
  message: string;
  patientId: string;
  conversationId: string;
  timestamp: string;
}

export interface ChatbotResponse {
  response: string;
  evidence?: any[];
  sources?: string[];
  confidence?: number;
  conversationId: string;
  timestamp: string;
}

export interface ConversationHistory {
  conversationId: string;
  messages: Message[];
  patientId: string;
  createdAt: string;
  updatedAt: string;
}

class ChatbotApiService {
  private baseUrl: string;

  constructor() {
    // Use deployed backend for chatbot
    this.baseUrl = process.env.REACT_APP_API_BASE_URL || 'https://ehr-backend-87r9.onrender.com';
  }

  async sendMessage(request: ChatbotRequest): Promise<ChatbotResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/chatbot/message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error sending message to chatbot:', error);
      throw error;
    }
  }

  async getConversationHistory(patientId: string, conversationId?: string): Promise<ConversationHistory[]> {
    try {
      const params = new URLSearchParams({ patientId });
      if (conversationId) {
        params.append('conversationId', conversationId);
      }

      const response = await fetch(`${this.baseUrl}/chatbot/conversations?${params}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching conversation history:', error);
      throw error;
    }
  }

  async saveConversation(conversation: ConversationHistory): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/chatbot/conversations`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(conversation)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
    } catch (error) {
      console.error('Error saving conversation:', error);
      throw error;
    }
  }

  async deleteConversation(conversationId: string): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/chatbot/conversations/${conversationId}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
    } catch (error) {
      console.error('Error deleting conversation:', error);
      throw error;
    }
  }

  async getSuggestedQuestions(patientId: string): Promise<string[]> {
    try {
      const response = await fetch(`${this.baseUrl}/chatbot/suggestions?patientId=${patientId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching suggested questions:', error);
      // Return default suggestions if API fails
      return [
        "What medications is this patient currently taking?",
        "Are there any drug interactions with their medications?",
        "What conditions has this patient been diagnosed with?",
        "Show me the patient's allergies",
        "What's the latest evidence for treating their condition?",
        "Are there any clinical alerts for this patient?"
      ];
    }
  }

  async getPatientSummary(patientId: string): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/patients/summary?patient=${patientId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching patient summary:', error);
      throw error;
    }
  }

  async searchEvidence(query: string, filters?: any): Promise<any[]> {
    try {
      const params = new URLSearchParams({ q: query });
      if (filters) {
        Object.entries(filters).forEach(([key, value]) => {
          params.append(key, String(value));
        });
      }

      const response = await fetch(`${this.baseUrl}/chatbot/evidence/search?${params}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error searching evidence:', error);
      return [];
    }
  }

  async getDrugInfo(drugName: string): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/chatbot/drugs/${encodeURIComponent(drugName)}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching drug info:', error);
      throw error;
    }
  }

  async getClinicalAlerts(patientId: string): Promise<any[]> {
    try {
      const response = await fetch(`${this.baseUrl}/chatbot/alerts?patientId=${patientId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching clinical alerts:', error);
      return [];
    }
  }

  // Health check for the chatbot service
  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/chatbot/health`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      return response.ok;
    } catch (error) {
      console.error('Chatbot health check failed:', error);
      return false;
    }
  }
}

// Export singleton instance
export const chatbotApi = new ChatbotApiService();
export default chatbotApi;
