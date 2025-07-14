require('dotenv').config();
const Exa = require('exa-js').default;

console.log('🔍 Testing API Keys (Simple Test)...\n');

// Test environment variables loading
console.log('📋 Environment Variables:');
console.log('✓ PINECONE_API_KEY:', process.env.PINECONE_API_KEY ? `Found (${process.env.PINECONE_API_KEY.length} chars)` : '❌ Missing');
console.log('✓ PINECONE_ENVIRONMENT:', process.env.PINECONE_ENVIRONMENT ? `Found (${process.env.PINECONE_ENVIRONMENT})` : '❌ Missing');
console.log('✓ EXA_API_KEY:', process.env.EXA_API_KEY ? `Found (${process.env.EXA_API_KEY.length} chars)` : '❌ Missing');
console.log('✓ OPENAI_API_KEY:', process.env.OPENAI_API_KEY ? `Found (${process.env.OPENAI_API_KEY.length} chars)` : '❌ Missing');
console.log('');

async function testExa() {
  console.log('🔍 Testing Exa AI...');
  try {
    const exa = new Exa(process.env.EXA_API_KEY);
    console.log('   Exa client created successfully');
    
    // Test with a simple search
    const result = await exa.search('artificial intelligence', { 
      numResults: 2,
      type: 'auto'
    });
    
    console.log('✅ Exa AI: Connection successful!');
    console.log(`   Found ${result.results.length} result(s)`);
    if (result.results.length > 0) {
      console.log(`   First result: ${result.results[0].title}`);
    }
  } catch (error) {
    console.log('❌ Exa AI: Failed');
    console.log('   Error:', error.message);
    if (error.response) {
      console.log('   Status:', error.response.status);
      console.log('   Response:', error.response.statusText);
    }
  }
  console.log('');
  console.log('🎉 Simple API testing complete!');
}

testExa().catch(console.error); 