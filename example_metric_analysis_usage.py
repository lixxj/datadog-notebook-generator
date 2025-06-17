"""
Example usage of the Metric Analysis API
Demonstrates how to analyze suggested metrics against customer's existing metrics
"""

import requests
import json

# Example usage with the API server
BASE_URL = "http://localhost:8000"

def example_analyze_metrics():
    """Example of analyzing suggested metrics"""
    
    # Sample suggested metrics (this would come from your GPT model)
    suggested_metrics = [
        {
            "metric_name": "aws.ec2.cpuutilization",
            "type": "gauge",
            "unit": "percent",
            "description": "CPU utilization percentage for EC2 instances"
        },
        {
            "metric_name": "nginx.net.connections",
            "type": "gauge", 
            "unit": "connection",
            "description": "Active connections to Nginx server"
        },
        {
            "metric_name": "mysql.performance.queries",
            "type": "rate",
            "unit": "query/second",
            "description": "Rate of MySQL queries per second"
        },
        {
            "metric_name": "system.cpu.user",  # This one should exist
            "type": "gauge",
            "unit": "percent",
            "description": "User CPU time"
        },
        {
            "metric_name": "custom.application.response_time",
            "type": "histogram",
            "unit": "millisecond", 
            "description": "Application response time"
        }
    ]
    
    print("🔍 Analyzing Suggested Metrics")
    print("=" * 50)
    
    # Make API call to analyze metrics
    try:
        response = requests.post(
            f"{BASE_URL}/metrics/analyze",
            json={
                "suggested_metrics": suggested_metrics,
                "customer_id": "example_customer_123"
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Analysis successful!")
            print(f"📊 Coverage: {result['coverage_percentage']:.1f}%")
            print(f"🎯 Total suggested: {len(suggested_metrics)}")
            print(f"❌ Missing: {len(result['missing_metrics'])}")
            print(f"✅ Existing: {len(result['existing_metrics'])}")
            
            print("\n📈 Missing Metrics:")
            for metric in result['missing_metrics']:
                print(f"  • {metric['metric_name']} [{metric['integration']}] - {metric['priority']} priority")
                print(f"    Setup: {metric['setup_url']}")
            
            print("\n🛠️  Recommendations:")
            for rec in result['recommendations']:
                print(f"  {rec['integration'].upper()}: {rec['missing_metrics_count']} missing metrics ({rec['priority']} priority)")
                print(f"    Setup: {rec.get('setup_url', 'N/A')}")
                
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API server. Make sure it's running on localhost:8000")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def example_get_integration_setup():
    """Example of getting setup guide for an integration"""
    
    print("\n" + "=" * 50)
    print("🛠️  Getting Integration Setup Guide")
    print("=" * 50)
    
    integration = "nginx"
    
    try:
        response = requests.get(f"{BASE_URL}/integration/{integration}/setup")
        
        if response.status_code == 200:
            result = response.json()
            setup_guide = result['setup_guide']
            
            print(f"📖 Setup Guide for {integration.upper()}:")
            print(f"Description: {setup_guide['description']}")
            print(f"Setup URL: {setup_guide['setup_url']}")
            print(f"Estimated time: {setup_guide['estimated_setup_time']}")
            print("\nSetup Steps:")
            for i, step in enumerate(setup_guide['setup_steps'], 1):
                print(f"  {i}. {step}")
            
            print(f"\nAvailable Metrics ({len(setup_guide['available_metrics'])}):")
            for metric in setup_guide['available_metrics'][:5]:  # Show first 5
                print(f"  • {metric}")
            if len(setup_guide['available_metrics']) > 5:
                print(f"  ... and {len(setup_guide['available_metrics']) - 5} more")
                
        else:
            print(f"❌ API Error: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API server. Make sure it's running on localhost:8000")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def example_workflow():
    """Complete workflow example"""
    
    print("\n" + "=" * 50)
    print("🔄 Complete Metric Analysis Workflow")
    print("=" * 50)
    
    # Step 1: Get suggested metrics from your GPT model
    print("Step 1: Generate suggested metrics (from your GPT model)")
    suggested_metrics_from_gpt = [
        {
            "metric_name": "container.cpu.usage",
            "type": "gauge",
            "unit": "percent",
            "description": "Container CPU usage percentage"
        },
        {
            "metric_name": "aws.rds.database_connections",
            "type": "gauge",
            "unit": "connection",
            "description": "Number of database connections"
        },
        {
            "metric_name": "custom.api.latency",
            "type": "histogram",
            "unit": "millisecond",
            "description": "API response latency"
        }
    ]
    
    # Step 2: Analyze against customer's existing metrics
    print("\nStep 2: Analyze against customer's existing metrics")
    try:
        response = requests.post(
            f"{BASE_URL}/metrics/analyze",
            json={
                "suggested_metrics": suggested_metrics_from_gpt,
                "customer_id": "customer456"
            }
        )
        
        if response.status_code == 200:
            analysis = response.json()
            
            # Step 3: Identify missing metrics and generate setup recommendations
            print("\nStep 3: Generate setup recommendations")
            missing_integrations = set()
            for metric in analysis['missing_metrics']:
                missing_integrations.add(metric['integration'])
            
            # Step 4: Provide setup guides for missing integrations
            print("\nStep 4: Provide setup guides")
            for integration in missing_integrations:
                try:
                    setup_response = requests.get(f"{BASE_URL}/integration/{integration}/setup")
                    if setup_response.status_code == 200:
                        setup_data = setup_response.json()
                        guide = setup_data['setup_guide']
                        print(f"\n📋 {integration.upper()} Setup:")
                        print(f"   Time needed: {guide['estimated_setup_time']}")
                        print(f"   Documentation: {guide['setup_url']}")
                        print(f"   Steps: {len(guide['setup_steps'])} steps required")
                except:
                    pass
            
            print(f"\n✅ Workflow completed!")
            print(f"📊 Result: {analysis['coverage_percentage']:.1f}% coverage")
            print(f"🔧 Action needed: Set up {len(missing_integrations)} integrations")
            
        else:
            print("❌ Analysis failed")
            
    except requests.exceptions.ConnectionError:
        print("❌ API server not available")

def example_with_custom_endpoint():
    """Example with custom metrics endpoint"""
    
    print("\n" + "=" * 50)
    print("🌐 Using Custom Metrics Endpoint")
    print("=" * 50)
    
    print("To use a custom metrics endpoint, set the environment variable:")
    print("export CUSTOMER_METRICS_ENDPOINT='https://your-api.com/metrics/{customer_id}'")
    print("")
    print("The system will:")
    print("1. Replace {customer_id} with the actual customer ID")
    print("2. Make a GET request to fetch their metrics")
    print("3. Parse the response (supports various formats)")
    print("4. Compare with suggested metrics")
    print("")
    print("Expected response formats:")
    print("- Simple array: ['metric1', 'metric2', ...]")
    print("- Object with 'metrics' key: {'metrics': ['metric1', ...]}")
    print("- Object with 'data' key: {'data': ['metric1', ...]}")

if __name__ == "__main__":
    print("🚀 Metric Analysis API Examples")
    print("Make sure your FastAPI server is running: python -m uvicorn main:app --reload")
    print("")
    
    # Run examples
    example_analyze_metrics()
    example_get_integration_setup()
    example_workflow()
    example_with_custom_endpoint()
    
    print("\n" + "=" * 50)
    print("✅ All examples completed!")
    print("💡 Next steps:")
    print("1. Configure your Datadog API keys")
    print("2. Set up your custom metrics endpoint (optional)")
    print("3. Integrate with your GPT model")
    print("4. Start analyzing customer metrics!")
    print("=" * 50) 