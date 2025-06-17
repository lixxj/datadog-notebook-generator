"""
Main FastAPI application for Notebook Generation and Deployment with LLM
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import json
import logging
import os
from pathlib import Path
import uvicorn
from datetime import datetime
import asyncio

# Import our custom modules
from notebook_generator import NotebookGenerator
from dashboard_generator import DashboardGenerator
from datadog_client import DatadogClient
from metric_analysis_service import MetricAnalysisService

# Configuration
try:
    import config
    OPENAI_API_KEY = config.OPENAI_API_KEY
    DATADOG_API_KEY = config.DATADOG_API_KEY
    DATADOG_APP_KEY = config.DATADOG_APP_KEY
    DATADOG_BASE_URL = config.DATADOG_BASE_URL
    PORT = config.PORT
    DEBUG = config.DEBUG
except ImportError:
    # Fallback to environment variables
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    DATADOG_API_KEY = os.getenv("DATADOG_API_KEY", "")
    DATADOG_APP_KEY = os.getenv("DATADOG_APP_KEY", "")
    DATADOG_BASE_URL = os.getenv("DATADOG_BASE_URL", "https://api.datadoghq.com")
    PORT = int(os.getenv("PORT", "8000"))
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"

# Set up logging
logging.basicConfig(level=logging.INFO if not DEBUG else logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Notebook Generation and Deployment with LLM",
    description="Generate and deploy Datadog notebooks using LLM",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
notebook_generator = None
dashboard_generator = None
datadog_client = None
metric_analysis_service = None

if OPENAI_API_KEY:
    notebook_generator = NotebookGenerator(OPENAI_API_KEY)
    dashboard_generator = DashboardGenerator(OPENAI_API_KEY)
    logger.info("Notebook and dashboard generators initialized")
else:
    logger.warning("OpenAI API key not provided")

if DATADOG_API_KEY and DATADOG_APP_KEY:
    datadog_client = DatadogClient(DATADOG_API_KEY, DATADOG_APP_KEY, DATADOG_BASE_URL)
    logger.info("Datadog client initialized")
    
    # Initialize metric analysis service
    customer_metrics_endpoint = os.getenv("CUSTOMER_METRICS_ENDPOINT")
    metric_analysis_service = MetricAnalysisService(datadog_client, customer_metrics_endpoint)
    logger.info("Metric analysis service initialized")
else:
    logger.warning("Datadog API credentials not provided")

# Static files for frontend
static_dir = Path("static")
if static_dir.exists():
    app.mount("/static", StaticFiles(directory="static"), name="static")

# TypeRacer static files
typeracer_dir = Path("typeracer")
if typeracer_dir.exists():
    app.mount("/typeracer-static", StaticFiles(directory="typeracer"), name="typeracer-static")

# Pydantic models
class NotebookRequest(BaseModel):
    description: str
    metric_names: Optional[str] = None
    timeframes: Optional[str] = None
    space_aggregation: Optional[str] = None
    rollup: Optional[str] = None
    create_in_datadog: bool = False

class NotebookResponse(BaseModel):
    success: bool
    message: str
    notebook_json: Optional[Dict[str, Any]] = None
    datadog_notebook_id: Optional[str] = None
    preview: Optional[str] = None

class DashboardRequest(BaseModel):
    description: str
    metric_names: Optional[str] = None
    timeframes: Optional[str] = None
    space_aggregation: Optional[str] = None
    rollup: Optional[str] = None
    create_in_datadog: bool = False

class DashboardResponse(BaseModel):
    success: bool
    message: str
    dashboard_json: Optional[Dict[str, Any]] = None
    datadog_dashboard_id: Optional[str] = None
    preview: Optional[str] = None

class MetricAnalysisRequest(BaseModel):
    suggested_metrics: List[Dict[str, Any]]
    customer_id: Optional[str] = None

class MetricAnalysisResponse(BaseModel):
    success: bool
    message: str
    analysis: Optional[Dict[str, Any]] = None
    existing_metrics: List[str]
    missing_metrics: List[Dict[str, Any]]
    coverage_percentage: float
    recommendations: List[Dict[str, Any]]

# API Routes
@app.get("/")
async def root():
    """Serve the main frontend page"""
    return FileResponse('static/index.html')

@app.get("/typeracer")
async def typeracer():
    """Serve the typeracer game page"""
    return FileResponse('typeracer/index.html')

@app.post("/generate", response_model=NotebookResponse)
async def generate_notebook(request: NotebookRequest):
    """Generate a notebook based on user description"""
    
    if not notebook_generator:
        raise HTTPException(status_code=500, detail="Notebook generator not initialized - OpenAI API key missing")
    
    try:
        # Prepare advanced settings
        advanced_settings = {}
        if request.metric_names:
            advanced_settings["metric_names"] = request.metric_names
        if request.timeframes:
            advanced_settings["timeframes"] = request.timeframes
        if request.space_aggregation:
            advanced_settings["space_aggregation"] = request.space_aggregation
        if request.rollup:
            advanced_settings["rollup"] = request.rollup
        
        # Generate notebook
        notebook_json = notebook_generator.generate_notebook(request.description, None, advanced_settings)
        
        # Generate preview
        preview = notebook_generator.preview_notebook(notebook_json)
        
        # Create in Datadog if requested
        datadog_notebook_id = None
        if request.create_in_datadog:
            if not datadog_client:
                raise HTTPException(status_code=500, detail="Datadog client not initialized - API credentials missing")
            
            # Validate notebook structure
            validation = datadog_client.validate_notebook_structure(notebook_json)
            if not validation["valid"]:
                raise HTTPException(status_code=400, detail=f"Invalid notebook structure: {validation['errors']}")
            
            # Create notebook in Datadog
            result = datadog_client.create_notebook(notebook_json)
            if "error" in result:
                raise HTTPException(status_code=500, detail=f"Failed to create notebook in Datadog: {result['error']}")
            
            notebook_id = result.get("data", {}).get("id")
            datadog_notebook_id = str(notebook_id) if notebook_id is not None else None
        
        return NotebookResponse(
            success=True,
            message="Notebook generated successfully!",
            notebook_json=notebook_json,
            datadog_notebook_id=datadog_notebook_id,
            preview=preview
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate notebook: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate notebook: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    status = {
        "status": "healthy",
        "openai_configured": notebook_generator is not None and dashboard_generator is not None,
        "datadog_configured": datadog_client is not None
    }
    
    if datadog_client:
        connection_test = datadog_client.test_connection()
        status["datadog_connection"] = connection_test["status"]
    
    return status

# Metric Analysis Endpoints
@app.post("/metrics/analyze", response_model=MetricAnalysisResponse)
async def analyze_metrics(request: MetricAnalysisRequest):
    """Analyze suggested metrics against customer's existing metrics"""
    
    if not metric_analysis_service:
        raise HTTPException(status_code=500, detail="Metric analysis service not initialized - Datadog credentials missing")
    
    try:
        analysis = metric_analysis_service.analyze_metrics(
            request.suggested_metrics, 
            request.customer_id
        )
        
        return MetricAnalysisResponse(
            success=True,
            message="Metric analysis completed successfully!",
            analysis={
                "total_suggested": analysis.total_suggested,
                "coverage_percentage": analysis.coverage_percentage,
                "summary": f"{len(analysis.missing_metrics)} missing metrics found out of {analysis.total_suggested} suggested"
            },
            existing_metrics=analysis.existing_metrics,
            missing_metrics=analysis.missing_metrics,
            coverage_percentage=analysis.coverage_percentage,
            recommendations=analysis.recommendations
        )
        
    except Exception as e:
        logger.error(f"Failed to analyze metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze metrics: {str(e)}")

@app.get("/metrics/customer/{customer_id}")
async def get_customer_metrics(customer_id: str):
    """Get customer's existing metrics"""
    
    if not metric_analysis_service:
        raise HTTPException(status_code=500, detail="Metric analysis service not initialized")
    
    try:
        metrics = metric_analysis_service._get_customer_metrics(customer_id)
        return {
            "success": True,
            "customer_id": customer_id,
            "metrics": metrics,
            "count": len(metrics)
        }
        
    except Exception as e:
        logger.error(f"Failed to get customer metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get customer metrics: {str(e)}")

@app.get("/integration/{integration_name}/setup")
async def get_integration_setup(integration_name: str):
    """Get setup guide for a specific integration"""
    
    if not metric_analysis_service:
        raise HTTPException(status_code=500, detail="Metric analysis service not initialized")
    
    try:
        setup_guide = metric_analysis_service.get_setup_guide(integration_name)
        return {
            "success": True,
            "setup_guide": setup_guide
        }
        
    except Exception as e:
        logger.error(f"Failed to get setup guide: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get setup guide: {str(e)}")

@app.get("/integration/{integration_name}/metrics")
async def get_integration_metrics(integration_name: str):
    """Get available metrics for a specific integration"""
    
    if not datadog_client:
        raise HTTPException(status_code=500, detail="Datadog client not initialized")
    
    try:
        metrics = datadog_client.get_integration_metrics(integration_name)
        doc_info = datadog_client.get_integration_documentation(integration_name)
        
        return {
            "success": True,
            "integration": integration_name,
            "metrics": metrics,
            "documentation": doc_info,
            "count": len(metrics)
        }
        
    except Exception as e:
        logger.error(f"Failed to get integration metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get integration metrics: {str(e)}")

@app.get("/notebooks")
async def list_notebooks(count: int = 5):
    """List existing notebooks"""
    if not datadog_client:
        raise HTTPException(status_code=500, detail="Datadog client not initialized")
    
    result = datadog_client.list_notebooks(count=count)
    if "error" in result:
        raise HTTPException(status_code=500, detail=f"Failed to list notebooks: {result['error']}")
    
    return result

@app.get("/notebooks/{notebook_id}")
async def get_notebook(notebook_id: str):
    """Get a specific notebook"""
    if not datadog_client:
        raise HTTPException(status_code=500, detail="Datadog client not initialized")
    
    result = datadog_client.get_notebook(notebook_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=f"Notebook not found: {result['error']}")
    
    return result

@app.post("/validate")
async def validate_notebook(notebook_data: Dict[str, Any]):
    """Validate notebook structure"""
    if not datadog_client:
        raise HTTPException(status_code=500, detail="Datadog client not initialized")
    
    validation = datadog_client.validate_notebook_structure(notebook_data)
    return validation

@app.get("/metrics/info")
async def get_metrics_info():
    """Get information about available metrics"""
    if not notebook_generator:
        raise HTTPException(status_code=500, detail="Notebook generator not initialized")
    
    return notebook_generator.get_metrics_info()

@app.post("/metrics/suggest")
async def suggest_metrics(request: Dict[str, str]):
    """Get suggested metrics for a user request"""
    if not notebook_generator:
        raise HTTPException(status_code=500, detail="Notebook generator not initialized")
    
    user_request = request.get("description", "")
    if not user_request:
        raise HTTPException(status_code=400, detail="Description is required")
    
    suggested_metrics = notebook_generator.get_suggested_metrics(user_request)
    return {"suggested_metrics": suggested_metrics}

@app.get("/examples/{example_type}")
async def get_example_suggestions(example_type: str):
    """Get suggestions for different example types"""
    examples = {
        "performance": {
            "description": "Create a comprehensive performance monitoring notebook showing CPU usage, memory consumption, disk I/O, and network metrics for our web application servers. Include response time analysis, error rate tracking, and resource utilization trends over the past 24 hours. Focus on identifying bottlenecks and performance degradation patterns.",
            "suggested_metrics": ["system.cpu.user", "system.cpu.system", "system.mem.used", "system.mem.free", "system.disk.used", "system.net.bytes_rcvd", "system.net.bytes_sent"],
            "timeframe": "1d",
            "space_aggregation": "avg",
            "rollup": "5m",
            "tips": [
                "Monitor CPU usage patterns to identify peak load times",
                "Track memory consumption to detect potential memory leaks",
                "Analyze disk I/O to spot storage bottlenecks",
                "Compare network traffic with application response times"
            ]
        },
        "troubleshooting": {
            "description": "Build a troubleshooting guide notebook for diagnosing application issues including error analysis, log correlation, database performance metrics, and infrastructure health checks. Include automated alerts setup and incident response workflows with step-by-step diagnostic procedures.",
            "suggested_metrics": ["system.cpu.system", "system.mem.free", "system.load.1", "system.load.5", "system.load.15", "system.processes.count"],
            "timeframe": "4h",
            "space_aggregation": "max",
            "rollup": "1m",
            "tips": [
                "Use system load averages to understand overall system health",
                "Monitor process count for application stability",
                "Track memory availability for resource constraints",
                "Correlate CPU spikes with application errors"
            ]
        },
        "capacity": {
            "description": "Design a capacity planning notebook analyzing resource trends, growth patterns, and forecasting future infrastructure needs. Include CPU, memory, storage, and network utilization analysis with predictive modeling for scaling decisions and budget planning.",
            "suggested_metrics": ["system.cpu.idle", "system.mem.total", "system.mem.usable", "system.disk.free", "system.disk.total"],
            "timeframe": "1m",
            "space_aggregation": "avg",
            "rollup": "1h",
            "tips": [
                "Analyze long-term trends for accurate capacity planning",
                "Monitor resource utilization patterns over weeks/months",
                "Track growth rates to predict future needs",
                "Identify seasonal patterns in resource usage"
            ]
        }
    }
    
    if example_type not in examples:
        raise HTTPException(status_code=404, detail="Example type not found")
    
    return examples[example_type]

# Dashboard API Endpoints
@app.post("/generate-dashboard", response_model=DashboardResponse)
async def generate_dashboard(request: DashboardRequest):
    """Generate a dashboard based on user description"""
    
    if not dashboard_generator:
        raise HTTPException(status_code=500, detail="Dashboard generator not initialized - OpenAI API key missing")
    
    try:
        # Prepare advanced settings
        advanced_settings = {}
        if request.metric_names:
            advanced_settings["metric_names"] = request.metric_names
        if request.timeframes:
            advanced_settings["timeframes"] = request.timeframes
        if request.space_aggregation:
            advanced_settings["space_aggregation"] = request.space_aggregation
        if request.rollup:
            advanced_settings["rollup"] = request.rollup
        
        # Generate dashboard
        dashboard_json = dashboard_generator.generate_dashboard(request.description, None, advanced_settings)
        
        # Generate preview
        preview = dashboard_generator.preview_dashboard(dashboard_json)
        
        # Create in Datadog if requested
        datadog_dashboard_id = None
        if request.create_in_datadog:
            if not datadog_client:
                raise HTTPException(status_code=500, detail="Datadog client not initialized - API credentials missing")
            
            # Validate dashboard structure
            validation = datadog_client.validate_dashboard_structure(dashboard_json)
            if not validation["valid"]:
                raise HTTPException(status_code=400, detail=f"Invalid dashboard structure: {validation['errors']}")
            
            # Create dashboard in Datadog
            result = datadog_client.create_dashboard(dashboard_json)
            if "error" in result:
                raise HTTPException(status_code=500, detail=f"Failed to create dashboard in Datadog: {result['error']}")
            
            dashboard_id = result.get("id")
            datadog_dashboard_id = str(dashboard_id) if dashboard_id is not None else None
        
        return DashboardResponse(
            success=True,
            message="Dashboard generated successfully!",
            dashboard_json=dashboard_json,
            datadog_dashboard_id=datadog_dashboard_id,
            preview=preview
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate dashboard: {str(e)}")

@app.get("/dashboards")
async def list_dashboards(count: int = 5):
    """List existing dashboards"""
    if not datadog_client:
        raise HTTPException(status_code=500, detail="Datadog client not initialized")
    
    result = datadog_client.list_dashboards(count=count)
    if "error" in result:
        raise HTTPException(status_code=500, detail=f"Failed to list dashboards: {result['error']}")
    
    return result

@app.get("/dashboards/{dashboard_id}")
async def get_dashboard(dashboard_id: str):
    """Get a specific dashboard"""
    if not datadog_client:
        raise HTTPException(status_code=500, detail="Datadog client not initialized")
    
    result = datadog_client.get_dashboard(dashboard_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=f"Dashboard not found: {result['error']}")
    
    return result

@app.post("/validate-dashboard")
async def validate_dashboard(dashboard_data: Dict[str, Any]):
    """Validate dashboard structure"""
    if not datadog_client:
        raise HTTPException(status_code=500, detail="Datadog client not initialized")
    
    validation = datadog_client.validate_dashboard_structure(dashboard_data)
    return validation

@app.post("/preview")
async def generate_preview(request: NotebookRequest):
    """Generate a preview of the notebook without creating it in Datadog"""
    
    if not notebook_generator:
        raise HTTPException(status_code=500, detail="Notebook generator not initialized - OpenAI API key missing")
    
    try:
        # Prepare advanced settings
        advanced_settings = {}
        if request.metric_names:
            advanced_settings["metric_names"] = request.metric_names
        if request.timeframes:
            advanced_settings["timeframes"] = request.timeframes
        if request.space_aggregation:
            advanced_settings["space_aggregation"] = request.space_aggregation
        if request.rollup:
            advanced_settings["rollup"] = request.rollup
        
        # Generate notebook for preview only
        notebook_json = notebook_generator.generate_notebook(request.description, None, advanced_settings)
        
        # Generate text preview
        preview = notebook_generator.preview_notebook(notebook_json)
        
        return {
            "success": True,
            "message": "Preview generated successfully!",
            "notebook_json": notebook_json,
            "preview": preview,
            "live_preview_data": {
                "cells_count": len(notebook_json.get("data", {}).get("attributes", {}).get("cells", [])),
                "time_range": notebook_json.get("data", {}).get("attributes", {}).get("time", {}).get("live_span", "1h"),
                "status": "preview"
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to generate preview: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate preview: {str(e)}")

# Add new endpoint for getting integration patterns
@app.get("/integrations/patterns")
async def get_integration_patterns():
    """Get metric patterns from all integration CSV files"""
    try:
        patterns = {}
        metrics_dir = "metrics"
        
        if not os.path.exists(metrics_dir):
            return {"patterns": {}}
        
        # Load patterns from CSV files
        for filename in os.listdir(metrics_dir):
            if filename.endswith('.csv'):
                integration_name = filename.replace('_metadata.csv', '').replace('.csv', '')
                csv_path = os.path.join(metrics_dir, filename)
                
                try:
                    import pandas as pd
                    df = pd.read_csv(csv_path)
                    
                    # Extract unique metric prefixes
                    metric_names = df['metric_name'].tolist()
                    prefixes = set()
                    
                    for metric in metric_names:
                        if '.' in metric:
                            # Get the first two parts for pattern matching
                            parts = metric.split('.')
                            if len(parts) >= 2:
                                prefix = f"{parts[0]}.{parts[1]}"
                                prefixes.add(prefix)
                    
                    patterns[integration_name] = {
                        'prefixes': list(prefixes),
                        'metrics': metric_names[:10],  # Sample metrics for reference
                        'integration': df['integration'].iloc[0] if 'integration' in df.columns else integration_name
                    }
                    
                except Exception as e:
                    logger.error(f"Failed to load patterns from {filename}: {str(e)}")
                    continue
        
        return {"patterns": patterns}
        
    except Exception as e:
        logger.error(f"Failed to get integration patterns: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Run the application
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="debug" if DEBUG else "info") 