# AI Customer Support Chat Interface

A modern, responsive chat interface built with Next.js, React, and Tailwind CSS for AI-powered customer support.

## Features

### 🎯 Core Chat Functionality
- **Prominent Chat Window**: Full-height responsive design with smooth scrolling
- **Text Input**: Auto-resizing textarea with keyboard shortcuts (Enter to send, Shift+Enter for new line)
- **Send Button**: Visual feedback with disabled states during loading
- **Message History**: Complete conversation state management with timestamps

### 🎤 Voice Input
- **Dual Voice Support**: Integrated with Vapi AI and browser Speech Recognition as fallback
- **Real-time Feedback**: Visual indicators for recording status and errors
- **Smart Integration**: Automatically populates text input with voice transcriptions

### 💬 Advanced UI/UX
- **Message Status Indicators**: Shows sending (⏳), delivered (✓), and error (❌) states
- **Typing Indicators**: Animated dots during AI response generation
- **User/AI Distinction**: Different styling, avatars, and positioning for clarity
- **Clear Conversation**: Reset button to start fresh conversations
- **Responsive Design**: Works perfectly on desktop, tablet, and mobile

### 🔧 Developer Features
- **Mock AI Responses**: Intelligent context-aware demo responses
- **API Integration Ready**: Commented examples for real AI service integration
- **Error Handling**: Comprehensive error states and user feedback
- **Accessibility**: Proper ARIA labels and keyboard navigation
- **Clean Architecture**: Modular components with custom hooks

## Getting Started

### Prerequisites
- Node.js 18+ 
- npm or yarn

### Installation

1. **Navigate to webapp directory**:
   ```bash
   cd webapp
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Run development server**:
   ```bash
   npm run dev
   ```

4. **Open in browser**:
   ```
   http://localhost:3000
   ```

## Configuration

### Voice Input Setup (Optional)

To enable Vapi AI voice input, add your API key to environment variables:

```bash
# Create .env.local file
NEXT_PUBLIC_VAPI_PUBLIC_KEY=your_vapi_public_key_here
```

**Note**: Without Vapi configuration, the app automatically falls back to browser Speech Recognition API.

### API Integration

The chat interface is ready for AI integration. See `pages/api/chat.js` for example implementations:

- **OpenAI Integration**: Example code for GPT models
- **Custom AI Models**: Template for your own AI services  
- **Knowledge Base**: Integration with scraped support data

## File Structure

```
webapp/
├── components/
│   ├── ChatInterface.js      # Main chat component
│   └── useVoiceInput.js      # Voice input hook
├── pages/
│   ├── api/
│   │   └── chat.js          # API endpoint example
│   ├── _app.js              # Next.js app wrapper
│   └── index.js             # Main page
├── styles/
│   └── globals.css          # Tailwind + custom styles
├── package.json
└── README.md
```

## Component Architecture

### ChatInterface.js
- **State Management**: Messages, input, loading states
- **Message Handling**: Send, display, status tracking
- **UI Rendering**: Chat window, input area, buttons
- **Voice Integration**: Connects with useVoiceInput hook

### useVoiceInput.js  
- **Dual Provider Support**: Vapi AI + Browser Speech Recognition
- **State Management**: Recording status, transcripts, errors
- **Error Handling**: Graceful fallbacks and user feedback

## Customization

### Styling
- **Tailwind CSS**: Modern utility-first styling
- **Custom Classes**: Defined in `globals.css`
- **Color Scheme**: Easily customizable in `tailwind.config.js`

### Mock Responses
The `generateMockResponse()` function provides intelligent context-aware responses for demo purposes. Replace with real AI integration when ready.

### Voice Configuration
Modify voice settings in `useVoiceInput.js`:
- Recognition language
- Continuous vs single-shot recording
- Error handling behavior

## API Integration Example

```javascript
// In ChatInterface.js, replace mock with real API call:
const response = await fetch('/api/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    message: userMessage.content,
    conversation_id: conversationId
  }),
});

const data = await response.json();
// Use data.response for AI message content
```

## Production Deployment

1. **Build the application**:
   ```bash
   npm run build
   ```

2. **Start production server**:
   ```bash
   npm start
   ```

3. **Environment Variables**: Set up production environment variables for API keys and endpoints.

## Browser Support

- **Modern Browsers**: Chrome, Firefox, Safari, Edge (latest versions)
- **Voice Input**: Chrome/Edge (full support), Firefox/Safari (basic support)
- **Mobile**: iOS Safari, Android Chrome

## Troubleshooting

### Voice Input Issues
- **Permission Denied**: Browser needs microphone permission
- **Not Working**: Check if HTTPS is enabled (required for voice input)
- **Vapi Errors**: Verify API key in environment variables

### Development Issues
- **Port Conflicts**: Use `npm run dev -- -p 3001` for different port
- **Module Errors**: Clear `node_modules` and reinstall dependencies

## Next Steps

1. **Integrate Real AI**: Replace mock responses with actual AI service
2. **Add Authentication**: User accounts and conversation persistence  
3. **Knowledge Base**: Connect with your scraped support data
4. **Analytics**: Track conversations and user satisfaction
5. **Deployment**: Deploy to Vercel, Netlify, or your preferred platform

## License

This project is part of the AI Customer Support Agent system. See main project for licensing details. 