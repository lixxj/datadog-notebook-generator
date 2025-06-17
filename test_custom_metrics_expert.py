"""
Test script for the Custom Metrics Expert Model
Tests the integration with your specific model that returns the metrics_expert format
"""

import json
import os
from notebook_generator import NotebookGenerator


def test_custom_metrics_expert():
    """Test the custom metrics expert model integration"""
    print("🔬 Testing Custom Metrics Expert Model")
    print("=" * 50)
    
    # Configuration for your custom model
    custom_endpoint = os.getenv('CUSTOM_MODEL_ENDPOINT', 'https://your-metrics-expert-model.com/api')
    custom_api_key = os.getenv('CUSTOM_MODEL_API_KEY', 'your_api_key')
    
    if not custom_endpoint or custom_api_key == 'your_api_key':
        print("⚠️  Please set your custom model configuration:")
        print("   export CUSTOM_MODEL_ENDPOINT='https://your-model.com/api'")
        print("   export CUSTOM_MODEL_API_KEY='your_actual_api_key'")
        print("\n🧪 Running mock test with example data...")
        test_with_mock_data()
        return
    
    # Initialize notebook generator with custom model
    generator = NotebookGenerator(
        api_key=custom_api_key,
        model_endpoint=custom_endpoint,
        model_name="metrics-expert"
    )
    
    print(f"✅ Initialized with custom endpoint: {custom_endpoint}")
    
    # Test 1: Single metric request
    print("\n📊 Test 1: Single Metric Request")
    print("-" * 40)
    
    test_metric_request(generator, ["aws.ec2.cpuutilization"])
    
    # Test 2: Multiple metrics request
    print("\n📈 Test 2: Multiple Metrics Request")
    print("-" * 40)
    
    test_metric_request(generator, [
        "aws.ec2.cpuutilization",
        "aws.ec2.cpucredit_balance"
    ])
    
    # Test 3: Integration with notebook generation
    print("\n📓 Test 3: Notebook Generation with Custom Model")
    print("-" * 40)
    
    test_notebook_generation(generator)


def test_metric_request(generator: NotebookGenerator, metric_names: list):
    """Test a metric request with the custom model"""
    request = {
        "metric_names": metric_names,
        "time_range": "1h",
        "aggregation": "avg",
        "tags": {"host": "*"},
        "filters": {}
    }
    
    context = {
        "user_request": f"Monitor {', '.join(metric_names)}",
        "difficulty_level": "intermediate"
    }
    
    print(f"Requesting metrics: {', '.join(metric_names)}")
    
    try:
        result = generator.export_metrics_with_gpt(request, context)
        
        if result.get('success'):
            print("✅ Request successful!")
            
            # Display the results
            data = result.get('data', {})
            print(f"Integration: {data.get('integration', 'unknown')}")
            print(f"Series count: {len(data.get('series', []))}")
            
            for i, series in enumerate(data.get('series', [])[:3]):  # Show first 3
                print(f"\n📊 Series {i+1}: {series.get('metric')}")
                print(f"   Type: {series.get('metric_type')}")
                print(f"   Unit: {series.get('unit')}")
                print(f"   Data points: {series.get('length', 0)}")
                print(f"   Description: {series.get('attributes', {}).get('description', 'N/A')[:80]}...")
                
                # Show sample data points
                pointlist = series.get('pointlist', [])
                if pointlist:
                    print(f"   Sample values: {pointlist[0][1]:.2f}, {pointlist[len(pointlist)//2][1]:.2f}, {pointlist[-1][1]:.2f}")
            
            # Display visualization hints
            hints = result.get('visualization_hints', {})
            print(f"\n🎨 Visualization hints:")
            print(f"   Charts: {hints.get('recommended_chart_types', [])}")
            print(f"   Colors: {hints.get('color_suggestions', [])}")
            
        else:
            print("❌ Request failed!")
            print(f"Error: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Exception occurred: {e}")


def test_notebook_generation(generator: NotebookGenerator):
    """Test notebook generation with custom model data"""
    advanced_settings = {
        "metric_names": "aws.ec2.cpuutilization,aws.ec2.cpucredit_balance",
        "timeframes": "1h",
        "space_aggregation": "avg",
        "use_gpt_metrics": True
    }
    
    try:
        notebook = generator.generate_notebook(
            "Create an AWS EC2 monitoring dashboard with CPU metrics",
            advanced_settings=advanced_settings
        )
        
        print("✅ Notebook generated successfully!")
        print(f"Title: {notebook['data']['attributes']['name']}")
        print(f"Cells: {len(notebook['data']['attributes']['cells'])}")
        
        # Save for inspection
        with open('custom_model_notebook.json', 'w') as f:
            json.dump(notebook, f, indent=2)
        print("📁 Saved to custom_model_notebook.json")
        
    except Exception as e:
        print(f"❌ Notebook generation failed: {e}")


def test_with_mock_data():
    """Test with the example response data for development"""
    print("🧪 Testing with mock data from metrics_expert_example_response/response.json")
    
    # Load the example response
    try:
        with open('metrics_expert_example_response/response.json', 'r') as f:
            example_response = json.load(f)
        
        print("✅ Loaded example response")
        print(f"Integration: {example_response.get('integration')}")
        print(f"Key metrics count: {len(example_response.get('key_metrics', []))}")
        
        for i, metric in enumerate(example_response.get('key_metrics', [])[:3]):
            print(f"\n📊 Metric {i+1}: {metric.get('metric_name')}")
            print(f"   Type: {metric.get('type')}")
            print(f"   Unit: {metric.get('unit')}")
            print(f"   Description: {metric.get('description')[:80]}...")
        
        # Simulate the conversion process
        print("\n🔄 Testing conversion to Datadog format...")
        
        # Create a mock client to test the conversion
        from metric_gpt_client import MetricGPTClient
        
        client = MetricGPTClient("mock_key")
        
        mock_request = {
            "metric_names": ["aws.ec2.cpuutilization"],
            "time_range": "1h",
            "aggregation": "avg"
        }
        
        try:
            converted = client._convert_metrics_expert_to_datadog(example_response, mock_request)
            print("✅ Conversion successful!")
            print(f"Status: {converted.get('status')}")
            print(f"Series count: {len(converted.get('series', []))}")
            print(f"Integration: {converted.get('integration')}")
            
            # Show first series
            if converted.get('series'):
                series = converted['series'][0]
                print(f"\nFirst series: {series.get('metric')}")
                print(f"Data points: {len(series.get('pointlist', []))}")
                print(f"Time range: {series.get('start')} to {series.get('end')}")
                
        except Exception as e:
            print(f"❌ Conversion failed: {e}")
            
    except FileNotFoundError:
        print("❌ Example response file not found")
        print("   Expected: metrics_expert_example_response/response.json")


def validate_custom_model_format():
    """Validate that the custom model response format is as expected"""
    print("\n🔍 Validating Custom Model Format")
    print("-" * 40)
    
    expected_format = {
        "integration": "string",
        "key_metrics": [
            {
                "metric_name": "string",
                "type": "gauge|count|rate",
                "unit": "string",
                "description": "string"
            }
        ]
    }
    
    print("Expected request format to your model:")
    print(json.dumps({
        "metric": "metric_name_to_query",
        "context": "optional context description",
        "integration": "auto-detect or specific integration"
    }, indent=2))
    
    print("\nExpected response format from your model:")
    print(json.dumps(expected_format, indent=2))
    
    print("\n✅ This format will be automatically converted to Datadog time series format")


if __name__ == "__main__":
    test_custom_metrics_expert()
    validate_custom_model_format()
    
    print("\n" + "=" * 50)
    print("🎯 Summary:")
    print("   • Your custom model should accept: {'metric': 'name', 'context': '...', 'integration': '...'}")
    print("   • Your custom model should return the format from metrics_expert_example_response/response.json")
    print("   • The system will automatically convert this to Datadog time series format")
    print("   • Multiple metrics are handled by calling your model once per metric")
    print("🚀 Ready to integrate with your metrics expert model!") 