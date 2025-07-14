const {
  initializePinecone,
  initializeOpenAI,
  initializeIndex,
  checkIndexExists,
  createIndex,
  chunkAndEmbedData,
  generateEmbeddings,
  createTextChunks,
  getIndexStats,
  healthCheck,
  PineconeError,
  CONFIG
} = require('./index');

/**
 * Test Pinecone client initialization
 */
async function testPineconeInit() {
  console.log('\n🧪 Testing Pinecone Initialization...');
  console.log('='.repeat(50));
  
  try {
    const client = await initializePinecone();
    console.log('✅ Pinecone client initialized successfully');
    
    // Test listing indexes
    const indexes = await client.listIndexes();
    console.log(`📋 Available indexes: ${indexes.indexes?.length || 0}`);
    
    return true;
  } catch (error) {
    console.log('❌ Pinecone initialization failed:', error.message);
    return false;
  }
}

/**
 * Test OpenAI client initialization
 */
async function testOpenAIInit() {
  console.log('\n🧪 Testing OpenAI Initialization...');
  console.log('='.repeat(50));
  
  try {
    const client = initializeOpenAI();
    console.log('✅ OpenAI client initialized successfully');
    
    // Test listing models
    const models = await client.models.list();
    console.log(`🤖 Available models: ${models.data?.length || 0}`);
    
    return true;
  } catch (error) {
    console.log('❌ OpenAI initialization failed:', error.message);
    return false;
  }
}

/**
 * Test text chunking functionality
 */
function testTextChunking() {
  console.log('\n🧪 Testing Text Chunking...');
  console.log('='.repeat(50));
  
  const testTexts = [
    {
      name: 'Short text',
      content: 'This is a short text for testing.',
      expectedChunks: 1
    },
    {
      name: 'Medium text',
      content: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. '.repeat(20),
      expectedChunks: 1
    },
    {
      name: 'Long text',
      content: 'This is a longer text that should be split into multiple chunks. '.repeat(50),
      expectedChunks: 3
    }
  ];
  
  let passed = 0;
  
  testTexts.forEach(test => {
    try {
      const chunks = createTextChunks(test.content, 1000, 200);
      const success = chunks.length > 0;
      
      console.log(`${success ? '✅' : '❌'} ${test.name}:`);
      console.log(`   • Content length: ${test.content.length} chars`);
      console.log(`   • Chunks created: ${chunks.length}`);
      console.log(`   • Avg chunk size: ${Math.round(chunks.reduce((sum, c) => sum + c.length, 0) / chunks.length)}`);
      
      if (success) passed++;
      
    } catch (error) {
      console.log(`❌ ${test.name}: ${error.message}`);
    }
  });
  
  console.log(`\n📊 Chunking tests: ${passed}/${testTexts.length} passed`);
  return passed === testTexts.length;
}

/**
 * Test embedding generation
 */
async function testEmbeddings() {
  console.log('\n🧪 Testing Embedding Generation...');
  console.log('='.repeat(50));
  
  const testTexts = [
    'This is a test sentence for embedding.',
    'Another test sentence with different content.',
    'A third test to verify batch processing.'
  ];
  
  try {
    const embeddings = await generateEmbeddings(testTexts);
    
    console.log('✅ Embeddings generated successfully');
    console.log(`   • Input texts: ${testTexts.length}`);
    console.log(`   • Output embeddings: ${embeddings.length}`);
    console.log(`   • Embedding dimension: ${embeddings[0]?.length || 'unknown'}`);
    console.log(`   • Expected dimension: ${CONFIG.VECTOR_DIMENSION}`);
    
    const correctDimension = embeddings[0]?.length === CONFIG.VECTOR_DIMENSION;
    const correctCount = embeddings.length === testTexts.length;
    
    if (correctDimension && correctCount) {
      console.log('✅ All embedding tests passed');
      return true;
    } else {
      console.log('❌ Embedding validation failed');
      return false;
    }
    
  } catch (error) {
    console.log('❌ Embedding generation failed:', error.message);
    return false;
  }
}

/**
 * Test index operations
 */
async function testIndexOperations() {
  console.log('\n🧪 Testing Index Operations...');
  console.log('='.repeat(50));
  
  try {
    // Check if index exists
    const exists = await checkIndexExists(CONFIG.INDEX_NAME);
    console.log(`📋 Index '${CONFIG.INDEX_NAME}' exists: ${exists}`);
    
    // Initialize index (will create if doesn't exist)
    const index = await initializeIndex();
    console.log('✅ Index initialized successfully');
    
    // Get index statistics
    const stats = await getIndexStats();
    console.log('📊 Index Statistics:');
    console.log(`   • Total vectors: ${stats.totalVectorCount}`);
    console.log(`   • Dimension: ${stats.dimension}`);
    console.log(`   • Index fullness: ${(stats.indexFullness * 100).toFixed(2)}%`);
    
    return true;
    
  } catch (error) {
    console.log('❌ Index operations failed:', error.message);
    return false;
  }
}

/**
 * Test complete chunk and embed process
 */
async function testChunkAndEmbed() {
  console.log('\n🧪 Testing Complete Chunk and Embed Process...');
  console.log('='.repeat(50));
  
  const testContent = `
    Aven Support Documentation
    
    Welcome to Aven support! This guide will help you understand how to use our platform effectively.
    
    Getting Started:
    1. Create your account
    2. Verify your email address
    3. Complete your profile setup
    4. Start using Aven features
    
    Common Issues:
    - Login problems: Check your email and password
    - Payment issues: Verify your payment method
    - Account verification: Check your email for verification link
    
    For additional help, contact our support team at support@aven.com.
  `.trim();
  
  try {
    const result = await chunkAndEmbedData(testContent, {
      id: 'test-content',
      source: 'test-script',
      category: 'support-docs'
    });
    
    console.log('✅ Chunk and embed process completed successfully');
    console.log('📊 Process Summary:');
    console.log(`   • Original content: ${result.summary.originalContentLength} chars`);
    console.log(`   • Chunks created: ${result.summary.chunksCreated}`);
    console.log(`   • Embeddings generated: ${result.summary.embeddingsGenerated}`);
    console.log(`   • Vectors upserted: ${result.summary.vectorsUpserted}`);
    console.log(`   • Processing time: ${result.summary.processingTime}`);
    
    // Show first chunk as example
    if (result.chunks.length > 0) {
      const firstChunk = result.chunks[0];
      console.log('\n📄 Sample Chunk:');
      console.log(`   • ID: ${firstChunk.id}`);
      console.log(`   • Length: ${firstChunk.length} chars`);
      console.log(`   • Text preview: ${firstChunk.text.substring(0, 100)}...`);
    }
    
    return true;
    
  } catch (error) {
    console.log('❌ Chunk and embed process failed:', error.message);
    return false;
  }
}

/**
 * Test health check functionality
 */
async function testHealthCheck() {
  console.log('\n🧪 Testing Health Check...');
  console.log('='.repeat(50));
  
  try {
    const health = await healthCheck();
    
    console.log('🔍 Health Check Results:');
    console.log(`   • Pinecone: ${health.pinecone ? '✅ Healthy' : '❌ Failed'}`);
    console.log(`   • OpenAI: ${health.openai ? '✅ Healthy' : '❌ Failed'}`);
    console.log(`   • Index: ${health.index ? '✅ Healthy' : '❌ Failed'}`);
    console.log(`   • Overall: ${health.overall ? '✅ Healthy' : '❌ Failed'}`);
    
    return health.overall;
    
  } catch (error) {
    console.log('❌ Health check failed:', error.message);
    return false;
  }
}

/**
 * Test error handling
 */
async function testErrorHandling() {
  console.log('\n🧪 Testing Error Handling...');
  console.log('='.repeat(50));
  
  const errorTests = [
    {
      name: 'Empty content',
      test: () => chunkAndEmbedData(''),
      expectedError: 'INVALID_CONTENT'
    },
    {
      name: 'Invalid text chunking',
      test: () => createTextChunks(null),
      expectedError: 'INVALID_TEXT'
    },
    {
      name: 'Invalid embedding input',
      test: () => generateEmbeddings([]),
      expectedError: 'EMBEDDING_ERROR'
    }
  ];
  
  let passed = 0;
  
  for (const test of errorTests) {
    try {
      await test.test();
      console.log(`❌ ${test.name}: Expected error but got success`);
    } catch (error) {
      if (error instanceof PineconeError && error.code === test.expectedError) {
        console.log(`✅ ${test.name}: Correctly caught expected error (${error.code})`);
        passed++;
      } else {
        console.log(`❌ ${test.name}: Unexpected error - ${error.message}`);
      }
    }
  }
  
  console.log(`\n📊 Error handling tests: ${passed}/${errorTests.length} passed`);
  return passed === errorTests.length;
}

/**
 * Performance test
 */
async function testPerformance() {
  console.log('\n🧪 Testing Performance...');
  console.log('='.repeat(50));
  
  const testContent = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. '.repeat(100);
  const startTime = Date.now();
  
  try {
    const result = await chunkAndEmbedData(testContent, {
      id: 'performance-test',
      source: 'performance-script'
    });
    
    const endTime = Date.now();
    const totalTime = endTime - startTime;
    
    console.log('✅ Performance test completed');
    console.log(`   • Content processed: ${testContent.length} chars`);
    console.log(`   • Chunks created: ${result.summary.chunksCreated}`);
    console.log(`   • Total time: ${totalTime}ms`);
    console.log(`   • Processing time: ${result.summary.processingTime}`);
    console.log(`   • Time per chunk: ${Math.round(totalTime / result.summary.chunksCreated)}ms`);
    
    // Performance benchmarks
    const isGoodPerformance = totalTime < 30000; // 30 seconds
    console.log(`   • Performance: ${isGoodPerformance ? '🚀 Good' : '⚠️ Slow'}`);
    
    return isGoodPerformance;
    
  } catch (error) {
    console.log('❌ Performance test failed:', error.message);
    return false;
  }
}

/**
 * Main test runner
 */
async function runAllTests() {
  console.log('🧪 PINECONE SETUP MODULE TESTS');
  console.log('==================================');
  
  const testResults = {};
  
  try {
    // Run all tests
    testResults.textChunking = testTextChunking();
    testResults.pineconeInit = await testPineconeInit();
    testResults.openaiInit = await testOpenAIInit();
    testResults.errorHandling = await testErrorHandling();
    testResults.embeddings = await testEmbeddings();
    testResults.indexOps = await testIndexOperations();
    testResults.healthCheck = await testHealthCheck();
    testResults.chunkAndEmbed = await testChunkAndEmbed();
    testResults.performance = await testPerformance();
    
    // Calculate results
    const totalTests = Object.keys(testResults).length;
    const passedTests = Object.values(testResults).filter(result => result === true).length;
    const successRate = Math.round((passedTests / totalTests) * 100);
    
    console.log('\n' + '='.repeat(50));
    console.log('📊 TEST RESULTS SUMMARY');
    console.log('='.repeat(50));
    
    Object.entries(testResults).forEach(([testName, passed]) => {
      console.log(`${passed ? '✅' : '❌'} ${testName}: ${passed ? 'PASSED' : 'FAILED'}`);
    });
    
    console.log(`\n🎯 Overall: ${passedTests}/${totalTests} tests passed (${successRate}%)`);
    
    if (successRate >= 80) {
      console.log('🎉 Test suite PASSED - Pinecone setup is working correctly!');
    } else {
      console.log('⚠️ Test suite FAILED - Some issues need to be addressed');
    }
    
    return successRate >= 80;
    
  } catch (error) {
    console.error('\n💥 Test suite crashed:', error.message);
    return false;
  }
}

// Run tests if this file is executed directly
if (require.main === module) {
  runAllTests().catch(console.error);
}

module.exports = {
  testPineconeInit,
  testOpenAIInit,
  testTextChunking,
  testEmbeddings,
  testIndexOperations,
  testChunkAndEmbed,
  testHealthCheck,
  testErrorHandling,
  testPerformance,
  runAllTests
}; 