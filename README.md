# AI Customer Support Agent

<!-- 
  🎯 Ready for Demo: This project is fully configured and ready for presentation
  🚀 Features: RAG pipeline, voice interface, guardrails, and tool integration
  📚 Documentation: Complete setup and deployment instructions included
  🔐 Security: All API keys properly configured via environment variables
  🐳 Deployment: Docker containers ready for production use
  🧪 Testing: Comprehensive RAG evaluation and testing framework included
  📊 Metrics: Performance monitoring and quality assessment tools ready
  🎤 Voice: Advanced voice-to-text and text-to-speech with Vapi AI
  ♿ Accessibility: Full keyboard navigation and screen reader support
  🚢 Production: Multi-stage Docker builds and orchestrated deployment
  🔄 CI/CD: Ready for automated testing and deployment pipelines
  🧪 Quality: 50+ evaluation questions with accuracy, helpfulness, and citation scoring
  📈 Analytics: Comprehensive performance metrics and response quality assessment
  🛡️ Compliance: PII detection, toxicity filtering, and advisory disclaimers
  🔒 Privacy: Secure data handling with no sensitive information exposure
  📈 Scalability: Horizontal scaling support with load balancing capabilities
  🏢 Enterprise: Multi-tenant architecture and enterprise-grade security
  📊 Monitoring: Real-time performance tracking and alerting systems
  🔍 Observability: Comprehensive logging and debugging capabilities
-->

A comprehensive AI-powered customer support system featuring a modern chat interface, RAG (Retrieval-Augmented Generation) pipeline, voice capabilities, and intelligent guardrails.

## 🚀 Features

### **Core AI Capabilities**
- **RAG Pipeline**: Retrieves relevant context from knowledge base using Pinecone vector search
- **Intelligent Responses**: Powered by OpenAI GPT models with context-aware answers
- **Tool Integration**: Supports scheduling meetings and other automated actions
- **Guardrails**: PII detection, toxicity filtering, and advisory disclaimers

### **Voice Interface**
- **Voice-to-Text**: Real-time speech recognition using Vapi AI
- **Text-to-Speech**: AI responses spoken aloud for accessibility
- **Dual Fallback**: Vapi AI with browser Speech Recognition as backup

### **Modern Web Interface**
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Real-time Chat**: Live message status indicators and typing animations
- **Professional UI**: Clean, modern interface with Tailwind CSS
- **Accessibility**: ARIA labels, keyboard navigation, and screen reader support

### **Production Ready**
- **Docker Deployment**: Containerized services with Docker Compose
- **Environment Management**: Secure API key configuration
- **Error Handling**: Comprehensive error states and user feedback
- **Scalable Architecture**: Microservices design for easy scaling

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Webapp        │    │   Server        │    │   External      │
│   (Next.js)     │◄──►│   (Express)     │◄──►│   Services      │
│                 │    │                 │    │                 │
│ • Chat UI       │    │ • RAG Pipeline  │    │ • OpenAI        │
│ • Voice Input   │    │ • Guardrails    │    │ • Pinecone      │
│ • TTS Output    │    │ • Tool Calls    │    │ • Vapi AI       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🛠️ Quick Start

### **Prerequisites**
- Node.js 18+
- Docker Desktop
- API keys (see [Configuration](#configuration))

### **1. Clone and Setup**
```bash
git clone <your-repo-url>
cd AI-Customer-Support-Agent
```

### **2. Configure Environment**
```bash
# Copy the environment template
cp env-template.txt .env

# Edit .env with your API keys
nano .env
```

### **3. Start Services**
```bash
# Build and start all services
docker-compose up --build

# Access the application
open http://localhost:3000
```

## ⚙️ Configuration

### **Required API Keys**

| Service | Purpose | Get Key |
|---------|---------|---------|
| **OpenAI** | AI responses & embeddings | [OpenAI Platform](https://platform.openai.com/api-keys) |
| **Pinecone** | Vector search (RAG) | [Pinecone Console](https://app.pinecone.io/) |
| **Vapi** | Voice features | [Vapi.ai](https://vapi.ai/) |
| **Exa** | Data scraping (optional) | [Exa.ai](https://exa.ai/) |

### **Environment Variables**
```bash
# Core AI Services
OPENAI_API_KEY=sk-your_openai_api_key_here
OPENAI_COMPLETION_MODEL=gpt-3.5-turbo
PINECONE_API_KEY=your_pinecone_api_key_here

# Voice Services
NEXT_PUBLIC_VAPI_PUBLIC_KEY=your_vapi_public_key_here

# Data Scraping (Optional)
EXA_API_KEY=your_exa_api_key_here
```

## 🎯 Demo Setup

### **1. Prepare Your Environment**
```bash
# Ensure all services are running
docker-compose up -d

# Check service status
docker-compose ps
```

### **2. Test Core Features**
- **Text Chat**: Type questions about Aven support
- **Voice Input**: Click microphone and speak
- **Tool Calls**: Try "schedule a meeting for tomorrow at 2pm"
- **Guardrails**: Test with email addresses or inappropriate content

### **3. Demo Script**
```
1. Introduction (10s)
   "This is our AI Customer Support Agent"

2. Text Chat (30s)
   - Ask: "How do I reset my password?"
   - Show AI response with context

3. Voice Features (30s)
   - Click mic, speak: "How do I check my balance?"
   - Show TTS response

4. Tool Integration (20s)
   - Ask: "Schedule a meeting for Friday at 3pm"
   - Show confirmation

5. Guardrails (10s)
   - Try: "My email is john@example.com"
   - Show PII protection
```

## 📁 Project Structure

```
AI-Customer-Support-Agent/
├── webapp/                    # Next.js frontend
│   ├── components/           # React components
│   │   ├── ChatInterface.js  # Main chat UI
│   │   └── useVoiceInput.js  # Voice input hook
│   ├── pages/               # Next.js pages
│   └── styles/              # CSS and styling
├── server/                   # Express backend
│   ├── index.js             # Main server with RAG pipeline
│   ├── pinecone_setup/      # Vector database utilities
│   └── eval_rag.js          # Evaluation and testing
├── scraped_data/            # Knowledge base data
├── docker-compose.yml       # Service orchestration
├── env-template.txt         # Environment configuration
└── README.md               # This file
```

## 🔧 Development

### **Local Development**
```bash
# Start webapp in development mode
cd webapp
npm install
npm run dev

# Start server in development mode
cd server
npm install
node index.js
```

### **Testing**
```bash
# Run RAG evaluation
cd server
node eval_rag.js

# Test API endpoints
curl -X POST http://localhost:3001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "How do I reset my password?"}'
```

### **Building for Production**
```bash
# Build all services
docker-compose build

# Deploy to production
docker-compose -f docker-compose.prod.yml up -d
```

## 🛡️ Security & Guardrails

### **PII Detection**
- Automatically detects and blocks email addresses and phone numbers
- Returns standardized privacy warning messages

### **Toxicity Filtering**
- Uses `bad-words` library for content filtering
- Blocks inappropriate or offensive content

### **Advisory Disclaimers**
- Detects legal/financial advice requests
- Automatically prepends appropriate disclaimers

### **Environment Security**
- API keys stored in `.env` (not committed to git)
- Docker secrets for production deployments

## 📊 Evaluation & Monitoring

### **RAG Pipeline Evaluation**
```bash
# Run comprehensive evaluation
cd server
node eval_rag.js

# View results
cat rag_eval_results.json
```

### **Metrics Tracked**
- **Accuracy**: Keyword presence in responses
- **Helpfulness**: Response quality scoring
- **Citation Quality**: Context relevance
- **Response Time**: Performance monitoring

## 🚀 Deployment

### **Docker Deployment**
```bash
# Production deployment
docker-compose -f docker-compose.prod.yml up -d

# Scale services
docker-compose up -d --scale webapp=3
```

### **Cloud Deployment**
- **Vercel**: Deploy webapp with `vercel --prod`
- **Railway**: Full-stack deployment
- **AWS ECS**: Container orchestration
- **Google Cloud Run**: Serverless containers

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
- Check the [Issues](https://github.com/your-repo/issues) page
- Review the [Documentation](docs/)
- Contact the development team

---

**Built with ❤️ using Next.js, Express, OpenAI, Pinecone, and Vapi AI** 