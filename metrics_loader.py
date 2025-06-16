"""
Metrics Loader for Real Datadog Metrics
Loads and manages real Datadog metrics from CSV files
"""

import csv
import os
import random
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class Metric:
    """Represents a Datadog metric with its metadata"""
    name: str
    type: str
    interval: str
    unit_name: str
    per_unit_name: str
    description: str
    orientation: str
    integration: str
    short_name: str
    curated_metric: str


class MetricsLoader:
    """Loads and manages real Datadog metrics from CSV files"""
    
    def __init__(self, metrics_dir: str = "metrics"):
        self.metrics_dir = metrics_dir
        self.metrics_by_integration: Dict[str, List[Metric]] = {}
        self.all_metrics: List[Metric] = []
        self._load_all_metrics()
    
    def _load_all_metrics(self):
        """Load all metrics from CSV files in the metrics directory"""
        if not os.path.exists(self.metrics_dir):
            print(f"Warning: Metrics directory '{self.metrics_dir}' not found")
            return
        
        for filename in os.listdir(self.metrics_dir):
            if filename.endswith('.csv'):
                filepath = os.path.join(self.metrics_dir, filename)
                integration_name = filename.replace('_metadata.csv', '')
                self._load_metrics_from_file(filepath, integration_name)
        
        print(f"Loaded {len(self.all_metrics)} metrics from {len(self.metrics_by_integration)} integrations")
    
    def _load_metrics_from_file(self, filepath: str, integration_name: str):
        """Load metrics from a single CSV file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                metrics = []
                
                for row in reader:
                    metric = Metric(
                        name=row.get('metric_name', ''),
                        type=row.get('metric_type', ''),
                        interval=row.get('interval', ''),
                        unit_name=row.get('unit_name', ''),
                        per_unit_name=row.get('per_unit_name', ''),
                        description=row.get('description', ''),
                        orientation=row.get('orientation', ''),
                        integration=row.get('integration', integration_name),
                        short_name=row.get('short_name', ''),
                        curated_metric=row.get('curated_metric', '')
                    )
                    metrics.append(metric)
                    self.all_metrics.append(metric)
                
                self.metrics_by_integration[integration_name] = metrics
                print(f"Loaded {len(metrics)} metrics from {integration_name}")
                
        except Exception as e:
            print(f"Error loading metrics from {filepath}: {e}")
    
    def get_metrics_by_category(self, category: str) -> List[Metric]:
        """Get metrics by category/keyword"""
        category_lower = category.lower()
        matching_metrics = []
        
        for metric in self.all_metrics:
            if (category_lower in metric.name.lower() or 
                category_lower in metric.description.lower() or
                category_lower in metric.short_name.lower()):
                matching_metrics.append(metric)
        
        return matching_metrics
    
    def get_metrics_by_integration(self, integration: str) -> List[Metric]:
        """Get all metrics for a specific integration"""
        return self.metrics_by_integration.get(integration, [])
    
    def get_system_metrics(self) -> List[Metric]:
        """Get system-level metrics"""
        return self.get_metrics_by_integration('system')
    
    def get_aws_metrics(self) -> List[Metric]:
        """Get AWS-related metrics"""
        aws_metrics = []
        for integration in self.metrics_by_integration:
            if integration.startswith('amazon_'):
                aws_metrics.extend(self.metrics_by_integration[integration])
        return aws_metrics
    
    def get_azure_metrics(self) -> List[Metric]:
        """Get Azure-related metrics"""
        azure_metrics = []
        for integration in self.metrics_by_integration:
            if integration.startswith('azure_'):
                azure_metrics.extend(self.metrics_by_integration[integration])
        return azure_metrics
    
    def suggest_metrics_for_request(self, user_request: str) -> List[Metric]:
        """Suggest relevant metrics based on user request"""
        request_lower = user_request.lower()
        suggested_metrics = []
        
        # Define keyword mappings
        keyword_mappings = {
            'cpu': ['cpu', 'processor', 'core'],
            'memory': ['memory', 'mem', 'ram'],
            'disk': ['disk', 'storage', 'io', 'filesystem', 'fs'],
            'network': ['network', 'net', 'bytes', 'packets'],
            'load': ['load', 'system'],
            'process': ['process', 'proc'],
            'aws': ['aws', 'ec2', 's3', 'sqs', 'vpc'],
            'azure': ['azure', 'functions'],
            'performance': ['cpu', 'memory', 'disk', 'network', 'load'],
            'monitoring': ['cpu', 'memory', 'disk', 'network', 'load', 'process'],
            'infrastructure': ['system', 'cpu', 'memory', 'disk', 'network'],
            'cloud': ['aws', 'azure', 'ec2', 's3']
        }
        
        # Find matching keywords
        matched_categories = set()
        for category, keywords in keyword_mappings.items():
            if any(keyword in request_lower for keyword in keywords):
                matched_categories.add(category)
        
        # If specific categories found, get metrics for those
        if matched_categories:
            for category in matched_categories:
                if category in ['aws', 'azure', 'cloud']:
                    if category == 'aws' or category == 'cloud':
                        suggested_metrics.extend(self.get_aws_metrics()[:10])  # Limit to 10
                    if category == 'azure' or category == 'cloud':
                        suggested_metrics.extend(self.get_azure_metrics()[:10])
                else:
                    category_metrics = self.get_metrics_by_category(category)
                    suggested_metrics.extend(category_metrics[:15])  # Limit per category
        else:
            # Fallback: search by keywords in the request
            for metric in self.all_metrics:
                if any(word in metric.name.lower() or word in metric.description.lower() 
                       for word in request_lower.split()):
                    suggested_metrics.append(metric)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_metrics = []
        for metric in suggested_metrics:
            if metric.name not in seen:
                seen.add(metric.name)
                unique_metrics.append(metric)
        
        # Limit total suggestions
        return unique_metrics[:20]
    
    def get_popular_metrics(self, limit: int = 10) -> List[Metric]:
        """Get commonly used metrics for general monitoring"""
        popular_metric_names = [
            'system.cpu.user',
            'system.cpu.system', 
            'system.cpu.idle',
            'system.mem.used',
            'system.mem.free',
            'system.load.1',
            'system.load.5',
            'system.disk.used',
            'system.disk.free',
            'system.net.bytes_sent',
            'system.net.bytes_rcvd',
            'system.processes.number'
        ]
        
        popular_metrics = []
        for metric_name in popular_metric_names:
            for metric in self.all_metrics:
                if metric.name == metric_name:
                    popular_metrics.append(metric)
                    break
        
        # Fill remaining slots with random system metrics if needed
        if len(popular_metrics) < limit:
            system_metrics = self.get_system_metrics()
            remaining = limit - len(popular_metrics)
            additional = random.sample(system_metrics, min(remaining, len(system_metrics)))
            popular_metrics.extend(additional)
        
        return popular_metrics[:limit]
    
    def get_metric_by_name(self, metric_name: str) -> Optional[Metric]:
        """Get a specific metric by name"""
        for metric in self.all_metrics:
            if metric.name == metric_name:
                return metric
        return None
    
    def get_available_integrations(self) -> List[str]:
        """Get list of available integrations"""
        return list(self.metrics_by_integration.keys())
    
    def format_metric_for_query(self, metric: Metric, aggregation: str = "avg", 
                               tags: Optional[List[str]] = None) -> str:
        """Format a metric for use in Datadog queries"""
        query = f"{aggregation}:{metric.name}"
        
        if tags:
            tag_string = ",".join(tags)
            query += f"{{{tag_string}}}"
        
        return query
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary statistics about loaded metrics"""
        return {
            "total_metrics": len(self.all_metrics),
            "integrations": len(self.metrics_by_integration),
            "integration_breakdown": {
                integration: len(metrics) 
                for integration, metrics in self.metrics_by_integration.items()
            },
            "metric_types": self._get_metric_type_breakdown()
        }
    
    def _get_metric_type_breakdown(self) -> Dict[str, int]:
        """Get breakdown of metrics by type"""
        type_counts = {}
        for metric in self.all_metrics:
            metric_type = metric.type or 'unknown'
            type_counts[metric_type] = type_counts.get(metric_type, 0) + 1
        return type_counts 