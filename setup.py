#!/usr/bin/env python3
"""
Setup script for Aven Support Scraper
"""
import os
import sys
import subprocess
from pathlib import Path

def print_banner():
    print("""
╔══════════════════════════════════════════════════════════════╗
║                Aven Support Scraper Setup                   ║
║              Powered by Exa.ai Neural Search                ║
╚══════════════════════════════════════════════════════════════╝
""")

def install_dependencies():
    """Install required Python packages"""
    print("📦 Installing dependencies...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def create_env_file():
    """Create .env file from template"""
    print("\n🔧 Setting up configuration...")
    
    env_file = Path(".env")
    template_file = Path("config.template")
    
    if env_file.exists():
        response = input("⚠️  .env file already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("Keeping existing .env file.")
            return True
    
    if not template_file.exists():
        print("❌ config.template not found!")
        return False
    
    # Copy template to .env
    with open(template_file, 'r') as src, open(env_file, 'w') as dst:
        dst.write(src.read())
    
    print("✅ Created .env file from template")
    
    # Get API key from user
    api_key = input("\n🔑 Please enter your Exa.ai API key (or press Enter to skip): ").strip()
    
    if api_key:
        # Update .env file with API key
        with open(env_file, 'r') as f:
            content = f.read()
        
        content = content.replace('your_exa_api_key_here', api_key)
        
        with open(env_file, 'w') as f:
            f.write(content)
        
        print("✅ API key saved to .env file")
    else:
        print("⚠️  You can add your API key later by editing the .env file")
    
    return True

def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")
    
    directories = [
        "scraped_data",
        "scraped_data/content_chunks",
        "scraped_data/by_content_type"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created: {directory}/")
    
    return True

def verify_installation():
    """Verify that everything is installed correctly"""
    print("\n🔍 Verifying installation...")
    
    try:
        # Test imports
        import exa_py
        print("✅ exa-py package available")
        
        import pandas as pd
        print("✅ pandas package available")
        
        import beautifulsoup4
        print("✅ beautifulsoup4 package available")
        
        # Test configuration
        from config import config
        print("✅ Configuration module loaded")
        
        # Test content processor
        from content_processor import ContentProcessor
        print("✅ Content processor available")
        
        # Test main scraper
        from aven_scraper import AvenScraper
        print("✅ Main scraper available")
        
        print("\n🎉 Installation verified successfully!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

def show_next_steps():
    """Show user what to do next"""
    print("""
🚀 Setup Complete! Next Steps:

1. Configure your API key (if not done already):
   • Edit .env file and add your Exa.ai API key
   • Get a free API key at: https://dashboard.exa.ai/

2. Test the installation:
   python run_scraper.py validate

3. Run your first scrape:
   python run_scraper.py scrape --max-pages 10

4. View all available options:
   python run_scraper.py --help

📁 Output will be saved to: ./scraped_data/

Happy scraping! 🕷️
""")

def main():
    """Main setup function"""
    print_banner()
    
    success = True
    
    # Install dependencies
    if not install_dependencies():
        success = False
    
    # Create configuration
    if success and not create_env_file():
        success = False
    
    # Create directories
    if success and not create_directories():
        success = False
    
    # Verify installation
    if success and not verify_installation():
        success = False
    
    if success:
        show_next_steps()
        return 0
    else:
        print("\n❌ Setup encountered errors. Please check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 