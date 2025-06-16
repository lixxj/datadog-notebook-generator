"""
Main FastAPI application for Notebook Generation and Deployment with LLM
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
import json
import logging
import os
from pathlib import Path

# Import our custom modules
from notebook_generator import NotebookGenerator
from datadog_client import DatadogClient

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
datadog_client = None

if OPENAI_API_KEY:
    notebook_generator = NotebookGenerator(OPENAI_API_KEY)
    logger.info("Notebook generator initialized")
else:
    logger.warning("OpenAI API key not provided")

if DATADOG_API_KEY and DATADOG_APP_KEY:
    datadog_client = DatadogClient(DATADOG_API_KEY, DATADOG_APP_KEY, DATADOG_BASE_URL)
    logger.info("Datadog client initialized")
else:
    logger.warning("Datadog API credentials not provided")

# Static files for frontend
static_dir = Path("static")
if static_dir.exists():
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Pydantic models
class NotebookRequest(BaseModel):
    description: str
    author_email: Optional[str] = None
    author_name: Optional[str] = None
    create_in_datadog: bool = False

class NotebookResponse(BaseModel):
    success: bool
    message: str
    notebook_json: Optional[Dict[str, Any]] = None
    datadog_notebook_id: Optional[str] = None
    preview: Optional[str] = None

# API Routes
@app.get("/")
async def root():
    """Serve the main frontend page"""
    return FileResponse('static/index.html')

@app.post("/generate", response_model=NotebookResponse)
async def generate_notebook(request: NotebookRequest):
    """Generate a notebook based on user description"""
    
    if not notebook_generator:
        raise HTTPException(status_code=500, detail="Notebook generator not initialized - OpenAI API key missing")
    
    try:
        # Create author info if provided
        author_info = None
        if request.author_email or request.author_name:
            author_info = {
                "name": request.author_name or "Unknown",
                "email": request.author_email or "unknown@example.com",
                "handle": request.author_email or "unknown@example.com"
            }
        
        # Generate notebook
        notebook_json = notebook_generator.generate_notebook(request.description, author_info)
        
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
            
            datadog_notebook_id = result.get("data", {}).get("id")
        
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
        "openai_configured": notebook_generator is not None,
        "datadog_configured": datadog_client is not None
    }
    
    if datadog_client:
        connection_test = datadog_client.test_connection()
        status["datadog_connection"] = connection_test["status"]
    
    return status

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

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="debug" if DEBUG else "info") 