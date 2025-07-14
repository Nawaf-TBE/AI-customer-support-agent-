#!/usr/bin/env python3
"""
Comprehensive CLI script for running the Aven Support Scraper
"""
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime

from aven_scraper import AvenScraper
from data_exporter import DataExporter
from config import config

def setup_logging(verbose=False):
    """Setup logging with optional verbose mode"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def print_banner():
    """Print application banner"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                    Aven Support Scraper                     ║
║              Powered by Exa.ai Neural Search                ║
╚══════════════════════════════════════════════════════════════╝
""")

def print_config_info():
    """Print current configuration"""
    print("📋 Configuration:")
    print(f"   • Base URL: {config.base_url}")
    print(f"   • Max pages: {config.max_subpages}")
    print(f"   • Chunk size: {config.chunk_size}")
    print(f"   • Output dir: {config.output_dir}")
    print(f"   • Rate limit: {config.requests_per_minute} req/min")
    print()

def validate_setup():
    """Validate that everything is set up correctly"""
    issues = []
    
    # Check API key
    if not config.exa_api_key or config.exa_api_key == "your_exa_api_key_here":
        issues.append("❌ EXA_API_KEY not configured")
    else:
        print("✅ Exa.ai API key configured")
    
    # Check output directory
    try:
        Path(config.output_dir).mkdir(exist_ok=True)
        print("✅ Output directory accessible")
    except Exception as e:
        issues.append(f"❌ Cannot access output directory: {e}")
    
    # Check dependencies
    try:
        from exa_py import Exa
        print("✅ Exa.ai Python SDK available")
    except ImportError:
        issues.append("❌ exa-py package not installed")
    
    try:
        import pandas as pd
        print("✅ Pandas available for data processing")
    except ImportError:
        issues.append("❌ pandas package not installed")
    
    if issues:
        print("\n🚨 Setup Issues Found:")
        for issue in issues:
            print(f"   {issue}")
        print("\nPlease fix these issues before running the scraper.")
        return False
    
    print("✅ All checks passed!\n")
    return True

def run_scraper(args):
    """Run the main scraping process"""
    print("🚀 Starting Aven support page scraping...")
    
    # Override config with command line arguments
    if args.max_pages:
        config.max_subpages = args.max_pages
        print(f"   • Override max pages: {args.max_pages}")
    
    if args.output_dir:
        config.output_dir = args.output_dir
        print(f"   • Override output dir: {args.output_dir}")
    
    if args.chunk_size:
        config.chunk_size = args.chunk_size
        print(f"   • Override chunk size: {args.chunk_size}")
    
    print()
    
    # Initialize scraper
    scraper = AvenScraper(api_key=args.api_key)
    
    # Run scraping
    start_time = datetime.now()
    results = scraper.scrape_support_pages()
    
    if not results['success']:
        print(f"❌ Scraping failed: {results.get('error', 'Unknown error')}")
        return False
    
    # Print results summary
    stats = results['session_stats']
    duration = (datetime.now() - start_time).total_seconds() / 60
    
    print(f"""
🎉 Scraping completed successfully!

📊 Results Summary:
   • Duration: {duration:.1f} minutes
   • URLs discovered: {stats['urls_discovered']}
   • URLs scraped: {stats['urls_scraped']}
   • URLs failed: {stats['urls_failed']}
   • Total chunks: {results['total_chunks']}
   • Total words: {stats['total_words']:,}
""")
    
    # Content type breakdown
    if stats.get('content_types'):
        print("📚 Content Types Found:")
        for content_type, count in stats['content_types'].items():
            print(f"   • {content_type.replace('_', ' ').title()}: {count} chunks")
        print()
    
    # Export in additional formats if requested
    if args.export_all:
        print("📦 Exporting in all formats...")
        exporter = DataExporter(config.output_dir)
        exported_files = exporter.export_all_formats(results)
        
        print("📁 Exported files:")
        for export_type, filepath in exported_files.items():
            print(f"   • {export_type}: {filepath}")
        print()
    
    print(f"📁 All output saved to: {config.output_dir}/")
    return True

def analyze_results(args):
    """Analyze previously scraped results"""
    import json
    
    results_file = Path(args.results_file)
    if not results_file.exists():
        print(f"❌ Results file not found: {results_file}")
        return False
    
    print(f"📊 Analyzing results from: {results_file}")
    
    with open(results_file, 'r', encoding='utf-8') as f:
        results = json.load(f)
    
    # Basic statistics
    chunks = results.get('chunks', [])
    stats = results.get('session_stats', {})
    
    print(f"""
📈 Analysis Results:
   • Total chunks: {len(chunks)}
   • Total words: {sum(chunk.get('word_count', 0) for chunk in chunks):,}
   • Average chunk size: {sum(chunk.get('word_count', 0) for chunk in chunks) / len(chunks):.0f} words
   • Scraped URLs: {len(results.get('scraped_urls', []))}
""")
    
    # Content type analysis
    content_types = {}
    for chunk in chunks:
        ct = chunk.get('content_type', 'unknown')
        content_types[ct] = content_types.get(ct, 0) + 1
    
    print("📚 Content Type Distribution:")
    for ct, count in sorted(content_types.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / len(chunks)) * 100
        print(f"   • {ct.replace('_', ' ').title()}: {count} chunks ({percentage:.1f}%)")
    
    # Export analysis if requested
    if args.export_analysis:
        exporter = DataExporter(Path(results_file).parent)
        analysis_files = exporter.export_all_formats(results)
        print(f"\n📁 Analysis exported to: {len(analysis_files)} files")
    
    return True

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Aven Support Scraper - Intelligent web scraping using Exa.ai",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s scrape                        # Basic scraping
  %(prog)s scrape --max-pages 100        # Scrape up to 100 pages
  %(prog)s scrape --export-all           # Scrape and export all formats
  %(prog)s analyze results.json          # Analyze previous results
  %(prog)s validate                      # Check configuration
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Scrape command
    scrape_parser = subparsers.add_parser('scrape', help='Run the scraper')
    scrape_parser.add_argument('--api-key', help='Exa.ai API key (overrides config)')
    scrape_parser.add_argument('--max-pages', type=int, help='Maximum pages to scrape')
    scrape_parser.add_argument('--output-dir', help='Output directory')
    scrape_parser.add_argument('--chunk-size', type=int, help='Text chunk size')
    scrape_parser.add_argument('--export-all', action='store_true', 
                               help='Export results in all available formats')
    scrape_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze scraped results')
    analyze_parser.add_argument('results_file', help='Path to results JSON file')
    analyze_parser.add_argument('--export-analysis', action='store_true',
                                help='Export analysis in multiple formats')
    analyze_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate configuration')
    validate_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    # Config command
    config_parser = subparsers.add_parser('config', help='Show current configuration')
    
    args = parser.parse_args()
    
    # Show banner
    print_banner()
    
    # Setup logging
    setup_logging(getattr(args, 'verbose', False))
    
    # Handle commands
    if args.command == 'scrape':
        print_config_info()
        if not validate_setup():
            return 1
        
        if run_scraper(args):
            return 0
        else:
            return 1
            
    elif args.command == 'analyze':
        setup_logging(args.verbose)
        if analyze_results(args):
            return 0
        else:
            return 1
            
    elif args.command == 'validate':
        print_config_info()
        if validate_setup():
            return 0
        else:
            return 1
            
    elif args.command == 'config':
        print_config_info()
        return 0
        
    else:
        parser.print_help()
        return 1

if __name__ == "__main__":
    sys.exit(main()) 