const { scrapeAvenData, validateScrapedData, ScrapingError, buildAvenQuery } = require('./index');

/**
 * Test the scraping functionality with various scenarios
 */
async function testScraping() {
  console.log('🧪 Testing Aven Data Scraping Module\n');
  
  const testQueries = [
    'support documentation',
    'payment issues',
    'account setup help',
    'Aven troubleshooting guide',
    'API integration'
  ];
  
  for (const query of testQueries) {
    console.log(`\n📝 Testing query: "${query}"`);
    console.log('=' .repeat(50));
    
    try {
      const result = await scrapeAvenData(query, {
        numResults: 5, // Limit to 5 for testing
        timeout: 15000 // 15 seconds for testing
      });
      
      console.log('✅ Success!');
      console.log('📊 Results Summary:');
      console.log(`   • Total results: ${result.metadata.totalResults}`);
      console.log(`   • Response time: ${result.metadata.responseTime}`);
      console.log(`   • Average score: ${result.statistics.averageScore.toFixed(3)}`);
      console.log(`   • Total characters: ${result.statistics.totalCharacters}`);
      
      // Display first result
      if (result.results.length > 0) {
        const first = result.results[0];
        console.log('\n📄 First Result:');
        console.log(`   • Title: ${first.title}`);
        console.log(`   • URL: ${first.url}`);
        console.log(`   • Score: ${first.score}`);
        console.log(`   • Content preview: ${first.text.substring(0, 150)}...`);
      }
      
      // Validate data quality
      const validation = validateScrapedData(result);
      if (validation.warnings.length > 0) {
        console.log('\n⚠️  Validation Warnings:');
        validation.warnings.forEach(warning => console.log(`   • ${warning}`));
      }
      if (validation.suggestions.length > 0) {
        console.log('\n💡 Suggestions:');
        validation.suggestions.forEach(suggestion => console.log(`   • ${suggestion}`));
      }
      
    } catch (error) {
      if (error instanceof ScrapingError) {
        console.log(`❌ Scraping Error [${error.code}]: ${error.message}`);
        if (error.details) {
          console.log(`   Details: ${error.details}`);
        }
      } else {
        console.log(`❌ Unexpected Error: ${error.message}`);
      }
    }
  }
}

/**
 * Test error handling scenarios
 */
async function testErrorHandling() {
  console.log('\n\n🛡️  Testing Error Handling\n');
  console.log('=' .repeat(50));
  
  const errorTests = [
    {
      name: 'Empty query',
      query: '',
      expectedError: 'INVALID_QUERY'
    },
    {
      name: 'Null query',
      query: null,
      expectedError: 'INVALID_QUERY'
    },
    {
      name: 'Whitespace only query',
      query: '   ',
      expectedError: 'INVALID_QUERY'
    }
  ];
  
  for (const test of errorTests) {
    console.log(`\n🧪 Testing: ${test.name}`);
    try {
      await scrapeAvenData(test.query);
      console.log('❌ Expected error but got success');
    } catch (error) {
      if (error instanceof ScrapingError && error.code === test.expectedError) {
        console.log(`✅ Correctly caught expected error: ${error.code}`);
      } else {
        console.log(`❌ Unexpected error type: ${error.message}`);
      }
    }
  }
}

/**
 * Test query enhancement
 */
function testQueryEnhancement() {
  console.log('\n\n🔍 Testing Query Enhancement\n');
  console.log('=' .repeat(50));
  
  const queryTests = [
    { input: 'login issues', expected: 'Aven login issues' },
    { input: 'Aven support help', expected: 'Aven support help' },
    { input: 'aven.com documentation', expected: 'aven.com documentation' },
    { input: 'payment processing', expected: 'Aven payment processing' }
  ];
  
  queryTests.forEach(test => {
    const result = buildAvenQuery(test.input);
    const isCorrect = result === test.expected;
    console.log(`${isCorrect ? '✅' : '❌'} "${test.input}" → "${result}"`);
    if (!isCorrect) {
      console.log(`   Expected: "${test.expected}"`);
    }
  });
}

/**
 * Performance test
 */
async function testPerformance() {
  console.log('\n\n⚡ Performance Test\n');
  console.log('=' .repeat(50));
  
  const startTime = Date.now();
  
  try {
    const result = await scrapeAvenData('account setup', {
      numResults: 3,
      timeout: 10000
    });
    
    const endTime = Date.now();
    const totalTime = endTime - startTime;
    
    console.log(`✅ Performance test completed`);
    console.log(`   • Total time: ${totalTime}ms`);
    console.log(`   • API response time: ${result.metadata.responseTime}`);
    console.log(`   • Results retrieved: ${result.metadata.totalResults}`);
    
    // Performance benchmarks
    if (totalTime < 5000) {
      console.log('🚀 Excellent performance (< 5s)');
    } else if (totalTime < 10000) {
      console.log('✅ Good performance (< 10s)');
    } else {
      console.log('⚠️  Slow performance (> 10s)');
    }
    
  } catch (error) {
    console.log(`❌ Performance test failed: ${error.message}`);
  }
}

/**
 * Main test runner
 */
async function runAllTests() {
  try {
    console.log('🧪 AVEN DATA SCRAPING MODULE TESTS');
    console.log('=====================================\n');
    
    // Test query enhancement (synchronous)
    testQueryEnhancement();
    
    // Test error handling
    await testErrorHandling();
    
    // Test performance
    await testPerformance();
    
    // Test main functionality
    await testScraping();
    
    console.log('\n\n🎉 All tests completed!');
    console.log('=====================================');
    
  } catch (error) {
    console.error('\n💥 Test suite failed:', error.message);
    process.exit(1);
  }
}

// Run tests if this file is executed directly
if (require.main === module) {
  runAllTests().catch(console.error);
}

module.exports = {
  testScraping,
  testErrorHandling,
  testQueryEnhancement,
  testPerformance,
  runAllTests
}; 