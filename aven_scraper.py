"""
Main Aven Support Scraper using Exa.ai API
"""
import json
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Set, Optional
from urllib.parse import urlparse

import pandas as pd
from exa_py import Exa
from tenacity import retry, stop_after_attempt, wait_exponential
from tqdm import tqdm

from config import config, get_output_paths, validate_config
from content_processor import ContentProcessor, TextChunk

# Constants
class ScrapingConstants:
    """Constants used throughout the scraping process"""
    RETRY_ATTEMPTS = 3
    RETRY_MIN_WAIT = 4
    RETRY_MAX_WAIT = 10
    RETRY_MULTIPLIER = 1
    
    SEARCH_DELAY_SECONDS = 1
    MAX_RESULTS_PER_QUERY = 10
    
    EXCLUDED_EXTENSIONS = ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.css', '.js']
    
    # Search query templates
    SEARCH_QUERIES = [
        "Aven credit card support documentation help center",
        "Aven frequently asked questions FAQ troubleshooting", 
        "Aven user guide getting started tutorial",
        "Aven customer support help articles",
        "Aven app setup installation guide",
        "Aven account management billing support",
        "This is the comprehensive support documentation for Aven:",
        "Here are helpful Aven support articles for users:",
        "Aven customer service FAQ and troubleshooting guides:",
    ]

# Custom Exceptions
class ScrapingError(Exception):
    """Base exception for scraping errors"""
    pass

class ConfigurationError(ScrapingError):
    """Raised when configuration is invalid"""
    pass

class APIError(ScrapingError):
    """Raised when API requests fail"""
    pass

class ContentProcessingError(ScrapingError):
    """Raised when content processing fails"""
    pass

# Data Classes
@dataclass
class SessionStats:
    """Statistics for a scraping session"""
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    urls_discovered: int = 0
    urls_scraped: int = 0
    urls_failed: int = 0
    total_chunks: int = 0
    total_words: int = 0
    content_types: Dict[str, int] = field(default_factory=dict)
    
    @property
    def duration_minutes(self) -> float:
        """Calculate session duration in minutes"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds() / 60
        return 0.0

@dataclass
class ScrapingResult:
    """Result of a scraping operation"""
    success: bool
    session_stats: SessionStats
    scraped_urls: List[str] = field(default_factory=list)
    failed_urls: List[str] = field(default_factory=list)
    discovered_urls: List[str] = field(default_factory=list)
    processed_pages: List[Dict[str, Any]] = field(default_factory=list)
    chunks: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None
    
    @property
    def total_chunks(self) -> int:
        """Total number of chunks processed"""
        return len(self.chunks)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'success': self.success,
            'session_stats': {
                'start_time': self.session_stats.start_time,
                'end_time': self.session_stats.end_time,
                'urls_discovered': self.session_stats.urls_discovered,
                'urls_scraped': self.session_stats.urls_scraped,
                'urls_failed': self.session_stats.urls_failed,
                'total_chunks': self.session_stats.total_chunks,
                'total_words': self.session_stats.total_words,
                'content_types': self.session_stats.content_types,
                'duration_minutes': self.session_stats.duration_minutes
            },
            'scraped_urls': self.scraped_urls,
            'failed_urls': self.failed_urls,
            'discovered_urls': self.discovered_urls,
            'processed_pages': self.processed_pages,
            'total_chunks': self.total_chunks,
            'chunks': self.chunks,
            'error': self.error
        }

# Setup logging
def setup_logging():
    """Setup logging configuration"""
    log_level = getattr(logging, config.log_level.upper())
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(get_output_paths()['logs']),
            logging.StreamHandler()
        ]
    )

logger = logging.getLogger(__name__)

class AvenScraper:
    """Main scraper class for Aven support pages using Exa.ai
    
    This class handles the complete scraping workflow:
    - Discovering support pages using Exa.ai neural search
    - Scraping content from discovered pages
    - Processing and chunking content
    - Saving results in multiple formats
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the scraper with configuration and dependencies
        
        Args:
            api_key: Optional Exa.ai API key (overrides config)
            
        Raises:
            ConfigurationError: If configuration is invalid
            APIError: If API initialization fails
        """
        try:
            validate_config()
        except ValueError as e:
            raise ConfigurationError(f"Invalid configuration: {e}")
            
        self.api_key = api_key or config.exa_api_key
        if not self.api_key:
            raise ConfigurationError("Exa.ai API key is required")
            
        try:
            self.exa = Exa(self.api_key)
        except Exception as e:
            raise APIError(f"Failed to initialize Exa.ai client: {e}")
            
        self.content_processor = ContentProcessor(
            chunk_size=config.chunk_size,
            overlap_size=config.overlap_size,
            min_chunk_size=config.min_chunk_size
        )
        
        # Tracking
        self.scraped_urls: Set[str] = set()
        self.failed_urls: Set[str] = set()
        self.all_results: List[Dict[str, Any]] = []
        self.all_chunks: List[TextChunk] = []
        self.session_stats = SessionStats()
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 60.0 / config.requests_per_minute
        
    @retry(
        stop=stop_after_attempt(ScrapingConstants.RETRY_ATTEMPTS), 
        wait=wait_exponential(
            multiplier=ScrapingConstants.RETRY_MULTIPLIER, 
            min=ScrapingConstants.RETRY_MIN_WAIT, 
            max=ScrapingConstants.RETRY_MAX_WAIT
        )
    )
    def _rate_limited_request(self, func, *args, **kwargs):
        """Execute Exa API request with rate limiting and retry logic
        
        Args:
            func: The API function to call
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            The result of the API call
            
        Raises:
            APIError: If the API request fails after retries
        """
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
            time.sleep(sleep_time)
        
        try:
            result = func(*args, **kwargs)
            self.last_request_time = time.time()
            return result
        except Exception as e:
            logger.error(f"API request failed: {e}")
            raise APIError(f"API request failed: {e}") from e
    
    def discover_support_pages(self) -> List[str]:
        """Use Exa.ai to discover support pages intelligently
        
        Returns:
            List of discovered support page URLs
            
        Raises:
            APIError: If discovery fails due to API issues
        """
        logger.info("Discovering Aven support pages using Exa.ai neural search...")
        
        discovered_urls = set()
        search_queries = self._get_search_queries()
        
        for query in tqdm(search_queries, desc="Discovering pages"):
            try:
                urls = self._search_with_query(query)
                discovered_urls.update(urls)
                time.sleep(ScrapingConstants.SEARCH_DELAY_SECONDS)
                
            except Exception as e:
                logger.warning(f"Failed to search with query '{query}': {e}")
                continue
        
        discovered_list = list(discovered_urls)
        self.session_stats.urls_discovered = len(discovered_list)
        logger.info(f"Discovered {len(discovered_list)} unique support URLs")
        
        return discovered_list
    
    def _get_search_queries(self) -> List[str]:
        """Get the list of search queries for discovery
        
        Returns:
            List of search query strings
        """
        return [config.base_url] + ScrapingConstants.SEARCH_QUERIES
    
    def _search_with_query(self, query: str) -> Set[str]:
        """Execute a single search query and extract URLs
        
        Args:
            query: The search query string
            
        Returns:
            Set of discovered URLs
            
        Raises:
            APIError: If the search request fails
        """
        logger.debug(f"Searching with query: {query}")
        discovered_urls = set()
        
        try:
            if query == config.base_url:
                response = self._search_direct_url(query)
            else:
                response = self._search_neural_content(query)
                
            discovered_urls.update(self._extract_urls_from_response(response))
            
        except Exception as e:
            raise APIError(f"Search failed for query '{query}': {e}")
            
        return discovered_urls
    
    def _search_direct_url(self, url: str):
        """Search using direct URL crawling with subpages"""
        return self._rate_limited_request(
            self.exa.get_contents,
            [url],
            subpages=config.max_subpages,
            subpage_target=config.target_content,
            text=True,
            highlights={
                "num_sentences": config.num_sentences_per_highlight,
                "highlights_per_url": config.highlights_per_url
            }
        )
    
    def _search_neural_content(self, query: str):
        """Search using neural search for content discovery"""
        return self._rate_limited_request(
            self.exa.search_and_contents,
            query,
            type=config.search_type,
            use_autoprompt=config.use_autoprompt,
            num_results=min(ScrapingConstants.MAX_RESULTS_PER_QUERY, config.max_subpages // 5),
            include_domains=config.include_domains,
            text=True,
            highlights={
                "num_sentences": config.num_sentences_per_highlight,
                "highlights_per_url": config.highlights_per_url
            }
        )
    
    def _extract_urls_from_response(self, response) -> Set[str]:
        """Extract valid URLs from API response
        
        Args:
            response: The API response object
            
        Returns:
            Set of valid URLs
        """
        discovered_urls = set()
        
        if hasattr(response, 'results'):
            for result in response.results:
                url = result.url
                if self._is_valid_support_url(url):
                    discovered_urls.add(url)
                    logger.debug(f"Discovered: {url}")
                    
                    # Also check subpages if available
                    if hasattr(result, 'subpages') and result.subpages:
                        for subpage in result.subpages:
                            if self._is_valid_support_url(subpage.url):
                                discovered_urls.add(subpage.url)
                                logger.debug(f"Discovered subpage: {subpage.url}")
        
        return discovered_urls
    
    def _is_valid_support_url(self, url: str) -> bool:
        """Check if URL is a valid Aven support page
        
        Args:
            url: The URL to validate
            
        Returns:
            True if the URL is valid for scraping, False otherwise
        """
        if not url or url in self.scraped_urls:
            return False
        
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        path = parsed.path.lower()
        
        # Must be Aven domain
        if not any(allowed_domain in domain for allowed_domain in config.include_domains):
            return False
        
        # Must be support-related or whitelisted
        if 'support' not in path and not any(pattern in path for pattern in config.target_content):
            # Check if it's the main support page
            if url != config.base_url:
                return False
        
        # Exclude unwanted paths
        if any(pattern in path for pattern in config.exclude_patterns):
            return False
        
        # Exclude non-content URLs
        if any(path.endswith(ext) for ext in ScrapingConstants.EXCLUDED_EXTENSIONS):
            return False
        
        return True
    
    def scrape_page_content(self, url: str) -> Optional[Dict[str, Any]]:
        """Scrape content from a single page using Exa.ai
        
        Args:
            url: The URL to scrape
            
        Returns:
            Processed content dictionary or None if scraping failed
            
        Raises:
            APIError: If API request fails
            ContentProcessingError: If content processing fails
        """
        if url in self.scraped_urls:
            logger.debug(f"Already scraped: {url}")
            return None
        
        try:
            logger.debug(f"Scraping content from: {url}")
            
            # Get page content using Exa.ai
            response = self._get_page_content(url)
            
            if not response.results:
                logger.warning(f"No content retrieved for {url}")
                self._track_failed_url(url)
                return None
            
            result = response.results[0]
            
            # Process the content
            processed = self._process_scraped_content(result, url)
            
            # Track successful scraping
            self._track_successful_scraping(url, processed)
            
            logger.info(f"Successfully scraped {url} ({processed['total_chunks']} chunks, "
                       f"{processed['total_words']} words, type: {processed['metadata']['content_type']})")
            
            return processed
            
        except ContentProcessingError as e:
            logger.error(f"Content processing failed for {url}: {e}")
            self._track_failed_url(url)
            return None
        except APIError as e:
            logger.error(f"API error while scraping {url}: {e}")
            self._track_failed_url(url)
            return None
        except Exception as e:
            logger.error(f"Unexpected error scraping {url}: {e}")
            self._track_failed_url(url)
            return None
    
    def _get_page_content(self, url: str):
        """Get page content from Exa.ai API
        
        Args:
            url: The URL to fetch content from
            
        Returns:
            API response object
        """
        return self._rate_limited_request(
            self.exa.get_contents,
            [url],
            text=True,
            highlights={
                "num_sentences": config.num_sentences_per_highlight,
                "highlights_per_url": config.highlights_per_url
            }
        )
    
    def _process_scraped_content(self, result, url: str) -> Dict[str, Any]:
        """Process scraped content and enhance with metadata
        
        Args:
            result: The API result object
            url: The source URL
            
        Returns:
            Processed content dictionary
            
        Raises:
            ContentProcessingError: If processing fails
        """
        # Process the content
        processed = self.content_processor.process_content(result.text or "", url)
        
        if not processed['success']:
            raise ContentProcessingError(f"Failed to process content: {processed.get('error')}")
        
        # Enhance with Exa.ai metadata
        processed['metadata'].update({
            'exa_score': getattr(result, 'score', 0),
            'published_date': getattr(result, 'published_date', None),
            'author': getattr(result, 'author', None),
            'highlights': getattr(result, 'highlights', []),
            'highlight_scores': getattr(result, 'highlight_scores', []),
            'scraped_at': datetime.now().isoformat()
        })
        
        return processed
    
    def _track_successful_scraping(self, url: str, processed: Dict[str, Any]) -> None:
        """Track successful scraping statistics
        
        Args:
            url: The scraped URL
            processed: The processed content data
        """
        content_type = processed['metadata']['content_type']
        
        # Update content type tracking
        if content_type in self.session_stats.content_types:
            self.session_stats.content_types[content_type] += 1
        else:
            self.session_stats.content_types[content_type] = 1
        
        # Update tracking sets and stats
        self.scraped_urls.add(url)
        self.session_stats.urls_scraped += 1
        self.session_stats.total_words += processed['total_words']
    
    def _track_failed_url(self, url: str) -> None:
        """Track failed URL scraping
        
        Args:
            url: The URL that failed to scrape
        """
        self.failed_urls.add(url)
        self.session_stats.urls_failed += 1
    
    def scrape_support_pages(self) -> ScrapingResult:
        """Main method to scrape all Aven support pages
        
        Returns:
            ScrapingResult object containing all scraping results and statistics
            
        Raises:
            ConfigurationError: If configuration is invalid
            ScrapingError: If scraping process fails
        """
        logger.info("Starting Aven support page scraping...")
        setup_logging()
        
        try:
            # Create output directories
            output_paths = get_output_paths()
            
            # Discover support pages
            discovered_urls = self.discover_support_pages()
            
            if not discovered_urls:
                logger.warning("No support pages discovered")
                return ScrapingResult(
                    success=False,
                    session_stats=self.session_stats,
                    error="No pages discovered"
                )
            
            # Scrape pages
            self._scrape_discovered_pages(discovered_urls)
            
            # Finalize session
            self.session_stats.end_time = datetime.now()
            
            # Create final results
            result = self._create_scraping_result(discovered_urls)
            
            # Save results
            self._save_results(result.to_dict(), output_paths)
            
            self._log_completion_stats()
            
            return result
            
        except (ConfigurationError, APIError, ContentProcessingError) as e:
            logger.error(f"Scraping failed: {e}")
            return ScrapingResult(
                success=False,
                session_stats=self.session_stats,
                error=str(e)
            )
        except Exception as e:
            logger.error(f"Unexpected error during scraping: {e}")
            return ScrapingResult(
                success=False,
                session_stats=self.session_stats,
                error=f"Unexpected error: {str(e)}"
            )
    
    def _scrape_discovered_pages(self, discovered_urls: List[str]) -> None:
        """Scrape all discovered pages
        
        Args:
            discovered_urls: List of URLs to scrape
        """
        # Limit URLs based on configuration
        urls_to_scrape = discovered_urls[:config.max_subpages]
        logger.info(f"Scraping {len(urls_to_scrape)} pages...")
        
        # Scrape each page
        for url in tqdm(urls_to_scrape, desc="Scraping pages"):
            result = self.scrape_page_content(url)
            if result:
                self.all_results.append(result)
                self.all_chunks.extend(result['chunks'])
                self.session_stats.total_chunks += result['total_chunks']
    
    def _create_scraping_result(self, discovered_urls: List[str]) -> ScrapingResult:
        """Create the final scraping result object
        
        Args:
            discovered_urls: List of all discovered URLs
            
        Returns:
            ScrapingResult object with all data
        """
        return ScrapingResult(
            success=True,
            session_stats=self.session_stats,
            scraped_urls=list(self.scraped_urls),
            failed_urls=list(self.failed_urls),
            discovered_urls=discovered_urls,
            processed_pages=self.all_results,
            chunks=[self._chunk_to_dict(chunk) for chunk in self.all_chunks]
        )
    
    def _log_completion_stats(self) -> None:
        """Log completion statistics"""
        logger.info("Scraping completed successfully!")
        logger.info(f"- Pages scraped: {self.session_stats.urls_scraped}")
        logger.info(f"- Total chunks: {len(self.all_chunks)}")
        logger.info(f"- Total words: {self.session_stats.total_words}")
        logger.info(f"- Duration: {self.session_stats.duration_minutes:.1f} minutes")
    
    def _chunk_to_dict(self, chunk: TextChunk) -> Dict[str, Any]:
        """Convert TextChunk to dictionary for serialization"""
        return {
            'content': chunk.content,
            'chunk_id': chunk.chunk_id,
            'source_url': chunk.source_url,
            'title': chunk.title,
            'chunk_index': chunk.chunk_index,
            'total_chunks': chunk.total_chunks,
            'word_count': chunk.word_count,
            'char_count': chunk.char_count,
            'section_title': chunk.section_title,
            'content_type': chunk.content_type,
            'keywords': chunk.keywords
        }
    
    def _save_results(self, results: Dict[str, Any], output_paths: Dict[str, str]):
        """Save scraping results in multiple formats"""
        logger.info("Saving results...")
        
        # Save raw JSON data
        with open(output_paths['raw_data'], 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        # Save processed chunks
        chunks_data = {
            'chunks': results['chunks'],
            'metadata': {
                'total_chunks': len(results['chunks']),
                'scraped_urls': results['scraped_urls'],
                'session_stats': results['session_stats']
            }
        }
        with open(output_paths['processed_data'], 'w', encoding='utf-8') as f:
            json.dump(chunks_data, f, indent=2, ensure_ascii=False, default=str)
        
        # Save summary CSV
        summary_data = []
        for page in results['processed_pages']:
            if page['success']:
                summary_data.append({
                    'url': page['metadata']['url'],
                    'title': page['metadata']['title'],
                    'content_type': page['metadata']['content_type'],
                    'word_count': page['total_words'],
                    'chunk_count': page['total_chunks'],
                    'scraped_at': page['metadata']['scraped_at']
                })
        
        pd.DataFrame(summary_data).to_csv(output_paths['summary_csv'], index=False)
        
        # Save individual chunk files
        for i, chunk in enumerate(results['chunks'], 1):
            chunk_file = os.path.join(output_paths['chunks_dir'], f"chunk_{i:04d}.md")
            with open(chunk_file, 'w', encoding='utf-8') as f:
                f.write(f"# {chunk['title']}\n\n")
                f.write(f"**Source:** {chunk['source_url']}\n")
                f.write(f"**Type:** {chunk['content_type']}\n")
                if chunk['section_title']:
                    f.write(f"**Section:** {chunk['section_title']}\n")
                f.write(f"**Chunk:** {chunk['chunk_index']}/{chunk['total_chunks']}\n\n")
                f.write("---\n\n")
                f.write(chunk['content'])
        
        # Save metadata
        metadata = {
            'scraping_config': {
                'base_url': config.base_url,
                'max_subpages': config.max_subpages,
                'chunk_size': config.chunk_size,
                'target_content': config.target_content
            },
            'session_stats': results['session_stats'],
            'output_files': output_paths
        }
        with open(output_paths['metadata'], 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, default=str)
        
        logger.info(f"Results saved to {config.output_dir}/")

def main():
    """Main CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Scrape Aven support pages using Exa.ai")
    parser.add_argument("--api-key", help="Exa.ai API key (overrides config)")
    parser.add_argument("--max-pages", type=int, help="Maximum pages to scrape")
    parser.add_argument("--output-dir", help="Output directory")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    # Override config if provided
    if args.max_pages:
        config.max_subpages = args.max_pages
    if args.output_dir:
        config.output_dir = args.output_dir
    if args.verbose:
        config.log_level = "DEBUG"
    
    # Run scraper
    try:
        scraper = AvenScraper(api_key=args.api_key)
        results = scraper.scrape_support_pages()
        
        if results.success:
            print(f"\n✅ Scraping completed successfully!")
            print(f"📊 Results: {results.session_stats.urls_scraped} pages, "
                  f"{results.total_chunks} chunks")
            print(f"📁 Output saved to: {config.output_dir}/")
        else:
            print(f"\n❌ Scraping failed: {results.error or 'Unknown error'}")
            exit(1)
            
    except (ConfigurationError, APIError, ContentProcessingError) as e:
        print(f"\n❌ Scraping failed: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        exit(1)

if __name__ == "__main__":
    main() 