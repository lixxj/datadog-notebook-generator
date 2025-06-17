"""
Notebook Generator using LLM
Generates Datadog notebook JSON based on user requirements
"""

import json
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime
import openai
from openai import OpenAI
from metrics_loader import MetricsLoader, Metric


class NotebookGenerator:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.example_notebook = self._load_example_notebook()
        self.metrics_loader = MetricsLoader()
    
    def _load_example_notebook(self) -> Dict[str, Any]:
        """Load the example notebook structure"""
        try:
            with open('NotebookExample1.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Fallback example structure
            return {
                "data": {
                    "type": "notebooks",
                    "attributes": {
                        "name": "Generated Notebook",
                        "cells": [],
                        "time": {"live_span": "1h"},
                        "metadata": {
                            "take_snapshots": False,
                            "is_template": False,
                            "is_favorite": False,
                            "type": None
                        },
                        "template_variables": [],
                        "status": "published"
                    }
                }
            }
    
    def generate_notebook(self, user_request: str, author_info: Optional[Dict] = None, advanced_settings: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Generate a notebook based on user request
        
        Args:
            user_request: Natural language description of what the notebook should contain
            author_info: Optional author information (deprecated)
            advanced_settings: Optional advanced settings including metric names, timeframes, rollup, etc.
            
        Returns:
            Dictionary containing the notebook JSON structure
        """
        # Create prompt for LLM
        prompt = self._create_prompt(user_request, advanced_settings)
        
        try:
            # Get LLM response
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a Datadog metric expert designed to help users understand and utilize available metrics in the Datadog ecosystem. You can interpret and explain metadata from various cloud services like Amazon EC2, S3, SQS, VPC, and Azure Functions, as well as on-premises systems. Your role includes clarifying metric definitions, recommending appropriate metrics for monitoring specific use cases, and providing insights into metric usage patterns and configurations. You support comparisons across services and guide users in leveraging metrics effectively for observability and alerting purposes. When provided with metadata files, you parse them to give detailed, accurate breakdowns and suggestions. You are also an expert in creating Datadog notebooks. You must respond with valid JSON only. Do not include any text before or after the JSON structure."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=4000
            )
            
            # Parse the response
            llm_response = response.choices[0].message.content.strip()
            
            try:
                # Try to parse the LLM response as JSON directly
                notebook_json = json.loads(llm_response)
                
                # Enhance with author info if provided
                if author_info:
                    if "data" in notebook_json and "attributes" in notebook_json["data"]:
                        notebook_json["data"]["attributes"]["author"] = author_info
                
                # Ensure all required fields are present
                notebook_json = self._validate_and_enhance_notebook(notebook_json, user_request)
                
                return notebook_json
                
            except json.JSONDecodeError:
                # If JSON parsing fails, extract cells from text response
                cells = self._extract_cells_from_response(llm_response, user_request)
                return self._create_notebook_structure(user_request, cells, author_info)
            
        except Exception as e:
            print(f"Error generating notebook with LLM: {e}")
            # Fallback to basic notebook
            return self._create_basic_notebook(user_request, author_info)
    
    def _create_prompt(self, user_request: str, advanced_settings: Optional[Dict] = None) -> str:
        """Create a detailed prompt for the LLM with example notebook structure and real metrics"""
        example_structure = json.dumps(self.example_notebook, indent=2)
        
        # Get relevant metrics for the user request
        suggested_metrics = self.metrics_loader.suggest_metrics_for_request(user_request)
        
        # Format metrics for the prompt
        metrics_info = []
        user_specified_metrics = False
        
        # Check if user specified specific metrics
        if advanced_settings and advanced_settings.get("metric_names"):
            user_specified_metrics = True
            user_metrics = [m.strip() for m in advanced_settings["metric_names"].split(",")]
            metrics_info = [f"- {metric} (USER SPECIFIED - MUST USE THIS EXACT METRIC NAME)" for metric in user_metrics]
            metrics_text = "USER SPECIFIED METRICS (MUST USE THESE EXACT NAMES):\n" + "\n".join(metrics_info)
        else:
            # Use AI-suggested metrics
            for metric in suggested_metrics[:15]:  # Limit to 15 most relevant
                metrics_info.append(f"- {metric.name}: {metric.description} (Type: {metric.type}, Unit: {metric.unit_name})")
            metrics_text = "SUGGESTED METRICS:\n" + ("\n".join(metrics_info) if metrics_info else "No specific metrics found, use general system metrics.")
        
        # Get integration summary
        integrations = self.metrics_loader.get_available_integrations()
        integrations_text = ", ".join(integrations)
        
        # Process additional advanced settings
        advanced_settings_text = ""
        if advanced_settings:
            settings_parts = []
            
            if advanced_settings.get("timeframes"):
                settings_parts.append(f"TIMEFRAME: MUST use {advanced_settings['timeframes']} as the live_span (do not auto-select)")
            
            if advanced_settings.get("space_aggregation"):
                settings_parts.append(f"SPACE AGGREGATION: MUST use {advanced_settings['space_aggregation']} aggregation in all metric queries (format: {advanced_settings['space_aggregation']}:metric_name)")
            
            if advanced_settings.get("rollup"):
                settings_parts.append(f"ROLLUP INTERVAL: MUST set rollup interval to {advanced_settings['rollup']} (do not auto-select)")
            
            if settings_parts:
                advanced_settings_text = f"\nCRITICAL USER REQUIREMENTS - MUST FOLLOW EXACTLY:\n{chr(10).join(settings_parts)}\nThese settings OVERRIDE any auto-selection logic.\n"
        
        return f"""
You are an expert Datadog notebook creator. Create a complete Datadog notebook JSON structure based on this user request: "{user_request}"

Here is an example of the exact JSON structure that Datadog expects:

{example_structure}

AVAILABLE REAL METRICS FOR THIS REQUEST:
{metrics_text}

AVAILABLE INTEGRATIONS: {integrations_text}
{advanced_settings_text}
IMPORTANT: You must return a complete, valid JSON structure that follows this exact format.

Key requirements:
1. The root structure must have "data" with "type": "notebooks" and "attributes"
2. "attributes" must contain: name, cells, time, metadata, template_variables, status
3. Each cell in "cells" array must have: type: "notebook_cells", id, and attributes.definition
4. Cell definition types can be: "markdown", "timeseries", "query_value", "log_stream", "distribution"

For the user request "{user_request}", create appropriate cells:

MARKDOWN CELLS: Use for explanations, headers, and documentation
- Set type: "markdown" 
- Include "text" field with markdown content

TIMESERIES CELLS: Use for metric visualizations
- Set type: "timeseries"
- Include "requests" array with queries
- Each request needs: display_type, q (query), style
- USE THE EXACT METRICS PROVIDED ABOVE - if user specified metrics, YOU MUST USE THOSE EXACT METRIC NAMES
- Format queries as: "avg:metric_name" or "sum:metric_name" etc.
- CRITICAL: When user specifies metrics like "system.cpu.user", use that EXACT name, not aws.ec2.cpu_utilization

QUERY_VALUE CELLS: Use for single metric displays, KPIs
- Set type: "query_value" 
- Include single metric query for current value
- Use real metrics from the list above

Choose an appropriate time range in "time.live_span":
- "5m", "15m", "1h", "4h", "1d", "2d", "1w" based on the use case

Generate a complete, valid JSON response that directly addresses the user's request with the EXACT METRICS provided above. Make sure all cell IDs are unique and:
- If USER SPECIFIED METRICS are provided, you MUST use those exact metric names in your queries
- Do NOT substitute different metrics (e.g., don't use aws.ec2.cpu_utilization when user specified system.cpu.user)
- Use the exact metric names as provided by the user or suggested by the system
"""
    
    def _extract_cells_from_response(self, llm_response: str, user_request: str) -> List[Dict[str, Any]]:
        """Extract and structure cells from LLM response"""
        cells = []
        
        # Add an introductory markdown cell
        intro_cell = {
            "type": "notebook_cells",
            "id": self._generate_cell_id(),
            "attributes": {
                "definition": {
                    "type": "markdown",
                    "text": f"# {self._generate_title(user_request)}\n\nThis notebook was generated based on your request: \"{user_request}\"\n\nGenerated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                }
            }
        }
        cells.append(intro_cell)
        
        # Parse LLM response and create appropriate cells
        if "timeseries" in llm_response.lower() or "metric" in llm_response.lower():
            # Add a timeseries cell
            timeseries_cell = {
                "type": "notebook_cells",
                "id": self._generate_cell_id(),
                "attributes": {
                    "definition": {
                        "type": "timeseries",
                        "requests": [
                            {
                                "display_type": "line",
                                "q": self._generate_metric_query(user_request),
                                "style": {
                                    "line_type": "solid",
                                    "line_width": "normal",
                                    "palette": "dog_classic"
                                }
                            }
                        ],
                        "show_legend": True,
                        "yaxis": {"scale": "linear"}
                    }
                }
            }
            cells.append(timeseries_cell)
        
        # Add explanatory markdown
        explanation_cell = {
            "type": "notebook_cells",
            "id": self._generate_cell_id(),
            "attributes": {
                "definition": {
                    "type": "markdown",
                    "text": f"## Analysis\n\nThis visualization shows key metrics relevant to your request. You can:\n- Adjust the time range using the time picker\n- Add filters using template variables\n- Modify queries to focus on specific hosts or services"
                }
            }
        }
        cells.append(explanation_cell)
        
        return cells
    
    def _generate_metric_query(self, user_request: str) -> str:
        """Generate appropriate metric query based on user request using real metrics"""
        suggested_metrics = self.metrics_loader.suggest_metrics_for_request(user_request)
        
        if suggested_metrics:
            # Use the first suggested metric
            metric = suggested_metrics[0]
            return self.metrics_loader.format_metric_for_query(metric, "avg", ["*"])
        else:
            # Fallback to popular metrics
            popular_metrics = self.metrics_loader.get_popular_metrics(1)
            if popular_metrics:
                return self.metrics_loader.format_metric_for_query(popular_metrics[0], "avg", ["*"])
            else:
                return "avg:system.cpu.user{*}"  # Ultimate fallback
    
    def _generate_title(self, user_request: str) -> str:
        """Generate appropriate title based on user request"""
        if len(user_request) > 50:
            return f"Analysis: {user_request[:47]}..."
        return f"Analysis: {user_request}"
    
    def _generate_cell_id(self) -> str:
        """Generate a unique cell ID"""
        return str(uuid.uuid4())[:8]
    
    def _create_notebook_structure(self, user_request: str, cells: List[Dict], author_info: Optional[Dict] = None) -> Dict[str, Any]:
        """Create the complete notebook structure"""
        now = datetime.now().isoformat() + "+00:00"
        
        notebook = {
            "data": {
                "type": "notebooks",
                "attributes": {
                    "name": self._generate_title(user_request),
                    "cells": cells,
                    "time": {"live_span": "1h"},
                    "metadata": {
                        "take_snapshots": False,
                        "is_template": False,
                        "is_favorite": False,
                        "type": "investigation"
                    },
                    "template_variables": [],
                    "status": "published",
                    "created": now,
                    "modified": now
                }
            }
        }
        
        if author_info:
            notebook["data"]["attributes"]["author"] = author_info
        
        return notebook
    
    def _validate_and_enhance_notebook(self, notebook_json: Dict[str, Any], user_request: str) -> Dict[str, Any]:
        """Validate and enhance the notebook JSON structure"""
        try:
            # Ensure basic structure exists
            if "data" not in notebook_json:
                notebook_json["data"] = {}
            
            if "attributes" not in notebook_json["data"]:
                notebook_json["data"]["attributes"] = {}
            
            attrs = notebook_json["data"]["attributes"]
            
            # Ensure required fields
            if "name" not in attrs:
                attrs["name"] = self._generate_title(user_request)
            
            if "cells" not in attrs:
                attrs["cells"] = []
            
            if "time" not in attrs:
                attrs["time"] = {"live_span": "1h"}
            
            if "metadata" not in attrs:
                attrs["metadata"] = {
                    "take_snapshots": False,
                    "is_template": False,
                    "is_favorite": False,
                    "type": "investigation"
                }
            
            if "template_variables" not in attrs:
                attrs["template_variables"] = []
            
            if "status" not in attrs:
                attrs["status"] = "published"
            
            # Add timestamps
            now = datetime.now().isoformat() + "+00:00"
            if "created" not in attrs:
                attrs["created"] = now
            if "modified" not in attrs:
                attrs["modified"] = now
            
            # Ensure cells have proper IDs
            for cell in attrs["cells"]:
                if "id" not in cell:
                    cell["id"] = self._generate_cell_id()
            
            # Set notebook type
            notebook_json["data"]["type"] = "notebooks"
            
            return notebook_json
            
        except Exception as e:
            print(f"Error validating notebook: {e}")
            return self._create_basic_notebook(user_request)
    
    def _create_basic_notebook(self, user_request: str, author_info: Optional[Dict] = None) -> Dict[str, Any]:
        """Create a basic notebook as fallback"""
        basic_cells = [
            {
                "type": "notebook_cells",
                "id": self._generate_cell_id(),
                "attributes": {
                    "definition": {
                        "type": "markdown",
                        "text": f"# {self._generate_title(user_request)}\n\nBasic notebook created for: {user_request}"
                    }
                }
            }
        ]
        
        return self._create_notebook_structure(user_request, basic_cells, author_info)
    
    def preview_notebook(self, notebook_json: Dict[str, Any]) -> str:
        """Generate a human-readable preview of the notebook"""
        try:
            attrs = notebook_json["data"]["attributes"]
            preview = f"📊 **Notebook Preview**\n\n"
            preview += f"**Title:** {attrs['name']}\n"
            preview += f"**Status:** {attrs['status']}\n"
            preview += f"**Time Range:** {attrs['time']['live_span']}\n"
            preview += f"**Cells:** {len(attrs['cells'])}\n\n"
            
            preview += "**Cell Contents:**\n"
            for i, cell in enumerate(attrs['cells'], 1):
                cell_def = cell["attributes"]["definition"]
                cell_type = cell_def["type"]
                preview += f"{i}. **{cell_type.title()} Cell**"
                
                if cell_type == "markdown":
                    text = cell_def["text"][:100]
                    if len(cell_def["text"]) > 100:
                        text += "..."
                    preview += f": {text}\n"
                elif cell_type == "timeseries":
                    query = cell_def["requests"][0]["q"]
                    preview += f": {query}\n"
                else:
                    preview += "\n"
            
            return preview
        except Exception as e:
            return f"Error generating preview: {str(e)}"
    
    def get_metrics_info(self) -> Dict[str, Any]:
        """Get information about available metrics for the UI"""
        return self.metrics_loader.get_metrics_summary()
    
    def get_suggested_metrics(self, user_request: str) -> List[Dict[str, Any]]:
        """Get suggested metrics for a user request (for UI display)"""
        metrics = self.metrics_loader.suggest_metrics_for_request(user_request)
        return [
            {
                "name": metric.name,
                "description": metric.description,
                "type": metric.type,
                "unit": metric.unit_name,
                "integration": metric.integration
            }
            for metric in metrics[:10]  # Limit for UI
        ] 