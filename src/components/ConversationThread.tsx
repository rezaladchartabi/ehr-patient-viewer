import React from 'react';
import { Message } from './ChatInterface';

interface ConversationThreadProps {
  messages: Message[];
  onMessageClick?: (message: Message) => void;
  selectedMessageId?: string;
}

const ConversationThread: React.FC<ConversationThreadProps> = ({
  messages,
  onMessageClick,
  selectedMessageId
}) => {
  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const formatDate = (date: Date) => {
    const today = new Date();
    const messageDate = new Date(date);
    
    if (messageDate.toDateString() === today.toDateString()) {
      return 'Today';
    }
    
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    if (messageDate.toDateString() === yesterday.toDateString()) {
      return 'Yesterday';
    }
    
    return messageDate.toLocaleDateString();
  };

  const groupMessagesByDate = (messages: Message[]) => {
    const groups: { [key: string]: Message[] } = {};
    
    messages.forEach(message => {
      const dateKey = formatDate(message.timestamp);
      if (!groups[dateKey]) {
        groups[dateKey] = [];
      }
      groups[dateKey].push(message);
    });
    
    return groups;
  };

  const messageGroups = groupMessagesByDate(messages);

  return (
    <div className="space-y-4">
      {Object.entries(messageGroups).map(([date, dateMessages]) => (
        <div key={date} className="space-y-2">
          {/* Date Header */}
          <div className="flex items-center justify-center">
            <div className="bg-gray-100 text-gray-600 text-xs px-3 py-1 rounded-full">
              {date}
            </div>
          </div>
          
          {/* Messages for this date */}
          <div className="space-y-1">
            {dateMessages.map((message) => (
              <div
                key={message.id}
                onClick={() => onMessageClick?.(message)}
                className={`p-2 rounded-lg cursor-pointer transition-colors ${
                  selectedMessageId === message.id
                    ? 'bg-blue-50 border border-blue-200'
                    : 'hover:bg-gray-50'
                }`}
              >
                <div className="flex items-start space-x-2">
                  {/* Message Icon */}
                  <div className={`w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 ${
                    message.sender === 'user' 
                      ? 'bg-blue-500 text-white' 
                      : 'bg-gray-500 text-white'
                  }`}>
                    <span className="text-xs font-semibold">
                      {message.sender === 'user' ? 'U' : 'AI'}
                    </span>
                  </div>
                  
                  {/* Message Content */}
                  <div className="flex-1 min-w-0">
                    <div className="text-sm text-gray-900 truncate">
                      {message.text}
                    </div>
                    <div className="flex items-center space-x-2 mt-1">
                      <span className="text-xs text-gray-500">
                        {formatTime(message.timestamp)}
                      </span>
                      {message.metadata?.confidence && (
                        <span className="text-xs text-gray-500">
                          {Math.round(message.metadata.confidence * 100)}% confidence
                        </span>
                      )}
                      {message.metadata?.evidence && message.metadata.evidence.length > 0 && (
                        <span className="text-xs bg-green-100 text-green-800 px-1 rounded">
                          {message.metadata.evidence.length} evidence
                        </span>
                      )}
                    </div>
                  </div>
                  
                  {/* Status Icon */}
                  <div className="flex-shrink-0">
                    {message.status === 'sending' && (
                      <div className="w-3 h-3 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                    )}
                    {message.status === 'error' && (
                      <svg className="w-3 h-3 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                      </svg>
                    )}
                    {message.status === 'sent' && (
                      <svg className="w-3 h-3 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
      
      {messages.length === 0 && (
        <div className="text-center text-gray-500 py-8">
          <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-3">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
          </div>
          <p>No messages yet</p>
          <p className="text-sm">Start a conversation to see the thread here</p>
        </div>
      )}
    </div>
  );
};

export default ConversationThread;
