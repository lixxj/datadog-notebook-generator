#!/usr/bin/env python3
"""
Test script to verify the notebook generator setup
Run this script to check if all components are working correctly
"""

import sys
import os
from pathlib import Path

def test_imports():
    """Test if all required modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        import openai
        print("✅ OpenAI module imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import OpenAI: {e}")
        return False
    
    try:
        import requests
        print("✅ Requests module imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import requests: {e}")
        return False
    
    try:
        import fastapi
        print("✅ FastAPI module imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import FastAPI: {e}")
        return False
    
    try:
        import aiofiles
        print("✅ Aiofiles module imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import aiofiles: {e}")
        return False
    
    return True

def test_configuration():
    """Test configuration loading"""
    print("\n🔧 Testing configuration...")
    
    # Try to import config
    try:
        import config
        print("✅ Config file found and imported")
        
        # Check required fields
        required_fields = ['OPENAI_API_KEY', 'DATADOG_API_KEY', 'DATADOG_APP_KEY']
        for field in required_fields:
            if hasattr(config, field) and getattr(config, field):
                print(f"✅ {field} configured")
            else:
                print(f"⚠️  {field} not configured or empty")
                
    except ImportError:
        print("⚠️  Config file not found, will use environment variables")
        
        # Check environment variables
        required_env_vars = ['OPENAI_API_KEY', 'DATADOG_API_KEY', 'DATADOG_APP_KEY']
        for var in required_env_vars:
            if os.getenv(var):
                print(f"✅ {var} environment variable set")
            else:
                print(f"⚠️  {var} environment variable not set")

def test_components():
    """Test individual components"""
    print("\n🧪 Testing components...")
    
    # Test notebook generator
    try:
        from notebook_generator import NotebookGenerator
        print("✅ NotebookGenerator class imported successfully")
        
        # Try to initialize (will fail without API key, but that's expected)
        try:
            import config
            if hasattr(config, 'OPENAI_API_KEY') and config.OPENAI_API_KEY:
                generator = NotebookGenerator(config.OPENAI_API_KEY)
                print("✅ NotebookGenerator initialized successfully")
            else:
                print("⚠️  NotebookGenerator not tested - no OpenAI API key")
        except:
            openai_key = os.getenv('OPENAI_API_KEY')
            if openai_key:
                generator = NotebookGenerator(openai_key)
                print("✅ NotebookGenerator initialized successfully")
            else:
                print("⚠️  NotebookGenerator not tested - no OpenAI API key")
                
    except Exception as e:
        print(f"❌ Failed to import/initialize NotebookGenerator: {e}")
    
    # Test Datadog client
    try:
        from datadog_client import DatadogClient
        print("✅ DatadogClient class imported successfully")
        
        # Try to initialize
        try:
            import config
            if (hasattr(config, 'DATADOG_API_KEY') and config.DATADOG_API_KEY and
                hasattr(config, 'DATADOG_APP_KEY') and config.DATADOG_APP_KEY):
                client = DatadogClient(config.DATADOG_API_KEY, config.DATADOG_APP_KEY)
                print("✅ DatadogClient initialized successfully")
            else:
                print("⚠️  DatadogClient not tested - missing Datadog credentials")
        except:
            api_key = os.getenv('DATADOG_API_KEY')
            app_key = os.getenv('DATADOG_APP_KEY')
            if api_key and app_key:
                client = DatadogClient(api_key, app_key)
                print("✅ DatadogClient initialized successfully")
            else:
                print("⚠️  DatadogClient not tested - missing Datadog credentials")
                
    except Exception as e:
        print(f"❌ Failed to import/initialize DatadogClient: {e}")
    
    # Test frontend static files
    print("🎨 Checking frontend static files...")
    static_files = [
        'static/index.html',
        'static/css/style.css',
        'static/js/app.js'
    ]
    
    for file_path in static_files:
        if Path(file_path).exists():
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} missing")

def test_files():
    """Test required files exist"""
    print("\n📁 Testing required files...")
    
    required_files = [
        'main.py',
        'notebook_generator.py', 
        'datadog_client.py',
        'requirements.txt',
        'NotebookExample1.json',
        'config.example.py',
        'static/index.html',
        'static/css/style.css',
        'static/js/app.js'
    ]
    
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} missing")

def test_example_notebook():
    """Test example notebook loading"""
    print("\n📊 Testing example notebook...")
    
    try:
        import json
        with open('NotebookExample1.json', 'r') as f:
            notebook = json.load(f)
        
        # Basic structure validation
        if 'data' in notebook and 'attributes' in notebook['data']:
            print("✅ Example notebook has valid structure")
            
            attrs = notebook['data']['attributes']
            if 'name' in attrs and 'cells' in attrs:
                print(f"✅ Notebook has name: '{attrs['name']}'")
                print(f"✅ Notebook has {len(attrs['cells'])} cells")
            else:
                print("⚠️  Notebook missing required attributes")
        else:
            print("❌ Example notebook has invalid structure")
            
    except FileNotFoundError:
        print("❌ NotebookExample1.json not found")
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in example notebook: {e}")
    except Exception as e:
        print(f"❌ Error reading example notebook: {e}")

def main():
    """Run all tests"""
    print("🚀 Testing Datadog Notebook Generator Setup\n")
    
    # Run all tests
    tests_passed = 0
    total_tests = 5
    
    if test_imports():
        tests_passed += 1
    
    test_configuration()
    test_components() 
    test_files()
    test_example_notebook()
    
    print(f"\n📈 Test Results: Basic imports passed ({tests_passed}/{total_tests})")
    
    if tests_passed == total_tests:
        print("🎉 Setup looks good! You can now run the application with: python main.py")
    else:
        print("⚠️  Some issues found. Please check the errors above and:")
        print("   1. Install missing dependencies: pip install -r requirements.txt")
        print("   2. Configure your API keys in config.py")
        print("   3. Ensure all required files are present")
    
    print("\n💡 Next steps:")
    print("   1. Configure your API keys in config.py")
    print("   2. Run the application: python main.py")
    print("   3. Open http://localhost:8000 in your browser")
    print("   4. Try generating a notebook!")

if __name__ == "__main__":
    main() 