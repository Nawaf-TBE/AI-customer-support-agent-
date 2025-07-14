const { 
  initializePinecone, 
  initializeOpenAI, 
  createTextChunks, 
  CONFIG,
  PineconeError 
} = require('./index');

/**
 * Quick health check for Pinecone setup
 */
async function quickHealthCheck() {
  console.log('🔍 Quick Pinecone Setup Health Check\n');
  
  const results = {
    pinecone: false,
    openai: false,
    chunking: false,
    config: false
  };
  
  try {
    // Test 1: Configuration
    console.log('1️⃣ Testing Configuration...');
    if (process.env.PINECONE_API_KEY && process.env.OPENAI_API_KEY) {
      results.config = true;
      console.log('✅ Environment variables found');
    } else {
      console.log('❌ Missing environment variables');
      console.log(`   PINECONE_API_KEY: ${process.env.PINECONE_API_KEY ? 'Found' : 'Missing'}`);
      console.log(`   OPENAI_API_KEY: ${process.env.OPENAI_API_KEY ? 'Found' : 'Missing'}`);
    }
    
    // Test 2: Pinecone Client
    console.log('\n2️⃣ Testing Pinecone Client...');
    try {
      const pineconeClient = await initializePinecone();
      const indexes = await pineconeClient.listIndexes();
      results.pinecone = true;
      console.log(`✅ Pinecone connected (${indexes.indexes?.length || 0} indexes available)`);
    } catch (error) {
      console.log(`❌ Pinecone failed: ${error.message}`);
    }
    
    // Test 3: OpenAI Client
    console.log('\n3️⃣ Testing OpenAI Client...');
    try {
      const openaiClient = initializeOpenAI();
      // Just test initialization, not API call to save costs
      results.openai = true;
      console.log('✅ OpenAI client initialized');
    } catch (error) {
      console.log(`❌ OpenAI failed: ${error.message}`);
    }
    
    // Test 4: Text Chunking
    console.log('\n4️⃣ Testing Text Chunking...');
    try {
      const testText = 'This is a simple test for text chunking functionality. '.repeat(20);
      const chunks = createTextChunks(testText, 100, 20);
      if (chunks.length > 0 && chunks[0].text.length > 0) {
        results.chunking = true;
        console.log(`✅ Text chunking works (${chunks.length} chunks created)`);
      } else {
        console.log('❌ Text chunking failed - no valid chunks created');
      }
    } catch (error) {
      console.log(`❌ Text chunking failed: ${error.message}`);
    }
    
    // Summary
    console.log('\n📊 Health Check Summary:');
    console.log('=' .repeat(30));
    Object.entries(results).forEach(([test, passed]) => {
      console.log(`${passed ? '✅' : '❌'} ${test}: ${passed ? 'PASSED' : 'FAILED'}`);
    });
    
    const passedCount = Object.values(results).filter(r => r).length;
    const totalCount = Object.keys(results).length;
    const successRate = Math.round((passedCount / totalCount) * 100);
    
    console.log(`\n🎯 Overall: ${passedCount}/${totalCount} tests passed (${successRate}%)`);
    
    if (successRate >= 75) {
      console.log('🎉 Basic setup is working! Ready for full testing.');
      return true;
    } else {
      console.log('⚠️ Some issues detected. Please check configuration and API keys.');
      return false;
    }
    
  } catch (error) {
    console.error('💥 Health check failed:', error.message);
    return false;
  }
}

/**
 * Test basic index operations
 */
async function testBasicIndexOps() {
  console.log('\n\n🔧 Testing Basic Index Operations\n');
  
  try {
    const { checkIndexExists, CONFIG } = require('./index');
    
    console.log(`🔍 Checking if index '${CONFIG.INDEX_NAME}' exists...`);
    const exists = await checkIndexExists(CONFIG.INDEX_NAME);
    
    if (exists) {
      console.log(`✅ Index '${CONFIG.INDEX_NAME}' exists`);
    } else {
      console.log(`❌ Index '${CONFIG.INDEX_NAME}' does not exist`);
      console.log('💡 The index will be created automatically when needed');
    }
    
    return exists;
    
  } catch (error) {
    console.log(`❌ Index check failed: ${error.message}`);
    return false;
  }
}

/**
 * Show configuration
 */
function showConfiguration() {
  console.log('\n\n⚙️ Configuration Summary\n');
  console.log('═'.repeat(40));
  
  console.log('📋 Pinecone Setup Configuration:');
  console.log(`   • Index Name: ${CONFIG.INDEX_NAME}`);
  console.log(`   • Vector Dimension: ${CONFIG.VECTOR_DIMENSION}`);
  console.log(`   • Embedding Model: ${CONFIG.EMBEDDING_MODEL}`);
  console.log(`   • Chunk Size: ${CONFIG.CHUNK_SIZE} characters`);
  console.log(`   • Chunk Overlap: ${CONFIG.CHUNK_OVERLAP} characters`);
  console.log(`   • Batch Size: ${CONFIG.BATCH_SIZE} vectors`);
  
  console.log('\n🔑 Environment Variables:');
  console.log(`   • PINECONE_API_KEY: ${process.env.PINECONE_API_KEY ? 'Set' : 'Not set'}`);
  console.log(`   • OPENAI_API_KEY: ${process.env.OPENAI_API_KEY ? 'Set' : 'Not set'}`);
}

/**
 * Main test runner
 */
async function runQuickTest() {
  console.log('🚀 PINECONE SETUP - QUICK TEST');
  console.log('═'.repeat(40));
  
  showConfiguration();
  
  const healthOk = await quickHealthCheck();
  
  if (healthOk) {
    await testBasicIndexOps();
  }
  
  console.log('\n' + '═'.repeat(40));
  
  if (healthOk) {
    console.log('✨ Quick test completed successfully!');
    console.log('💡 You can now run the full test suite: node test-pinecone.js');
    console.log('🎬 Or try the demos: node demo.js');
  } else {
    console.log('⚠️ Please fix the issues above before proceeding.');
  }
  
  return healthOk;
}

// Run quick test if this file is executed directly
if (require.main === module) {
  runQuickTest().catch(console.error);
}

module.exports = {
  quickHealthCheck,
  testBasicIndexOps,
  showConfiguration,
  runQuickTest
}; 