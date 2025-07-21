require('dotenv').config();
const express = require('express');
const bodyParser = require('body-parser');
const { 
  generateEmbeddings, 
  queryPinecone, 
  CONFIG, 
  initializeOpenAI, 
  initializeIndex, 
  PineconeError 
} = require('./pinecone_setup');
const OpenAI = require('openai');
const Filter = require('bad-words');

// PII regex patterns
const emailRegex = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/;
const phoneRegex = /\b(\+?\d{1,3}[\s-]?)?(\(?\d{3}\)?[\s-]?)?\d{3}[\s-]?\d{4}\b/;

// Advisory keywords
const advisoryKeywords = [
  'legal', 'lawyer', 'attorney', 'lawsuit', 'court', 'sue', 'regulation', 'compliance',
  'financial', 'investment', 'invest', 'stock', 'securities', 'tax', 'accountant', 'advice', 'advisory', 'fiduciary'
];
const advisoryDisclaimer = 'Disclaimer: This response is for informational purposes only and does not constitute legal or financial advice. Please consult a qualified professional for specific guidance.\n\n';

// Toxicity threshold (bad-words is binary, so any match is considered toxic)
const filter = new Filter();

const app = express();
const PORT = process.env.PORT || 3001;

app.use(bodyParser.json());

// Initialize OpenAI client for LLM
let openaiClient = null;
function getOpenAIClient() {
  if (!openaiClient) {
    openaiClient = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
  }
  return openaiClient;
}

// RAG pipeline endpoint
app.post('/api/chat', async (req, res) => {
  try {
    const { message } = req.body;
    if (!message || typeof message !== 'string') {
      return res.status(400).json({ error: 'Message is required' });
    }

    // 1. PII Detection
    if (emailRegex.test(message) || phoneRegex.test(message)) {
      return res.json({
        response: 'For your privacy and security, please do not share personal information such as email addresses or phone numbers. How else can I assist you?',
        context: [],
        matches: [],
        model: process.env.OPENAI_COMPLETION_MODEL || 'gpt-3.5-turbo'
      });
    }

    // 2. Toxicity Filter
    if (filter.isProfane(message)) {
      return res.json({
        response: 'I am unable to respond to inappropriate or offensive content. Please rephrase your question.',
        context: [],
        matches: [],
        model: process.env.OPENAI_COMPLETION_MODEL || 'gpt-3.5-turbo'
      });
    }

    // 3. Advisory Detection
    let prependDisclaimer = false;
    const lowerMsg = message.toLowerCase();
    for (const keyword of advisoryKeywords) {
      if (lowerMsg.includes(keyword)) {
        prependDisclaimer = true;
        break;
      }
    }

    // 4. RAG pipeline (unchanged)
    const [embedding] = await generateEmbeddings(message);
    const matches = await queryPinecone(embedding, 5, CONFIG.INDEX_NAME);
    const contextChunks = matches.map(match => match.metadata?.text || '').filter(Boolean);
    const contextText = contextChunks.map((chunk, i) => `Context ${i+1}:\n${chunk}`).join('\n\n');
    const prompt = `You are a helpful AI customer support agent. Use the following context from the knowledge base to answer the user's question as comprehensively and helpfully as possible.\n\nContext:\n${contextText}\n\nUser message:\n${message}\n\nAnswer:`;
    const openai = getOpenAIClient();
    const completion = await openai.chat.completions.create({
      model: process.env.OPENAI_COMPLETION_MODEL || 'gpt-3.5-turbo',
      messages: [
        { role: 'system', content: 'You are a helpful AI customer support agent.' },
        { role: 'user', content: prompt }
      ],
      max_tokens: 512,
      temperature: 0.3
    });
    let aiResponse = completion.choices[0]?.message?.content?.trim() || 'Sorry, I could not generate a response.';
    if (prependDisclaimer) {
      aiResponse = advisoryDisclaimer + aiResponse;
    }
    res.json({
      response: aiResponse,
      context: contextChunks,
      matches: matches.map(m => ({ score: m.score, id: m.id, metadata: m.metadata })),
      model: process.env.OPENAI_COMPLETION_MODEL || 'gpt-3.5-turbo'
    });
  } catch (error) {
    console.error('RAG pipeline error:', error);
    if (error instanceof PineconeError) {
      return res.status(500).json({ error: error.message, code: error.code });
    }
    res.status(500).json({ error: error.message || 'Internal server error' });
  }
});

app.listen(PORT, () => {
  console.log(`RAG API server running on port ${PORT}`);
}); 