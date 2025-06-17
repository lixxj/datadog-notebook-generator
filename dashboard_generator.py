"""
Dashboard Generator using OpenAI API
Generates Datadog dashboard JSON based on user descriptions and available metrics
"""

import json
import logging
from typing import Dict, Any, Optional, List
from openai import OpenAI
from metrics_loader import MetricsLoader

logger = logging.getLogger(__name__)


class DashboardGenerator:
    def __init__(self, openai_api_key: str):
        """
        Initialize the dashboard generator with OpenAI API key
        """
        self.client = OpenAI(api_key=openai_api_key)
        self.metrics_loader = MetricsLoader()
        self.available_metrics = {metric.name: metric for metric in self.metrics_loader.all_metrics}
        
    def generate_dashboard(self, description: str, author_info: Optional[Dict[str, str]] = None, 
                          advanced_settings: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate a dashboard JSON based on user description and available metrics
        
        Args:
            description: User description of what they want to monitor
            author_info: Author information (optional, for backward compatibility)
            advanced_settings: Dictionary containing advanced settings like metric_names, timeframes, etc.
            
        Returns:
            Dashboard JSON structure
        """
        try:
            # Prepare the prompt with metrics information
            prompt = self._build_dashboard_prompt(description, advanced_settings)
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a Datadog metric expert designed to help users understand and utilize available metrics in the Datadog ecosystem. You can interpret and explain metadata from various cloud services like Amazon EC2, S3, SQS, VPC, and Azure Functions, as well as on-premises systems. Your role includes clarifying metric definitions, recommending appropriate metrics for monitoring specific use cases, and providing insights into metric usage patterns and configurations. You support comparisons across services and guide users in leveraging metrics effectively for observability and alerting purposes. When provided with metadata files, you parse them to give detailed, accurate breakdowns and suggestions. You are also an expert in creating Datadog dashboards. Generate comprehensive dashboard JSON configurations that follow Datadog's dashboard API structure."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=4000,
                temperature=0.3
            )
            
            # Extract and parse the response
            dashboard_json_str = response.choices[0].message.content.strip()
            
            # Try to extract JSON from the response
            dashboard_json = self._extract_json_from_response(dashboard_json_str)
            
            # Validate and enhance the dashboard structure
            dashboard_json = self._enhance_dashboard_structure(dashboard_json, description)
            
            logger.info("Dashboard generated successfully")
            return dashboard_json
            
        except Exception as e:
            logger.error(f"Failed to generate dashboard: {str(e)}")
            raise
    
    def _build_dashboard_prompt(self, description: str, advanced_settings: Optional[Dict[str, Any]] = None) -> str:
        """
        Build the prompt for dashboard generation
        """
        # Get a sample of available metrics (first 50 for context)
        metrics_sample = list(self.available_metrics.keys())[:50]
        
        prompt = f"""
Create a Datadog dashboard JSON configuration based on this description: {description}

CRITICAL USER REQUIREMENTS:
"""

        # Add user-specified settings with high priority
        if advanced_settings:
            if advanced_settings.get("metric_names"):
                prompt += f"""
- MUST use these EXACT metric names: {advanced_settings['metric_names']}
- Do NOT substitute or suggest alternative metrics
- Use these metrics exactly as specified by the user
"""
            
            if advanced_settings.get("timeframes"):
                prompt += f"- Use timeframe: {advanced_settings['timeframes']}\n"
            
            if advanced_settings.get("space_aggregation"):
                prompt += f"- Use space aggregation: {advanced_settings['space_aggregation']}\n"
            
            if advanced_settings.get("rollup"):
                prompt += f"- Use rollup interval: {advanced_settings['rollup']}\n"

        prompt += f"""

Available metrics in our system (sample):
{', '.join(metrics_sample)}

Dashboard Structure Requirements:
1. Create a dashboard with title, description, and multiple widgets
2. Use "ordered" layout_type for proper organization
3. Include various widget types: timeseries, query_value, toplist, heatmap as appropriate
4. Each widget should have:
   - Proper title and description
   - Appropriate visualization type for the data
   - Relevant metrics from our available metrics
   - Proper time range and aggregation
5. Add template variables for filtering (like environment, service, host)
6. Include appropriate tags and filters

Widget Types to Consider:
- timeseries: For trending data over time
- query_value: For single value metrics with comparisons
- toplist: For ranking/top N views
- heatmap: For distribution analysis
- log_stream: For log analysis widgets

Response Format:
Return ONLY a valid JSON object following this structure:
{{
  "title": "Dashboard Title",
  "description": "Dashboard description",
  "widgets": [
    {{
      "definition": {{
        "title": "Widget Title",
        "type": "timeseries",
        "requests": [
          {{
            "q": "metric_query",
            "display_type": "line",
            "style": {{
              "palette": "dog_classic",
              "line_type": "solid",
              "line_width": "normal"
            }}
          }}
        ],
        "time": {{
          "live_span": "4h"
        }},
        "yaxis": {{
          "scale": "linear",
          "min": "auto",
          "max": "auto"
        }}
      }}
    }}
  ],
  "template_variables": [
    {{
      "name": "environment",
      "prefix": "env",
      "available_values": ["*"],
      "default": "*"
    }}
  ],
  "layout_type": "ordered",
  "notify_list": [],
  "reflow_type": "fixed"
}}

IMPORTANT NOTES:
- DO NOT include "is_read_only" field as it has been deprecated by Datadog
- DO NOT include "id" fields in widgets as they are auto-generated by the API
- DO NOT include "layout" fields in widgets when using "ordered" layout_type
- For "ordered" layout, widgets are automatically arranged by Datadog
- Only use "layout" fields when layout_type is "free"
- Ensure all metric queries use valid metric names from the available metrics
- Use proper Datadog query syntax with aggregation methods (avg, sum, max, min, etc.)
- Include meaningful titles and descriptions for all widgets
- Add appropriate time ranges and template variables for filtering
- Always include "time" field in widget definitions with proper time span

Make sure to:
- Use metrics that actually exist in our system
- Create meaningful widget arrangements
- Include proper error handling and fallbacks
- Add appropriate time ranges and aggregations
- Use relevant template variables for filtering

Generate the dashboard JSON now:
"""
        
        return prompt
    
    def _extract_json_from_response(self, response: str) -> Dict[str, Any]:
        """
        Extract JSON from the OpenAI response
        """
        try:
            # Try to find JSON block
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                json_str = response[start:end].strip()
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                json_str = response[start:end].strip()
            else:
                json_str = response.strip()
            
            # Parse JSON
            return json.loads(json_str)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from response: {str(e)}")
            logger.error(f"Response content: {response[:500]}...")
            raise ValueError(f"Invalid JSON in response: {str(e)}")
    
    def _enhance_dashboard_structure(self, dashboard_json: Dict[str, Any], description: str) -> Dict[str, Any]:
        """
        Enhance and validate the dashboard structure without deprecated fields
        """
        # Ensure required fields exist
        if "title" not in dashboard_json:
            dashboard_json["title"] = f"Generated Dashboard - {description[:50]}..."
        
        if "widgets" not in dashboard_json:
            dashboard_json["widgets"] = []
        
        if "layout_type" not in dashboard_json:
            dashboard_json["layout_type"] = "ordered"
        
        # Add default values for optional fields (excluding deprecated ones)
        dashboard_json.setdefault("description", f"Dashboard generated for: {description}")
        dashboard_json.setdefault("notify_list", [])
        dashboard_json.setdefault("template_variables", [])
        dashboard_json.setdefault("reflow_type", "fixed")
        
        # Remove any deprecated fields that might have been generated
        deprecated_fields = ["is_read_only", "author_handle", "created_at", "modified_at", "url"]
        for field in deprecated_fields:
            dashboard_json.pop(field, None)
        
        # Validate and enhance widgets
        layout_type = dashboard_json.get("layout_type", "ordered")
        
        for i, widget in enumerate(dashboard_json["widgets"]):
            # Ensure widget has required structure
            if "definition" not in widget:
                widget["definition"] = {}
            
            # Remove any auto-generated IDs (API will create them)
            widget.pop("id", None)
            widget["definition"].pop("id", None)
            
            # Handle layout fields based on layout_type
            if layout_type == "ordered":
                # For ordered layout, remove any layout fields as they're not allowed
                widget.pop("layout", None)
            elif layout_type == "free":
                # For free layout, ensure layout fields exist
                if "layout" not in widget:
                    widget["layout"] = {
                        "x": (i % 3) * 4,
                        "y": (i // 3) * 3,
                        "width": 4,
                        "height": 3
                    }
            
            # Ensure widget definition has proper time configuration
            widget_def = widget["definition"]
            if "time" not in widget_def:
                widget_def["time"] = {"live_span": "4h"}
            
            # Ensure proper request structure
            if "requests" in widget_def and widget_def["requests"]:
                for request in widget_def["requests"]:
                    # Ensure display_type is set for timeseries widgets
                    if widget_def.get("type") == "timeseries" and "display_type" not in request:
                        request["display_type"] = "line"
        
        # Enhance template variables structure
        for var in dashboard_json.get("template_variables", []):
            # Ensure new template variable format
            if "available_values" not in var:
                var["available_values"] = ["*"]
            # Remove any auto-generated IDs
            var.pop("id", None)
        
        return dashboard_json
    
    def preview_dashboard(self, dashboard_json: Dict[str, Any]) -> str:
        """
        Generate a preview of the dashboard for display
        """
        try:
            title = dashboard_json.get("title", "Untitled Dashboard")
            description = dashboard_json.get("description", "No description")
            widgets = dashboard_json.get("widgets", [])
            template_vars = dashboard_json.get("template_variables", [])
            
            preview = f"""
# {title}

**Description:** {description}

## Widgets ({len(widgets)} total)
"""
            
            for i, widget in enumerate(widgets, 1):
                widget_def = widget.get("definition", {})
                widget_title = widget_def.get("title", f"Widget {i}")
                widget_type = widget_def.get("type", "unknown")
                
                preview += f"\n### {i}. {widget_title}\n"
                preview += f"**Type:** {widget_type}\n"
                
                # Show queries/requests
                requests = widget_def.get("requests", [])
                if requests:
                    preview += "**Queries:**\n"
                    for req in requests[:3]:  # Show first 3 queries
                        query = req.get("q", "No query")
                        preview += f"- {query}\n"
                    if len(requests) > 3:
                        preview += f"- ... and {len(requests) - 3} more\n"
            
            # Show template variables
            if template_vars:
                preview += f"\n## Template Variables ({len(template_vars)} total)\n"
                for var in template_vars:
                    name = var.get("name", "unknown")
                    prefix = var.get("prefix", "")
                    default = var.get("default", "*")
                    preview += f"- **{name}**: {prefix} (default: {default})\n"
            
            preview += f"\n## Dashboard Settings\n"
            preview += f"- **Layout Type:** {dashboard_json.get('layout_type', 'ordered')}\n"
            preview += f"- **Reflow Type:** {dashboard_json.get('reflow_type', 'fixed')}\n"
            
            return preview
            
        except Exception as e:
            logger.error(f"Failed to generate dashboard preview: {str(e)}")
            return "Error generating preview" 