import { useState, useRef, useEffect } from 'react'
import { Send, Mic, MicOff, Bot, User, AlertCircle, Trash2, RotateCcw } from 'lucide-react'
import { useVoiceInput } from './useVoiceInput'

export default function ChatInterface() {
  // State management
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'ai',
      content: 'Hello! I\'m your AI customer support assistant. How can I help you today?',
      timestamp: new Date(),
      status: 'delivered'
    }
  ])
  const [inputValue, setInputValue] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [isLoading, setIsLoading] = useState(false)

  // Voice input hook
  const {
    isRecording,
    isVapiEnabled,
    transcript,
    error: voiceError,
    toggleRecording,
    clearTranscript,
    clearError,
    getVapiInstance,
    startVapiConversation
  } = useVoiceInput()
  
  // Refs
  const textareaRef = useRef(null)
  const messagesEndRef = useRef(null)
  const chatContainerRef = useRef(null)

  // Auto-scroll to bottom when new messages are added
  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`
    }
  }, [inputValue])

  // Handle voice transcript
  useEffect(() => {
    if (transcript) {
      setInputValue(transcript)
      clearTranscript()
    }
  }, [transcript, clearTranscript])

  // Handle Vapi voice-to-text and text-to-voice integration
  useEffect(() => {
    if (isVapiEnabled && transcript) {
      // Add user message to chat
      const userMessage = {
        id: Date.now(),
        type: 'user',
        content: transcript,
        timestamp: new Date(),
        status: 'sending'
      }
      setMessages(prev => [...prev, userMessage])
      setIsTyping(true)
      setIsLoading(true)
      // Send to /api/chat endpoint
      fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: transcript })
      })
        .then(res => res.json())
        .then(data => {
          const aiMessage = {
            id: Date.now() + 1,
            type: 'ai',
            content: data.response,
            timestamp: new Date(),
            status: 'delivered'
          }
          setMessages(prev => prev.map(msg =>
            msg.id === userMessage.id ? { ...msg, status: 'delivered' } : msg
          ).concat(aiMessage))
          setIsTyping(false)
          setIsLoading(false)
          // Use Vapi TTS to play the AI response
          const vapi = getVapiInstance()
          if (vapi && typeof vapi.say === 'function') {
            vapi.say(data.response)
          }
        })
        .catch(err => {
          setMessages(prev => prev.map(msg =>
            msg.id === userMessage.id ? { ...msg, status: 'error' } : msg
          ))
          setIsTyping(false)
          setIsLoading(false)
        })
      clearTranscript()
    }
  }, [transcript, isVapiEnabled, getVapiInstance, clearTranscript])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputValue.trim(),
      timestamp: new Date(),
      status: 'sending'
    }

    // Add user message
    setMessages(prev => [...prev, userMessage])
    setInputValue('')
    setIsLoading(true)
    setIsTyping(true)

    // Update message status to delivered
    setTimeout(() => {
      setMessages(prev => prev.map(msg => 
        msg.id === userMessage.id ? { ...msg, status: 'delivered' } : msg
      ))
    }, 500)

    try {
      // TODO: Replace this mock response with actual API call
      // Example API integration:
      /*
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage.content,
          conversation_id: conversationId // if maintaining conversation context
        }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to get AI response');
      }
      
      const data = await response.json();
      const aiResponse = {
        id: Date.now() + 1,
        type: 'ai',
        content: data.response,
        timestamp: new Date(),
        status: 'delivered'
      };
      */
      
      // Mock response for demo (remove when implementing real API)
    setTimeout(() => {
      const aiResponse = {
        id: Date.now() + 1,
        type: 'ai',
        content: generateMockResponse(userMessage.content),
          timestamp: new Date(),
          status: 'delivered'
      }
      
      setMessages(prev => [...prev, aiResponse])
      setIsTyping(false)
      setIsLoading(false)
    }, 1500 + Math.random() * 1000) // Simulate variable response time
      
    } catch (error) {
      console.error('Error getting AI response:', error)
      
      // Update user message status to error
      setMessages(prev => prev.map(msg => 
        msg.id === userMessage.id ? { ...msg, status: 'error' } : msg
      ))
      
      // Add error message
      const errorResponse = {
        id: Date.now() + 1,
        type: 'ai',
        content: 'I apologize, but I\'m having trouble responding right now. Please try again in a moment.',
        timestamp: new Date(),
        status: 'delivered'
      }
      
      setMessages(prev => [...prev, errorResponse])
      setIsTyping(false)
      setIsLoading(false)
    }
  }

  const generateMockResponse = (userMessage) => {
    const message = userMessage.toLowerCase()
    
    // More intelligent mock responses based on user input
    if (message.includes('hello') || message.includes('hi') || message.includes('hey')) {
      return "Hello! Welcome to our AI support system. I'm here to help you with any questions or issues you might have. What can I assist you with today?"
    }
    
    if (message.includes('problem') || message.includes('issue') || message.includes('error')) {
      return "I understand you're experiencing an issue. Let me help you troubleshoot this. Could you please provide more details about what specifically is happening? I'll guide you through the solution step by step."
    }
    
    if (message.includes('account') || message.includes('login') || message.includes('password')) {
      return "I can help you with account-related issues. For security reasons, I'll need to verify your identity first. Are you having trouble logging in, or do you need help with account settings?"
    }
    
    if (message.includes('payment') || message.includes('billing') || message.includes('charge')) {
      return "I can assist you with billing and payment inquiries. Please note that for security, I cannot access specific payment details, but I can help you understand charges, update payment methods, or direct you to the right resources."
    }
    
    if (message.includes('cancel') || message.includes('refund')) {
      return "I understand you'd like to discuss cancellation or refunds. Let me help you with this process. Can you tell me more about what you'd like to cancel or your reason for requesting a refund?"
    }
    
    if (message.includes('how') || message.includes('tutorial') || message.includes('guide')) {
      return "I'd be happy to walk you through the process! Let me provide you with a step-by-step guide. Which specific feature or task would you like help with?"
    }
    
    if (message.includes('thank')) {
      return "You're very welcome! I'm glad I could help. Is there anything else you'd like assistance with today? I'm here whenever you need support."
    }
    
    // Default contextual responses
    const responses = [
      `I understand you're asking about "${userMessage}". Let me provide you with the most relevant information and help you resolve this. Based on our knowledge base, here's what I recommend...`,
      `Thank you for reaching out about this matter. I've analyzed your query and found some helpful information that should address your concerns. Let me walk you through the solution.`,
      `Great question! This is something many of our users ask about. I have the perfect solution for you, and I'll make sure to explain it clearly so you can get back on track.`,
      `I see what you're looking for. Let me provide you with accurate, up-to-date information about this topic. Here's everything you need to know...`,
      `I'm here to help with exactly this type of question! Based on your inquiry, I can provide several options and recommendations. Let me guide you through the best approach.`
    ]
    return responses[Math.floor(Math.random() * responses.length)]
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const handleVoiceToggle = async () => {
    try {
      clearError()
      if (isVapiEnabled) {
        await startVapiConversation()
      } else {
      await toggleRecording()
      }
    } catch (error) {
      console.error('Voice toggle error:', error)
    }
  }

  const formatTimestamp = (timestamp) => {
    return timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  const clearConversation = () => {
    setMessages([
      {
        id: 1,
        type: 'ai',
        content: 'Hello! I\'m your AI customer support assistant. How can I help you today?',
        timestamp: new Date(),
        status: 'delivered'
      }
    ])
  }

  return (
    <div className="flex flex-col h-screen max-w-4xl mx-auto bg-white shadow-lg">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-primary-500 rounded-full flex items-center justify-center">
            <Bot className="w-6 h-6 text-white" />
          </div>
          <div className="flex-1">
            <h1 className="text-xl font-semibold text-gray-900">AI Support Assistant</h1>
            <p className="text-sm text-gray-500">Always here to help</p>
          </div>
          <div className="flex items-center space-x-4">
            <button
              onClick={clearConversation}
              className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
              title="Clear conversation"
            >
              <RotateCcw className="w-5 h-5" />
            </button>
            <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-green-400 rounded-full"></div>
            <span className="text-sm text-gray-500">Online</span>
            </div>
          </div>
        </div>
      </div>

      {/* Chat Messages */}
      <div 
        ref={chatContainerRef}
        className="flex-1 overflow-y-auto px-6 py-4 space-y-4 scrollbar-hide"
        style={{ minHeight: 0 }}
      >
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div className="flex max-w-xs lg:max-w-md space-x-3">
              {message.type === 'ai' && (
                <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center flex-shrink-0">
                  <Bot className="w-5 h-5 text-primary-600" />
                </div>
              )}
              
              <div className="flex flex-col space-y-1">
                <div
                  className={`chat-message ${
                    message.type === 'user' ? 'chat-message-user' : 'chat-message-ai'
                  }`}
                >
                  <p className="text-sm leading-relaxed">{message.content}</p>
                </div>
                <div className={`flex items-center space-x-2 ${
                  message.type === 'user' ? 'justify-end' : 'justify-start'
                }`}>
                  <span className={`text-xs text-gray-400`}>
                  {formatTimestamp(message.timestamp)}
                </span>
                  {message.type === 'user' && (
                    <span className={`text-xs message-status ${
                      message.status === 'sending' 
                        ? 'message-status-sending text-gray-400' 
                        : message.status === 'delivered' 
                          ? 'message-status-delivered text-green-500' 
                          : 'message-status-error'
                    }`}>
                      {message.status === 'sending' ? '⏳' : message.status === 'delivered' ? '✓' : '❌'}
                    </span>
                  )}
                </div>
              </div>

              {message.type === 'user' && (
                <div className="w-8 h-8 bg-primary-500 rounded-full flex items-center justify-center flex-shrink-0">
                  <User className="w-5 h-5 text-white" />
                </div>
              )}
            </div>
          </div>
        ))}

        {/* Typing Indicator */}
        {isTyping && (
          <div className="flex justify-start">
            <div className="flex space-x-3">
              <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
                <Bot className="w-5 h-5 text-primary-600" />
              </div>
              <div className="chat-message chat-message-ai">
                <div className="typing-indicator">
                  <div className="typing-dot" style={{ animationDelay: '0ms' }}></div>
                  <div className="typing-dot" style={{ animationDelay: '150ms' }}></div>
                  <div className="typing-dot" style={{ animationDelay: '300ms' }}></div>
                </div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t border-gray-200 bg-white px-6 py-4">
        <div className="flex items-end space-x-4">
          {/* Voice Recording Button */}
          <button
            onClick={handleVoiceToggle}
            className={`mic-button ${
              isRecording ? 'mic-button-active' : 'mic-button-inactive'
            }`}
            aria-label={isRecording ? 'Stop recording' : 'Start voice input'}
          >
            {isRecording ? (
              <MicOff className="w-5 h-5" />
            ) : (
              <Mic className="w-5 h-5" />
            )}
          </button>

          {/* Text Input */}
          <div className="flex-1">
            <textarea
              ref={textareaRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your message here..."
              className="chat-input"
              rows={1}
              style={{ minHeight: '44px', maxHeight: '120px' }}
              disabled={isLoading}
            />
          </div>

          {/* Send Button */}
          <button
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || isLoading}
            className={`btn-primary ${
              (!inputValue.trim() || isLoading) 
                ? 'opacity-50 cursor-not-allowed' 
                : 'hover:bg-primary-600'
            }`}
            aria-label="Send message"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>

        {/* Voice Status Messages */}
        {isRecording && (
          <div className="mt-2 flex items-center space-x-2 text-sm text-red-600">
            <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
            <span>
              Recording with {isVapiEnabled ? 'Vapi AI' : 'Browser Speech Recognition'}... 
              Click the microphone to stop
            </span>
          </div>
        )}

        {voiceError && (
          <div className="mt-2 flex items-center space-x-2 text-sm text-red-600">
            <AlertCircle className="w-4 h-4" />
            <span>{voiceError}</span>
            <button 
              onClick={clearError}
              className="ml-2 text-xs underline hover:no-underline"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Input Hint */}
        <div className="mt-2 text-xs text-gray-400">
          Press Enter to send, Shift + Enter for new line
        </div>
      </div>
    </div>
  )
} 