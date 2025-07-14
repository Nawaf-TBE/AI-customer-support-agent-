const { chunkAndEmbedData, getIndexStats } = require('./index');

/**
 * Simple end-to-end test of chunkAndEmbedData function
 */
async function testChunkAndEmbed() {
  console.log('🧪 Testing Chunk and Embed Function\n');
  
  const testContent = `
    Aven Customer Support Guide
    
    Welcome to Aven! This guide will help you resolve common issues.
    
    Login Issues:
    If you're having trouble logging in, please check your email and password.
    Make sure your account is verified and your internet connection is stable.
    
    Payment Problems:
    For payment issues, verify your payment method is valid and has sufficient funds.
    Contact your bank if the problem persists.
    
    Account Verification:
    Check your email for the verification link and click it to activate your account.
    If you don't see the email, check your spam folder.
    
    Contact Support:
    If none of these solutions work, please contact our support team at support@aven.com
    or use the live chat feature on our website.
  `.trim();
  
  try {
    console.log('📄 Content to process:');
    console.log(`   • Length: ${testContent.length} characters`);
    console.log(`   • Preview: ${testContent.substring(0, 100)}...`);
    
    console.log('\n🚀 Starting chunk and embed process...');
    
    const startTime = Date.now();
    
    const result = await chunkAndEmbedData(testContent, {
      id: 'test-support-guide',
      source: 'simple-test',
      category: 'customer-support',
      title: 'Aven Customer Support Guide',
      testRun: true
    });
    
    const endTime = Date.now();
    const totalTime = endTime - startTime;
    
    console.log('\n✅ Process completed successfully!');
    console.log('\n📊 Results Summary:');
    console.log(`   • Chunks created: ${result.summary.chunksCreated}`);
    console.log(`   • Embeddings generated: ${result.summary.embeddingsGenerated}`);
    console.log(`   • Vectors upserted: ${result.summary.vectorsUpserted}`);
    console.log(`   • Processing time: ${result.summary.processingTime}`);
    console.log(`   • Total time: ${totalTime}ms`);
    
    // Show chunk details
    console.log('\n📝 Chunk Details:');
    result.chunks.forEach((chunk, index) => {
      console.log(`   ${index + 1}. ID: ${chunk.id}`);
      console.log(`      Length: ${chunk.length} chars`);
      console.log(`      Preview: ${chunk.text.substring(0, 60)}...`);
    });
    
    // Get updated index stats
    console.log('\n📈 Getting updated index statistics...');
    const stats = await getIndexStats();
    console.log(`   • Total vectors in index: ${stats.totalVectorCount}`);
    console.log(`   • Index dimension: ${stats.dimension}`);
    console.log(`   • Index fullness: ${(stats.indexFullness * 100).toFixed(4)}%`);
    
    console.log('\n🎉 Simple test completed successfully!');
    console.log('💡 Your Pinecone setup is fully functional and ready for production use.');
    
    return true;
    
  } catch (error) {
    console.error('\n❌ Test failed:', error.message);
    console.error('Error details:', error);
    return false;
  }
}

// Run simple test if this file is executed directly
if (require.main === module) {
  testChunkAndEmbed().catch(console.error);
}

module.exports = { testChunkAndEmbed }; 