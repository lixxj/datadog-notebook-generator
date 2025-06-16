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


class NotebookGenerator:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.example_notebook = self._load_example_notebook()
    
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
    
    def generate_notebook(self, user_request: str, author_info: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Generate a notebook based on user request
        
        Args:
            user_request: Natural language description of what the notebook should contain
            author_info: Optional author information
            
        Returns:
            Dictionary containing the notebook JSON structure
        """
        # Create prompt for LLM
        prompt = self._create_prompt(user_request)
        
        try:
            # Get LLM response
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert in creating Datadog notebooks. You must respond with valid JSON only. Do not include any text before or after the JSON structure."},
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
    
    def _create_prompt(self, user_request: str) -> str:
        """Create a detailed prompt for the LLM with example notebook structure"""
        example_structure = json.dumps(self.example_notebook, indent=2)
        
        return f"""
You are an expert Datadog notebook creator. Create a complete Datadog notebook JSON structure based on this user request: "{user_request}"

Here is an example of the exact JSON structure that Datadog expects:

{example_structure}

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
- Choose appropriate metrics based on request:
  * CPU/Load: system.cpu.user, system.load.1, system.load.5
  * Memory: system.memory.used, system.memory.free, system.memory.usable
  * Disk: system.disk.used, system.disk.free, system.io.*
  * Network: system.net.bytes_sent, system.net.bytes_rcvd
  * Application: trace.*, apm.*, custom application metrics
  * Database: mysql.*, postgresql.*, mongodb.*
  * Web servers: nginx.*, apache.*

QUERY_VALUE CELLS: Use for single metric displays, KPIs
- Set type: "query_value" 
- Include single metric query for current value

Choose an appropriate time range in "time.live_span":
- "5m", "15m", "1h", "4h", "1d", "2d", "1w" based on the use case

Generate a complete, valid JSON response that directly addresses the user's request with relevant metrics and useful visualizations. Make sure all cell IDs are unique.
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
        """Generate appropriate metric query based on user request"""
        request_lower = user_request.lower()
        
        if any(word in request_lower for word in ['cpu', 'processor', 'load']):
            return "avg:system.cpu.user{*}"
        elif any(word in request_lower for word in ['memory', 'ram', 'mem']):
            return "avg:system.mem.used{*}"
        elif any(word in request_lower for word in ['disk', 'storage', 'io']):
            return "avg:system.disk.used{*}"
        elif any(word in request_lower for word in ['network', 'net', 'bandwidth']):
            return "avg:system.net.bytes_rcvd{*}"
        elif any(word in request_lower for word in ['application', 'app', 'response']):
            return "avg:application.response.time{*}"
        elif any(word in request_lower for word in ['error', 'exception', 'failure']):
            return "sum:application.errors{*}"
        else:
            return "avg:system.load.1{*}"
    
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