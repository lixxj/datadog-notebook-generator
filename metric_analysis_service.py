"""
Metric Analysis Service
Handles analysis of suggested vs existing metrics and provides setup documentation
"""

import requests
import json
from typing import Dict, Any, List, Optional, Set
import logging
from dataclasses import dataclass
import time
import os
import pandas as pd
from datadog_client import DatadogClient

logger = logging.getLogger(__name__)


@dataclass
class MetricAnalysis:
    """Results of metric analysis"""
    existing_metrics: List[str]
    missing_metrics: List[Dict[str, Any]]
    total_suggested: int
    coverage_percentage: float
    recommendations: List[Dict[str, Any]]


@dataclass
class MissingMetric:
    """Information about a missing metric"""
    name: str
    integration: str
    description: str
    setup_url: str
    setup_steps: List[str]
    priority: str  # 'high', 'medium', 'low'


class MetricAnalysisService:
    def __init__(self, datadog_client: DatadogClient, customer_metrics_endpoint: Optional[str] = None):
        """
        Initialize the metric analysis service
        
        Args:
            datadog_client: Configured Datadog client
            customer_metrics_endpoint: Optional custom endpoint for retrieving customer metrics
        """
        self.datadog_client = datadog_client
        self.customer_metrics_endpoint = customer_metrics_endpoint
        self._metrics_cache = {}
        self._cache_ttl = 300  # 5 minutes
        self._integration_patterns = self._load_integration_patterns()
        
    def _load_integration_patterns(self) -> Dict[str, Dict[str, Any]]:
        """
        Load integration patterns from CSV files in the metrics directory
        
        Returns:
            Dictionary mapping integration names to their patterns and metadata
        """
        patterns = {}
        metrics_dir = "metrics"
        
        if not os.path.exists(metrics_dir):
            logger.warning(f"Metrics directory {metrics_dir} not found, using fallback patterns")
            return self._get_fallback_patterns()
        
        try:
            for filename in os.listdir(metrics_dir):
                if filename.endswith('.csv'):
                    integration_name = filename.replace('_metadata.csv', '').replace('.csv', '')
                    csv_path = os.path.join(metrics_dir, filename)
                    
                    try:
                        df = pd.read_csv(csv_path)
                        
                        # Extract metric names and prefixes
                        metric_names = df['metric_name'].tolist()
                        prefixes = set()
                        
                        for metric in metric_names:
                            if '.' in metric:
                                # Get the first two parts for pattern matching
                                parts = metric.split('.')
                                if len(parts) >= 2:
                                    prefix = f"{parts[0]}.{parts[1]}"
                                    prefixes.add(prefix)
                        
                        # Get integration name from CSV or filename
                        integration_key = df['integration'].iloc[0] if 'integration' in df.columns and len(df) > 0 else integration_name
                        
                        patterns[integration_key] = {
                            'prefixes': list(prefixes),
                            'metrics': metric_names,
                            'filename': filename,
                            'display_name': integration_name.replace('_', ' ').title()
                        }
                        
                        logger.info(f"Loaded {len(metric_names)} metrics for {integration_key} integration")
                        
                    except Exception as e:
                        logger.error(f"Failed to load patterns from {filename}: {str(e)}")
                        continue
            
            if patterns:
                logger.info(f"Successfully loaded patterns for {len(patterns)} integrations: {list(patterns.keys())}")
            else:
                logger.warning("No integration patterns loaded, using fallback patterns")
                return self._get_fallback_patterns()
                
            return patterns
            
        except Exception as e:
            logger.error(f"Failed to load integration patterns: {str(e)}")
            return self._get_fallback_patterns()
    
    def _get_fallback_patterns(self) -> Dict[str, Dict[str, Any]]:
        """
        Get fallback integration patterns when CSV loading fails
        
        Returns:
            Dictionary of fallback patterns
        """
        return {
            'aws': {'prefixes': ['aws.'], 'display_name': 'AWS'},
            'azure': {'prefixes': ['azure.'], 'display_name': 'Azure'},
            'azure_vm': {'prefixes': ['azure.vm'], 'display_name': 'Azure VM'},
            'gcp': {'prefixes': ['gcp.'], 'display_name': 'Google Cloud'},
            'nginx': {'prefixes': ['nginx.'], 'display_name': 'NGINX'},
            'mysql': {'prefixes': ['mysql.'], 'display_name': 'MySQL'},
            'postgresql': {'prefixes': ['postgresql.'], 'display_name': 'PostgreSQL'},
            'redis': {'prefixes': ['redis.'], 'display_name': 'Redis'},
            'mongodb': {'prefixes': ['mongodb.'], 'display_name': 'MongoDB'},
            'docker': {'prefixes': ['docker.'], 'display_name': 'Docker'},
            'kubernetes': {'prefixes': ['kubernetes.'], 'display_name': 'Kubernetes'},
            'system': {'prefixes': ['system.'], 'display_name': 'System'}
        }

    def analyze_metrics(self, suggested_metrics: List[Dict[str, Any]], 
                       customer_id: Optional[str] = None) -> MetricAnalysis:
        """
        Analyze suggested metrics against customer's existing metrics
        
        Args:
            suggested_metrics: List of suggested metrics from GPT model
            customer_id: Optional customer ID for custom endpoint
            
        Returns:
            MetricAnalysis with results and recommendations
        """
        try:
            # Get customer's existing metrics
            existing_metrics = self._get_customer_metrics(customer_id)
            existing_metric_names = set(existing_metrics)
            
            # Extract metric names from suggestions
            suggested_metric_names = []
            for metric in suggested_metrics:
                if isinstance(metric, dict):
                    metric_name = metric.get('metric_name') or metric.get('name')
                    if metric_name:
                        suggested_metric_names.append(metric_name)
                elif isinstance(metric, str):
                    suggested_metric_names.append(metric)
            
            # Find missing metrics
            missing_metrics = []
            for i, suggested_metric in enumerate(suggested_metrics):
                metric_name = None
                if isinstance(suggested_metric, dict):
                    metric_name = suggested_metric.get('metric_name') or suggested_metric.get('name')
                elif isinstance(suggested_metric, str):
                    metric_name = suggested_metric
                    suggested_metric = {'metric_name': metric_name}
                
                if metric_name and metric_name not in existing_metric_names:
                    # Get integration and documentation info
                    integration = self._detect_integration(metric_name)
                    doc_info = self.datadog_client.get_integration_documentation(integration)
                    
                    missing_metric = {
                        'metric_name': metric_name,
                        'integration': integration,
                        'description': suggested_metric.get('description', f"Metric from {integration} integration"),
                        'type': suggested_metric.get('type', 'gauge'),
                        'unit': suggested_metric.get('unit', ''),
                        'setup_url': doc_info.get('setup_url', ''),
                        'metrics_url': doc_info.get('metrics_url', ''),
                        'setup_steps': doc_info.get('setup_steps', []),
                        'priority': self._calculate_priority(metric_name, integration)
                    }
                    missing_metrics.append(missing_metric)
            
            # Calculate coverage
            total_suggested = len(suggested_metric_names)
            missing_count = len(missing_metrics)
            coverage_percentage = ((total_suggested - missing_count) / total_suggested * 100) if total_suggested > 0 else 100
            
            # Generate recommendations
            recommendations = self._generate_recommendations(missing_metrics, existing_metrics)
            
            return MetricAnalysis(
                existing_metrics=list(existing_metric_names),
                missing_metrics=missing_metrics,
                total_suggested=total_suggested,
                coverage_percentage=coverage_percentage,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Failed to analyze metrics: {str(e)}")
            raise

    def _get_customer_metrics(self, customer_id: Optional[str] = None) -> List[str]:
        """
        Get customer's existing metrics from Datadog or custom endpoint
        
        Args:
            customer_id: Optional customer ID
            
        Returns:
            List of existing metric names
        """
        cache_key = f"customer_metrics_{customer_id or 'default'}"
        
        # Check cache first
        if cache_key in self._metrics_cache:
            cached_data = self._metrics_cache[cache_key]
            if time.time() - cached_data['timestamp'] < self._cache_ttl:
                return cached_data['metrics']
        
        try:
            if self.customer_metrics_endpoint and customer_id:
                # Use custom endpoint if provided
                metrics = self._fetch_from_custom_endpoint(customer_id)
            else:
                # Use Datadog API to get active metrics
                result = self.datadog_client.get_active_metrics()
                if 'error' in result:
                    logger.error(f"Failed to get metrics from Datadog: {result['error']}")
                    return []
                
                # Extract metric names from Datadog API v2 response
                metrics = []
                if 'data' in result and isinstance(result['data'], list):
                    # API v2 format: {"data": [{"type": "metrics", "id": "metric.name"}, ...]}
                    metrics = [item['id'] for item in result['data'] if item.get('type') == 'metrics']
                elif 'metrics' in result:
                    # Fallback for other formats
                    metrics = result['metrics']
                elif isinstance(result, list):
                    metrics = result
            
            # Cache the results
            self._metrics_cache[cache_key] = {
                'metrics': metrics,
                'timestamp': time.time()
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get customer metrics: {str(e)}")
            return []

    def _fetch_from_custom_endpoint(self, customer_id: str) -> List[str]:
        """
        Fetch metrics from custom API endpoint
        
        Args:
            customer_id: Customer ID
            
        Returns:
            List of metric names
        """
        if not self.customer_metrics_endpoint:
            raise ValueError("Custom metrics endpoint not configured")
        
        try:
            # Replace placeholder in endpoint URL
            url = self.customer_metrics_endpoint.replace('{customer_id}', customer_id)
            
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract metric names based on expected response format
            # This may need to be adjusted based on the actual API response format
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                if 'metrics' in data:
                    return data['metrics']
                elif 'data' in data and isinstance(data['data'], list):
                    return data['data']
            
            logger.warning(f"Unexpected response format from custom endpoint: {type(data)}")
            return []
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch from custom endpoint: {str(e)}")
            raise

    def _detect_integration(self, metric_name: str) -> str:
        """
        Detect integration type from metric name using loaded patterns
        
        Args:
            metric_name: Name of the metric
            
        Returns:
            Integration name
        """
        metric_lower = metric_name.lower()
        
        # Check against loaded integration patterns
        for integration_key, pattern_info in self._integration_patterns.items():
            prefixes = pattern_info.get('prefixes', [])
            for prefix in prefixes:
                if metric_lower.startswith(prefix.lower()):
                    return integration_key
        
        # If no pattern matches, try to detect from the metric structure
        if '.' in metric_name:
            parts = metric_name.split('.')
            if len(parts) >= 2:
                potential_integration = f"{parts[0]}.{parts[1]}"
                # Check if this looks like a known integration pattern
                for integration_key, pattern_info in self._integration_patterns.items():
                    if potential_integration.lower() in [p.lower() for p in pattern_info.get('prefixes', [])]:
                        return integration_key
        
        # Default to 'custom' if no pattern matches
        return 'custom'

    def _calculate_priority(self, metric_name: str, integration: str) -> str:
        """
        Calculate priority for missing metric
        
        Args:
            metric_name: Name of the metric
            integration: Integration type
            
        Returns:
            Priority level: 'high', 'medium', 'low'
        """
        metric_lower = metric_name.lower()
        
        # High priority patterns (performance and availability metrics)
        high_priority_patterns = [
            'cpu', 'memory', 'disk', 'error', 'latency', 'response_time',
            'availability', 'uptime', 'connection', 'queue'
        ]
        
        # Medium priority patterns (throughput and capacity metrics)
        medium_priority_patterns = [
            'request', 'throughput', 'rate', 'count', 'usage', 'utilization'
        ]
        
        for pattern in high_priority_patterns:
            if pattern in metric_lower:
                return 'high'
        
        for pattern in medium_priority_patterns:
            if pattern in metric_lower:
                return 'medium'
        
        return 'low'

    def _generate_recommendations(self, missing_metrics: List[Dict[str, Any]], 
                                existing_metrics: List[str]) -> List[Dict[str, Any]]:
        """
        Generate recommendations based on missing metrics
        
        Args:
            missing_metrics: List of missing metrics
            existing_metrics: List of existing metrics
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Group missing metrics by integration
        integrations = {}
        for metric in missing_metrics:
            integration = metric['integration']
            if integration not in integrations:
                integrations[integration] = []
            integrations[integration].append(metric)
        
        # Generate recommendations per integration
        for integration, metrics in integrations.items():
            high_priority_count = sum(1 for m in metrics if m['priority'] == 'high')
            
            recommendation = {
                'integration': integration,
                'missing_metrics_count': len(metrics),
                'high_priority_count': high_priority_count,
                'setup_url': metrics[0]['setup_url'] if metrics else '',
                'description': f"Set up {integration} integration to monitor {len(metrics)} missing metrics",
                'priority': 'high' if high_priority_count > 0 else 'medium',
                'metrics': [{'name': m['metric_name'], 'priority': m['priority']} for m in metrics]
            }
            
            recommendations.append(recommendation)
        
        # Sort by priority and impact
        recommendations.sort(key=lambda x: (
            0 if x['priority'] == 'high' else 1,
            -x['high_priority_count'],
            -x['missing_metrics_count']
        ))
        
        return recommendations

    def get_setup_guide(self, integration: str) -> Dict[str, Any]:
        """
        Get detailed setup guide for an integration
        
        Args:
            integration: Integration name
            
        Returns:
            Detailed setup guide
        """
        doc_info = self.datadog_client.get_integration_documentation(integration)
        available_metrics = self.datadog_client.get_integration_metrics(integration)
        
        return {
            'integration': integration,
            'description': doc_info.get('description', f'Set up {integration} integration'),
            'setup_url': doc_info.get('setup_url', ''),
            'metrics_url': doc_info.get('metrics_url', ''),
            'setup_steps': doc_info.get('setup_steps', []),
            'available_metrics': available_metrics,
            'estimated_setup_time': self._estimate_setup_time(integration)
        }

    def _estimate_setup_time(self, integration: str) -> str:
        """
        Estimate setup time for integration
        
        Args:
            integration: Integration name
            
        Returns:
            Estimated setup time as string
        """
        time_estimates = {
            'aws': '15-30 minutes',
            'azure': '15-30 minutes', 
            'gcp': '15-30 minutes',
            'nginx': '5-10 minutes',
            'mysql': '10-15 minutes',
            'postgresql': '10-15 minutes',
            'redis': '5-10 minutes',
            'docker': '10-20 minutes',
            'kubernetes': '20-45 minutes',
            'custom': '5-15 minutes'
        }
        
        return time_estimates.get(integration, '10-20 minutes') 