"""
 Configuration module for Aven Support Scraper ...TODO: add description
"""
import os
from typing import List, Optional
try:
    from pydantic_settings import BaseSettings
    from pydantic import Field
except ImportError:
    from pydantic import BaseSettings, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ScrapingConfig(BaseSettings):
    """ Configuration for the Aven support scraper"""
    
    # API Configuration
    exa_api_key: str = Field(..., env="EXA_API_KEY")
    
    # Target Configuration
    base_url: str = "https://www.aven.com/support"
    domain: str = "aven.com"
    
    # Scraping Parameters
    max_subpages: int = Field(default=50, env="MAX_SUBPAGES")
    requests_per_minute: int = Field(default=30, env="REQUESTS_PER_MINUTE")
    max_retries: int = Field(default=3, env="MAX_RETRIES")
    timeout_seconds: int = Field(default=30, env="TIMEOUT_SECONDS")
    
    # Content Processing
    chunk_size: int = Field(default=1000, env="CHUNK_SIZE")
    overlap_size: int = Field(default=100, env="OVERLAP_SIZE")
    min_chunk_size: int = Field(default=100, env="MIN_CHUNK_SIZE")
    
    # Target Content Types
    target_content: List[str] = Field(default=[
        "faq", "guide", "tutorial", "help", "support", "documentation",
        "troubleshooting", "getting started", "how to", "setup", "installation"
    ])
    
    # Output Configuration
    output_dir: str = Field(default="./scraped_data", env="OUTPUT_DIR")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    save_raw_html: bool = Field(default=False, env="SAVE_RAW_HTML")
    
    # Exa.ai Specific Settings
    search_type: str = "neural"  # neural, keyword, or auto
    use_autoprompt: bool = True
    highlights_per_url: int = 3
    num_sentences_per_highlight: int = 5
    
    # Content Filtering
    exclude_patterns: List[str] = Field(default=[
        "privacy-policy", "terms-of-service", "cookie-policy",
        "legal", "careers", "about-us", "contact", "blog"
    ])
    
    include_domains: List[str] = Field(default=["aven.com", "support.aven.com"])
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global configuration instance
config = ScrapingConfig()

def get_output_paths():
    """Get all output file paths"""
    base_dir = config.output_dir
    os.makedirs(base_dir, exist_ok=True)
    os.makedirs(f"{base_dir}/content_chunks", exist_ok=True)
    
    return {
        "raw_data": f"{base_dir}/aven_support_raw.json",
        "processed_data": f"{base_dir}/aven_support_processed.json",
        "summary_csv": f"{base_dir}/aven_support_summary.csv",
        "chunks_dir": f"{base_dir}/content_chunks",
        "metadata": f"{base_dir}/scraping_metadata.json",
        "logs": f"{base_dir}/scraping.log"
    }

def validate_config():
    """Validate configuration settings"""
    if not config.exa_api_key or config.exa_api_key == "your_exa_api_key_here":
        raise ValueError("EXA_API_KEY must be set in environment or .env file")
    
    if config.chunk_size < config.min_chunk_size:
        raise ValueError(f"chunk_size ({config.chunk_size}) must be >= min_chunk_size ({config.min_chunk_size})")
    
    if config.overlap_size >= config.chunk_size:
        raise ValueError(f"overlap_size ({config.overlap_size}) must be < chunk_size ({config.chunk_size})")
    
    return True 

# TODO: add description
