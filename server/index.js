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

    // 1. Generate embedding for the incoming message
    const [embedding] = await generateEmbeddings(message);

    // 2. Query Pinecone for top 5 most relevant chunks
    const matches = await queryPinecone(embedding, 5, CONFIG.INDEX_NAME);
    const contextChunks = matches.map(match => match.metadata?.text || '').filter(Boolean);

    // 3. Construct prompt for LLM
    const contextText = contextChunks.map((chunk, i) => `Context ${i+1}:
${chunk}`).join('\n\n');
    const prompt = `You are a helpful AI customer support agent. Use the following context from the knowledge base to answer the user's question as comprehensively and helpfully as possible.\n\nContext:\n${contextText}\n\nUser message:\n${message}\n\nAnswer:`;

    // 4. Call OpenAI LLM (gpt-3.5-turbo or gpt-4)
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
    const aiResponse = completion.choices[0]?.message?.content?.trim() || 'Sorry, I could not generate a response.';

    // 5. Return response
    res.json({
      response: aiResponse,
      context: contextChunks,
      matches: matches.map(m => ({ score: m.score, id: m.id })),
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