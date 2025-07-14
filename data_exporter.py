"""
Data export utilities for Aven scraper results
"""
import json
import csv
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class DataExporter:
    """Enhanced data export functionality"""
    
    def __init__(self, output_dir: str = "./scraped_data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def export_to_jsonl(self, chunks: List[Dict[str, Any]], filename: str = "aven_chunks.jsonl"):
        """Export chunks to JSONL format (one JSON object per line)"""
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            for chunk in chunks:
                json.dump(chunk, f, ensure_ascii=False)
                f.write('\n')
        
        logger.info(f"Exported {len(chunks)} chunks to JSONL: {filepath}")
        return str(filepath)
    
    def export_to_parquet(self, chunks: List[Dict[str, Any]], filename: str = "aven_chunks.parquet"):
        """Export chunks to Parquet format for efficient storage and analysis"""
        try:
            filepath = self.output_dir / filename
            
            # Flatten the data for DataFrame
            flattened_chunks = []
            for chunk in chunks:
                flat_chunk = chunk.copy()
                # Convert list fields to strings for CSV compatibility
                flat_chunk['keywords'] = ', '.join(chunk.get('keywords', []))
                flattened_chunks.append(flat_chunk)
            
            df = pd.DataFrame(flattened_chunks)
            df.to_parquet(filepath, index=False)
            
            logger.info(f"Exported {len(chunks)} chunks to Parquet: {filepath}")
            return str(filepath)
            
        except ImportError:
            logger.warning("PyArrow not available, skipping Parquet export")
            return None
    
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
    
    def export_structured_csv(self, results: Dict[str, Any], filename: str = "aven_structured.csv"):
        """Export a comprehensive CSV with all metadata"""
        filepath = self.output_dir / filename
        
        csv_data = []
        for chunk in results.get('chunks', []):
            row = {
                'chunk_id': chunk['chunk_id'],
                'source_url': chunk['source_url'],
                'title': chunk['title'],
                'content_type': chunk['content_type'],
                'section_title': chunk.get('section_title', ''),
                'chunk_index': chunk['chunk_index'],
                'total_chunks': chunk['total_chunks'],
                'word_count': chunk['word_count'],
                'char_count': chunk['char_count'],
                'keywords': ', '.join(chunk.get('keywords', [])),
                'content_preview': chunk['content'][:200] + '...' if len(chunk['content']) > 200 else chunk['content'],
                'content_full': chunk['content']
            }
            csv_data.append(row)
        
        df = pd.DataFrame(csv_data)
        df.to_csv(filepath, index=False, encoding='utf-8')
        
        logger.info(f"Exported structured CSV with {len(csv_data)} rows: {filepath}")
        return str(filepath)
    
    def create_search_index(self, chunks: List[Dict[str, Any]], filename: str = "search_index.json"):
        """Create a simple search index for the content"""
        filepath = self.output_dir / filename
        
        # Create keyword-based search index
        search_index = {
            'created_at': datetime.now().isoformat(),
            'total_chunks': len(chunks),
            'index': {}
        }
        
        for chunk in chunks:
            chunk_id = chunk['chunk_id']
            content = chunk['content'].lower()
            title = chunk.get('title', '').lower()
            keywords = chunk.get('keywords', [])
            
            # Extract searchable terms
            terms = set()
            
            # Add words from content (significant words only)
            content_words = [word.strip('.,!?;:"()[]{}') for word in content.split()]
            significant_words = [word for word in content_words 
                               if len(word) > 3 and word.isalpha()]
            terms.update(significant_words[:50])  # Limit to first 50 significant words
            
            # Add title words
            title_words = [word.strip('.,!?;:"()[]{}') for word in title.split()]
            terms.update(title_words)
            
            # Add keywords
            terms.update([kw.lower().strip() for kw in keywords])
            
            # Add to index
            for term in terms:
                if term not in search_index['index']:
                    search_index['index'][term] = []
                search_index['index'][term].append({
                    'chunk_id': chunk_id,
                    'url': chunk['source_url'],
                    'title': chunk.get('title', ''),
                    'content_type': chunk.get('content_type', ''),
                    'relevance': 1.0  # Could implement TF-IDF scoring
                })
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(search_index, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Created search index with {len(search_index['index'])} terms: {filepath}")
        return str(filepath)
    
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
    
    def export_all_formats(self, results: Dict[str, Any]) -> Dict[str, str]:
        """Export results in all available formats"""
        logger.info("Exporting results in all formats...")
        
        chunks = results.get('chunks', [])
        exported_files = {}
        
        # Standard exports
        exported_files['jsonl'] = self.export_to_jsonl(chunks)
        exported_files['structured_csv'] = self.export_structured_csv(results)
        exported_files['sitemap'] = self.export_url_sitemap(results)
        exported_files['report'] = self.create_summary_report(results)
        exported_files['search_index'] = self.create_search_index(chunks)
        
        # Content type exports
        content_type_files = self.export_content_by_type(results)
        exported_files.update(content_type_files)
        
        # Try Parquet export
        parquet_file = self.export_to_parquet(chunks)
        if parquet_file:
            exported_files['parquet'] = parquet_file
        
        logger.info(f"Exported {len(exported_files)} files to {self.output_dir}")
        return exported_files 