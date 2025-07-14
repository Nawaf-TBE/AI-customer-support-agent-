require('dotenv').config();
const { Pinecone } = require('pinecone-client');
const OpenAI = require('openai');

/**
 * Custom error class for Pinecone operations
 */
class PineconeError extends Error {
  constructor(message, code, details = null) {
    super(message);
    this.name = 'PineconeError';
    this.code = code;
    this.details = details;
  }
}

/**
 * Configuration constants
 */
const CONFIG = {
  INDEX_NAME: 'aven-support',
  EMBEDDING_MODEL: 'text-embedding-ada-002',
  VECTOR_DIMENSION: 1536,
  CHUNK_SIZE: 1000,
  CHUNK_OVERLAP: 200,
  MAX_TOKENS_PER_CHUNK: 8000,
  BATCH_SIZE: 100
};

let pineconeClient = null;
let openaiClient = null;
let pineconeIndex = null;

/**
 * Initialize Pinecone client with environment variables
 */
async function initializePinecone() {
  try {
    console.log('🔧 Initializing Pinecone client...');
    
    const apiKey = process.env.PINECONE_API_KEY;
    const environment = process.env.PINECONE_ENVIRONMENT;
    
    if (!apiKey) {
      throw new PineconeError(
        'PINECONE_API_KEY environment variable is not set',
        'MISSING_API_KEY'
      );
    }
    
    if (!environment) {
      throw new PineconeError(
        'PINECONE_ENVIRONMENT environment variable is not set',
        'MISSING_ENVIRONMENT'
      );
    }
    
    pineconeClient = new Pinecone({
      apiKey: apiKey,
      environment: environment
    });
    
    console.log('✅ Pinecone client initialized successfully');
    return pineconeClient;
    
  } catch (error) {
    if (error instanceof PineconeError) {
      throw error;
    }
    throw new PineconeError(
      'Failed to initialize Pinecone client',
      'INITIALIZATION_ERROR',
      error.message
    );
  }
}

/**
 * Initialize OpenAI client for embeddings
 */
function initializeOpenAI() {
  try {
    console.log('🔧 Initializing OpenAI client...');
    
    const apiKey = process.env.OPENAI_API_KEY;
    
    if (!apiKey) {
      throw new PineconeError(
        'OPENAI_API_KEY environment variable is not set',
        'MISSING_OPENAI_KEY'
      );
    }
    
    openaiClient = new OpenAI({
      apiKey: apiKey
    });
    
    console.log('✅ OpenAI client initialized successfully');
    return openaiClient;
    
  } catch (error) {
    throw new PineconeError(
      'Failed to initialize OpenAI client',
      'OPENAI_INIT_ERROR',
      error.message
    );
  }
}

/**
 * Check if Pinecone index exists
 */
async function checkIndexExists(indexName) {
  try {
    if (!pineconeClient) {
      await initializePinecone();
    }
    
    console.log(`🔍 Checking if index '${indexName}' exists...`);
    
    const indexList = await pineconeClient.listIndexes();
    const exists = indexList.indexes?.some(index => index.name === indexName) || false;
    
    console.log(`${exists ? '✅' : '❌'} Index '${indexName}' ${exists ? 'exists' : 'does not exist'}`);
    return exists;
    
  } catch (error) {
    throw new PineconeError(
      `Failed to check if index '${indexName}' exists`,
      'INDEX_CHECK_ERROR',
      error.message
    );
  }
}

/**
 * Create a new Pinecone index
 */
async function createIndex(indexName, dimension = CONFIG.VECTOR_DIMENSION) {
  try {
    if (!pineconeClient) {
      await initializePinecone();
    }
    
    console.log(`🚀 Creating index '${indexName}' with dimension ${dimension}...`);
    
    const indexConfig = {
      name: indexName,
      dimension: dimension,
      spec: {
        serverless: {
          cloud: 'aws',
          region: 'us-east-1'
        }
      },
      metric: 'cosine'
    };
    
    await pineconeClient.createIndex(indexConfig);
    
    // Wait for index to be ready
    console.log('⏳ Waiting for index to be ready...');
    let isReady = false;
    let attempts = 0;
    const maxAttempts = 30; // 5 minutes max wait time
    
    while (!isReady && attempts < maxAttempts) {
      await new Promise(resolve => setTimeout(resolve, 10000)); // Wait 10 seconds
      
      try {
        const indexStats = await pineconeClient.index(indexName).describeIndexStats();
        isReady = true;
        console.log('✅ Index is ready!');
      } catch (error) {
        attempts++;
        console.log(`⏳ Index not ready yet (attempt ${attempts}/${maxAttempts})...`);
      }
    }
    
    if (!isReady) {
      throw new PineconeError(
        'Index creation timeout - index not ready after 5 minutes',
        'INDEX_TIMEOUT'
      );
    }
    
    console.log(`✅ Index '${indexName}' created successfully`);
    return true;
    
  } catch (error) {
    if (error instanceof PineconeError) {
      throw error;
    }
    throw new PineconeError(
      `Failed to create index '${indexName}'`,
      'INDEX_CREATION_ERROR',
      error.message
    );
  }
}

/**
 * Initialize the Pinecone index connection
 */
async function initializeIndex(indexName = CONFIG.INDEX_NAME) {
  try {
    if (!pineconeClient) {
      await initializePinecone();
    }
    
    // Check if index exists, create if it doesn't
    const exists = await checkIndexExists(indexName);
    
    if (!exists) {
      await createIndex(indexName);
    }
    
    // Connect to the index
    pineconeIndex = pineconeClient.index(indexName);
    console.log(`✅ Connected to index '${indexName}'`);
    
    return pineconeIndex;
    
  } catch (error) {
    if (error instanceof PineconeError) {
      throw error;
    }
    throw new PineconeError(
      `Failed to initialize index '${indexName}'`,
      'INDEX_INIT_ERROR',
      error.message
    );
  }
}

/**
 * Split text into overlapping chunks
 */
function createTextChunks(text, chunkSize = CONFIG.CHUNK_SIZE, overlap = CONFIG.CHUNK_OVERLAP) {
  if (!text || typeof text !== 'string') {
    throw new PineconeError(
      'Invalid text input for chunking',
      'INVALID_TEXT'
    );
  }
  
  const chunks = [];
  let startIndex = 0;
  
  while (startIndex < text.length) {
    const endIndex = Math.min(startIndex + chunkSize, text.length);
    let chunk = text.slice(startIndex, endIndex);
    
    // Try to break at word boundaries for better chunks
    if (endIndex < text.length) {
      const lastSpaceIndex = chunk.lastIndexOf(' ');
      if (lastSpaceIndex > chunkSize * 0.7) { // Only break at word if it's not too far back
        chunk = chunk.slice(0, lastSpaceIndex);
        endIndex = startIndex + lastSpaceIndex;
      }
    }
    
    chunks.push({
      text: chunk.trim(),
      index: chunks.length,
      startChar: startIndex,
      endChar: endIndex,
      length: chunk.trim().length
    });
    
    // Move start index, accounting for overlap
    startIndex = endIndex - overlap;
    
    // Prevent infinite loops
    if (startIndex >= endIndex) {
      break;
    }
  }
  
  console.log(`📝 Created ${chunks.length} text chunks (size: ${chunkSize}, overlap: ${overlap})`);
  return chunks;
}

/**
 * Generate embeddings for text using OpenAI
 */
async function generateEmbeddings(texts) {
  try {
    if (!openaiClient) {
      initializeOpenAI();
    }
    
    if (!Array.isArray(texts)) {
      texts = [texts];
    }
    
    console.log(`🧠 Generating embeddings for ${texts.length} text(s)...`);
    
    const response = await openaiClient.embeddings.create({
      model: CONFIG.EMBEDDING_MODEL,
      input: texts,
      encoding_format: 'float'
    });
    
    const embeddings = response.data.map(item => item.embedding);
    
    console.log(`✅ Generated ${embeddings.length} embeddings (dimension: ${embeddings[0]?.length || 'unknown'})`);
    return embeddings;
    
  } catch (error) {
    throw new PineconeError(
      'Failed to generate embeddings',
      'EMBEDDING_ERROR',
      error.message
    );
  }
}

/**
 * Upsert vectors to Pinecone index
 */
async function upsertVectors(vectors) {
  try {
    if (!pineconeIndex) {
      await initializeIndex();
    }
    
    if (!Array.isArray(vectors) || vectors.length === 0) {
      throw new PineconeError(
        'Invalid vectors array for upserting',
        'INVALID_VECTORS'
      );
    }
    
    console.log(`⬆️  Upserting ${vectors.length} vectors to Pinecone...`);
    
    // Process in batches to avoid rate limits
    const batches = [];
    for (let i = 0; i < vectors.length; i += CONFIG.BATCH_SIZE) {
      batches.push(vectors.slice(i, i + CONFIG.BATCH_SIZE));
    }
    
    let totalUpserted = 0;
    
    for (let i = 0; i < batches.length; i++) {
      const batch = batches[i];
      console.log(`📦 Processing batch ${i + 1}/${batches.length} (${batch.length} vectors)...`);
      
      try {
        const upsertResponse = await pineconeIndex.upsert(batch);
        totalUpserted += batch.length;
        
        console.log(`✅ Batch ${i + 1} completed successfully`);
        
        // Small delay between batches to respect rate limits
        if (i < batches.length - 1) {
          await new Promise(resolve => setTimeout(resolve, 1000));
        }
        
      } catch (error) {
        console.error(`❌ Batch ${i + 1} failed:`, error.message);
        throw new PineconeError(
          `Failed to upsert batch ${i + 1}`,
          'BATCH_UPSERT_ERROR',
          error.message
        );
      }
    }
    
    console.log(`✅ Successfully upserted ${totalUpserted} vectors to Pinecone`);
    return totalUpserted;
    
  } catch (error) {
    if (error instanceof PineconeError) {
      throw error;
    }
    throw new PineconeError(
      'Failed to upsert vectors to Pinecone',
      'UPSERT_ERROR',
      error.message
    );
  }
}

/**
 * Main function: Chunk and embed data
 */
async function chunkAndEmbedData(content, metadata = {}) {
  const startTime = Date.now();
  
  try {
    console.log('🚀 Starting chunk and embed process...');
    console.log(`📄 Content length: ${content.length} characters`);
    
    // Validate input
    if (!content || typeof content !== 'string' || content.trim().length === 0) {
      throw new PineconeError(
        'Content must be a non-empty string',
        'INVALID_CONTENT'
      );
    }
    
    // Initialize connections if needed
    if (!pineconeIndex) {
      await initializeIndex();
    }
    if (!openaiClient) {
      initializeOpenAI();
    }
    
    // Step 1: Create text chunks
    const chunks = createTextChunks(content);
    
    if (chunks.length === 0) {
      throw new PineconeError(
        'No chunks were created from the content',
        'NO_CHUNKS_CREATED'
      );
    }
    
    // Step 2: Generate embeddings for all chunks
    const chunkTexts = chunks.map(chunk => chunk.text);
    const embeddings = await generateEmbeddings(chunkTexts);
    
    if (embeddings.length !== chunks.length) {
      throw new PineconeError(
        'Mismatch between number of chunks and embeddings',
        'EMBEDDING_MISMATCH'
      );
    }
    
    // Step 3: Prepare vectors for Pinecone
    const vectors = chunks.map((chunk, index) => {
      const vectorId = `${metadata.id || 'chunk'}_${Date.now()}_${index}`;
      
      return {
        id: vectorId,
        values: embeddings[index],
        metadata: {
          text: chunk.text,
          chunkIndex: chunk.index,
          startChar: chunk.startChar,
          endChar: chunk.endChar,
          length: chunk.length,
          originalContentLength: content.length,
          createdAt: new Date().toISOString(),
          ...metadata // Include any additional metadata
        }
      };
    });
    
    // Step 4: Upsert to Pinecone
    const upsertedCount = await upsertVectors(vectors);
    
    const endTime = Date.now();
    const processingTime = endTime - startTime;
    
    // Return comprehensive results
    const result = {
      success: true,
      summary: {
        originalContentLength: content.length,
        chunksCreated: chunks.length,
        embeddingsGenerated: embeddings.length,
        vectorsUpserted: upsertedCount,
        processingTime: `${processingTime}ms`
      },
      chunks: chunks.map((chunk, index) => ({
        id: vectors[index].id,
        text: chunk.text,
        index: chunk.index,
        length: chunk.length,
        embeddingDimension: embeddings[index].length
      })),
      metadata: {
        indexName: CONFIG.INDEX_NAME,
        embeddingModel: CONFIG.EMBEDDING_MODEL,
        chunkSize: CONFIG.CHUNK_SIZE,
        chunkOverlap: CONFIG.CHUNK_OVERLAP,
        timestamp: new Date().toISOString()
      }
    };
    
    console.log('🎉 Chunk and embed process completed successfully!');
    console.log(`📊 Summary: ${result.summary.chunksCreated} chunks, ${result.summary.processingTime}`);
    
    return result;
    
  } catch (error) {
    const endTime = Date.now();
    const processingTime = endTime - startTime;
    
    console.error('💥 Chunk and embed process failed:', error.message);
    
    if (error instanceof PineconeError) {
      throw error;
    }
    
    throw new PineconeError(
      'Chunk and embed process failed',
      'PROCESS_ERROR',
      error.message
    );
  }
}

/**
 * Get index statistics
 */
async function getIndexStats(indexName = CONFIG.INDEX_NAME) {
  try {
    if (!pineconeIndex) {
      await initializeIndex(indexName);
    }
    
    console.log(`📊 Getting statistics for index '${indexName}'...`);
    
    const stats = await pineconeIndex.describeIndexStats();
    
    console.log('✅ Index statistics retrieved successfully');
    return {
      indexName: indexName,
      totalVectorCount: stats.totalVectorCount || 0,
      dimension: stats.dimension || CONFIG.VECTOR_DIMENSION,
      indexFullness: stats.indexFullness || 0,
      namespaces: stats.namespaces || {},
      retrievedAt: new Date().toISOString()
    };
    
  } catch (error) {
    throw new PineconeError(
      `Failed to get statistics for index '${indexName}'`,
      'STATS_ERROR',
      error.message
    );
  }
}

/**
 * Health check for all services
 */
async function healthCheck() {
  const health = {
    pinecone: false,
    openai: false,
    index: false,
    overall: false
  };
  
  try {
    // Check Pinecone connection
    try {
      if (!pineconeClient) {
        await initializePinecone();
      }
      await pineconeClient.listIndexes();
      health.pinecone = true;
      console.log('✅ Pinecone connection: healthy');
    } catch (error) {
      console.log('❌ Pinecone connection: failed');
    }
    
    // Check OpenAI connection
    try {
      if (!openaiClient) {
        initializeOpenAI();
      }
      await openaiClient.models.list();
      health.openai = true;
      console.log('✅ OpenAI connection: healthy');
    } catch (error) {
      console.log('❌ OpenAI connection: failed');
    }
    
    // Check index access
    try {
      await getIndexStats();
      health.index = true;
      console.log('✅ Index access: healthy');
    } catch (error) {
      console.log('❌ Index access: failed');
    }
    
    health.overall = health.pinecone && health.openai && health.index;
    
    return health;
    
  } catch (error) {
    console.error('💥 Health check failed:', error.message);
    return health;
  }
}

module.exports = {
  initializePinecone,
  initializeOpenAI,
  initializeIndex,
  checkIndexExists,
  createIndex,
  chunkAndEmbedData,
  generateEmbeddings,
  createTextChunks,
  upsertVectors,
  getIndexStats,
  healthCheck,
  PineconeError,
  CONFIG
}; 