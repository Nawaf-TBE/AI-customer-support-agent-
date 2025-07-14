require('dotenv').config({ path: '.env.local' });

console.log('🔍 Testing Webapp API Keys...\n');

// Test environment variables loading
console.log('📋 Environment Variables:');
console.log('✓ NEXT_PUBLIC_VAPI_PUBLIC_KEY:', process.env.NEXT_PUBLIC_VAPI_PUBLIC_KEY ? 'Found' : '❌ Missing');
console.log('');

async function testVapiAI() {
  console.log('🎙️ Testing Vapi AI...');
  
  if (!process.env.NEXT_PUBLIC_VAPI_PUBLIC_KEY) {
    console.log('❌ Vapi AI: No API key found');
    return;
  }

  try {
    // Basic test to validate the key format and connection
    // Note: This is a simple validation since Vapi is primarily client-side
    const apiKey = process.env.NEXT_PUBLIC_VAPI_PUBLIC_KEY;
    
    if (apiKey.length < 10) {
      console.log('❌ Vapi AI: API key seems too short');
      return;
    }
    
    console.log('✅ Vapi AI: API key format looks valid!');
    console.log('   Key length:', apiKey.length, 'characters');
    console.log('   Note: Full functionality testing requires client-side implementation');
    
  } catch (error) {
    console.log('❌ Vapi AI: Failed -', error.message);
  }
  
  console.log('');
  console.log('🎉 Webapp API testing complete!');
}

testVapiAI().catch(console.error); 