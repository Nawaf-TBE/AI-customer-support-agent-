"""
Data Export Utilities for AI Customer Support Agent

This module provides comprehensive data export functionality for the Aven support
scraper results, enabling multiple output formats optimized for different use cases
in the AI Customer Support Agent pipeline.

Key Features:
- Multi-format exports (JSON, CSV, Parquet, Markdown) for maximum compatibility
- Content organization by type (FAQ, guides, troubleshooting, etc.)
- Search index generation for rapid content discovery
- Comprehensive reporting and analytics
- RAG pipeline optimization with chunked content export

Export Formats Supported:
- JSONL: Line-delimited JSON for streaming and big data processing
- Parquet: Columnar format for efficient analytics and data science workflows
- CSV: Structured tabular data for spreadsheet analysis
- Markdown: Human-readable documentation organized by content type
- Search Index: JSON-based keyword index for fast content lookup

Integration Points:
- Pinecone vector database ingestion via structured JSON exports
- RAG pipeline content chunks for AI model training and retrieval
- Analytics dashboards via CSV and Parquet exports
- Documentation generation via organized Markdown outputs

Author: AI Customer Support Agent Development Team
License: MIT
Version: 1.0.0
"""
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

import pandas as pd

logger = logging.getLogger(__name__)

# Constants
class ExportConstants:
    """Constants used throughout data export operations"""
    # Default filenames
    DEFAULT_JSONL_FILENAME = "aven_chunks.jsonl"
    DEFAULT_PARQUET_FILENAME = "aven_chunks.parquet"
    DEFAULT_CSV_FILENAME = "aven_structured.csv"
    DEFAULT_SITEMAP_FILENAME = "scraped_urls.txt"
    DEFAULT_REPORT_FILENAME = "scraping_report.md"
    DEFAULT_SEARCH_INDEX_FILENAME = "search_index.json"
    
    # Directory names
    CONTENT_TYPE_SUBDIR = "by_content_type"
    DEFAULT_OUTPUT_DIR = "./scraped_data"
    
    # Content processing
    CONTENT_PREVIEW_LENGTH = 200
    MAX_SIGNIFICANT_WORDS = 50
    MIN_WORD_LENGTH = 3
    
    # File encoding
    DEFAULT_ENCODING = 'utf-8'
    
    # Search index settings
    DEFAULT_RELEVANCE_SCORE = 1.0
    
    # Text processing patterns
    PUNCTUATION_CHARS = '.,!?;:"()[]{}'
    
    # Report formatting
    DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
    
    # CSV field names
    CSV_FIELDS = [
        'chunk_id', 'source_url', 'title', 'content_type', 'section_title',
        'chunk_index', 'total_chunks', 'word_count', 'char_count', 
        'keywords', 'content_preview', 'content_full'
    ]

# Custom Exceptions
class DataExportError(Exception):
    """Base exception for data export errors"""
    pass

class FileWriteError(DataExportError):
    """Raised when file writing operations fail"""
    pass

class DataValidationError(DataExportError):
    """Raised when input data validation fails"""
    pass

class FormatNotSupportedError(DataExportError):
    """Raised when requested export format is not supported"""
    pass

class DirectoryCreationError(DataExportError):
    """Raised when output directory creation fails"""
    pass

# Data Classes
@dataclass
class ExportResult:
    """Result of an export operation"""
    success: bool
    file_path: Optional[str] = None
    format_type: Optional[str] = None
    record_count: int = 0
    file_size_bytes: int = 0
    error_message: Optional[str] = None
    export_time: datetime = field(default_factory=datetime.now)
    
    @property
    def file_size_mb(self) -> float:
        """Get file size in megabytes"""
        return self.file_size_bytes / (1024 * 1024) if self.file_size_bytes else 0.0

@dataclass
class ExportSummary:
    """Summary of all export operations"""
    total_exports: int = 0
    successful_exports: int = 0
    failed_exports: int = 0
    total_records: int = 0
    total_size_bytes: int = 0
    export_results: List[ExportResult] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage"""
        if self.total_exports == 0:
            return 0.0
        return (self.successful_exports / self.total_exports) * 100
    
    @property
    def duration_seconds(self) -> float:
        """Calculate total duration in seconds"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

class DataExporter:
    """
    Enhanced data export functionality for AI Customer Support Agent.
    
    This class provides a comprehensive suite of export methods to transform
    scraped support content into various formats optimized for different
    downstream applications including RAG pipelines, analytics, and documentation.
    
    The exporter handles content chunking, metadata preservation, and format
    optimization to ensure maximum compatibility with ML/AI workflows and
    traditional data analysis tools.
    
    Attributes:
        output_dir (Path): Base directory for all exported files
        export_summary (ExportSummary): Summary of all export operations
        
    Export Methods:
        - export_to_jsonl(): Line-delimited JSON for big data processing
        - export_to_parquet(): Columnar format for analytics
        - export_structured_csv(): Comprehensive CSV with all metadata
        - export_content_by_type(): Organized Markdown by content category
        - create_search_index(): Keyword-based search functionality
        - create_summary_report(): Analytics and session reporting
    """
    
    def __init__(self, output_dir: str = ExportConstants.DEFAULT_OUTPUT_DIR):
        """
        Initialize the DataExporter with output directory configuration.
        
        Args:
            output_dir (str): Directory path for exported files. Creates directory
                            if it doesn't exist. Defaults to "./scraped_data"
                            
        Raises:
            DirectoryCreationError: If output directory cannot be created
            ValueError: If output_dir is invalid
        """
        if not output_dir or not output_dir.strip():
            raise ValueError("Output directory cannot be empty")
            
        try:
            self.output_dir = Path(output_dir).resolve()
            self.output_dir.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError) as e:
            raise DirectoryCreationError(f"Failed to create output directory '{output_dir}': {e}") from e
            
        self.export_summary = ExportSummary()
        logger.info(f"DataExporter initialized with output directory: {self.output_dir}")
    
    def _validate_chunks_data(self, chunks: List[Dict[str, Any]]) -> None:
        """Validate chunks data structure
        
        Args:
            chunks: List of chunk dictionaries to validate
            
        Raises:
            DataValidationError: If chunks data is invalid
        """
        if not isinstance(chunks, list):
            raise DataValidationError("Chunks must be a list")
        
        if not chunks:
            logger.warning("Empty chunks list provided for export")
            return
            
        # Validate first chunk structure as sample
        sample_chunk = chunks[0]
        required_fields = ['chunk_id', 'content', 'source_url']
        
        for field in required_fields:
            if field not in sample_chunk:
                raise DataValidationError(f"Required field '{field}' missing from chunk data")
    
    def _validate_results_data(self, results: Dict[str, Any]) -> None:
        """Validate results data structure
        
        Args:
            results: Results dictionary to validate
            
        Raises:
            DataValidationError: If results data is invalid
        """
        if not isinstance(results, dict):
            raise DataValidationError("Results must be a dictionary")
        
        if 'chunks' not in results:
            raise DataValidationError("Results must contain 'chunks' key")
            
        self._validate_chunks_data(results['chunks'])
    
    def _get_file_size(self, filepath: Path) -> int:
        """Get file size in bytes
        
        Args:
            filepath: Path to the file
            
        Returns:
            File size in bytes, 0 if file doesn't exist
        """
        try:
            return filepath.stat().st_size if filepath.exists() else 0
        except OSError:
            return 0
    
    def _create_export_result(
        self, 
        success: bool, 
        file_path: Optional[str] = None, 
        format_type: Optional[str] = None,
        record_count: int = 0,
        error_message: Optional[str] = None
    ) -> ExportResult:
        """Create an ExportResult object
        
        Args:
            success: Whether the export was successful
            file_path: Path to the exported file
            format_type: Type of export format
            record_count: Number of records exported
            error_message: Error message if export failed
            
        Returns:
            ExportResult object
        """
        file_size = 0
        if file_path and success:
            file_size = self._get_file_size(Path(file_path))
            
        result = ExportResult(
            success=success,
            file_path=file_path,
            format_type=format_type,
            record_count=record_count,
            file_size_bytes=file_size,
            error_message=error_message
        )
        
        # Update summary
        self.export_summary.total_exports += 1
        if success:
            self.export_summary.successful_exports += 1
            self.export_summary.total_records += record_count
            self.export_summary.total_size_bytes += file_size
        else:
            self.export_summary.failed_exports += 1
            
        self.export_summary.export_results.append(result)
        
        return result
    
    def export_to_jsonl(
        self, 
        chunks: List[Dict[str, Any]], 
        filename: str = ExportConstants.DEFAULT_JSONL_FILENAME
    ) -> ExportResult:
        """
        Export content chunks to JSONL format for big data and streaming applications.
        
        JSONL (JSON Lines) format stores each chunk as a separate JSON object on its
        own line, making it ideal for streaming processing, Pinecone vector database
        ingestion, and distributed computing frameworks like Apache Spark.
        
        This format is particularly well-suited for:
        - RAG pipeline data ingestion
        - Vector database bulk uploads
        - Streaming data processing
        - Large dataset handling with memory efficiency
        
        Args:
            chunks (List[Dict[str, Any]]): Processed content chunks with metadata
            filename (str): Output filename, defaults to "aven_chunks.jsonl"
            
        Returns:
            ExportResult: Result object containing export status and metadata
            
        Raises:
            DataValidationError: If chunks data is invalid
            FileWriteError: If file writing fails
            
        Example chunk structure:
            {
                "chunk_id": "url_chunk_001",
                "content": "FAQ content...",
                "source_url": "https://aven.com/support/faq",
                "content_type": "faq",
                "word_count": 150,
                "keywords": ["password", "reset", "login"]
            }
        """
        try:
            self._validate_chunks_data(chunks)
            
            if not filename or not filename.strip():
                filename = ExportConstants.DEFAULT_JSONL_FILENAME
                
            filepath = self.output_dir / filename
            
            # Write JSONL file
            self._write_jsonl_file(filepath, chunks)
            
            logger.info(f"Exported {len(chunks)} chunks to JSONL: {filepath}")
            return self._create_export_result(
                success=True,
                file_path=str(filepath),
                format_type="jsonl",
                record_count=len(chunks)
            )
            
        except (DataValidationError, FileWriteError) as e:
            logger.error(f"JSONL export failed: {e}")
            return self._create_export_result(
                success=False,
                format_type="jsonl",
                error_message=str(e)
            )
        except Exception as e:
            logger.error(f"Unexpected error during JSONL export: {e}")
            return self._create_export_result(
                success=False,
                format_type="jsonl",
                error_message=f"Unexpected error: {str(e)}"
            )
    
    def _write_jsonl_file(self, filepath: Path, chunks: List[Dict[str, Any]]) -> None:
        """Write chunks to JSONL file
        
        Args:
            filepath: Path to output file
            chunks: List of chunks to write
            
        Raises:
            FileWriteError: If file writing fails
        """
        try:
            with open(filepath, 'w', encoding=ExportConstants.DEFAULT_ENCODING) as f:
                for chunk in chunks:
                    json.dump(chunk, f, ensure_ascii=False)
                    f.write('\n')
        except (OSError, IOError, PermissionError) as e:
            raise FileWriteError(f"Failed to write JSONL file '{filepath}': {e}") from e
    
    def export_to_parquet(
        self, 
        chunks: List[Dict[str, Any]], 
        filename: str = ExportConstants.DEFAULT_PARQUET_FILENAME
    ) -> ExportResult:
        """Export chunks to Parquet format for efficient storage and analysis
        
        Args:
            chunks: List of chunk dictionaries to export
            filename: Output filename for Parquet file
            
        Returns:
            ExportResult: Result object containing export status and metadata
            
        Raises:
            DataValidationError: If chunks data is invalid
            FormatNotSupportedError: If PyArrow is not available
            FileWriteError: If file writing fails
        """
        try:
            self._validate_chunks_data(chunks)
            
            if not filename or not filename.strip():
                filename = ExportConstants.DEFAULT_PARQUET_FILENAME
                
            filepath = self.output_dir / filename
            
            # Check if PyArrow is available
            try:
                import pyarrow
            except ImportError:
                raise FormatNotSupportedError("PyArrow not available for Parquet export")
            
            # Flatten and prepare data
            flattened_chunks = self._flatten_chunks_for_tabular(chunks)
            
            # Create DataFrame and export
            df = pd.DataFrame(flattened_chunks)
            df.to_parquet(filepath, index=False)
            
            logger.info(f"Exported {len(chunks)} chunks to Parquet: {filepath}")
            return self._create_export_result(
                success=True,
                file_path=str(filepath),
                format_type="parquet",
                record_count=len(chunks)
            )
            
        except (DataValidationError, FormatNotSupportedError, FileWriteError) as e:
            logger.error(f"Parquet export failed: {e}")
            return self._create_export_result(
                success=False,
                format_type="parquet",
                error_message=str(e)
            )
        except Exception as e:
            logger.error(f"Unexpected error during Parquet export: {e}")
            return self._create_export_result(
                success=False,
                format_type="parquet",
                error_message=f"Unexpected error: {str(e)}"
            )
    
    def _flatten_chunks_for_tabular(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Flatten chunk data for tabular formats (CSV, Parquet)
        
        Args:
            chunks: List of chunk dictionaries
            
        Returns:
            List of flattened chunk dictionaries
        """
        flattened_chunks = []
        for chunk in chunks:
            flat_chunk = chunk.copy()
            # Convert list fields to strings for tabular compatibility
            if 'keywords' in flat_chunk and isinstance(flat_chunk['keywords'], list):
                flat_chunk['keywords'] = ', '.join(flat_chunk['keywords'])
            flattened_chunks.append(flat_chunk)
        return flattened_chunks
    
    def export_content_by_type(self, results: Dict[str, Any], output_subdir: str = "by_content_type"):
        """Export content organized by content type"""
        type_dir = self.output_dir / output_subdir
        type_dir.mkdir(exist_ok=True)
        
        # Group chunks by content type
        chunks_by_type = {}
        for chunk in results.get('chunks', []):
            content_type = chunk.get('content_type', 'unknown')
            if content_type not in chunks_by_type:
                chunks_by_type[content_type] = []
            chunks_by_type[content_type].append(chunk)
        
        exported_files = {}
        for content_type, chunks in chunks_by_type.items():
            # Create markdown file for each content type
            filename = f"{content_type}_content.md"
            filepath = type_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"# Aven Support: {content_type.replace('_', ' ').title()}\n\n")
                f.write(f"*Exported on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
                f.write(f"**Total sections:** {len(chunks)}\n\n")
                f.write("---\n\n")
                
                for i, chunk in enumerate(chunks, 1):
                    f.write(f"## {i}. {chunk.get('title', 'Untitled')}\n\n")
                    f.write(f"**Source:** [{chunk['source_url']}]({chunk['source_url']})\n")
                    if chunk.get('section_title'):
                        f.write(f"**Section:** {chunk['section_title']}\n")
                    f.write(f"**Chunk:** {chunk['chunk_index']}/{chunk['total_chunks']}\n\n")
                    f.write(chunk['content'])
                    f.write("\n\n---\n\n")
            
            exported_files[content_type] = str(filepath)
            logger.info(f"Exported {len(chunks)} {content_type} chunks to: {filepath}")
        
        return exported_files
    
    def export_structured_csv(
        self, 
        results: Dict[str, Any], 
        filename: str = ExportConstants.DEFAULT_CSV_FILENAME
    ) -> ExportResult:
        """Export a comprehensive CSV with all metadata
        
        Args:
            results: Results dictionary containing chunks and metadata
            filename: Output filename for CSV file
            
        Returns:
            ExportResult: Result object containing export status and metadata
            
        Raises:
            DataValidationError: If results data is invalid
            FileWriteError: If file writing fails
        """
        try:
            self._validate_results_data(results)
            
            if not filename or not filename.strip():
                filename = ExportConstants.DEFAULT_CSV_FILENAME
                
            filepath = self.output_dir / filename
            chunks = results.get('chunks', [])
            
            # Prepare CSV data
            csv_data = self._prepare_csv_data(chunks)
            
            # Create DataFrame and export
            df = pd.DataFrame(csv_data)
            df.to_csv(filepath, index=False, encoding=ExportConstants.DEFAULT_ENCODING)
            
            logger.info(f"Exported structured CSV with {len(csv_data)} rows: {filepath}")
            return self._create_export_result(
                success=True,
                file_path=str(filepath),
                format_type="csv",
                record_count=len(csv_data)
            )
            
        except (DataValidationError, FileWriteError) as e:
            logger.error(f"CSV export failed: {e}")
            return self._create_export_result(
                success=False,
                format_type="csv",
                error_message=str(e)
            )
        except Exception as e:
            logger.error(f"Unexpected error during CSV export: {e}")
            return self._create_export_result(
                success=False,
                format_type="csv",
                error_message=f"Unexpected error: {str(e)}"
            )
    
    def _prepare_csv_data(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prepare chunk data for CSV export
        
        Args:
            chunks: List of chunk dictionaries
            
        Returns:
            List of CSV row dictionaries
        """
        csv_data = []
        for chunk in chunks:
            # Create content preview
            content = chunk.get('content', '')
            content_preview = (
                content[:ExportConstants.CONTENT_PREVIEW_LENGTH] + '...' 
                if len(content) > ExportConstants.CONTENT_PREVIEW_LENGTH 
                else content
            )
            
            row = {
                'chunk_id': chunk.get('chunk_id', ''),
                'source_url': chunk.get('source_url', ''),
                'title': chunk.get('title', ''),
                'content_type': chunk.get('content_type', ''),
                'section_title': chunk.get('section_title', ''),
                'chunk_index': chunk.get('chunk_index', 0),
                'total_chunks': chunk.get('total_chunks', 0),
                'word_count': chunk.get('word_count', 0),
                'char_count': chunk.get('char_count', 0),
                'keywords': ', '.join(chunk.get('keywords', [])),
                'content_preview': content_preview,
                'content_full': content
            }
            csv_data.append(row)
        
        return csv_data
    
    def create_search_index(
        self, 
        chunks: List[Dict[str, Any]], 
        filename: str = ExportConstants.DEFAULT_SEARCH_INDEX_FILENAME
    ) -> ExportResult:
        """Create a keyword-based search index for the content
        
        Args:
            chunks: List of chunk dictionaries to index
            filename: Output filename for search index
            
        Returns:
            ExportResult: Result object containing export status and metadata
            
        Raises:
            DataValidationError: If chunks data is invalid
            FileWriteError: If file writing fails
        """
        try:
            self._validate_chunks_data(chunks)
            
            if not filename or not filename.strip():
                filename = ExportConstants.DEFAULT_SEARCH_INDEX_FILENAME
                
            filepath = self.output_dir / filename
            
            # Build search index
            search_index = self._build_search_index(chunks)
            
            # Write index file
            self._write_search_index_file(filepath, search_index)
            
            term_count = len(search_index['index'])
            logger.info(f"Created search index with {term_count} terms: {filepath}")
            
            return self._create_export_result(
                success=True,
                file_path=str(filepath),
                format_type="search_index",
                record_count=term_count
            )
            
        except (DataValidationError, FileWriteError) as e:
            logger.error(f"Search index creation failed: {e}")
            return self._create_export_result(
                success=False,
                format_type="search_index",
                error_message=str(e)
            )
        except Exception as e:
            logger.error(f"Unexpected error during search index creation: {e}")
            return self._create_export_result(
                success=False,
                format_type="search_index",
                error_message=f"Unexpected error: {str(e)}"
            )
    
    def _build_search_index(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build search index from chunks
        
        Args:
            chunks: List of chunk dictionaries
            
        Returns:
            Search index dictionary
        """
        search_index = {
            'created_at': datetime.now().isoformat(),
            'total_chunks': len(chunks),
            'index': {}
        }
        
        for chunk in chunks:
            chunk_id = chunk.get('chunk_id', '')
            content = chunk.get('content', '').lower()
            title = chunk.get('title', '').lower()
            keywords = chunk.get('keywords', [])
            
            # Extract searchable terms
            terms = self._extract_search_terms(content, title, keywords)
            
            # Add to index
            for term in terms:
                if term not in search_index['index']:
                    search_index['index'][term] = []
                    
                search_index['index'][term].append({
                    'chunk_id': chunk_id,
                    'url': chunk.get('source_url', ''),
                    'title': chunk.get('title', ''),
                    'content_type': chunk.get('content_type', ''),
                    'relevance': ExportConstants.DEFAULT_RELEVANCE_SCORE
                })
        
        return search_index
    
    def _extract_search_terms(self, content: str, title: str, keywords: List[str]) -> set:
        """Extract searchable terms from content
        
        Args:
            content: Content text
            title: Title text
            keywords: List of keywords
            
        Returns:
            Set of search terms
        """
        terms = set()
        
        # Add words from content (significant words only)
        content_words = [
            word.strip(ExportConstants.PUNCTUATION_CHARS) 
            for word in content.split()
        ]
        significant_words = [
            word for word in content_words 
            if len(word) > ExportConstants.MIN_WORD_LENGTH and word.isalpha()
        ]
        terms.update(significant_words[:ExportConstants.MAX_SIGNIFICANT_WORDS])
        
        # Add title words
        title_words = [
            word.strip(ExportConstants.PUNCTUATION_CHARS) 
            for word in title.split()
        ]
        terms.update([word for word in title_words if word.isalpha()])
        
        # Add keywords
        terms.update([kw.lower().strip() for kw in keywords if kw.strip()])
        
        return terms
    
    def _write_search_index_file(self, filepath: Path, search_index: Dict[str, Any]) -> None:
        """Write search index to file
        
        Args:
            filepath: Path to output file
            search_index: Search index dictionary
            
        Raises:
            FileWriteError: If file writing fails
        """
        try:
            with open(filepath, 'w', encoding=ExportConstants.DEFAULT_ENCODING) as f:
                json.dump(search_index, f, indent=2, ensure_ascii=False)
        except (OSError, IOError, PermissionError) as e:
            raise FileWriteError(f"Failed to write search index file '{filepath}': {e}") from e
    
    def export_url_sitemap(self, results: Dict[str, Any], filename: str = "scraped_urls.txt"):
        """Export a simple sitemap of all scraped URLs"""
        filepath = self.output_dir / filename
        
        urls = results.get('scraped_urls', [])
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# Aven Support URLs Scraped\n")
            f.write(f"# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# Total URLs: {len(urls)}\n\n")
            
            for url in sorted(urls):
                f.write(f"{url}\n")
        
        logger.info(f"Exported {len(urls)} URLs to sitemap: {filepath}")
        return str(filepath)
    
    def create_summary_report(self, results: Dict[str, Any], filename: str = "scraping_report.md"):
        """Create a comprehensive markdown report"""
        filepath = self.output_dir / filename
        
        stats = results.get('session_stats', {})
        chunks = results.get('chunks', [])
        
        # Analyze content types
        content_type_counts = {}
        word_count_by_type = {}
        
        for chunk in chunks:
            content_type = chunk.get('content_type', 'unknown')
            content_type_counts[content_type] = content_type_counts.get(content_type, 0) + 1
            word_count_by_type[content_type] = word_count_by_type.get(content_type, 0) + chunk.get('word_count', 0)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("# Aven Support Scraping Report\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Session Statistics
            f.write("## Session Statistics\n\n")
            f.write(f"- **Duration:** {stats.get('duration_minutes', 0):.1f} minutes\n")
            f.write(f"- **URLs Discovered:** {stats.get('urls_discovered', 0)}\n")
            f.write(f"- **URLs Scraped:** {stats.get('urls_scraped', 0)}\n")
            f.write(f"- **URLs Failed:** {stats.get('urls_failed', 0)}\n")
            f.write(f"- **Total Chunks:** {len(chunks)}\n")
            f.write(f"- **Total Words:** {stats.get('total_words', 0):,}\n\n")
            
            # Content Type Analysis
            f.write("## Content Type Analysis\n\n")
            f.write("| Content Type | Chunks | Words | Avg Words/Chunk |\n")
            f.write("|--------------|--------|-------|------------------|\n")
            
            for content_type in sorted(content_type_counts.keys()):
                chunk_count = content_type_counts[content_type]
                word_count = word_count_by_type[content_type]
                avg_words = word_count / chunk_count if chunk_count > 0 else 0
                
                f.write(f"| {content_type.replace('_', ' ').title()} | {chunk_count} | {word_count:,} | {avg_words:.0f} |\n")
            
            f.write("\n")
            
            # URLs Scraped
            f.write("## Scraped URLs\n\n")
            for url in sorted(results.get('scraped_urls', [])):
                f.write(f"- [{url}]({url})\n")
            
            if results.get('failed_urls'):
                f.write("\n## Failed URLs\n\n")
                for url in sorted(results.get('failed_urls', [])):
                    f.write(f"- {url}\n")
        
        logger.info(f"Created summary report: {filepath}")
        return str(filepath)
    
    def export_all_formats(self, results: Dict[str, Any]) -> ExportSummary:
        """
        Export scraped results in all available formats for comprehensive coverage.
        
        This master export method generates the complete suite of output formats,
        providing maximum flexibility for downstream applications. Each format is
        optimized for specific use cases within the AI Customer Support Agent pipeline.
        
        Generated Outputs:
        - JSONL: For RAG pipeline and vector database ingestion
        - Structured CSV: For spreadsheet analysis and data science workflows  
        - Parquet: For high-performance analytics and big data processing
        - Content by Type: Organized Markdown files for human review
        - Search Index: Keyword-based content discovery system
        - URL Sitemap: Complete list of processed URLs
        - Summary Report: Comprehensive analytics and session statistics
        
        This method ensures data accessibility across different technical skill levels
        and application requirements, from AI/ML workflows to business analysis.
        
        Args:
            results (Dict[str, Any]): Complete scraping session results including
                                    chunks, metadata, URLs, and session statistics
                                    
        Returns:
            ExportSummary: Summary of all export operations with success/failure details
                               
        Example:
            summary = exporter.export_all_formats(scraping_results)
            print(f"Success rate: {summary.success_rate:.1f}%")
            for result in summary.export_results:
                if result.success:
                    print(f"✅ {result.format_type}: {result.file_path}")
        """
        logger.info("Exporting results in all formats...")
        
        try:
            self._validate_results_data(results)
            chunks = results.get('chunks', [])
            
            # Reset export summary for this batch
            self.export_summary = ExportSummary()
            
            # Standard exports
            self.export_to_jsonl(chunks)
            self.export_structured_csv(results)
            self.export_url_sitemap(results)
            self.create_summary_report(results)
            self.create_search_index(chunks)
            
            # Content type exports (returns dict of files, not ExportResult)
            content_type_files = self.export_content_by_type(results)
            
            # Try Parquet export
            self.export_to_parquet(chunks)
            
            # Finalize summary
            self.export_summary.end_time = datetime.now()
            
            logger.info(f"Export batch completed: {self.export_summary.successful_exports}/"
                       f"{self.export_summary.total_exports} successful")
            
            return self.export_summary
            
        except Exception as e:
            logger.error(f"Export batch failed: {e}")
            self.export_summary.end_time = datetime.now()
            return self.export_summary
    
    def get_export_summary(self) -> ExportSummary:
        """Get the current export summary
        
        Returns:
            ExportSummary: Current export summary with all operations
        """
        return self.export_summary 