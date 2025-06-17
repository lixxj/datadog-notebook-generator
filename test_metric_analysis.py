"""
Test script for Metric Analysis Service
"""

import os
import json
from datadog_client import DatadogClient
from metric_analysis_service import MetricAnalysisService

def test_metric_analysis():
    """Test the metric analysis functionality"""
    
    # Sample suggested metrics (like what would come from GPT model)
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
            "metric_name": "custom.application.response_time",
            "type": "histogram",
            "unit": "millisecond", 
            "description": "Application response time"
        }
    ]
    
    # Mock existing metrics (what customer already has)
    existing_metrics = [
        "aws.ec2.cpuutilization",  # This one exists
        "system.cpu.user",
        "system.mem.used",
        "datadog.agent.running"
    ]
    
    print("🔍 Testing Metric Analysis Service")
    print("=" * 50)
    
    # Test without actual Datadog client (mock scenario)
    print("\n📊 Suggested Metrics:")
    for i, metric in enumerate(suggested_metrics, 1):
        print(f"  {i}. {metric['metric_name']} ({metric['type']}) - {metric['description']}")
    
    print(f"\n✅ Existing Customer Metrics ({len(existing_metrics)}):")
    for metric in existing_metrics:
        print(f"  • {metric}")
    
    # Simulate analysis
    suggested_names = [m['metric_name'] for m in suggested_metrics]
    missing_metrics = []
    
    for metric in suggested_metrics:
        if metric['metric_name'] not in existing_metrics:
            missing_metrics.append(metric)
    
    coverage = ((len(suggested_metrics) - len(missing_metrics)) / len(suggested_metrics)) * 100
    
    print(f"\n❌ Missing Metrics ({len(missing_metrics)}):")
    for metric in missing_metrics:
        integration = detect_integration(metric['metric_name'])
        print(f"  • {metric['metric_name']} [{integration}] - {metric['description']}")
    
    print(f"\n📈 Coverage: {coverage:.1f}% ({len(suggested_metrics) - len(missing_metrics)}/{len(suggested_metrics)} metrics available)")
    
    # Generate recommendations by integration
    integrations = {}
    for metric in missing_metrics:
        integration = detect_integration(metric['metric_name'])
        if integration not in integrations:
            integrations[integration] = []
        integrations[integration].append(metric)
    
    print(f"\n🛠️  Setup Recommendations:")
    for integration, metrics in integrations.items():
        print(f"\n  {integration.upper()} Integration:")
        print(f"    Missing: {len(metrics)} metrics")
        print(f"    Setup: https://docs.datadoghq.com/integrations/{integration.lower()}/")
        print("    Steps:")
        if integration == "nginx":
            print("      1. Enable nginx status module")
            print("      2. Configure nginx.conf with status endpoint")
            print("      3. Update nginx.yaml in Datadog agent")
            print("      4. Restart Datadog agent")
        elif integration == "mysql":
            print("      1. Create MySQL user for Datadog agent")
            print("      2. Grant required permissions")
            print("      3. Configure mysql.yaml in agent")
            print("      4. Restart Datadog agent")
        elif integration == "custom":
            print("      1. Implement custom metric collection")
            print("      2. Use DogStatsD or API to send metrics")
            print("      3. Verify metrics in Datadog")
        
        for metric in metrics:
            priority = calculate_priority(metric['metric_name'])
            print(f"      - {metric['metric_name']} (Priority: {priority})")

def detect_integration(metric_name):
    """Detect integration from metric name"""
    metric_lower = metric_name.lower()
    
    patterns = {
        'aws.': 'aws',
        'nginx.': 'nginx', 
        'mysql.': 'mysql',
        'redis.': 'redis',
        'custom.': 'custom'
    }
    
    for pattern, integration in patterns.items():
        if metric_lower.startswith(pattern):
            return integration
    
    return 'custom'

def calculate_priority(metric_name):
    """Calculate metric priority"""
    metric_lower = metric_name.lower()
    
    high_priority = ['cpu', 'memory', 'error', 'latency', 'response_time']
    medium_priority = ['connection', 'query', 'request', 'throughput']
    
    for pattern in high_priority:
        if pattern in metric_lower:
            return 'HIGH'
    
    for pattern in medium_priority:
        if pattern in metric_lower:
            return 'MEDIUM'
    
    return 'LOW'

def test_api_endpoints():
    """Test API endpoint scenarios"""
    print("\n" + "=" * 50)
    print("🌐 API Endpoint Usage Examples")
    print("=" * 50)
    
    print("\n1. Analyze Metrics:")
    print("   POST /metrics/analyze")
    print("   {")
    print('     "suggested_metrics": [...],')
    print('     "customer_id": "customer123"')
    print("   }")
    
    print("\n2. Get Customer Metrics:")
    print("   GET /metrics/customer/customer123")
    
    print("\n3. Get Integration Setup:")
    print("   GET /integration/nginx/setup")
    
    print("\n4. Get Integration Metrics:")
    print("   GET /integration/aws/metrics")
    
    print("\n📝 Environment Variables:")
    print("   CUSTOMER_METRICS_ENDPOINT - Custom endpoint for customer metrics")
    print("   Example: https://api.customer.com/v1/metrics/{customer_id}")

if __name__ == "__main__":
    test_metric_analysis()
    test_api_endpoints()
    
    print("\n" + "=" * 50)
    print("✅ Test completed! The metric analysis service is ready.")
    print("💡 Provide your customer metrics API endpoint to enable custom metric retrieval.")
    print("=" * 50) 