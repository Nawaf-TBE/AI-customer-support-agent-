"""
Content processing module for converting HTML to clean text chunks

This module provides a modular architecture for processing HTML content:
- ContentProcessor: Main coordinator class
- MetadataExtractor: Extracts metadata from HTML
- HTMLCleaner: Cleans and converts HTML to text
- TextChunker: Splits content into manageable chunks
- ContentTypeDetector: Detects content type from HTML and URLs
"""
import logging
import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union
from urllib.parse import urljoin, urlparse

import html2text
from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)

# Constants
class ProcessingConstants:
    """Constants used throughout content processing"""
    # Default chunk settings
    DEFAULT_CHUNK_SIZE = 1000
    DEFAULT_OVERLAP_SIZE = 100
    DEFAULT_MIN_CHUNK_SIZE = 100
    
    # Text processing
    CHARS_PER_WORD_ESTIMATE = 5
    SECTION_TITLE_PREVIEW_LENGTH = 200
    MAX_HEADING_LEVELS = 6
    
    # HTML elements to remove
    UNWANTED_HTML_ELEMENTS = ['script', 'style', 'nav', 'footer', 'aside', 'header']
    
    # CSS class/ID patterns to remove
    UNWANTED_CSS_PATTERNS = [
        'nav', 'menu', 'sidebar', 'footer', 'header', 'advertisement',
        'social', 'share', 'cookie', 'popup', 'modal', 'breadcrumb'
    ]
    
    # Content type detection patterns
    CONTENT_TYPE_PATTERNS = {
        'faq': {
            'url_patterns': ['faq', 'frequently-asked'],
            'content_patterns': ['frequently asked questions', 'q:']
        },
        'guide': {
            'url_patterns': ['guide', 'tutorial', 'how-to'],
            'content_patterns': ['step 1', 'first step', 'getting started']
        },
        'troubleshooting': {
            'url_patterns': ['troubleshoot', 'problem', 'fix'],
            'content_patterns': ['error', 'troubleshoot', 'problem', 'issue']
        },
        'getting_started': {
            'url_patterns': ['getting-started', 'setup', 'install'],
            'content_patterns': []
        },
        'documentation': {
            'url_patterns': ['api', 'reference', 'documentation'],
            'content_patterns': []
        }
    }
    
    # Default language
    DEFAULT_LANGUAGE = 'en'
    
    # Domain patterns for internal links
    INTERNAL_DOMAINS = ['aven.com']

# Custom Exceptions
class ContentProcessingError(Exception):
    """Base exception for content processing errors"""
    pass

class HTMLParsingError(ContentProcessingError):
    """Raised when HTML parsing fails"""
    pass

class TextCleaningError(ContentProcessingError):
    """Raised when text cleaning fails"""
    pass

class ChunkingError(ContentProcessingError):
    """Raised when content chunking fails"""
    pass

class MetadataExtractionError(ContentProcessingError):
    """Raised when metadata extraction fails"""
    pass

@dataclass
class TextChunk:
    """Represents a processed text chunk with metadata
    
    Attributes:
        content: The actual text content of the chunk
        chunk_id: Unique identifier for this chunk
        source_url: URL where this content originated
        title: Title of the source document
        chunk_index: Index of this chunk (1-based)
        total_chunks: Total number of chunks in the document
        word_count: Number of words in this chunk
        char_count: Number of characters in this chunk
        section_title: Title of the section this chunk belongs to
        content_type: Type of content (faq, guide, etc.)
        keywords: List of keywords associated with this chunk
    """
    content: str
    chunk_id: str
    source_url: str
    title: str
    chunk_index: int
    total_chunks: int
    word_count: int
    char_count: int
    section_title: Optional[str] = None
    content_type: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate chunk data after initialization"""
        if not self.content.strip():
            raise ValueError("Chunk content cannot be empty")
        if self.chunk_index < 1:
            raise ValueError("Chunk index must be >= 1")
        if self.total_chunks < 1:
            raise ValueError("Total chunks must be >= 1")
        if self.chunk_index > self.total_chunks:
            raise ValueError("Chunk index cannot exceed total chunks")
        if self.word_count < 0 or self.char_count < 0:
            raise ValueError("Word count and char count must be non-negative")
    
    @property
    def is_first_chunk(self) -> bool:
        """Check if this is the first chunk"""
        return self.chunk_index == 1
    
    @property
    def is_last_chunk(self) -> bool:
        """Check if this is the last chunk"""
        return self.chunk_index == self.total_chunks
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert chunk to dictionary for serialization"""
        return {
            'content': self.content,
            'chunk_id': self.chunk_id,
            'source_url': self.source_url,
            'title': self.title,
            'chunk_index': self.chunk_index,
            'total_chunks': self.total_chunks,
            'word_count': self.word_count,
            'char_count': self.char_count,
            'section_title': self.section_title,
            'content_type': self.content_type,
            'keywords': self.keywords
        }

class ContentProcessor:
    """Processes HTML content into clean, structured text chunks
    
    This class handles the complete content processing workflow:
    - Extracting metadata from HTML
    - Cleaning and converting HTML to text
    - Chunking content into manageable pieces
    - Maintaining content structure and context
    """
    
    def __init__(
        self, 
        chunk_size: int = ProcessingConstants.DEFAULT_CHUNK_SIZE,
        overlap_size: int = ProcessingConstants.DEFAULT_OVERLAP_SIZE, 
        min_chunk_size: int = ProcessingConstants.DEFAULT_MIN_CHUNK_SIZE
    ):
        """Initialize the content processor with chunking parameters
        
        Args:
            chunk_size: Maximum size of each text chunk in characters
            overlap_size: Number of characters to overlap between chunks
            min_chunk_size: Minimum size for a chunk to be considered valid
            
        Raises:
            ValueError: If parameters are invalid
        """
        self._validate_chunk_parameters(chunk_size, overlap_size, min_chunk_size)
        
        self.chunk_size = chunk_size
        self.overlap_size = overlap_size
        self.min_chunk_size = min_chunk_size
        
        # Configure html2text converter
        self.h2t = self._configure_html2text()
    
    def _validate_chunk_parameters(self, chunk_size: int, overlap_size: int, min_chunk_size: int) -> None:
        """Validate chunking parameters
        
        Args:
            chunk_size: Maximum chunk size
            overlap_size: Overlap between chunks
            min_chunk_size: Minimum chunk size
            
        Raises:
            ValueError: If parameters are invalid
        """
        if chunk_size <= 0:
            raise ValueError("Chunk size must be positive")
        if overlap_size < 0:
            raise ValueError("Overlap size cannot be negative")
        if min_chunk_size <= 0:
            raise ValueError("Minimum chunk size must be positive")
        if overlap_size >= chunk_size:
            raise ValueError("Overlap size must be less than chunk size")
        if min_chunk_size > chunk_size:
            raise ValueError("Minimum chunk size cannot exceed chunk size")
    
    def _configure_html2text(self) -> html2text.HTML2Text:
        """Configure and return html2text converter
        
        Returns:
            Configured HTML2Text instance
        """
        h2t = html2text.HTML2Text()
        h2t.ignore_links = False
        h2t.ignore_images = True
        h2t.ignore_emphasis = False
        h2t.body_width = 0  # No line wrapping
        h2t.single_line_break = True
        return h2t
        
    def extract_metadata(self, html_content: str, url: str) -> Dict[str, Any]:
        """Extract comprehensive metadata from HTML content
        
        Args:
            html_content: Raw HTML content to process
            url: Source URL of the content
            
        Returns:
            Dictionary containing extracted metadata
            
        Raises:
            MetadataExtractionError: If metadata extraction fails
            HTMLParsingError: If HTML parsing fails
        """
        if not html_content or not html_content.strip():
            raise ValueError("HTML content cannot be empty")
        if not url or not url.strip():
            raise ValueError("URL cannot be empty")
            
        try:
            soup = self._parse_html(html_content)
            
            metadata = self._initialize_metadata(url, html_content)
            metadata.update({
                'title': self._extract_title(soup),
                'description': self._extract_description(soup),
                'keywords': self._extract_keywords(soup),
                'headings': self._extract_headings(soup),
                'links': self._extract_internal_links(soup, url),
                'content_type': self._detect_content_type(html_content, url)
            })
            
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to extract metadata from {url}: {e}")
            raise MetadataExtractionError(f"Metadata extraction failed: {e}") from e
    
    def _parse_html(self, html_content: str) -> BeautifulSoup:
        """Parse HTML content with error handling
        
        Args:
            html_content: Raw HTML to parse
            
        Returns:
            BeautifulSoup object
            
        Raises:
            HTMLParsingError: If parsing fails
        """
        try:
            return BeautifulSoup(html_content, 'lxml')
        except Exception as e:
            raise HTMLParsingError(f"Failed to parse HTML: {e}") from e
    
    def _initialize_metadata(self, url: str, html_content: str) -> Dict[str, Any]:
        """Initialize metadata dictionary with default values
        
        Args:
            url: Source URL
            html_content: Raw HTML content
            
        Returns:
            Dictionary with default metadata values
        """
        return {
            'url': url,
            'title': '',
            'description': '',
            'keywords': [],
            'headings': [],
            'links': [],
            'content_type': 'support_article',
            'word_count': 0,
            'char_count': len(html_content),
            'language': ProcessingConstants.DEFAULT_LANGUAGE
        }
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title from HTML
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Extracted title or empty string
        """
        # Try title tag first
        title_tag = soup.find('title')
        if title_tag and title_tag.get_text().strip():
            return title_tag.get_text().strip()
        
        # Fallback to h1 tag
        h1_tag = soup.find('h1')
        if h1_tag and h1_tag.get_text().strip():
            return h1_tag.get_text().strip()
        
        return ''
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract meta description from HTML
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Meta description or empty string
        """
        desc_tag = soup.find('meta', attrs={'name': 'description'})
        if desc_tag and desc_tag.get('content'):
            return desc_tag['content'].strip()
        return ''
    
    def _extract_keywords(self, soup: BeautifulSoup) -> List[str]:
        """Extract meta keywords from HTML
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            List of keywords
        """
        keywords_tag = soup.find('meta', attrs={'name': 'keywords'})
        if keywords_tag and keywords_tag.get('content'):
            return [k.strip() for k in keywords_tag['content'].split(',') if k.strip()]
        return []
    
    def _extract_headings(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract all headings from HTML
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            List of heading dictionaries with level, text, and id
        """
        headings = []
        for level in range(1, ProcessingConstants.MAX_HEADING_LEVELS + 1):
            for heading in soup.find_all(f'h{level}'):
                text = heading.get_text().strip()
                if text:  # Only include non-empty headings
                    headings.append({
                        'level': level,
                        'text': text,
                        'id': heading.get('id', '')
                    })
        return headings
    
    def _extract_internal_links(self, soup: BeautifulSoup, url: str) -> List[Dict[str, str]]:
        """Extract internal links from HTML
        
        Args:
            soup: BeautifulSoup object
            url: Source URL for determining internal links
            
        Returns:
            List of internal link dictionaries
        """
        base_domain = urlparse(url).netloc
        links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            absolute_url = urljoin(url, href)
            link_domain = urlparse(absolute_url).netloc
            
            # Check if link is internal
            if self._is_internal_link(base_domain, link_domain):
                link_text = link.get_text().strip()
                if link_text:  # Only include links with text
                    links.append({
                        'url': absolute_url,
                        'text': link_text,
                        'title': link.get('title', '')
                    })
        
        return links
    
    def _is_internal_link(self, base_domain: str, link_domain: str) -> bool:
        """Check if a link is internal based on domain
        
        Args:
            base_domain: Domain of the source page
            link_domain: Domain of the link
            
        Returns:
            True if link is internal, False otherwise
        """
        if base_domain in link_domain:
            return True
        return any(domain in link_domain for domain in ProcessingConstants.INTERNAL_DOMAINS)
    
    def _detect_content_type(self, html_content: str, url: str) -> str:
        """Detect the type of content based on HTML and URL patterns
        
        Args:
            html_content: HTML content to analyze
            url: URL to analyze for patterns
            
        Returns:
            Detected content type string
        """
        html_lower = html_content.lower()
        url_lower = url.lower()
        
        # Check each content type pattern
        for content_type, patterns in ProcessingConstants.CONTENT_TYPE_PATTERNS.items():
            # Check URL patterns
            if any(pattern in url_lower for pattern in patterns['url_patterns']):
                return content_type
            
            # Check content patterns
            if patterns['content_patterns']:
                if content_type == 'faq':
                    # Special case for FAQ detection
                    if 'frequently asked questions' in html_lower or html_lower.count('q:') > 3:
                        return content_type
                else:
                    if any(phrase in html_lower for phrase in patterns['content_patterns']):
                        return content_type
        
        return 'support_article'
    
    def clean_html(self, html_content: str) -> str:
        """Clean and convert HTML to markdown/text
        
        Args:
            html_content: Raw HTML content to clean
            
        Returns:
            Cleaned text content
            
        Raises:
            TextCleaningError: If text cleaning fails
            HTMLParsingError: If HTML parsing fails
        """
        if not html_content or not html_content.strip():
            return ""
            
        try:
            soup = self._parse_html(html_content)
            
            # Remove unwanted elements and attributes
            self._remove_unwanted_elements(soup)
            self._remove_unwanted_css_elements(soup)
            
            # Convert to clean text
            clean_text = self._convert_to_text(soup)
            
            # Final text cleanup
            return self._clean_text(clean_text)
            
        except Exception as e:
            logger.error(f"Failed to clean HTML content: {e}")
            raise TextCleaningError(f"HTML cleaning failed: {e}") from e
    
    def _remove_unwanted_elements(self, soup: BeautifulSoup) -> None:
        """Remove unwanted HTML elements
        
        Args:
            soup: BeautifulSoup object to modify in-place
        """
        for element in soup(ProcessingConstants.UNWANTED_HTML_ELEMENTS):
            element.decompose()
    
    def _remove_unwanted_css_elements(self, soup: BeautifulSoup) -> None:
        """Remove elements with unwanted CSS classes or IDs
        
        Args:
            soup: BeautifulSoup object to modify in-place
        """
        for pattern in ProcessingConstants.UNWANTED_CSS_PATTERNS:
            # Remove by class
            for element in soup.find_all(attrs={'class': re.compile(pattern, re.I)}):
                element.decompose()
            # Remove by ID
            for element in soup.find_all(attrs={'id': re.compile(pattern, re.I)}):
                element.decompose()
    
    def _convert_to_text(self, soup: BeautifulSoup) -> str:
        """Convert HTML to text using html2text or fallback
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Converted text content
        """
        try:
            # First try html2text for better markdown conversion
            return self.h2t.handle(str(soup))
        except Exception as e:
            logger.warning(f"html2text failed, falling back to BeautifulSoup: {e}")
            return soup.get_text()
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content"""
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)  # Multiple newlines to double
        text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces to single
        text = re.sub(r'\n[ \t]+', '\n', text)  # Leading whitespace on lines
        
        # Remove empty markdown elements
        text = re.sub(r'\*\*\s*\*\*', '', text)  # Empty bold
        text = re.sub(r'__\s*__', '', text)  # Empty underline
        text = re.sub(r'\[\s*\]\(\s*\)', '', text)  # Empty links
        
        # Clean up lists
        text = re.sub(r'\n\s*[-\*\+]\s*\n', '\n', text)  # Empty list items
        
        # Remove excessive dashes or equals (from markdown headers)
        text = re.sub(r'\n[-=]{4,}\n', '\n', text)
        
        return text.strip()
    
    def create_chunks(self, content: str, metadata: Dict[str, Any]) -> List[TextChunk]:
        """Split content into overlapping chunks with metadata
        
        Args:
            content: Clean text content to chunk
            metadata: Metadata dictionary for the content
            
        Returns:
            List of TextChunk objects
            
        Raises:
            ChunkingError: If chunking fails
            ValueError: If content or metadata is invalid
        """
        if not content or not content.strip():
            raise ValueError("Content cannot be empty")
        if not metadata or 'url' not in metadata:
            raise ValueError("Metadata must contain at least a URL")
            
        try:
            # Handle single chunk case
            if len(content) <= self.chunk_size:
                return self._create_single_chunk(content, metadata)
            
            # Handle multi-chunk case
            return self._create_multiple_chunks(content, metadata)
            
        except Exception as e:
            logger.error(f"Failed to create chunks: {e}")
            raise ChunkingError(f"Chunking failed: {e}") from e
    
    def _create_single_chunk(self, content: str, metadata: Dict[str, Any]) -> List[TextChunk]:
        """Create a single chunk when content fits in one piece
        
        Args:
            content: Text content
            metadata: Content metadata
            
        Returns:
            List containing single TextChunk
        """
        return [TextChunk(
            content=content,
            chunk_id=f"{metadata['url']}_chunk_001",
            source_url=metadata['url'],
            title=metadata.get('title', ''),
            chunk_index=1,
            total_chunks=1,
            word_count=len(content.split()),
            char_count=len(content),
            content_type=metadata.get('content_type', 'support_article'),
            keywords=metadata.get('keywords', [])
        )]
    
    def _create_multiple_chunks(self, content: str, metadata: Dict[str, Any]) -> List[TextChunk]:
        """Create multiple chunks for large content
        
        Args:
            content: Text content to split
            metadata: Content metadata
            
        Returns:
            List of TextChunk objects
        """
        chunks = []
        words = content.split()
        total_words = len(words)
        
        # Calculate chunking parameters
        words_per_chunk = self.chunk_size // ProcessingConstants.CHARS_PER_WORD_ESTIMATE
        overlap_words = self.overlap_size // ProcessingConstants.CHARS_PER_WORD_ESTIMATE
        
        start_idx = 0
        chunk_num = 1
        
        while start_idx < total_words:
            chunk_content = self._extract_chunk_content(words, start_idx, words_per_chunk, total_words)
            
            # Skip chunks that are too small (unless it's the last chunk)
            if self._is_valid_chunk(chunk_content, start_idx + words_per_chunk >= total_words):
                chunk = self._create_chunk(chunk_content, metadata, chunk_num)
                chunks.append(chunk)
                chunk_num += 1
            
            # Move to next chunk with overlap
            start_idx = self._calculate_next_start_index(start_idx, words_per_chunk, overlap_words, total_words)
            if start_idx >= total_words:
                break
        
        # Update total_chunks for all chunks
        self._update_total_chunks(chunks)
        
        return chunks
    
    def _extract_chunk_content(self, words: List[str], start_idx: int, words_per_chunk: int, total_words: int) -> str:
        """Extract content for a single chunk
        
        Args:
            words: List of all words
            start_idx: Starting word index
            words_per_chunk: Target words per chunk
            total_words: Total number of words
            
        Returns:
            Chunk content string
        """
        end_idx = min(start_idx + words_per_chunk, total_words)
        chunk_words = words[start_idx:end_idx]
        chunk_content = ' '.join(chunk_words)
        
        # Adjust chunk size if too large
        while len(chunk_content) > self.chunk_size and len(chunk_words) > 1:
            chunk_words = chunk_words[:-1]
            chunk_content = ' '.join(chunk_words)
        
        # Try to find a good breaking point (sentence boundary)
        if end_idx < total_words:
            chunk_content = self._find_sentence_boundary(chunk_content)
        
        return chunk_content.strip()
    
    def _find_sentence_boundary(self, content: str) -> str:
        """Find a good sentence boundary for chunk splitting
        
        Args:
            content: Content to find boundary in
            
        Returns:
            Content trimmed to sentence boundary
        """
        sentences = content.split('.')
        if len(sentences) > 1:
            # Keep all but the last incomplete sentence
            return '.'.join(sentences[:-1]) + '.'
        return content
    
    def _is_valid_chunk(self, content: str, is_last_chunk: bool) -> bool:
        """Check if a chunk meets minimum size requirements
        
        Args:
            content: Chunk content
            is_last_chunk: Whether this is the last chunk
            
        Returns:
            True if chunk is valid, False otherwise
        """
        return len(content) >= self.min_chunk_size or is_last_chunk
    
    def _create_chunk(self, content: str, metadata: Dict[str, Any], chunk_num: int) -> TextChunk:
        """Create a TextChunk object
        
        Args:
            content: Chunk content
            metadata: Source metadata
            chunk_num: Chunk number
            
        Returns:
            TextChunk object
        """
        chunk = TextChunk(
            content=content,
            chunk_id=f"{metadata['url']}_chunk_{chunk_num:03d}",
            source_url=metadata['url'],
            title=metadata.get('title', ''),
            chunk_index=chunk_num,
            total_chunks=0,  # Will be updated later
            word_count=len(content.split()),
            char_count=len(content),
            content_type=metadata.get('content_type', 'support_article'),
            keywords=metadata.get('keywords', [])
        )
        
        # Extract section title if available
        section_title = self._extract_section_title(content, metadata.get('headings', []))
        chunk.section_title = section_title
        
        return chunk
    
    def _calculate_next_start_index(self, current_start: int, words_per_chunk: int, overlap_words: int, total_words: int) -> int:
        """Calculate the starting index for the next chunk
        
        Args:
            current_start: Current starting index
            words_per_chunk: Words per chunk
            overlap_words: Overlap in words
            total_words: Total words available
            
        Returns:
            Next starting index
        """
        next_start = current_start + words_per_chunk - overlap_words
        return max(next_start, current_start + 1)
    
    def _update_total_chunks(self, chunks: List[TextChunk]) -> None:
        """Update total_chunks field for all chunks
        
        Args:
            chunks: List of chunks to update
        """
        total_chunks = len(chunks)
        for chunk in chunks:
            chunk.total_chunks = total_chunks
    
    def _extract_section_title(self, chunk_content: str, headings: List[Dict]) -> Optional[str]:
        """Extract the most relevant section title for a chunk
        
        Args:
            chunk_content: Content of the chunk
            headings: List of heading dictionaries
            
        Returns:
            Most relevant section title or None
        """
        if not headings or not chunk_content:
            return None
            
        chunk_start = chunk_content[:ProcessingConstants.SECTION_TITLE_PREVIEW_LENGTH].lower()
        
        for heading in headings:
            heading_text = heading.get('text', '').lower()
            if not heading_text:
                continue
                
            # Check if heading text appears in chunk start
            if heading_text in chunk_start:
                return heading['text']
            
            # Check if any words from heading appear in chunk start
            heading_words = heading_text.split()
            if len(heading_words) > 1 and any(word in chunk_start for word in heading_words):
                return heading['text']
        
        return None
    
    def process_content(self, html_content: str, url: str) -> Dict[str, Any]:
        """Process HTML content into structured chunks
        
        Args:
            html_content: Raw HTML content to process
            url: Source URL of the content
            
        Returns:
            Dictionary containing processing results with success status
            
        Raises:
            ContentProcessingError: If processing fails critically
        """
        if not html_content or not html_content.strip():
            return self._create_error_result("HTML content cannot be empty", url)
        if not url or not url.strip():
            return self._create_error_result("URL cannot be empty", url)
            
        try:
            # Extract metadata
            metadata = self.extract_metadata(html_content, url)
            
            # Clean HTML and convert to text
            clean_content = self.clean_html(html_content)
            
            # Update metadata with word count
            metadata['word_count'] = len(clean_content.split()) if clean_content else 0
            
            # Create chunks
            chunks = self.create_chunks(clean_content, metadata) if clean_content else []
            
            return self._create_success_result(metadata, clean_content, chunks)
            
        except (MetadataExtractionError, HTMLParsingError, TextCleaningError, ChunkingError) as e:
            logger.error(f"Content processing error for {url}: {e}")
            return self._create_error_result(str(e), url)
        except Exception as e:
            logger.error(f"Unexpected error processing content from {url}: {e}")
            return self._create_error_result(f"Unexpected error: {str(e)}", url)
    
    def _create_success_result(self, metadata: Dict[str, Any], clean_content: str, chunks: List[TextChunk]) -> Dict[str, Any]:
        """Create a successful processing result
        
        Args:
            metadata: Extracted metadata
            clean_content: Cleaned text content
            chunks: List of text chunks
            
        Returns:
            Success result dictionary
        """
        return {
            'success': True,
            'metadata': metadata,
            'content': clean_content,
            'chunks': chunks,
            'total_chunks': len(chunks),
            'total_words': metadata.get('word_count', 0),
            'total_chars': len(clean_content)
        }
    
    def _create_error_result(self, error_message: str, url: str) -> Dict[str, Any]:
        """Create an error processing result
        
        Args:
            error_message: Error description
            url: Source URL
            
        Returns:
            Error result dictionary
        """
        return {
            'success': False,
            'error': error_message,
            'url': url,
            'metadata': {},
            'content': '',
            'chunks': [],
            'total_chunks': 0,
            'total_words': 0,
            'total_chars': 0
        } 