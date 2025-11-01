#!/usr/bin/env python3
"""
Quick launcher script for the eBay Card Scraper GUI
"""

import sys
import os
import subprocess

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import customtkinter
        import scrapy
        return True
    except ImportError:
        return False

def install_dependencies():
    """Install required dependencies"""
    print("Installing dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    print("Dependencies installed successfully!")

def main():
    """Main launcher function"""
    print("=" * 60)
    print("eBay Card Scraper - GUI Launcher")
    print("=" * 60)
    
    # Check dependencies
    if not check_dependencies():
        print("\n⚠️  Missing dependencies detected!")
        response = input("Would you like to install them now? (y/n): ")
        if response.lower() == 'y':
            try:
                install_dependencies()
            except Exception as e:
                print(f"❌ Failed to install dependencies: {e}")
                print("\nPlease run: pip install -r requirements.txt")
                sys.exit(1)
        else:
            print("\nPlease install dependencies manually:")
            print("  pip install -r requirements.txt")
            sys.exit(1)
    
    # Launch GUI
    print("\n✅ Starting GUI application...")
    print("=" * 60)
    
    try:
        from gui_app import main as gui_main
        gui_main()
    except Exception as e:
        print(f"\n❌ Error launching GUI: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
