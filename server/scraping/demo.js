const { scrapeAvenData, validateScrapedData } = require('./index');

/**
 * Demo: Basic usage of the scraping module
 */
async function basicDemo() {
  console.log('🚀 Basic Scraping Demo\n');
  
  try {
    const result = await scrapeAvenData('payment troubleshooting', {
      numResults: 3
    });
    
    console.log('✅ Successfully scraped Aven data!');
    console.log(`📊 Found ${result.results.length} results in ${result.metadata.responseTime}`);
    
    // Show first result
    if (result.results.length > 0) {
      const first = result.results[0];
      console.log('\n📄 Top Result:');
      console.log(`   Title: ${first.title}`);
      console.log(`   URL: ${first.url}`);
      console.log(`   Content: ${first.text.substring(0, 200)}...`);
    }
    
  } catch (error) {
    console.error('❌ Error:', error.message);
  }
}

/**
 * Demo: Customer support knowledge base building
 */
async function knowledgeBaseDemo() {
  console.log('\n\n🏗️  Knowledge Base Building Demo\n');
  
  const supportTopics = [
    'login problems',
    'password reset',
    'account verification'
  ];
  
  const knowledgeBase = [];
  
  for (const topic of supportTopics) {
    console.log(`🔍 Scraping: ${topic}`);
    
    try {
      const result = await scrapeAvenData(topic, {
        numResults: 2,
        maxCharacters: 1500
      });
      
      // Add to knowledge base
      result.results.forEach(item => {
        knowledgeBase.push({
          topic: topic,
          title: item.title,
          url: item.url,
          content: item.text,
          lastUpdated: item.extractedAt
        });
      });
      
      console.log(`   ✅ Added ${result.results.length} entries`);
      
    } catch (error) {
      console.log(`   ❌ Failed: ${error.message}`);
    }
  }
  
  console.log(`\n📚 Knowledge Base Complete: ${knowledgeBase.length} total entries`);
  return knowledgeBase;
}

/**
 * Demo: Real-time customer query handling
 */
async function customerQueryDemo() {
  console.log('\n\n💬 Customer Query Handling Demo\n');
  
  // Simulate customer queries
  const customerQueries = [
    "I can't log into my account",
    "My payment was declined",
    "How do I update my information?"
  ];
  
  for (const query of customerQueries) {
    console.log(`👤 Customer Query: "${query}"`);
    
    try {
      const result = await scrapeAvenData(query, {
        numResults: 1,
        timeout: 10000
      });
      
      if (result.results.length > 0) {
        const answer = result.results[0];
        console.log(`🤖 AI Response Source: ${answer.title}`);
        console.log(`🔗 Reference: ${answer.url}`);
        console.log(`📝 Content Summary: ${answer.text.substring(0, 150)}...\n`);
      } else {
        console.log('🤖 No specific documentation found. Escalating to human agent.\n');
      }
      
    } catch (error) {
      console.log(`❌ Error processing query: ${error.message}\n`);
    }
  }
}

/**
 * Demo: Data quality analysis
 */
async function dataQualityDemo() {
  console.log('\n\n📊 Data Quality Analysis Demo\n');
  
  const result = await scrapeAvenData('support documentation', {
    numResults: 5
  });
  
  const validation = validateScrapedData(result);
  
  console.log('🔍 Quality Report:');
  console.log(`   • Results found: ${result.metadata.totalResults}`);
  console.log(`   • Average relevance: ${result.statistics.averageScore.toFixed(3)}`);
  console.log(`   • Total content: ${result.statistics.totalCharacters} characters`);
  console.log(`   • Valid URLs: ${result.statistics.urlsFound}`);
  
  if (validation.warnings.length > 0) {
    console.log('\n⚠️  Quality Issues:');
    validation.warnings.forEach(warning => console.log(`   • ${warning}`));
  }
  
  if (validation.suggestions.length > 0) {
    console.log('\n💡 Recommendations:');
    validation.suggestions.forEach(suggestion => console.log(`   • ${suggestion}`));
  }
}

/**
 * Run all demos
 */
async function runDemos() {
  console.log('🎬 AVEN SCRAPING MODULE DEMOS');
  console.log('===============================');
  
  try {
    await basicDemo();
    await knowledgeBaseDemo();
    await customerQueryDemo();
    await dataQualityDemo();
    
    console.log('\n✨ All demos completed successfully!');
    
  } catch (error) {
    console.error('\n💥 Demo failed:', error.message);
  }
}

// Run demos if this file is executed directly
if (require.main === module) {
  runDemos().catch(console.error);
}

module.exports = {
  basicDemo,
  knowledgeBaseDemo,
  customerQueryDemo,
  dataQualityDemo,
  runDemos
};
// Safe no-op comment for CI/test commit 