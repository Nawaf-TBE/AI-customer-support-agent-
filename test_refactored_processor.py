#!/usr/bin/env python3
"""
Test script for refactored ContentProcessor
Validates that the refactored code maintains the same functionality as before.
"""

import sys
import logging
from content_processor import (
    ContentProcessor,
    MetadataExtractor,
    HTMLCleaner,
    TextChunker,
    ContentTypeDetector,
    TextChunk,
    ProcessingConstants
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def test_content_type_detector():
    """Test ContentTypeDetector functionality"""
    logger.info("Testing ContentTypeDetector...")
    
    # Test FAQ detection
    faq_html = "<html><body><h1>Frequently Asked Questions</h1></body></html>"
    faq_url = "https://example.com/faq"
    content_type = ContentTypeDetector.detect(faq_html, faq_url)
    assert content_type == "faq", f"Expected 'faq', got '{content_type}'"
    
    # Test guide detection
    guide_url = "https://example.com/guide/getting-started"
    guide_html = "<html><body><p>Step 1: Install</p></body></html>"
    content_type = ContentTypeDetector.detect(guide_html, guide_url)
    assert content_type == "guide", f"Expected 'guide', got '{content_type}'"
    
    # Test default
    default_html = "<html><body><p>Some content</p></body></html>"
    default_url = "https://example.com/article"
    content_type = ContentTypeDetector.detect(default_html, default_url)
    assert content_type == "support_article", f"Expected 'support_article', got '{content_type}'"
    
    logger.info("✓ ContentTypeDetector tests passed")


def test_metadata_extractor():
    """Test MetadataExtractor functionality"""
    logger.info("Testing MetadataExtractor...")
    
    extractor = MetadataExtractor()
    
    test_html = """
    <html>
        <head>
            <title>Test Page Title</title>
            <meta name="description" content="Test description">
            <meta name="keywords" content="test, page, keywords">
        </head>
        <body>
            <h1>Main Heading</h1>
            <h2>Subheading</h2>
            <p>Some content</p>
            <a href="https://example.com/page1">Internal Link</a>
        </body>
    </html>
    """
    
    url = "https://example.com/test"
    metadata = extractor.extract(test_html, url)
    
    assert metadata['title'] == "Test Page Title", f"Title mismatch: {metadata['title']}"
    assert metadata['description'] == "Test description", f"Description mismatch: {metadata['description']}"
    assert 'test' in metadata['keywords'], f"Keywords missing 'test': {metadata['keywords']}"
    assert len(metadata['headings']) == 2, f"Expected 2 headings, got {len(metadata['headings'])}"
    assert metadata['url'] == url, f"URL mismatch: {metadata['url']}"
    
    logger.info("✓ MetadataExtractor tests passed")


def test_html_cleaner():
    """Test HTMLCleaner functionality"""
    logger.info("Testing HTMLCleaner...")
    
    cleaner = HTMLCleaner()
    
    test_html = """
    <html>
        <head><script>alert('test');</script></head>
        <body>
            <nav>Navigation</nav>
            <h1>Main Content</h1>
            <p>This is a test paragraph.</p>
            <footer>Footer content</footer>
        </body>
    </html>
    """
    
    clean_text = cleaner.clean(test_html)
    
    assert "Main Content" in clean_text, "Main content should be present"
    assert "test paragraph" in clean_text, "Paragraph content should be present"
    assert "alert" not in clean_text, "Script content should be removed"
    assert "Navigation" not in clean_text, "Nav content should be removed"
    assert "Footer" not in clean_text, "Footer content should be removed"
    
    logger.info("✓ HTMLCleaner tests passed")


def test_text_chunker():
    """Test TextChunker functionality"""
    logger.info("Testing TextChunker...")
    
    chunker = TextChunker(chunk_size=100, overlap_size=20, min_chunk_size=30)
    
    # Test single chunk (small content)
    small_content = "This is a small piece of content that fits in one chunk."
    metadata = {
        'url': 'https://example.com/test',
        'title': 'Test',
        'content_type': 'support_article',
        'keywords': []
    }
    
    chunks = chunker.create_chunks(small_content, metadata)
    assert len(chunks) == 1, f"Expected 1 chunk, got {len(chunks)}"
    assert chunks[0].content == small_content, "Single chunk content mismatch"
    assert chunks[0].chunk_index == 1, "Chunk index should be 1"
    assert chunks[0].total_chunks == 1, "Total chunks should be 1"
    
    # Test multiple chunks (large content)
    large_content = " ".join(["This is sentence number {}.".format(i) for i in range(100)])
    chunks = chunker.create_chunks(large_content, metadata)
    assert len(chunks) > 1, f"Expected multiple chunks, got {len(chunks)}"
    
    # Verify chunk properties
    for i, chunk in enumerate(chunks, 1):
        assert chunk.chunk_index == i, f"Chunk {i} has wrong index: {chunk.chunk_index}"
        assert chunk.total_chunks == len(chunks), f"Chunk {i} has wrong total: {chunk.total_chunks}"
        assert chunk.source_url == metadata['url'], f"Chunk {i} has wrong URL"
        assert len(chunk.content) > 0, f"Chunk {i} is empty"
    
    logger.info("✓ TextChunker tests passed")


def test_content_processor():
    """Test ContentProcessor (main coordinator)"""
    logger.info("Testing ContentProcessor...")
    
    processor = ContentProcessor(chunk_size=200, overlap_size=50)
    
    test_html = """
    <html>
        <head>
            <title>Test Article</title>
            <meta name="description" content="A test article">
        </head>
        <body>
            <h1>Welcome to the Test</h1>
            <p>This is the first paragraph of the test article.</p>
            <p>This is the second paragraph with more content to process.</p>
            <p>And here's a third paragraph to make sure we have enough content.</p>
        </body>
    </html>
    """
    
    url = "https://example.com/test-article"
    result = processor.process_content(test_html, url)
    
    assert result['success'] == True, f"Processing should succeed: {result.get('error', '')}"
    assert 'metadata' in result, "Result should contain metadata"
    assert 'content' in result, "Result should contain content"
    assert 'chunks' in result, "Result should contain chunks"
    assert result['total_chunks'] > 0, "Should have at least one chunk"
    
    # Verify metadata
    metadata = result['metadata']
    assert metadata['title'] == "Test Article", f"Title mismatch: {metadata['title']}"
    assert metadata['url'] == url, f"URL mismatch: {metadata['url']}"
    
    # Verify content
    content = result['content']
    assert "Welcome to the Test" in content, "Content should contain heading"
    assert "first paragraph" in content, "Content should contain paragraph text"
    
    # Verify chunks
    chunks = result['chunks']
    assert len(chunks) == result['total_chunks'], "Chunk count mismatch"
    for chunk in chunks:
        assert isinstance(chunk, TextChunk), "Each chunk should be a TextChunk instance"
        assert chunk.source_url == url, "Chunk URL should match"
    
    logger.info("✓ ContentProcessor tests passed")


def test_backward_compatibility():
    """Test backward compatibility with original API"""
    logger.info("Testing backward compatibility...")
    
    processor = ContentProcessor()
    
    # Verify attributes exist
    assert hasattr(processor, 'chunk_size'), "Should have chunk_size attribute"
    assert hasattr(processor, 'overlap_size'), "Should have overlap_size attribute"
    assert hasattr(processor, 'min_chunk_size'), "Should have min_chunk_size attribute"
    
    # Verify methods exist
    assert hasattr(processor, 'extract_metadata'), "Should have extract_metadata method"
    assert hasattr(processor, 'clean_html'), "Should have clean_html method"
    assert hasattr(processor, 'create_chunks'), "Should have create_chunks method"
    assert hasattr(processor, 'process_content'), "Should have process_content method"
    
    logger.info("✓ Backward compatibility tests passed")


def test_error_handling():
    """Test error handling"""
    logger.info("Testing error handling...")
    
    processor = ContentProcessor()
    
    # Test empty HTML
    result = processor.process_content("", "https://example.com")
    assert result['success'] == False, "Should fail for empty HTML"
    
    # Test empty URL
    result = processor.process_content("<html><body>Test</body></html>", "")
    assert result['success'] == False, "Should fail for empty URL"
    
    logger.info("✓ Error handling tests passed")


def run_all_tests():
    """Run all tests"""
    logger.info("=" * 60)
    logger.info("Running refactored ContentProcessor tests")
    logger.info("=" * 60)
    
    try:
        test_content_type_detector()
        test_metadata_extractor()
        test_html_cleaner()
        test_text_chunker()
        test_content_processor()
        test_backward_compatibility()
        test_error_handling()
        
        logger.info("=" * 60)
        logger.info("✓ ALL TESTS PASSED!")
        logger.info("=" * 60)
        return 0
    
    except AssertionError as e:
        logger.error("=" * 60)
        logger.error(f"✗ TEST FAILED: {e}")
        logger.error("=" * 60)
        return 1
    
    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"✗ UNEXPECTED ERROR: {e}")
        logger.error("=" * 60)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())

