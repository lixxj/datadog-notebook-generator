#!/usr/bin/env python3
"""
Demo script showcasing the Notebook Generation functionality
Run this to see examples of generated notebooks
"""

import json
import os
from notebook_generator import NotebookGenerator
from datadog_client import DatadogClient

def demo_basic_generation():
    """Demo basic notebook generation without Datadog deployment"""
    print("🎯 Demo: Basic Notebook Generation")
    print("=" * 50)
    
    # Load configuration
    try:
        import config
        openai_key = config.OPENAI_API_KEY
    except ImportError:
        openai_key = os.getenv('OPENAI_API_KEY')
    
    if not openai_key:
        print("❌ OpenAI API key not configured. Please set it in config.py or as environment variable.")
        return
    
    # Initialize generator
    generator = NotebookGenerator(openai_key)
    
    # Demo requests
    demo_requests = [
        "Show CPU and memory usage for troubleshooting performance issues",
        "Monitor database connection pool metrics",
        "Create error rate analysis for web application",
        "Analyze disk I/O performance for storage optimization"
    ]
    
    for i, request in enumerate(demo_requests, 1):
        print(f"\n📝 Example {i}: {request}")
        print("-" * 60)
        
        try:
            # Generate notebook
            notebook = generator.generate_notebook(request)
            
            # Generate preview
            preview = generator.preview_notebook(notebook)
            print(preview)
            
            # Save to file for inspection
            filename = f"demo_notebook_{i}.json"
            with open(filename, 'w') as f:
                json.dump(notebook, f, indent=2)
            print(f"💾 Full JSON saved to: {filename}")
            
        except Exception as e:
            print(f"❌ Error generating notebook: {e}")
        
        print()

def demo_datadog_integration():
    """Demo Datadog integration (validation only, no actual creation)"""
    print("🐕 Demo: Datadog Integration")
    print("=" * 50)
    
    # Load configuration
    try:
        import config
        openai_key = config.OPENAI_API_KEY
        dd_api_key = config.DATADOG_API_KEY
        dd_app_key = config.DATADOG_APP_KEY
    except ImportError:
        openai_key = os.getenv('OPENAI_API_KEY')
        dd_api_key = os.getenv('DATADOG_API_KEY')
        dd_app_key = os.getenv('DATADOG_APP_KEY')
    
    if not all([openai_key, dd_api_key, dd_app_key]):
        print("❌ Missing API credentials. Datadog integration demo requires:")
        print("   - OPENAI_API_KEY")
        print("   - DATADOG_API_KEY") 
        print("   - DATADOG_APP_KEY")
        return
    
    # Initialize components
    generator = NotebookGenerator(openai_key)
    dd_client = DatadogClient(dd_api_key, dd_app_key)
    
    print("✅ Datadog client initialized")
    
    # Test connection
    connection_test = dd_client.test_connection()
    print(f"🔗 Connection test: {connection_test['status']} - {connection_test['message']}")
    
    # Generate a sample notebook
    request = "Show system performance metrics for production monitoring"
    print(f"\n📝 Generating notebook: {request}")
    
    try:
        notebook = generator.generate_notebook(request)
        
        # Validate structure
        validation = dd_client.validate_notebook_structure(notebook)
        print(f"\n✅ Validation result: {'Valid' if validation['valid'] else 'Invalid'}")
        
        if validation['errors']:
            print("❌ Validation errors:")
            for error in validation['errors']:
                print(f"   - {error}")
        
        if validation['warnings']:
            print("⚠️  Validation warnings:")
            for warning in validation['warnings']:
                print(f"   - {warning}")
        
        if validation['valid']:
            print("\n🎉 Notebook structure is valid and ready for Datadog deployment!")
            print("💡 To actually create in Datadog, use the web interface or set create_in_datadog=True")
        
        # Generate preview
        preview = generator.preview_notebook(notebook)
        print(f"\n📊 Notebook Preview:\n{preview}")
        
    except Exception as e:
        print(f"❌ Error in Datadog integration demo: {e}")

def demo_use_cases():
    """Demo different use cases"""
    print("🎯 Demo: Different Use Cases")
    print("=" * 50)
    
    use_cases = {
        "Support Case": "Investigate high memory usage on web servers causing timeouts",
        "Metric Demo": "Demonstrate metric rollup functions with 5m, 1h, and 1d windows",
        "Escalation": "Comprehensive analysis of database performance degradation incident",
        "Prototyping": "Quick monitoring setup for new microservice deployment"
    }
    
    # Load configuration
    try:
        import config
        openai_key = config.OPENAI_API_KEY
    except ImportError:
        openai_key = os.getenv('OPENAI_API_KEY')
    
    if not openai_key:
        print("❌ OpenAI API key not configured.")
        return
    
    generator = NotebookGenerator(openai_key)
    
    for use_case, request in use_cases.items():
        print(f"\n📋 {use_case}")
        print(f"Request: {request}")
        print("-" * 40)
        
        try:
            notebook = generator.generate_notebook(request)
            preview = generator.preview_notebook(notebook)
            
            # Show abbreviated preview
            lines = preview.split('\n')
            for line in lines[:8]:  # Show first few lines
                print(line)
            if len(lines) > 8:
                print("... (preview truncated)")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print()

def main():
    """Run all demos"""
    print("🚀 Datadog Notebook Generator - Demo")
    print("=" * 60)
    print("This demo showcases the notebook generation capabilities.")
    print("Make sure you have configured your API keys in config.py\n")
    
    # Run demos
    demo_basic_generation()
    print("\n" + "=" * 60 + "\n")
    
    demo_use_cases() 
    print("\n" + "=" * 60 + "\n")
    
    demo_datadog_integration()
    
    print("\n🎉 Demo completed!")
    print("\n💡 Next steps:")
    print("   1. Review the generated demo_notebook_*.json files")
    print("   2. Run the web application: python main.py")
    print("   3. Try the Slack integration")
    print("   4. Create notebooks in your Datadog organization")

if __name__ == "__main__":
    main() 