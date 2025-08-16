import React, { useState } from 'react';
import { Message } from './ChatInterface';

interface MessageBubbleProps {
  message: Message;
  patientName?: string;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ message, patientName }) => {
  const [showEvidence, setShowEvidence] = useState(false);

  const isUser = message.sender === 'user';
  const hasEvidence = message.metadata?.evidence && message.metadata.evidence.length > 0;
  const hasSources = message.metadata?.sources && message.metadata.sources.length > 0;
  const confidence = message.metadata?.confidence;

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const getStatusIcon = () => {
    switch (message.status) {
      case 'sending':
        return (
          <div className="flex space-x-1">
            <div className="w-1 h-1 bg-gray-400 rounded-full animate-bounce"></div>
            <div className="w-1 h-1 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
            <div className="w-1 h-1 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
          </div>
        );
      case 'error':
        return (
          <svg className="w-3 h-3 text-red-500" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
        );
      case 'sent':
        return (
          <svg className="w-3 h-3 text-green-500" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
          </svg>
        );
      default:
        return null;
    }
  };

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-xs lg:max-w-md xl:max-w-lg ${isUser ? 'order-2' : 'order-1'}`}>
        {/* Avatar */}
        {!isUser && (
          <div className="flex items-center space-x-2 mb-1">
            <div className="w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center">
              <span className="text-white text-xs font-semibold">AI</span>
            </div>
            <span className="text-xs text-gray-500">Medical Assistant</span>
          </div>
        )}

        {/* Message Bubble */}
        <div
          className={`rounded-lg px-4 py-2 ${
            isUser
              ? 'bg-blue-500 text-white'
              : 'bg-gray-100 text-gray-900'
          }`}
        >
          <div className="text-sm whitespace-pre-wrap">{message.text}</div>
          
          {/* Evidence Section */}
          {!isUser && hasEvidence && (
            <div className="mt-3 pt-3 border-t border-gray-200">
              <button
                onClick={() => setShowEvidence(!showEvidence)}
                className="text-xs text-blue-600 hover:text-blue-800 font-medium flex items-center space-x-1"
              >
                <span>{showEvidence ? 'Hide' : 'Show'} Evidence</span>
                <svg 
                  className={`w-3 h-3 transition-transform ${showEvidence ? 'rotate-180' : ''}`} 
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              
              {showEvidence && (
                <div className="mt-2 space-y-2">
                  {message.metadata.evidence.map((evidence, index) => (
                    <div key={index} className="bg-white rounded p-2 border border-gray-200">
                      <div className="text-xs font-medium text-gray-700">
                        {evidence.title || `Evidence ${index + 1}`}
                      </div>
                      {evidence.abstract && (
                        <div className="text-xs text-gray-600 mt-1 line-clamp-2">
                          {evidence.abstract}
                        </div>
                      )}
                      {evidence.journal && (
                        <div className="text-xs text-gray-500 mt-1">
                          {evidence.journal}
                        </div>
                      )}
                      {evidence.evidence_level && (
                        <span className="inline-block bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full mt-1">
                          {evidence.evidence_level}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Sources Section */}
          {!isUser && hasSources && (
            <div className="mt-2">
              <div className="text-xs text-gray-500">
                Sources: {message.metadata.sources.join(', ')}
              </div>
            </div>
          )}

          {/* Confidence Score */}
          {!isUser && confidence !== undefined && (
            <div className="mt-2 flex items-center space-x-2">
              <div className="text-xs text-gray-500">Confidence:</div>
              <div className="flex-1 bg-gray-200 rounded-full h-1.5">
                <div 
                  className="bg-green-500 h-1.5 rounded-full transition-all duration-300"
                  style={{ width: `${confidence * 100}%` }}
                ></div>
              </div>
              <span className="text-xs text-gray-500">{Math.round(confidence * 100)}%</span>
            </div>
          )}
        </div>

        {/* Message Footer */}
        <div className={`flex items-center justify-between mt-1 px-1 ${isUser ? 'justify-end' : 'justify-start'}`}>
          <div className="flex items-center space-x-2">
            <span className="text-xs text-gray-400">
              {formatTime(message.timestamp)}
            </span>
            {isUser && getStatusIcon()}
          </div>
        </div>
      </div>
    </div>
  );
};

export default MessageBubble;
