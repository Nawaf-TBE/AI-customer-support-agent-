"""
Main Aven Support Scraper using Exa.ai API
"""
import asyncio
import json
import logging
import time
from datetime import datetime
from typing import List, Dict, Any, Set, Optional
from urllib.parse import urlparse, urljoin
import pandas as pd
from tqdm import tqdm
import os

from exa_py import Exa
from tenacity import retry, stop_after_attempt, wait_exponential

from config import config, get_output_paths, validate_config
from content_processor import ContentProcessor, TextChunk

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
    """Main scraper class for Aven support pages using Exa.ai"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the scraper"""
        self.api_key = api_key or config.exa_api_key
        self.exa = Exa(self.api_key)
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
        self.session_stats = {
            'start_time': datetime.now(),
            'urls_discovered': 0,
            'urls_scraped': 0,
            'urls_failed': 0,
            'total_chunks': 0,
            'total_words': 0,
            'content_types': {}
        }
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 60.0 / config.requests_per_minute
        
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def _rate_limited_request(self, func, *args, **kwargs):
        """Execute Exa API request with rate limiting and retry logic"""
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
            raise
    
    def discover_support_pages(self) -> List[str]:
        """Use Exa.ai to discover support pages intelligently"""
        logger.info("Discovering Aven support pages using Exa.ai neural search...")
        
        discovered_urls = set()
        
        # Multiple search strategies to comprehensively discover content
        search_queries = [
            # Direct URL-based discovery
            config.base_url,
            
            # Content-based discovery
            "Aven credit card support documentation help center",
            "Aven frequently asked questions FAQ troubleshooting",
            "Aven user guide getting started tutorial",
            "Aven customer support help articles",
            "Aven app setup installation guide",
            "Aven account management billing support",
            
            # Neural search prompts
            "This is the comprehensive support documentation for Aven:",
            "Here are helpful Aven support articles for users:",
            "Aven customer service FAQ and troubleshooting guides:",
        ]
        
        for query in tqdm(search_queries, desc="Discovering pages"):
            try:
                logger.debug(f"Searching with query: {query}")
                
                # Use Exa's subpage crawling for comprehensive discovery
                if query == config.base_url:
                    # Direct URL crawling with subpages
                    response = self._rate_limited_request(
                        self.exa.get_contents,
                        [query],
                        subpages=config.max_subpages,
                        subpage_target=config.target_content,
                        text=True,
                        highlights={
                            "num_sentences": config.num_sentences_per_highlight,
                            "highlights_per_url": config.highlights_per_url
                        }
                    )
                else:
                    # Neural search for content discovery
                    response = self._rate_limited_request(
                        self.exa.search_and_contents,
                        query,
                        type=config.search_type,
                        use_autoprompt=config.use_autoprompt,
                        num_results=min(10, config.max_subpages // 5),
                        include_domains=config.include_domains,
                        text=True,
                        highlights={
                            "num_sentences": config.num_sentences_per_highlight,
                            "highlights_per_url": config.highlights_per_url
                        }
                    )
                
                # Extract URLs from response
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
                
                # Small delay between searches
                time.sleep(1)
                
            except Exception as e:
                logger.warning(f"Failed to search with query '{query}': {e}")
                continue
        
        discovered_list = list(discovered_urls)
        self.session_stats['urls_discovered'] = len(discovered_list)
        logger.info(f"Discovered {len(discovered_list)} unique support URLs")
        
        return discovered_list
    
    def _is_valid_support_url(self, url: str) -> bool:
        """Check if URL is a valid Aven support page"""
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
        excluded_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.css', '.js']
        if any(path.endswith(ext) for ext in excluded_extensions):
            return False
        
        return True
    
    def scrape_page_content(self, url: str) -> Optional[Dict[str, Any]]:
        """Scrape content from a single page using Exa.ai"""
        if url in self.scraped_urls:
            logger.debug(f"Already scraped: {url}")
            return None
        
        try:
            logger.debug(f"Scraping content from: {url}")
            
            # Get page content using Exa.ai
            response = self._rate_limited_request(
                self.exa.get_contents,
                [url],
                text=True,
                highlights={
                    "num_sentences": config.num_sentences_per_highlight,
                    "highlights_per_url": config.highlights_per_url
                }
            )
            
            if not response.results:
                logger.warning(f"No content retrieved for {url}")
                return None
            
            result = response.results[0]
            
            # Process the content
            processed = self.content_processor.process_content(result.text or "", url)
            
            if not processed['success']:
                logger.error(f"Failed to process content from {url}: {processed.get('error')}")
                return None
            
            # Enhance with Exa.ai metadata
            processed['metadata'].update({
                'exa_score': getattr(result, 'score', 0),
                'published_date': getattr(result, 'published_date', None),
                'author': getattr(result, 'author', None),
                'highlights': getattr(result, 'highlights', []),
                'highlight_scores': getattr(result, 'highlight_scores', []),
                'scraped_at': datetime.now().isoformat()
            })
            
            # Track content type
            content_type = processed['metadata']['content_type']
            self.session_stats['content_types'][content_type] = \
                self.session_stats['content_types'].get(content_type, 0) + 1
            
            self.scraped_urls.add(url)
            self.session_stats['urls_scraped'] += 1
            self.session_stats['total_words'] += processed['total_words']
            
            logger.info(f"Successfully scraped {url} ({processed['total_chunks']} chunks, "
                       f"{processed['total_words']} words, type: {content_type})")
            
            return processed
            
        except Exception as e:
            logger.error(f"Failed to scrape {url}: {e}")
            self.failed_urls.add(url)
            self.session_stats['urls_failed'] += 1
            return None
    
    def scrape_support_pages(self) -> Dict[str, Any]:
        """Main method to scrape all Aven support pages"""
        logger.info("Starting Aven support page scraping...")
        setup_logging()
        
        try:
            validate_config()
        except ValueError as e:
            logger.error(f"Configuration error: {e}")
            return {'success': False, 'error': str(e)}
        
        # Create output directories
        output_paths = get_output_paths()
        
        try:
            # Discover support pages
            discovered_urls = self.discover_support_pages()
            
            if not discovered_urls:
                logger.warning("No support pages discovered")
                return {'success': False, 'error': 'No pages discovered'}
            
            # Limit URLs based on configuration
            urls_to_scrape = discovered_urls[:config.max_subpages]
            logger.info(f"Scraping {len(urls_to_scrape)} pages...")
            
            # Scrape each page
            for url in tqdm(urls_to_scrape, desc="Scraping pages"):
                result = self.scrape_page_content(url)
                if result:
                    self.all_results.append(result)
                    self.all_chunks.extend(result['chunks'])
                    self.session_stats['total_chunks'] += result['total_chunks']
            
            # Compile final results
            session_end = datetime.now()
            self.session_stats['end_time'] = session_end
            self.session_stats['duration_minutes'] = \
                (session_end - self.session_stats['start_time']).total_seconds() / 60
            
            final_results = {
                'success': True,
                'session_stats': self.session_stats,
                'scraped_urls': list(self.scraped_urls),
                'failed_urls': list(self.failed_urls),
                'discovered_urls': discovered_urls,
                'processed_pages': self.all_results,
                'total_chunks': len(self.all_chunks),
                'chunks': [self._chunk_to_dict(chunk) for chunk in self.all_chunks]
            }
            
            # Save results
            self._save_results(final_results, output_paths)
            
            logger.info(f"Scraping completed successfully!")
            logger.info(f"- Pages scraped: {self.session_stats['urls_scraped']}")
            logger.info(f"- Total chunks: {len(self.all_chunks)}")
            logger.info(f"- Total words: {self.session_stats['total_words']}")
            logger.info(f"- Duration: {self.session_stats['duration_minutes']:.1f} minutes")
            
            return final_results
            
        except Exception as e:
            logger.error(f"Scraping failed: {e}")
            return {'success': False, 'error': str(e)}
    
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
    scraper = AvenScraper(api_key=args.api_key)
    results = scraper.scrape_support_pages()
    
    if results['success']:
        print(f"\n✅ Scraping completed successfully!")
        print(f"📊 Results: {results['session_stats']['urls_scraped']} pages, "
              f"{results['total_chunks']} chunks")
        print(f"📁 Output saved to: {config.output_dir}/")
    else:
        print(f"\n❌ Scraping failed: {results.get('error', 'Unknown error')}")
        exit(1)

if __name__ == "__main__":
    main() 