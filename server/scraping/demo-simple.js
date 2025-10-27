/**
 * Simple Demo - Aven Scraping Module
 * 
 * This demo shows how to use the scraping module to search for
 * Aven support documentation using the Exa.ai API.
 */

const { scrapeAvenData, validateScrapedData } = require('./index');

async function simpleDemo() {
  console.log('🎯 Simple Scraping Demo\n');
  console.log('Searching for: "account setup help"\n');
  
  try {
    // Perform a simple search
    const result = await scrapeAvenData('account setup help', {
      numResults: 3,
      timeout: 30000 // 30 seconds
    });
    
    console.log('✅ Search successful!\n');
    console.log(`📊 Found ${result.results.length} results`);
    console.log(`⏱️  Response time: ${result.metadata.responseTime}\n`);
    
    // Display each result
    result.results.forEach((item, index) => {
      console.log(`Result ${index + 1}:`);
      console.log(`  📰 Title: ${item.title}`);
      console.log(`  🔗 URL: ${item.url}`);
      console.log(`  ⭐ Score: ${item.score}`);
      console.log(`  📝 Content: ${item.text.substring(0, 100)}...`);
      console.log('');
    });
    
    // Validate the data quality
    const validation = validateScrapedData(result);
    if (validation.warnings.length > 0) {
      console.log('⚠️  Warnings:');
      validation.warnings.forEach(warning => console.log(`   • ${warning}`));
      console.log('');
    }
    
  } catch (error) {
    console.error('❌ Error occurred:', error.message);
    console.error('\n💡 Make sure you have:');
    console.error('   1. Created a .env file in the server directory');
    console.error('   2. Added your EXA_API_KEY to the .env file');
    console.error('   3. Installed all dependencies (npm install)');
  }
}

// Run the demo
if (require.main === module) {
  simpleDemo();
}

module.exports = { simpleDemo };

