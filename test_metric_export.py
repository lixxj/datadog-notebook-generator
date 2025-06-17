"""
Test script for the Metric Export functionality
Demonstrates how to use the new GPT-based metric export service
"""

import json
import os
from notebook_generator import NotebookGenerator


def test_metric_export():
    """Test the metric export functionality"""
    print("🚀 Testing Metric Export Service")
    print("=" * 50)
    
    # Initialize with API key from environment or config
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        try:
            import config
            api_key = config.OPENAI_API_KEY
        except ImportError:
            print("❌ No API key found. Please set OPENAI_API_KEY environment variable or create config.py")
            return
    
    # Initialize notebook generator with metric export service
    generator = NotebookGenerator(api_key)
    
    # Test 1: Get GPT metric suggestions
    print("\n📊 Test 1: Getting GPT Metric Suggestions")
    print("-" * 40)
    
    user_request = "I want to monitor CPU and memory usage on my servers"
    suggestions = generator.get_gpt_metric_suggestions(user_request, limit=5)
    
    print(f"User request: {user_request}")
    print(f"GPT suggestions ({len(suggestions)} found):")
    for i, suggestion in enumerate(suggestions, 1):
        print(f"  {i}. {suggestion['name']}")
        print(f"     Description: {suggestion['description']}")
        print(f"     Type: {suggestion['type']}, Unit: {suggestion['unit']}")
        if 'relevance_score' in suggestion:
            print(f"     Relevance Score: {suggestion['relevance_score']}")
        print()
    
    # Test 2: Export metrics using GPT
    print("\n📈 Test 2: Exporting Metrics with GPT")
    print("-" * 40)
    
    metric_request = {
        "metric_names": ["system.cpu.user", "system.memory.used"],
        "time_range": "1h",
        "aggregation": "avg",
        "tags": {"host": "*"},
        "filters": {}
    }
    
    notebook_context = {
        "user_request": user_request,
        "difficulty_level": "intermediate",
        "target_audience": "developers"
    }
    
    print("Metric request:")
    print(json.dumps(metric_request, indent=2))
    
    # Validate request first
    validation = generator.validate_metric_export_request(metric_request)
    print(f"\nValidation result: {'✅ Valid' if validation['valid'] else '❌ Invalid'}")
    if validation['errors']:
        print("Errors:", validation['errors'])
    if validation['warnings']:
        print("Warnings:", validation['warnings'])
    
    if validation['valid']:
        print("\n🔄 Calling GPT model to export metrics...")
        
        try:
            exported_data = generator.export_metrics_with_gpt(metric_request, notebook_context)
            
            if exported_data.get('success'):
                print("✅ Metric export successful!")
                
                # Display summary
                summary = exported_data.get('summary', {})
                print(f"\n📋 Export Summary:")
                print(f"  Total series: {summary.get('total_series', 0)}")
                print(f"  Total data points: {summary.get('data_points_total', 0)}")
                
                for metric in summary.get('metrics', []):
                    print(f"\n  📊 {metric['name']}:")
                    print(f"    Unit: {metric['unit']}")
                    print(f"    Data points: {metric['data_points']}")
                    if metric['min_value'] is not None:
                        print(f"    Min: {metric['min_value']}")
                        print(f"    Max: {metric['max_value']}")
                        print(f"    Avg: {metric['avg_value']:.2f}")
                
                # Display visualization hints
                hints = exported_data.get('visualization_hints', {})
                print(f"\n🎨 Visualization Hints:")
                print(f"  Recommended charts: {hints.get('recommended_chart_types', [])}")
                print(f"  Color suggestions: {hints.get('color_suggestions', [])}")
                print(f"  Layout: {hints.get('layout_suggestions', {})}")
                
                # Test 3: Generate summary
                print("\n📊 Test 3: Generating Data Summary")
                print("-" * 40)
                
                raw_data = exported_data.get('data', {})
                detailed_summary = generator.get_metric_export_summary(raw_data)
                print("Detailed summary:")
                print(json.dumps(detailed_summary, indent=2, default=str))
                
            else:
                print("❌ Metric export failed!")
                print("Error:", exported_data.get('error', 'Unknown error'))
                
        except Exception as e:
            print(f"❌ Error during metric export: {e}")
    
    # Test 4: Integration with notebook generation
    print("\n📓 Test 4: Integration with Notebook Generation")
    print("-" * 40)
    
    print("Generating notebook with GPT metric data...")
    
    # Create advanced settings that include metric export
    advanced_settings = {
        "metric_names": "system.cpu.user,system.memory.used",
        "timeframes": "1h",
        "space_aggregation": "avg",
        "use_gpt_metrics": True  # Flag to indicate using GPT for metrics
    }
    
    try:
        notebook = generator.generate_notebook(
            user_request="Create a server monitoring dashboard with CPU and memory metrics",
            advanced_settings=advanced_settings
        )
        
        print("✅ Notebook generated successfully!")
        print(f"Notebook title: {notebook['data']['attributes']['name']}")
        print(f"Number of cells: {len(notebook['data']['attributes']['cells'])}")
        
        # Save the notebook for inspection
        with open('test_notebook_with_gpt_metrics.json', 'w') as f:
            json.dump(notebook, f, indent=2)
        print("📁 Notebook saved to 'test_notebook_with_gpt_metrics.json'")
        
    except Exception as e:
        print(f"❌ Error generating notebook: {e}")
    
    print("\n🎉 Test complete!")
    print("=" * 50)


def test_custom_model_endpoint():
    """Test with custom model endpoint (if available)"""
    print("\n🔧 Testing Custom Model Endpoint")
    print("=" * 50)
    
    # Example of how to use a custom trained model
    custom_endpoint = os.getenv('CUSTOM_MODEL_ENDPOINT')
    custom_api_key = os.getenv('CUSTOM_MODEL_API_KEY')
    
    if not custom_endpoint or not custom_api_key:
        print("ℹ️  Custom model endpoint not configured.")
        print("   Set CUSTOM_MODEL_ENDPOINT and CUSTOM_MODEL_API_KEY environment variables")
        print("   to test with a custom trained model.")
        return
    
    try:
        # Initialize with custom endpoint
        generator = NotebookGenerator(
            api_key=custom_api_key,
            model_endpoint=custom_endpoint,
            model_name="custom-datadog-model"
        )
        
        # Test with custom model
        metric_request = {
            "metric_names": ["custom.application.response_time"],
            "time_range": "24h",
            "aggregation": "avg"
        }
        
        print("Testing custom trained model...")
        result = generator.export_metrics_with_gpt(metric_request)
        
        if result.get('success'):
            print("✅ Custom model test successful!")
        else:
            print("❌ Custom model test failed!")
            
    except Exception as e:
        print(f"❌ Error testing custom model: {e}")


if __name__ == "__main__":
    test_metric_export()
    test_custom_model_endpoint() 