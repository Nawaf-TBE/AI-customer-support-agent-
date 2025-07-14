require('dotenv').config();
const Exa = require('exa-js').default;

console.log('🔍 Testing API Keys...\n');

// Test environment variables loading
console.log('📋 Environment Variables:');
console.log('✓ PINECONE_API_KEY:', process.env.PINECONE_API_KEY ? 'Found' : '❌ Missing');
console.log('✓ PINECONE_ENVIRONMENT:', process.env.PINECONE_ENVIRONMENT ? 'Found' : '❌ Missing');
console.log('✓ EXA_API_KEY:', process.env.EXA_API_KEY ? 'Found' : '❌ Missing');
console.log('✓ OPENAI_API_KEY:', process.env.OPENAI_API_KEY ? 'Found' : '❌ Missing');
console.log('');

async function testAPIs() {
  // Test Exa AI
  console.log('🔍 Testing Exa AI...');
  try {
    const exa = new Exa(process.env.EXA_API_KEY);
    const result = await exa.search('test query', { numResults: 1 });
    console.log('✅ Exa AI: Connection successful!');
    console.log(`   Found ${result.results.length} result(s)`);
  } catch (error) {
    console.log('❌ Exa AI: Failed -', error.message);
  }
  console.log('');

  // Test OpenAI (if available)
  if (process.env.OPENAI_API_KEY) {
    console.log('🤖 Testing OpenAI...');
    try {
      const response = await fetch('https://api.openai.com/v1/models', {
        headers: {
          'Authorization': `Bearer ${process.env.OPENAI_API_KEY}`,
          'Content-Type': 'application/json',
        },
      });
      
      if (response.ok) {
        console.log('✅ OpenAI: Connection successful!');
      } else {
        console.log('❌ OpenAI: Failed - HTTP', response.status);
      }
    } catch (error) {
      console.log('❌ OpenAI: Failed -', error.message);
    }
    console.log('');
  }

  // Test Pinecone (basic connection test)
  if (process.env.PINECONE_API_KEY && process.env.PINECONE_ENVIRONMENT) {
    console.log('📌 Testing Pinecone...');
    try {
      const response = await fetch('https://controller.pinecone.io/actions/whoami', {
        headers: {
          'Api-Key': process.env.PINECONE_API_KEY,
          'Content-Type': 'application/json',
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log('✅ Pinecone: Connection successful!');
        console.log(`   User: ${data.username || 'Unknown'}`);
      } else {
        console.log('❌ Pinecone: Failed - HTTP', response.status);
      }
    } catch (error) {
      console.log('❌ Pinecone: Failed -', error.message);
    }
    console.log('');
  }

  console.log('🎉 API testing complete!');
}

testAPIs().catch(console.error); 