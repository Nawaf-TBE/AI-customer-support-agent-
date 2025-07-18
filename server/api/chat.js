const express = require('express');
const { 
  initializePinecone, 
  initializeOpenAI, 
  initializeIndex, 
  generateEmbeddings,
  PineconeError,
  CONFIG 
} = require('../pinecone_setup/index');
const OpenAI = require('openai');

const router = express.Router();

// Initialize clients
let pineconeIndex = null;
let openaiClient = null;

// Initialize services on startup
async function initializeServices() {
  try {
    console.log('🔧 Initializing RAG pipeline services...');
    
    // Initialize OpenAI
    openaiClient = new OpenAI({
      apiKey: process.env.OPENAI_API_KEY
    });
    
    // Initialize Pinecone
    pineconeIndex = await initializeIndex(CONFIG.INDEX_NAME);
    
    console.log('✅ RAG pipeline services initialized successfully');
    return true;
  } catch (error) {
    console.error('❌ Failed to initialize RAG pipeline services:', error);
    return false;
  }
}

// Call initialization
initializeServices();

/**
 * Generate embedding for a single message
 */
async function generateMessageEmbedding(message) {
  try {
    if (!openaiClient) {
      throw new Error('OpenAI client not initialized');
    }
    
    console.log('🧠 Generating embedding for user message...');
    
    const response = await openaiClient.embeddings.create({
      model: CONFIG.EMBEDDING_MODEL,
      input: message,
      encoding_format: 'float'
    });
    
    const embedding = response.data[0].embedding;
    console.log(`✅ Generated embedding (dimension: ${embedding.length})`);
    
    return embedding;
  } catch (error) {
    console.error('❌ Failed to generate embedding:', error);
    throw new Error(`Embedding generation failed: ${error.message}`);
  }
}

/**
 * Query Pinecone for relevant chunks
 */
async function queryRelevantChunks(embedding, topK = 5) {
  try {
    if (!pineconeIndex) {
      throw new Error('Pinecone index not initialized');
    }
    
    console.log(`🔍 Querying Pinecone for top ${topK} relevant chunks...`);
    
    const queryResponse = await pineconeIndex.query({
      vector: embedding,
      topK: topK,
      includeValues: false,
      includeMetadata: true
    });
    
    const relevantChunks = queryResponse.matches.map(match => ({
      id: match.id,
      score: match.score,
      text: match.metadata.text,
      chunkIndex: match.metadata.chunkIndex || 0,
      createdAt: match.metadata.createdAt || 'unknown'
    }));
    
    console.log(`✅ Retrieved ${relevantChunks.length} relevant chunks`);
    console.log(`📊 Relevance scores: ${relevantChunks.map(c => c.score.toFixed(3)).join(', ')}`);
    
    return relevantChunks;
  } catch (error) {
    console.error('❌ Failed to query Pinecone:', error);
    throw new Error(`Pinecone query failed: ${error.message}`);
  }
}

/**
 * Construct detailed prompt with context
 */
function constructPrompt(userMessage, relevantChunks) {
  console.log('📝 Constructing detailed prompt with context...');
  
  // Build context from relevant chunks
  const context = relevantChunks
    .map((chunk, index) => `[Context ${index + 1}] (Relevance: ${(chunk.score * 100).toFixed(1)}%)\n${chunk.text}`)
    .join('\n\n');
  
  const prompt = `You are an AI customer support assistant with access to a knowledge base. Your goal is to provide helpful, accurate, and comprehensive responses based on the provided context and your general knowledge.

CONTEXT FROM KNOWLEDGE BASE:
${context}

USER QUESTION:
${userMessage}

INSTRUCTIONS:
1. Use the provided context as your primary source of information
2. If the context directly answers the user's question, use that information
3. If the context is partially relevant, combine it with your general knowledge
4. If the context is not relevant, politely indicate that and provide general help
5. Always be helpful, professional, and concise
6. If you're uncertain about something, say so rather than guessing
7. Provide actionable steps when appropriate

Please provide a comprehensive and helpful response:`;

  console.log(`✅ Constructed prompt with ${relevantChunks.length} context chunks`);
  
  return prompt;
}

/**
 * Generate response using language model
 */
async function generateResponse(prompt) {
  try {
    if (!openaiClient) {
      throw new Error('OpenAI client not initialized');
    }
    
    console.log('🤖 Generating response with language model...');
    
    const response = await openaiClient.chat.completions.create({
      model: process.env.OPENAI_MODEL || 'gpt-3.5-turbo',
      messages: [
        {
          role: 'system',
          content: 'You are a helpful and knowledgeable customer support assistant. Provide clear, accurate, and actionable responses based on the given context.'
        },
        {
          role: 'user',
          content: prompt
        }
      ],
      max_tokens: parseInt(process.env.MAX_TOKENS) || 1000,
      temperature: parseFloat(process.env.TEMPERATURE) || 0.7,
      top_p: 1,
      frequency_penalty: 0,
      presence_penalty: 0
    });
    
    const generatedResponse = response.choices[0].message.content.trim();
    
    console.log(`✅ Generated response (${generatedResponse.length} characters)`);
    console.log(`📊 Token usage: ${response.usage.total_tokens} total, ${response.usage.prompt_tokens} prompt, ${response.usage.completion_tokens} completion`);
    
    return {
      text: generatedResponse,
      usage: response.usage
    };
  } catch (error) {
    console.error('❌ Failed to generate response:', error);
    throw new Error(`Response generation failed: ${error.message}`);
  }
}

/**
 * Main RAG pipeline
 */
async function runRAGPipeline(userMessage) {
  const startTime = Date.now();
  
  try {
    console.log('🚀 Starting RAG pipeline...');
    console.log(`📝 User message: "${userMessage}"`);
    
    // Step 1: Generate embedding for user message
    const embedding = await generateMessageEmbedding(userMessage);
    
    // Step 2: Query Pinecone for relevant chunks
    const relevantChunks = await queryRelevantChunks(embedding, 5);
    
    // Step 3: Construct detailed prompt
    const prompt = constructPrompt(userMessage, relevantChunks);
    
    // Step 4: Generate response using language model
    const responseData = await generateResponse(prompt);
    
    const endTime = Date.now();
    const processingTime = endTime - startTime;
    
    console.log(`🎉 RAG pipeline completed successfully in ${processingTime}ms`);
    
    return {
      response: responseData.text,
      metadata: {
        processingTime: processingTime,
        relevantChunks: relevantChunks.length,
        tokenUsage: responseData.usage,
        retrievedContext: relevantChunks.map(chunk => ({
          id: chunk.id,
          score: chunk.score,
          preview: chunk.text.substring(0, 100) + '...'
        }))
      }
    };
  } catch (error) {
    const endTime = Date.now();
    const processingTime = endTime - startTime;
    
    console.error(`💥 RAG pipeline failed after ${processingTime}ms:`, error);
    throw error;
  }
}

/**
 * POST /api/chat - Main chat endpoint
 */
router.post('/chat', async (req, res) => {
  const startTime = Date.now();
  
  try {
    // Validate request body
    const { message, conversation_id } = req.body;
    
    if (!message || typeof message !== 'string' || message.trim().length === 0) {
      return res.status(400).json({
        error: 'Invalid request',
        message: 'Message is required and must be a non-empty string',
        timestamp: new Date().toISOString()
      });
    }
    
    if (message.length > 10000) {
      return res.status(400).json({
        error: 'Message too long',
        message: 'Message must be less than 10,000 characters',
        timestamp: new Date().toISOString()
      });
    }
    
    console.log(`💬 Received chat request: "${message.substring(0, 100)}${message.length > 100 ? '...' : ''}"`);
    
    // Check if services are initialized
    if (!pineconeIndex || !openaiClient) {
      console.log('⚠️ Services not ready, attempting to reinitialize...');
      const initialized = await initializeServices();
      
      if (!initialized) {
        return res.status(503).json({
          error: 'Service unavailable',
          message: 'RAG pipeline services are not available. Please try again later.',
          timestamp: new Date().toISOString()
        });
      }
    }
    
    // Run the RAG pipeline
    const result = await runRAGPipeline(message.trim());
    
    const endTime = Date.now();
    const totalTime = endTime - startTime;
    
    // Return successful response
    res.json({
      response: result.response,
      conversation_id: conversation_id || `conv_${Date.now()}`,
      timestamp: new Date().toISOString(),
      processing_time: totalTime,
      metadata: {
        ...result.metadata,
        totalProcessingTime: totalTime,
        model: process.env.OPENAI_MODEL || 'gpt-3.5-turbo',
        indexName: CONFIG.INDEX_NAME
      }
    });
    
    console.log(`✅ Chat request completed successfully in ${totalTime}ms`);
    
  } catch (error) {
    const endTime = Date.now();
    const totalTime = endTime - startTime;
    
    console.error(`🔥 Chat request failed after ${totalTime}ms:`, error);
    
    // Determine error type and status code
    let statusCode = 500;
    let errorMessage = 'Internal server error occurred while processing your request';
    
    if (error instanceof PineconeError) {
      statusCode = 503;
      errorMessage = 'Knowledge base service is currently unavailable';
    } else if (error.message.includes('OpenAI')) {
      statusCode = 502;
      errorMessage = 'AI service is currently unavailable';
    } else if (error.message.includes('timeout')) {
      statusCode = 504;
      errorMessage = 'Request timed out. Please try again.';
    }
    
    res.status(statusCode).json({
      error: 'Chat processing failed',
      message: errorMessage,
      timestamp: new Date().toISOString(),
      processing_time: totalTime,
      ...(process.env.NODE_ENV === 'development' && { debug: error.message })
    });
  }
});

/**
 * GET /api/chat/health - Health check for chat services
 */
router.get('/chat/health', async (req, res) => {
  try {
    const health = {
      status: 'healthy',
      services: {
        pinecone: false,
        openai: false,
        index: false
      },
      timestamp: new Date().toISOString()
    };
    
    // Check Pinecone
    try {
      if (pineconeIndex) {
        await pineconeIndex.describeIndexStats();
        health.services.pinecone = true;
      }
    } catch (error) {
      console.log('❌ Pinecone health check failed:', error.message);
    }
    
    // Check OpenAI
    try {
      if (openaiClient) {
        await openaiClient.models.list();
        health.services.openai = true;
      }
    } catch (error) {
      console.log('❌ OpenAI health check failed:', error.message);
    }
    
    // Check index
    health.services.index = health.services.pinecone;
    
    const allHealthy = Object.values(health.services).every(status => status === true);
    health.status = allHealthy ? 'healthy' : 'degraded';
    
    res.status(allHealthy ? 200 : 503).json(health);
    
  } catch (error) {
    console.error('🔥 Health check failed:', error);
    res.status(500).json({
      status: 'unhealthy',
      error: 'Health check failed',
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * GET /api/chat/stats - Get index statistics
 */
router.get('/chat/stats', async (req, res) => {
  try {
    if (!pineconeIndex) {
      return res.status(503).json({
        error: 'Service unavailable',
        message: 'Pinecone index not initialized'
      });
    }
    
    const stats = await pineconeIndex.describeIndexStats();
    
    res.json({
      indexName: CONFIG.INDEX_NAME,
      totalVectors: stats.totalVectorCount || 0,
      dimension: stats.dimension || CONFIG.VECTOR_DIMENSION,
      indexFullness: stats.indexFullness || 0,
      namespaces: stats.namespaces || {},
      embeddingModel: CONFIG.EMBEDDING_MODEL,
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    console.error('🔥 Stats request failed:', error);
    res.status(500).json({
      error: 'Failed to retrieve statistics',
      message: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

module.exports = router; 