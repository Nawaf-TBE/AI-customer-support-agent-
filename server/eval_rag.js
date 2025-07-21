const fetch = require('node-fetch');
const fs = require('fs');

// 1. Define at least 50 realistic user questions about Aven
const evaluationSet = [
  "How do I reset my Aven account password?",
  "What should I do if I can't log in to my Aven account?",
  "How can I update my billing information on Aven?",
  "Where can I find my transaction history in Aven?",
  "How do I contact Aven customer support?",
  "What are the fees for using Aven's services?",
  "How do I close my Aven account?",
  "Is my personal information safe with Aven?",
  "How do I enable two-factor authentication on Aven?",
  "What should I do if I suspect fraudulent activity?",
  "How do I verify my identity on Aven?",
  "Can I use Aven outside the United States?",
  "How do I change my email address in Aven?",
  "What is Aven's refund policy?",
  "How do I dispute a charge on my Aven account?",
  "How long does it take to process a withdrawal?",
  "What payment methods does Aven accept?",
  "How do I set up direct deposit with Aven?",
  "Why was my transaction declined?",
  "How do I report a lost or stolen card?",
  "How do I activate my new Aven card?",
  "What should I do if I forget my PIN?",
  "How do I set spending limits on my Aven card?",
  "Can I get a replacement card from Aven?",
  "How do I refer a friend to Aven?",
  "What rewards does Aven offer?",
  "How do I redeem Aven rewards?",
  "How do I update my phone number in Aven?",
  "What is Aven's privacy policy?",
  "How do I opt out of marketing emails from Aven?",
  "How do I check my Aven account balance?",
  "Can I link external bank accounts to Aven?",
  "How do I set up account alerts in Aven?",
  "What should I do if my account is locked?",
  "How do I upload documents for verification?",
  "How do I change my address in Aven?",
  "What is the minimum balance required for Aven?",
  "How do I download my Aven statements?",
  "How do I reset my security questions?",
  "How do I request a credit limit increase?",
  "How do I check my application status?",
  "What is Aven's customer service phone number?",
  "How do I set up recurring payments?",
  "How do I cancel a subscription through Aven?",
  "How do I update my employment information?",
  "How do I add an authorized user?",
  "How do I report a technical issue?",
  "How do I access Aven's mobile app?",
  "How do I enable push notifications?",
  "How do I reset my app password?"
];

// 2. Scoring functions
function scoreAccuracy(response, contextChunks) {
  // Score 1 if at least one keyword from context is in the response, else 0
  if (!contextChunks || contextChunks.length === 0) return 0;
  const keywords = contextChunks
    .join(' ')
    .toLowerCase()
    .split(/\W+/)
    .filter(w => w.length > 4);
  const uniqueKeywords = Array.from(new Set(keywords));
  const responseText = (response || '').toLowerCase();
  return uniqueKeywords.some(kw => responseText.includes(kw)) ? 1 : 0;
}

function scoreHelpfulness(response) {
  // Placeholder: always return 1 (can be replaced with human eval or LLM)
  return 1;
}

function scoreCitationQuality(response, matches, contextChunks) {
  // Score 1 if the response references a keyword from the top context chunk
  if (!matches || matches.length === 0) return 0;
  const topContext = contextChunks[0] || '';
  const keywords = topContext.toLowerCase().split(/\W+/).filter(w => w.length > 4);
  const responseText = (response || '').toLowerCase();
  return keywords.some(kw => responseText.includes(kw)) ? 1 : 0;
}

// 3. Main evaluation loop
async function evaluateRAG() {
  const results = [];
  for (let i = 0; i < evaluationSet.length; i++) {
    const question = evaluationSet[i];
    console.log(`\n[${i+1}/${evaluationSet.length}] Q: ${question}`);
    try {
      const res = await fetch('http://localhost:3001/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: question })
      });
      const data = await res.json();
      const { response, context, matches } = data;
      const accuracy = scoreAccuracy(response, context);
      const helpfulness = scoreHelpfulness(response);
      const citation = scoreCitationQuality(response, matches, context);
      results.push({ question, response, accuracy, helpfulness, citation });
      console.log('AI:', response);
      console.log('Accuracy:', accuracy, 'Helpfulness:', helpfulness, 'Citation:', citation);
    } catch (err) {
      console.error('Error:', err);
      results.push({ question, response: '', accuracy: 0, helpfulness: 0, citation: 0 });
    }
  }
  // Write results to file
  fs.writeFileSync('rag_eval_results.json', JSON.stringify(results, null, 2));
  console.log('\nEvaluation complete. Results saved to rag_eval_results.json');
}

if (require.main === module) {
  evaluateRAG();
} 