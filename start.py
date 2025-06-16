#!/usr/bin/env python3
"""
Startup script for the Datadog Notebook Generator
This script provides an easy way to start the application
"""

import os
import sys
import subprocess

def check_config():
    """Check if configuration is available"""
    config_methods = []
    
    # Check for config file
    if os.path.exists('config.py'):
        config_methods.append("config.py file")
    
    # Check for environment variables
    env_vars = ['OPENAI_API_KEY', 'DATADOG_API_KEY', 'DATADOG_APP_KEY']
    if any(os.getenv(var) for var in env_vars):
        config_methods.append("environment variables")
    
    return config_methods

def main():
    """Main startup function"""
    print("🚀 Starting Datadog Notebook Generator")
    print("=" * 50)
    
    # Check configuration
    config_methods = check_config()
    
    if not config_methods:
        print("⚠️  No configuration found!")
        print("\n📝 To get started:")
        print("1. Copy the example config: cp config.example.py config.py")
        print("2. Edit config.py with your API keys")
        print("3. Or set environment variables:")
        print("   export OPENAI_API_KEY='your-openai-key'")
        print("   export DATADOG_API_KEY='your-datadog-api-key'")
        print("   export DATADOG_APP_KEY='your-datadog-app-key'")
        print("\n❓ Do you want to create config.py now? (y/n): ", end="")
        
        response = input().lower().strip()
        if response in ['y', 'yes']:
            try:
                # Copy config example
                with open('config.example.py', 'r') as src:
                    content = src.read()
                with open('config.py', 'w') as dst:
                    dst.write(content)
                print("✅ config.py created! Please edit it with your API keys.")
                print("💡 Then run this script again: python start.py")
                return
            except Exception as e:
                print(f"❌ Failed to create config.py: {e}")
                return
        else:
            print("👋 Setup cancelled. Configure your API keys and try again!")
            return
    else:
        print(f"✅ Configuration found via: {', '.join(config_methods)}")
    
    # Start the application
    print("\n🌐 Starting web server...")
    print("📍 Application will be available at: http://localhost:8000")
    print("🔄 Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        # Start uvicorn server
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000",
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        print("\n🔧 Try running manually:")
        print("   python main.py")
        print("   # or")
        print("   uvicorn main:app --reload")

if __name__ == "__main__":
    main() 