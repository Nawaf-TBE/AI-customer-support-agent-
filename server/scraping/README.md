# Aven Data Scraping Module

A robust module for scraping Aven-related information using the Exa.ai API with comprehensive error handling and retry logic.

## Features

- 🔍 **Intelligent Search**: Automatically enhances queries to focus on Aven-related content
- 🛡️ **Robust Error Handling**: Custom error types with detailed error codes and retry logic
- ⚡ **Performance Optimized**: Configurable timeouts, retry strategies, and response caching
- 📊 **Rich Metadata**: Detailed statistics and validation for scraped data
- 🎯 **Domain Targeting**: Focuses on official Aven domains for accurate results

## Installation

The module is part of the server package and uses the existing dependencies:

```bash
# Already installed in server package
npm install exa-js dotenv
```

## Usage

### Basic Usage

```javascript
const { scrapeAvenData } = require('./scraping');

// Simple search
const result = await scrapeAvenData('payment issues');
console.log(result.results); // Array of scraped results
```

### Advanced Usage

```javascript
const { scrapeAvenData, validateScrapedData } = require('./scraping');

// Advanced search with custom options
const result = await scrapeAvenData('account setup help', {
  numResults: 15,                    // Get more results
  maxCharacters: 5000,              // Longer content
  includeDomains: [                 // Custom domains
    'aven.com', 
    'help.aven.com',
    'support.aven.com'
  ],
  timeout: 20000,                   // 20 second timeout
  retries: 5                        // More retry attempts
});

// Validate data quality
const validation = validateScrapedData(result);
if (validation.warnings.length > 0) {
  console.log('Data quality issues:', validation.warnings);
}
```

## API Reference

### `scrapeAvenData(query, options)`

Main function to scrape Aven-related data.

**Parameters:**
- `query` (string): Search query related to Aven
- `options` (object, optional): Configuration options

**Options:**
```javascript
{
  numResults: 10,                     // Number of results to retrieve
  includeDomains: [                   // Domains to focus on
    'aven.com', 
    'help.aven.com', 
    'support.aven.com'
  ],
  type: 'auto',                       // Search type ('auto', 'neural', 'keyword')
  maxCharacters: 3000,                // Max characters per result
  timeout: 30000,                     // Request timeout in ms
  retries: 3                          // Number of retry attempts
}
```

**Returns:**
```javascript
{
  success: true,
  query: {
    original: "payment issues",
    enhanced: "Aven payment issues",
    timestamp: "2024-01-01T12:00:00.000Z"
  },
  results: [
    {
      id: "aven_result_1",
      title: "Aven Payment Troubleshooting",
      url: "https://help.aven.com/payments",
      text: "Content about payment issues...",
      score: 0.95,
      publishedDate: "2023-12-01",
      author: "Aven Support",
      extractedAt: "2024-01-01T12:00:00.000Z"
    }
    // ... more results
  ],
  metadata: {
    totalResults: 10,
    maxResults: 10,
    domains: ["aven.com", "help.aven.com"],
    responseTime: "1250ms",
    attempt: 1,
    apiProvider: "Exa.ai"
  },
  statistics: {
    averageScore: 0.87,
    totalCharacters: 25000,
    urlsFound: 10
  }
}
```

### `validateScrapedData(data)`

Validates the quality of scraped data.

**Parameters:**
- `data` (object): Result object from `scrapeAvenData`

**Returns:**
```javascript
{
  isValid: true,
  warnings: ["Low relevance scores detected"],
  suggestions: ["Consider refining your search query"]
}
```

### `buildAvenQuery(query)`

Enhances queries to focus on Aven-related content.

**Parameters:**
- `query` (string): Original search query

**Returns:**
- `string`: Enhanced query with Aven context

### Error Handling

The module uses custom `ScrapingError` class with specific error codes:

```javascript
try {
  const result = await scrapeAvenData('invalid query');
} catch (error) {
  if (error instanceof ScrapingError) {
    console.log('Error code:', error.code);
    console.log('Message:', error.message);
    console.log('Details:', error.details);
  }
}
```

**Error Codes:**
- `MISSING_API_KEY`: EXA_API_KEY not configured
- `INVALID_QUERY`: Query parameter is invalid
- `CLIENT_INIT_ERROR`: Failed to initialize Exa client
- `TIMEOUT_ERROR`: Request exceeded timeout
- `UNAUTHORIZED`: Invalid API key
- `API_ERROR`: General API error
- `INVALID_RESPONSE`: Malformed API response
- `MAX_RETRIES_EXCEEDED`: All retry attempts failed

## Testing

Run the comprehensive test suite:

```bash
cd server/scraping
node test-scraping.js
```

The test suite includes:
- ✅ Query enhancement testing
- ✅ Error handling validation
- ✅ Performance benchmarking
- ✅ Real API functionality testing
- ✅ Data validation testing

## Configuration

Set up your environment variables in `server/.env`:

```bash
EXA_API_KEY=your_exa_api_key_here
```

## Best Practices

1. **Query Optimization**: Use specific, relevant queries for better results
2. **Rate Limiting**: Be mindful of API rate limits in production
3. **Error Handling**: Always wrap calls in try-catch blocks
4. **Data Validation**: Use `validateScrapedData()` to check result quality
5. **Caching**: Consider implementing caching for frequently accessed data

## Examples

### Customer Support Use Case

```javascript
// Search for common support topics
const topics = [
  'login problems',
  'password reset',
  'account verification',
  'payment failed',
  'subscription cancellation'
];

const supportData = await Promise.all(
  topics.map(topic => scrapeAvenData(topic, { numResults: 5 }))
);

// Build knowledge base from results
const knowledgeBase = supportData.flatMap(data => data.results);
```

### Content Analysis

```javascript
// Analyze content quality
const result = await scrapeAvenData('feature documentation');
const validation = validateScrapedData(result);

if (validation.warnings.includes('Low relevance scores detected')) {
  console.log('Try more specific search terms');
}

// Get content statistics
console.log(`Average relevance: ${result.statistics.averageScore}`);
console.log(`Total content: ${result.statistics.totalCharacters} characters`);
```

## License

Part of the AI Customer Support Agent project. 