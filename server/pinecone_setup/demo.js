const { chunkAndEmbedData, getIndexStats, healthCheck } = require('./index');
const { scrapeAvenData } = require('../scraping');

/**
 * Demo: Integration with scraping module
 */
async function scrapingIntegrationDemo() {
  console.log('🔗 Scraping + Pinecone Integration Demo\n');
  
  try {
    console.log('1️⃣ Scraping Aven support data...');
    const scrapedData = await scrapeAvenData('payment troubleshooting', {
      numResults: 2
    });
    
    console.log(`✅ Scraped ${scrapedData.results.length} results`);
    
    for (let i = 0; i < scrapedData.results.length; i++) {
      const result = scrapedData.results[i];
      console.log(`\n2️⃣ Processing result ${i + 1}: "${result.title}"`);
      
      // Embed the scraped content
      const embedResult = await chunkAndEmbedData(result.text, {
        id: `scraped_${Date.now()}_${i}`,
        source: 'aven-scraper',
        url: result.url,
        title: result.title,
        scrapedAt: result.extractedAt,
        category: 'support-content'
      });
      
      console.log(`✅ Processed into ${embedResult.summary.chunksCreated} chunks`);
      console.log(`   • Processing time: ${embedResult.summary.processingTime}`);
      console.log(`   • Vectors upserted: ${embedResult.summary.vectorsUpserted}`);
    }
    
    console.log('\n🎉 Integration demo completed successfully!');
    
  } catch (error) {
    console.error('❌ Integration demo failed:', error.message);
  }
}

/**
 * Demo: Building knowledge base from multiple sources
 */
async function knowledgeBaseDemo() {
  console.log('\n\n📚 Knowledge Base Building Demo\n');
  
  const supportTopics = [
    'account setup',
    'login issues',
    'payment problems'
  ];
  
  const knowledgeBaseStats = {
    totalChunks: 0,
    totalContent: 0,
    processingTime: 0
  };
  
  try {
    for (let i = 0; i < supportTopics.length; i++) {
      const topic = supportTopics[i];
      console.log(`\n📖 Processing topic ${i + 1}/${supportTopics.length}: "${topic}"`);
      
      // Scrape content for this topic
      const scrapedData = await scrapeAvenData(topic, { numResults: 1 });
      
      if (scrapedData.results.length > 0) {
        const content = scrapedData.results[0];
        
        // Embed the content
        const embedResult = await chunkAndEmbedData(content.text, {
          id: `kb_${topic.replace(/\s+/g, '_')}_${Date.now()}`,
          source: 'knowledge-base',
          topic: topic,
          url: content.url,
          title: content.title,
          category: 'kb-content'
        });
        
        // Update stats
        knowledgeBaseStats.totalChunks += embedResult.summary.chunksCreated;
        knowledgeBaseStats.totalContent += embedResult.summary.originalContentLength;
        knowledgeBaseStats.processingTime += parseInt(embedResult.summary.processingTime);
        
        console.log(`   ✅ Added ${embedResult.summary.chunksCreated} chunks to knowledge base`);
      } else {
        console.log(`   ⚠️ No content found for topic "${topic}"`);
      }
    }
    
    console.log('\n📊 Knowledge Base Summary:');
    console.log(`   • Topics processed: ${supportTopics.length}`);
    console.log(`   • Total chunks: ${knowledgeBaseStats.totalChunks}`);
    console.log(`   • Total content: ${knowledgeBaseStats.totalContent} characters`);
    console.log(`   • Total processing time: ${knowledgeBaseStats.processingTime}ms`);
    
  } catch (error) {
    console.error('❌ Knowledge base demo failed:', error.message);
  }
}

/**
 * Demo: Real-time content processing
 */
async function realTimeProcessingDemo() {
  console.log('\n\n⚡ Real-time Content Processing Demo\n');
  
  // Simulate incoming support content
  const incomingContent = [
    {
      title: 'Password Reset Guide',
      content: `How to reset your Aven password:
        1. Go to the login page
        2. Click "Forgot Password"
        3. Enter your email address
        4. Check your email for reset instructions
        5. Follow the link to create a new password
        Make sure your new password is secure and unique.`
    },
    {
      title: 'Account Verification Process',
      content: `Verifying your Aven account:
        1. Check your email for verification message
        2. Click the verification link
        3. Complete any additional required information
        4. Your account will be activated within 24 hours
        Contact support if you don't receive the verification email.`
    }
  ];
  
  try {
    for (let i = 0; i < incomingContent.length; i++) {
      const content = incomingContent[i];
      console.log(`\n📥 Processing incoming content: "${content.title}"`);
      
      const startTime = Date.now();
      
      const result = await chunkAndEmbedData(content.content, {
        id: `realtime_${Date.now()}_${i}`,
        source: 'real-time-input',
        title: content.title,
        processedAt: new Date().toISOString(),
        category: 'real-time-content'
      });
      
      const processingTime = Date.now() - startTime;
      
      console.log(`   ✅ Processed in ${processingTime}ms`);
      console.log(`   • Chunks: ${result.summary.chunksCreated}`);
      console.log(`   • Vectors: ${result.summary.vectorsUpserted}`);
      
      // Simulate real-time processing delay
      await new Promise(resolve => setTimeout(resolve, 500));
    }
    
    console.log('\n🚀 Real-time processing demo completed!');
    
  } catch (error) {
    console.error('❌ Real-time processing demo failed:', error.message);
  }
}

/**
 * Demo: System monitoring and statistics
 */
async function systemMonitoringDemo() {
  console.log('\n\n📊 System Monitoring Demo\n');
  
  try {
    // Health check
    console.log('🔍 Performing health check...');
    const health = await healthCheck();
    
    console.log('Health Status:');
    console.log(`   • Pinecone: ${health.pinecone ? '✅ Healthy' : '❌ Unhealthy'}`);
    console.log(`   • OpenAI: ${health.openai ? '✅ Healthy' : '❌ Unhealthy'}`);
    console.log(`   • Index: ${health.index ? '✅ Healthy' : '❌ Unhealthy'}`);
    console.log(`   • Overall: ${health.overall ? '✅ System OK' : '❌ Issues Detected'}`);
    
    // Get index statistics
    console.log('\n📈 Getting index statistics...');
    const stats = await getIndexStats();
    
    console.log('Index Statistics:');
    console.log(`   • Index name: ${stats.indexName}`);
    console.log(`   • Total vectors: ${stats.totalVectorCount.toLocaleString()}`);
    console.log(`   • Vector dimension: ${stats.dimension}`);
    console.log(`   • Index fullness: ${(stats.indexFullness * 100).toFixed(2)}%`);
    console.log(`   • Last updated: ${stats.retrievedAt}`);
    
    // Calculate storage info
    const estimatedSize = stats.totalVectorCount * stats.dimension * 4; // 4 bytes per float
    const sizeInMB = (estimatedSize / 1024 / 1024).toFixed(2);
    
    console.log(`   • Estimated size: ${sizeInMB} MB`);
    
    if (stats.totalVectorCount > 0) {
      console.log('\n✅ System is operational with data');
    } else {
      console.log('\n⚠️ System is operational but no data found');
    }
    
  } catch (error) {
    console.error('❌ System monitoring demo failed:', error.message);
  }
}

/**
 * Demo: Error handling and recovery
 */
async function errorHandlingDemo() {
  console.log('\n\n🛡️ Error Handling Demo\n');
  
  const testCases = [
    {
      name: 'Empty content handling',
      content: '',
      expectError: true
    },
    {
      name: 'Very large content handling',
      content: 'A'.repeat(50000), // 50KB of text
      expectError: false
    },
    {
      name: 'Special characters handling',
      content: 'Content with émojis 🚀 and spëcial châractérs ñ',
      expectError: false
    }
  ];
  
  for (const testCase of testCases) {
    console.log(`\n🧪 Testing: ${testCase.name}`);
    
    try {
      const result = await chunkAndEmbedData(testCase.content, {
        id: `error_test_${Date.now()}`,
        source: 'error-handling-demo',
        testCase: testCase.name
      });
      
      if (testCase.expectError) {
        console.log('   ❌ Expected error but operation succeeded');
      } else {
        console.log(`   ✅ Successfully processed ${result.summary.chunksCreated} chunks`);
      }
      
    } catch (error) {
      if (testCase.expectError) {
        console.log(`   ✅ Correctly caught expected error: ${error.code || error.message}`);
      } else {
        console.log(`   ❌ Unexpected error: ${error.message}`);
      }
    }
  }
}

/**
 * Run all demos
 */
async function runAllDemos() {
  console.log('🎬 PINECONE SETUP MODULE DEMOS');
  console.log('===============================');
  
  try {
    await scrapingIntegrationDemo();
    await knowledgeBaseDemo();
    await realTimeProcessingDemo();
    await systemMonitoringDemo();
    await errorHandlingDemo();
    
    console.log('\n\n🎉 All demos completed successfully!');
    console.log('===============================');
    
  } catch (error) {
    console.error('\n💥 Demo suite failed:', error.message);
  }
}

// Run demos if this file is executed directly
if (require.main === module) {
  runAllDemos().catch(console.error);
}

module.exports = {
  scrapingIntegrationDemo,
  knowledgeBaseDemo,
  realTimeProcessingDemo,
  systemMonitoringDemo,
  errorHandlingDemo,
  runAllDemos
}; 