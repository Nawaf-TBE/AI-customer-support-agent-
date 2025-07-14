"""
Content processing module for converting HTML to clean text chunks
"""
import re
import html2text
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup, Tag
from markdownify import markdownify
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
import logging

logger = logging.getLogger(__name__)

@dataclass
class TextChunk:
    """Represents a processed text chunk with metadata"""
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
    keywords: List[str] = None
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []

class ContentProcessor:
    """Processes HTML content into clean, structured text chunks"""
    
    def __init__(self, chunk_size: int = 1000, overlap_size: int = 100, min_chunk_size: int = 100):
        self.chunk_size = chunk_size
        self.overlap_size = overlap_size
        self.min_chunk_size = min_chunk_size
        
        # Configure html2text
        self.h2t = html2text.HTML2Text()
        self.h2t.ignore_links = False
        self.h2t.ignore_images = True
        self.h2t.ignore_emphasis = False
        self.h2t.body_width = 0  # No line wrapping
        self.h2t.single_line_break = True
        
    def extract_metadata(self, html_content: str, url: str) -> Dict[str, Any]:
        """Extract metadata from HTML content"""
        soup = BeautifulSoup(html_content, 'lxml')
        
        metadata = {
            'url': url,
            'title': '',
            'description': '',
            'keywords': [],
            'headings': [],
            'links': [],
            'content_type': self._detect_content_type(html_content, url),
            'word_count': 0,
            'char_count': len(html_content),
            'language': 'en'  # Default, could be detected
        }
        
        # Extract title
        title_tag = soup.find('title')
        if title_tag:
            metadata['title'] = title_tag.get_text().strip()
        
        # Try alternative title sources
        if not metadata['title']:
            h1_tag = soup.find('h1')
            if h1_tag:
                metadata['title'] = h1_tag.get_text().strip()
        
        # Extract meta description
        desc_tag = soup.find('meta', attrs={'name': 'description'})
        if desc_tag and desc_tag.get('content'):
            metadata['description'] = desc_tag['content'].strip()
        
        # Extract meta keywords
        keywords_tag = soup.find('meta', attrs={'name': 'keywords'})
        if keywords_tag and keywords_tag.get('content'):
            metadata['keywords'] = [k.strip() for k in keywords_tag['content'].split(',')]
        
        # Extract headings
        headings = []
        for level in range(1, 7):
            for heading in soup.find_all(f'h{level}'):
                headings.append({
                    'level': level,
                    'text': heading.get_text().strip(),
                    'id': heading.get('id', '')
                })
        metadata['headings'] = headings
        
        # Extract internal links
        base_domain = urlparse(url).netloc
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            absolute_url = urljoin(url, href)
            link_domain = urlparse(absolute_url).netloc
            
            if base_domain in link_domain or 'aven.com' in link_domain:
                links.append({
                    'url': absolute_url,
                    'text': link.get_text().strip(),
                    'title': link.get('title', '')
                })
        metadata['links'] = links
        
        return metadata
    
    def _detect_content_type(self, html_content: str, url: str) -> str:
        """Detect the type of content based on HTML and URL patterns"""
        html_lower = html_content.lower()
        url_lower = url.lower()
        
        # Check URL patterns
        if any(pattern in url_lower for pattern in ['faq', 'frequently-asked']):
            return 'faq'
        elif any(pattern in url_lower for pattern in ['guide', 'tutorial', 'how-to']):
            return 'guide'
        elif any(pattern in url_lower for pattern in ['troubleshoot', 'problem', 'fix']):
            return 'troubleshooting'
        elif any(pattern in url_lower for pattern in ['getting-started', 'setup', 'install']):
            return 'getting_started'
        elif any(pattern in url_lower for pattern in ['api', 'reference', 'documentation']):
            return 'documentation'
        
        # Check content patterns
        if 'frequently asked questions' in html_lower or html_lower.count('q:') > 3:
            return 'faq'
        elif any(phrase in html_lower for phrase in ['step 1', 'first step', 'getting started']):
            return 'guide'
        elif any(phrase in html_lower for phrase in ['error', 'troubleshoot', 'problem', 'issue']):
            return 'troubleshooting'
        
        return 'support_article'
    
    def clean_html(self, html_content: str) -> str:
        """Clean and convert HTML to markdown/text"""
        soup = BeautifulSoup(html_content, 'lxml')
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'footer', 'aside', 'header']):
            element.decompose()
        
        # Remove elements with certain classes/ids (common navigation/UI elements)
        unwanted_patterns = [
            'nav', 'menu', 'sidebar', 'footer', 'header', 'advertisement',
            'social', 'share', 'cookie', 'popup', 'modal', 'breadcrumb'
        ]
        
        for pattern in unwanted_patterns:
            for element in soup.find_all(attrs={'class': re.compile(pattern, re.I)}):
                element.decompose()
            for element in soup.find_all(attrs={'id': re.compile(pattern, re.I)}):
                element.decompose()
        
        # Convert to clean text
        try:
            # First try html2text for better markdown conversion
            clean_text = self.h2t.handle(str(soup))
        except Exception as e:
            logger.warning(f"html2text failed, falling back to BeautifulSoup: {e}")
            clean_text = soup.get_text()
        
        # Clean up the text
        clean_text = self._clean_text(clean_text)
        
        return clean_text
    
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
        """Split content into overlapping chunks with metadata"""
        if len(content) <= self.chunk_size:
            # Content fits in one chunk
            return [TextChunk(
                content=content,
                chunk_id=f"{metadata['url']}_chunk_001",
                source_url=metadata['url'],
                title=metadata['title'],
                chunk_index=1,
                total_chunks=1,
                word_count=len(content.split()),
                char_count=len(content),
                content_type=metadata['content_type'],
                keywords=metadata['keywords']
            )]
        
        chunks = []
        words = content.split()
        total_words = len(words)
        
        # Calculate approximate chunks needed
        words_per_chunk = self.chunk_size // 5  # Rough estimate: 5 chars per word
        overlap_words = self.overlap_size // 5
        
        start_idx = 0
        chunk_num = 1
        
        while start_idx < total_words:
            # Calculate end index
            end_idx = min(start_idx + words_per_chunk, total_words)
            
            # Get chunk content
            chunk_words = words[start_idx:end_idx]
            chunk_content = ' '.join(chunk_words)
            
            # Adjust chunk size if too large
            while len(chunk_content) > self.chunk_size and len(chunk_words) > 1:
                chunk_words = chunk_words[:-1]
                chunk_content = ' '.join(chunk_words)
            
            # Skip chunks that are too small (unless it's the last chunk)
            if len(chunk_content) >= self.min_chunk_size or end_idx == total_words:
                # Try to find a good breaking point (sentence boundary)
                if end_idx < total_words:
                    sentences = chunk_content.split('.')
                    if len(sentences) > 1:
                        # Keep all but the last incomplete sentence
                        chunk_content = '.'.join(sentences[:-1]) + '.'
                
                chunk = TextChunk(
                    content=chunk_content.strip(),
                    chunk_id=f"{metadata['url']}_chunk_{chunk_num:03d}",
                    source_url=metadata['url'],
                    title=metadata['title'],
                    chunk_index=chunk_num,
                    total_chunks=0,  # Will be updated later
                    word_count=len(chunk_content.split()),
                    char_count=len(chunk_content),
                    content_type=metadata['content_type'],
                    keywords=metadata['keywords']
                )
                
                # Extract section title if available
                section_title = self._extract_section_title(chunk_content, metadata['headings'])
                chunk.section_title = section_title
                
                chunks.append(chunk)
                chunk_num += 1
            
            # Move start index forward (with overlap)
            if end_idx == total_words:
                break
            start_idx = max(start_idx + words_per_chunk - overlap_words, start_idx + 1)
        
        # Update total_chunks for all chunks
        total_chunks = len(chunks)
        for chunk in chunks:
            chunk.total_chunks = total_chunks
        
        return chunks
    
    def _extract_section_title(self, chunk_content: str, headings: List[Dict]) -> Optional[str]:
        """Extract the most relevant section title for a chunk"""
        chunk_start = chunk_content[:200].lower()
        
        for heading in headings:
            heading_text = heading['text'].lower()
            if heading_text in chunk_start or any(word in chunk_start for word in heading_text.split()):
                return heading['text']
        
        return None
    
    def process_content(self, html_content: str, url: str) -> Dict[str, Any]:
        """Process HTML content into structured chunks"""
        try:
            # Extract metadata
            metadata = self.extract_metadata(html_content, url)
            
            # Clean HTML and convert to text
            clean_content = self.clean_html(html_content)
            metadata['word_count'] = len(clean_content.split())
            
            # Create chunks
            chunks = self.create_chunks(clean_content, metadata)
            
            return {
                'success': True,
                'metadata': metadata,
                'content': clean_content,
                'chunks': chunks,
                'total_chunks': len(chunks),
                'total_words': metadata['word_count'],
                'total_chars': len(clean_content)
            }
            
        except Exception as e:
            logger.error(f"Error processing content from {url}: {e}")
            return {
                'success': False,
                'error': str(e),
                'url': url
            } 