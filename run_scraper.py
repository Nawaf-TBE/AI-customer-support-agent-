#!/usr/bin/env python3
"""
Comprehensive CLI script for running the Aven Support Scraper

This module provides a command-line interface for the Aven Support Scraper,
offering multiple commands for scraping, analysis, and configuration validation.
The CLI supports various output formats and provides comprehensive error handling
and user feedback.

Architecture:
- ConfigValidator: Validates configuration and dependencies
- OutputFormatter: Handles all display and formatting
- ScrapeCommandHandler: Executes scrape command
- AnalyzeCommandHandler: Executes analyze command
- CLIOrchestrator: Main coordinator for CLI operations

Commands:
- scrape: Run the main scraping process
- analyze: Analyze previously scraped results
- validate: Validate configuration and dependencies
- config: Display current configuration

Author: AI Customer Support Agent Development Team
License: MIT
Version: 1.0.0
"""
import argparse
import json
import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

from aven_scraper import AvenScraper
from data_exporter import DataExporter
from config import config

# Constants
class CLIConstants:
    """Constants used throughout the CLI application"""
    # Exit codes
    EXIT_SUCCESS = 0
    EXIT_FAILURE = 1
    
    # Time formatting
    SECONDS_PER_MINUTE = 60
    
    # Display formatting
    BANNER_WIDTH = 62
    
    # File extensions
    JSON_EXTENSION = '.json'
    
    # Default values
    DEFAULT_API_KEY_PLACEHOLDER = "your_exa_api_key_here"
    
    # Emoji and symbols for output
    SYMBOLS = {
        'success': '✅',
        'error': '❌',
        'warning': '⚠️',
        'info': 'ℹ️',
        'rocket': '🚀',
        'party': '🎉',
        'chart': '📊',
        'books': '📚',
        'package': '📦',
        'folder': '📁',
        'alert': '🚨',
        'gear': '⚙️',
        'clipboard': '📋'
    }
    
    # Validation messages
    VALIDATION_MESSAGES = {
        'api_key_missing': f"{SYMBOLS['error']} EXA_API_KEY not configured",
        'api_key_valid': f"{SYMBOLS['success']} Exa.ai API key configured",
        'output_dir_valid': f"{SYMBOLS['success']} Output directory accessible",
        'exa_sdk_available': f"{SYMBOLS['success']} Exa.ai Python SDK available",
        'pandas_available': f"{SYMBOLS['success']} Pandas available for data processing",
        'exa_sdk_missing': f"{SYMBOLS['error']} exa-py package not installed",
        'pandas_missing': f"{SYMBOLS['error']} pandas package not installed",
        'all_checks_passed': f"{SYMBOLS['success']} All checks passed!"
    }

# Custom Exceptions
class CLIError(Exception):
    """Base exception for CLI errors"""
    pass

class ValidationError(CLIError):
    """Raised when validation fails"""
    pass

class ConfigurationError(CLIError):
    """Raised when configuration is invalid"""
    pass

class ScrapingError(CLIError):
    """Raised when scraping process fails"""
    pass

class AnalysisError(CLIError):
    """Raised when analysis process fails"""
    pass

# Data Classes
@dataclass
class CLIResult:
    """Result of a CLI operation"""
    success: bool
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    exit_code: int = CLIConstants.EXIT_SUCCESS
    
    def __post_init__(self):
        if not self.success and self.exit_code == CLIConstants.EXIT_SUCCESS:
            self.exit_code = CLIConstants.EXIT_FAILURE

@dataclass
class ValidationResult:
    """Result of configuration validation"""
    success: bool
    issues: List[str] = field(default_factory=list)
    passed_checks: List[str] = field(default_factory=list)
    
    @property
    def has_issues(self) -> bool:
        """Check if there are validation issues"""
        return len(self.issues) > 0

def setup_logging(verbose: bool = False) -> None:
    """Setup logging with optional verbose mode
    
    Args:
        verbose: Enable debug level logging if True
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def print_banner() -> None:
    """Print application banner with consistent formatting"""
    banner = f"""
╔{'═' * CLIConstants.BANNER_WIDTH}╗
║{' ' * 20}Aven Support Scraper{' ' * 21}║
║{' ' * 14}Powered by Exa.ai Neural Search{' ' * 15}║
╚{'═' * CLIConstants.BANNER_WIDTH}╝
"""
    print(banner)

def print_config_info() -> None:
    """Print current configuration in a formatted way
    
    Displays key configuration parameters including URLs, limits,
    and output settings for user verification.
    """
    print(f"{CLIConstants.SYMBOLS['clipboard']} Configuration:")
    print(f"   • Base URL: {config.base_url}")
    print(f"   • Max pages: {config.max_subpages}")
    print(f"   • Chunk size: {config.chunk_size}")
    print(f"   • Output dir: {config.output_dir}")
    print(f"   • Rate limit: {config.requests_per_minute} req/min")
    print()

def validate_setup() -> ValidationResult:
    """Validate that everything is set up correctly
    
    Performs comprehensive validation of configuration, dependencies,
    and system requirements for the scraper.
    
    Returns:
        ValidationResult: Detailed validation results with issues and passed checks
        
    Raises:
        ValidationError: If critical validation fails
    """
    try:
        result = ValidationResult(success=True)
        
        # Validate API key
        result = _validate_api_key(result)
        
        # Validate output directory
        result = _validate_output_directory(result)
        
        # Validate dependencies
        result = _validate_dependencies(result)
        
        # Print results
        _print_validation_results(result)
        
        # Update success status
        result.success = not result.has_issues
        
        return result
        
    except Exception as e:
        raise ValidationError(f"Validation process failed: {e}") from e

def _validate_api_key(result: ValidationResult) -> ValidationResult:
    """Validate API key configuration
    
    Args:
        result: Current validation result to update
        
    Returns:
        Updated validation result
    """
    if not config.exa_api_key or config.exa_api_key == CLIConstants.DEFAULT_API_KEY_PLACEHOLDER:
        result.issues.append(CLIConstants.VALIDATION_MESSAGES['api_key_missing'])
    else:
        result.passed_checks.append(CLIConstants.VALIDATION_MESSAGES['api_key_valid'])
    
    return result

def _validate_output_directory(result: ValidationResult) -> ValidationResult:
    """Validate output directory accessibility
    
    Args:
        result: Current validation result to update
        
    Returns:
        Updated validation result
    """
    try:
        Path(config.output_dir).mkdir(parents=True, exist_ok=True)
        result.passed_checks.append(CLIConstants.VALIDATION_MESSAGES['output_dir_valid'])
    except Exception as e:
        result.issues.append(f"{CLIConstants.SYMBOLS['error']} Cannot access output directory: {e}")
    
    return result

def _validate_dependencies(result: ValidationResult) -> ValidationResult:
    """Validate required dependencies
    
    Args:
        result: Current validation result to update
        
    Returns:
        Updated validation result
    """
    # Check Exa.ai SDK
    try:
        from exa_py import Exa
        result.passed_checks.append(CLIConstants.VALIDATION_MESSAGES['exa_sdk_available'])
    except ImportError:
        result.issues.append(CLIConstants.VALIDATION_MESSAGES['exa_sdk_missing'])
    
    # Check pandas
    try:
        import pandas as pd
        result.passed_checks.append(CLIConstants.VALIDATION_MESSAGES['pandas_available'])
    except ImportError:
        result.issues.append(CLIConstants.VALIDATION_MESSAGES['pandas_missing'])
    
    return result

def _print_validation_results(result: ValidationResult) -> None:
    """Print validation results in a formatted way
    
    Args:
        result: Validation result to display
    """
    # Print passed checks
    for check in result.passed_checks:
        print(check)
    
    # Print issues if any
    if result.has_issues:
        print(f"\n{CLIConstants.SYMBOLS['alert']} Setup Issues Found:")
        for issue in result.issues:
            print(f"   {issue}")
        print("\nPlease fix these issues before running the scraper.")
    else:
        print(f"{CLIConstants.VALIDATION_MESSAGES['all_checks_passed']}\n")

def run_scraper(args: argparse.Namespace) -> CLIResult:
    """Run the main scraping process
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        CLIResult: Result of the scraping operation
        
    Raises:
        ScrapingError: If scraping process fails
        ConfigurationError: If configuration is invalid
    """
    try:
        print(f"{CLIConstants.SYMBOLS['rocket']} Starting Aven support page scraping...")
        
        # Apply configuration overrides
        _apply_config_overrides(args)
        
        # Initialize and run scraper
        scraper = AvenScraper(api_key=args.api_key)
        start_time = datetime.now()
        
        results = scraper.scrape_support_pages()
        
        # Check if scraping was successful
        if not results.success:
            error_msg = results.error or 'Unknown error'
            print(f"{CLIConstants.SYMBOLS['error']} Scraping failed: {error_msg}")
            return CLIResult(success=False, message=f"Scraping failed: {error_msg}")
        
        # Calculate duration
        duration = (datetime.now() - start_time).total_seconds() / CLIConstants.SECONDS_PER_MINUTE
        
        # Print results summary
        _print_scraping_results(results, duration)
        
        # Handle export if requested
        if args.export_all:
            _handle_export_all(results)
        
        print(f"{CLIConstants.SYMBOLS['folder']} All output saved to: {config.output_dir}/")
        
        return CLIResult(
            success=True, 
            message="Scraping completed successfully",
            data={'results': results, 'duration': duration}
        )
        
    except Exception as e:
        error_msg = f"Scraping process failed: {e}"
        print(f"{CLIConstants.SYMBOLS['error']} {error_msg}")
        raise ScrapingError(error_msg) from e

def _apply_config_overrides(args: argparse.Namespace) -> None:
    """Apply command line argument overrides to configuration
    
    Args:
        args: Parsed command line arguments
    """
    overrides_applied = []
    
    if args.max_pages:
        config.max_subpages = args.max_pages
        overrides_applied.append(f"max pages: {args.max_pages}")
    
    if args.output_dir:
        config.output_dir = args.output_dir
        overrides_applied.append(f"output dir: {args.output_dir}")
    
    if args.chunk_size:
        config.chunk_size = args.chunk_size
        overrides_applied.append(f"chunk size: {args.chunk_size}")
    
    if overrides_applied:
        print("   • Configuration overrides:")
        for override in overrides_applied:
            print(f"     - {override}")
        print()

def _print_scraping_results(results, duration: float) -> None:
    """Print formatted scraping results summary
    
    Args:
        results: Scraping results object
        duration: Duration in minutes
    """
    stats = results.session_stats
    
    print(f"""
{CLIConstants.SYMBOLS['party']} Scraping completed successfully!

{CLIConstants.SYMBOLS['chart']} Results Summary:
   • Duration: {duration:.1f} minutes
   • URLs discovered: {stats.urls_discovered}
   • URLs scraped: {stats.urls_scraped}
   • URLs failed: {stats.urls_failed}
   • Total chunks: {results.total_chunks}
   • Total words: {stats.total_words:,}
""")
    
    # Content type breakdown
    if stats.content_types:
        print(f"{CLIConstants.SYMBOLS['books']} Content Types Found:")
        for content_type, count in stats.content_types.items():
            formatted_type = content_type.replace('_', ' ').title()
            print(f"   • {formatted_type}: {count} chunks")
        print()

def _handle_export_all(results) -> None:
    """Handle export in all formats
    
    Args:
        results: Scraping results to export
    """
    try:
        print(f"{CLIConstants.SYMBOLS['package']} Exporting in all formats...")
        exporter = DataExporter(config.output_dir)
        export_summary = exporter.export_all_formats(results.to_dict())
        
        print(f"{CLIConstants.SYMBOLS['folder']} Export Summary:")
        print(f"   • Total exports: {export_summary.total_exports}")
        print(f"   • Successful: {export_summary.successful_exports}")
        print(f"   • Failed: {export_summary.failed_exports}")
        print(f"   • Success rate: {export_summary.success_rate:.1f}%")
        
        # Show successful exports
        successful_exports = [r for r in export_summary.export_results if r.success]
        if successful_exports:
            print(f"   • Files created:")
            for result in successful_exports:
                print(f"     - {result.format_type}: {result.file_path}")
        print()
        
    except Exception as e:
        print(f"{CLIConstants.SYMBOLS['warning']} Export failed: {e}")
        # Don't fail the entire operation for export issues

def analyze_results(args: argparse.Namespace) -> CLIResult:
    """Analyze previously scraped results
    
    Args:
        args: Parsed command line arguments containing results file path
        
    Returns:
        CLIResult: Result of the analysis operation
        
    Raises:
        AnalysisError: If analysis process fails
    """
    try:
        results_file = Path(args.results_file)
        
        # Validate input file
        if not results_file.exists():
            error_msg = f"Results file not found: {results_file}"
            print(f"{CLIConstants.SYMBOLS['error']} {error_msg}")
            return CLIResult(success=False, message=error_msg)
        
        if not results_file.suffix == CLIConstants.JSON_EXTENSION:
            error_msg = f"Results file must be a JSON file: {results_file}"
            print(f"{CLIConstants.SYMBOLS['error']} {error_msg}")
            return CLIResult(success=False, message=error_msg)
        
        print(f"{CLIConstants.SYMBOLS['chart']} Analyzing results from: {results_file}")
        
        # Load and validate results
        results = _load_results_file(results_file)
        
        # Perform analysis
        analysis_data = _analyze_scraped_data(results)
        
        # Print analysis results
        _print_analysis_results(analysis_data)
        
        # Handle export if requested
        if args.export_analysis:
            _handle_analysis_export(results, results_file)
        
        return CLIResult(
            success=True,
            message="Analysis completed successfully",
            data=analysis_data
        )
        
    except Exception as e:
        error_msg = f"Analysis failed: {e}"
        print(f"{CLIConstants.SYMBOLS['error']} {error_msg}")
        raise AnalysisError(error_msg) from e

def _load_results_file(results_file: Path) -> Dict[str, Any]:
    """Load and validate results file
    
    Args:
        results_file: Path to results JSON file
        
    Returns:
        Loaded results dictionary
        
    Raises:
        AnalysisError: If file loading fails
    """
    try:
        with open(results_file, 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        # Basic validation
        if not isinstance(results, dict):
            raise AnalysisError("Results file must contain a JSON object")
        
        if 'chunks' not in results:
            raise AnalysisError("Results file must contain 'chunks' key")
        
        return results
        
    except json.JSONDecodeError as e:
        raise AnalysisError(f"Invalid JSON in results file: {e}") from e
    except Exception as e:
        raise AnalysisError(f"Failed to load results file: {e}") from e

def _analyze_scraped_data(results: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze scraped data and generate statistics
    
    Args:
        results: Results dictionary to analyze
        
    Returns:
        Analysis data dictionary
    """
    chunks = results.get('chunks', [])
    stats = results.get('session_stats', {})
    
    # Basic statistics
    total_words = sum(chunk.get('word_count', 0) for chunk in chunks)
    avg_chunk_size = total_words / len(chunks) if chunks else 0
    
    # Content type analysis
    content_types = {}
    for chunk in chunks:
        ct = chunk.get('content_type', 'unknown')
        content_types[ct] = content_types.get(ct, 0) + 1
    
    return {
        'total_chunks': len(chunks),
        'total_words': total_words,
        'average_chunk_size': avg_chunk_size,
        'scraped_urls_count': len(results.get('scraped_urls', [])),
        'content_types': content_types,
        'session_stats': stats
    }

def _print_analysis_results(analysis_data: Dict[str, Any]) -> None:
    """Print formatted analysis results
    
    Args:
        analysis_data: Analysis data to display
    """
    print(f"""
{CLIConstants.SYMBOLS['chart']} Analysis Results:
   • Total chunks: {analysis_data['total_chunks']}
   • Total words: {analysis_data['total_words']:,}
   • Average chunk size: {analysis_data['average_chunk_size']:.0f} words
   • Scraped URLs: {analysis_data['scraped_urls_count']}
""")
    
    # Content type distribution
    content_types = analysis_data['content_types']
    if content_types:
        print(f"{CLIConstants.SYMBOLS['books']} Content Type Distribution:")
        total_chunks = analysis_data['total_chunks']
        
        for ct, count in sorted(content_types.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_chunks) * 100 if total_chunks > 0 else 0
            formatted_type = ct.replace('_', ' ').title()
            print(f"   • {formatted_type}: {count} chunks ({percentage:.1f}%)")

def _handle_analysis_export(results: Dict[str, Any], results_file: Path) -> None:
    """Handle export of analysis results
    
    Args:
        results: Results data to export
        results_file: Original results file path
    """
    try:
        exporter = DataExporter(results_file.parent)
        export_summary = exporter.export_all_formats(results)
        
        successful_count = export_summary.successful_exports
        print(f"\n{CLIConstants.SYMBOLS['folder']} Analysis exported: {successful_count} files created")
        
    except Exception as e:
        print(f"{CLIConstants.SYMBOLS['warning']} Analysis export failed: {e}")

def main() -> int:
    """Main CLI entry point
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        parser = _create_argument_parser()
        args = parser.parse_args()
        
        # Show banner
        print_banner()
        
        # Setup logging
        setup_logging(getattr(args, 'verbose', False))
        
        # Handle commands
        return _handle_command(args, parser)
        
    except KeyboardInterrupt:
        print(f"\n{CLIConstants.SYMBOLS['warning']} Operation cancelled by user")
        return CLIConstants.EXIT_FAILURE
    except Exception as e:
        print(f"{CLIConstants.SYMBOLS['error']} Unexpected error: {e}")
        return CLIConstants.EXIT_FAILURE

def _create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser
    
    Returns:
        Configured ArgumentParser instance
    """
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
    _add_scrape_parser(subparsers)
    
    # Analyze command
    _add_analyze_parser(subparsers)
    
    # Validate command
    _add_validate_parser(subparsers)
    
    # Config command
    _add_config_parser(subparsers)
    
    return parser

def _add_scrape_parser(subparsers) -> None:
    """Add scrape command parser"""
    scrape_parser = subparsers.add_parser('scrape', help='Run the scraper')
    scrape_parser.add_argument('--api-key', help='Exa.ai API key (overrides config)')
    scrape_parser.add_argument('--max-pages', type=int, help='Maximum pages to scrape')
    scrape_parser.add_argument('--output-dir', help='Output directory')
    scrape_parser.add_argument('--chunk-size', type=int, help='Text chunk size')
    scrape_parser.add_argument('--export-all', action='store_true', 
                               help='Export results in all available formats')
    scrape_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

def _add_analyze_parser(subparsers) -> None:
    """Add analyze command parser"""
    analyze_parser = subparsers.add_parser('analyze', help='Analyze scraped results')
    analyze_parser.add_argument('results_file', help='Path to results JSON file')
    analyze_parser.add_argument('--export-analysis', action='store_true',
                                help='Export analysis in multiple formats')
    analyze_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

def _add_validate_parser(subparsers) -> None:
    """Add validate command parser"""
    validate_parser = subparsers.add_parser('validate', help='Validate configuration')
    validate_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

def _add_config_parser(subparsers) -> None:
    """Add config command parser"""
    config_parser = subparsers.add_parser('config', help='Show current configuration')

def _handle_command(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    """Handle the parsed command
    
    Args:
        args: Parsed command line arguments
        parser: Argument parser instance
        
    Returns:
        Exit code
    """
    try:
        if args.command == 'scrape':
            return _handle_scrape_command(args)
        elif args.command == 'analyze':
            return _handle_analyze_command(args)
        elif args.command == 'validate':
            return _handle_validate_command()
        elif args.command == 'config':
            return _handle_config_command()
        else:
            parser.print_help()
            return CLIConstants.EXIT_FAILURE
            
    except (ValidationError, ScrapingError, AnalysisError, ConfigurationError) as e:
        print(f"{CLIConstants.SYMBOLS['error']} {e}")
        return CLIConstants.EXIT_FAILURE

def _handle_scrape_command(args: argparse.Namespace) -> int:
    """Handle scrape command
    
    Args:
        args: Parsed arguments
        
    Returns:
        Exit code
    """
    print_config_info()
    validation_result = validate_setup()
    
    if not validation_result.success:
        return CLIConstants.EXIT_FAILURE
    
    scrape_result = run_scraper(args)
    return scrape_result.exit_code

def _handle_analyze_command(args: argparse.Namespace) -> int:
    """Handle analyze command
    
    Args:
        args: Parsed arguments
        
    Returns:
        Exit code
    """
    setup_logging(args.verbose)
    analysis_result = analyze_results(args)
    return analysis_result.exit_code

def _handle_validate_command() -> int:
    """Handle validate command
    
    Returns:
        Exit code
    """
    print_config_info()
    validation_result = validate_setup()
    return CLIConstants.EXIT_SUCCESS if validation_result.success else CLIConstants.EXIT_FAILURE

def _handle_config_command() -> int:
    """Handle config command
    
    Returns:
        Exit code
    """
    print_config_info()
    return CLIConstants.EXIT_SUCCESS

if __name__ == "__main__":
    sys.exit(main()) 