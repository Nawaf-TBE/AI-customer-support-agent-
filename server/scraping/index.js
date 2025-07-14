require('dotenv').config();
const Exa = require('exa-js').default;

/**
 * Custom error class for scraping operations
 */
class ScrapingError extends Error {
  constructor(message, code, details = null) {
    super(message);
    this.name = 'ScrapingError';
    this.code = code;
    this.details = details;
  }
}

/**
 * Initialize Exa client with error handling
 */
function initializeExaClient() {
  const apiKey = process.env.EXA_API_KEY;
  
  if (!apiKey) {
    throw new ScrapingError(
      'EXA_API_KEY is not configured',
      'MISSING_API_KEY'
    );
  }
  
  try {
    return new Exa(apiKey);
  } catch (error) {
    throw new ScrapingError(
      'Failed to initialize Exa client',
      'CLIENT_INIT_ERROR',
      error.message
    );
  }
}

/**
 * Build Aven-specific search query
 * @param {string} query - User provided query
 * @returns {string} Enhanced query for Aven-specific search
 */
function buildAvenQuery(query) {
  // Enhance the query to focus on Aven-related content
  const avenKeywords = ['Aven', 'aven.com', 'Aven support', 'Aven platform'];
  
  // If query already contains Aven, use as-is, otherwise enhance it
  const hasAvenContext = avenKeywords.some(keyword => 
    query.toLowerCase().includes(keyword.toLowerCase())
  );
  
  if (hasAvenContext) {
    return query;
  }
  
  return `Aven ${query}`;
}

/**
 * Scrape Aven-related data using Exa.ai API
 * @param {string} query - Search query related to Aven
 * @param {Object} options - Optional configuration
 * @returns {Promise<Object>} Scraped data with metadata
 */
async function scrapeAvenData(query, options = {}) {
  const startTime = Date.now();
  
  // Default options
  const config = {
    numResults: 10,
    includeDomains: ['aven.com', 'help.aven.com', 'support.aven.com'],
    type: 'auto',
    includeText: true,
    maxCharacters: 3000,
    timeout: 30000, // 30 seconds timeout
    retries: 3,
    ...options
  };
  
  // Validate input
  if (!query || typeof query !== 'string' || query.trim().length === 0) {
    throw new ScrapingError(
      'Query parameter is required and must be a non-empty string',
      'INVALID_QUERY'
    );
  }
  
  const enhancedQuery = buildAvenQuery(query.trim());
  let exa;
  
  try {
    exa = initializeExaClient();
  } catch (error) {
    throw error; // Re-throw initialization errors
  }
  
  let lastError;
  
  // Retry logic
  for (let attempt = 1; attempt <= config.retries; attempt++) {
    try {
      console.log(`[Scraping] Attempt ${attempt}/${config.retries} - Query: "${enhancedQuery}"`);
      
      // Create a timeout promise
      const timeoutPromise = new Promise((_, reject) => {
        setTimeout(() => {
          reject(new ScrapingError(
            `Request timeout after ${config.timeout}ms`,
            'TIMEOUT_ERROR'
          ));
        }, config.timeout);
      });
      
      // Make the API call with timeout
      const searchPromise = exa.searchAndContents(enhancedQuery, {
        numResults: config.numResults,
        includeDomains: config.includeDomains,
        type: config.type,
        text: {
          maxCharacters: config.maxCharacters,
          includeHtmlTags: false
        }
      });
      
      const result = await Promise.race([searchPromise, timeoutPromise]);
      
      if (!result || !result.results) {
        throw new ScrapingError(
          'Invalid response format from Exa API',
          'INVALID_RESPONSE'
        );
      }
      
      // Process and validate results
      const processedResults = result.results.map((item, index) => {
        return {
          id: `aven_result_${index + 1}`,
          title: item.title || 'No title available',
          url: item.url || '',
          text: item.text || 'No content available',
          score: item.score || 0,
          publishedDate: item.publishedDate || null,
          author: item.author || null,
          extractedAt: new Date().toISOString()
        };
      });
      
      const endTime = Date.now();
      const responseTime = endTime - startTime;
      
      // Return structured response
      return {
        success: true,
        query: {
          original: query,
          enhanced: enhancedQuery,
          timestamp: new Date().toISOString()
        },
        results: processedResults,
        metadata: {
          totalResults: processedResults.length,
          maxResults: config.numResults,
          domains: config.includeDomains,
          responseTime: `${responseTime}ms`,
          attempt: attempt,
          apiProvider: 'Exa.ai'
        },
        statistics: {
          averageScore: processedResults.length > 0 
            ? processedResults.reduce((sum, r) => sum + r.score, 0) / processedResults.length 
            : 0,
          totalCharacters: processedResults.reduce((sum, r) => sum + (r.text?.length || 0), 0),
          urlsFound: processedResults.filter(r => r.url).length
        }
      };
      
    } catch (error) {
      lastError = error;
      
      // Handle specific error types
      if (error instanceof ScrapingError) {
        // Don't retry on configuration errors
        if (['MISSING_API_KEY', 'INVALID_QUERY', 'CLIENT_INIT_ERROR'].includes(error.code)) {
          throw error;
        }
      }
      
      // Handle API-specific errors
      if (error.response) {
        const status = error.response.status;
        if (status === 401) {
          throw new ScrapingError(
            'Invalid API key or unauthorized access',
            'UNAUTHORIZED',
            `HTTP ${status}: ${error.response.statusText}`
          );
        } else if (status === 429) {
          console.log(`[Scraping] Rate limited (attempt ${attempt}), waiting before retry...`);
          await new Promise(resolve => setTimeout(resolve, 2000 * attempt)); // Exponential backoff
        } else if (status >= 500) {
          console.log(`[Scraping] Server error (attempt ${attempt}): HTTP ${status}`);
          await new Promise(resolve => setTimeout(resolve, 1000 * attempt));
        } else {
          throw new ScrapingError(
            'API request failed',
            'API_ERROR',
            `HTTP ${status}: ${error.response.statusText}`
          );
        }
      } else if (error.code === 'ENOTFOUND' || error.code === 'ECONNREFUSED') {
        console.log(`[Scraping] Network error (attempt ${attempt}), retrying...`);
        await new Promise(resolve => setTimeout(resolve, 1000 * attempt));
      } else {
        console.log(`[Scraping] Unexpected error (attempt ${attempt}):`, error.message);
        await new Promise(resolve => setTimeout(resolve, 500 * attempt));
      }
      
      // If this was the last attempt, throw the error
      if (attempt === config.retries) {
        throw new ScrapingError(
          `Failed to scrape data after ${config.retries} attempts`,
          'MAX_RETRIES_EXCEEDED',
          lastError?.message || 'Unknown error'
        );
      }
    }
  }
}

/**
 * Validate scraped data quality
 * @param {Object} data - Scraped data to validate
 * @returns {Object} Validation results
 */
function validateScrapedData(data) {
  const validation = {
    isValid: true,
    warnings: [],
    suggestions: []
  };
  
  if (!data.results || data.results.length === 0) {
    validation.warnings.push('No results found');
    validation.suggestions.push('Try a more general query or remove domain restrictions');
  }
  
  const emptyResults = data.results?.filter(r => !r.text || r.text.length < 50) || [];
  if (emptyResults.length > 0) {
    validation.warnings.push(`${emptyResults.length} results have minimal content`);
  }
  
  const averageScore = data.statistics?.averageScore || 0;
  if (averageScore < 0.5) {
    validation.warnings.push('Low relevance scores detected');
    validation.suggestions.push('Consider refining your search query');
  }
  
  return validation;
}

module.exports = {
  scrapeAvenData,
  validateScrapedData,
  ScrapingError,
  buildAvenQuery
}; 