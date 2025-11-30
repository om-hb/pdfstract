from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request
import os
import tempfile
from pathlib import Path

from services.ocrfactory import OCRFactory
from services.base import OutputFormat
from services.logger import logger

app = FastAPI(title="PDFStract - Unified PDF extraction wrapper", description="Convert PDF files to Markdown using various libraries")

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files if they exist (built React app)
static_dir = Path("static")
if static_dir.exists():
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Ensure upload directory exists
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Initialize factory (singleton pattern)
factory = OCRFactory()

@app.get("/")
async def read_root(request: Request = None):
    """Serve the React app"""
    index_path = static_dir / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    else:
        # Fallback to old template if React app not built
        from fastapi.templating import Jinja2Templates
        templates = Jinja2Templates(directory="templates")
        return templates.TemplateResponse("index.html", {"request": request or Request})

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.get("/libraries")
async def get_available_libraries():
    """Get list of available conversion libraries"""
    return {"libraries": factory.list_all_converters()}

@app.post("/convert")
async def convert_pdf(
    file: UploadFile = File(...),
    library: str = Form(...),
    output_format: str = Form("markdown")
):
    """Convert PDF using specified library and format"""
    
    # Validate file type
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Validate output format
    try:
        format_enum = OutputFormat(output_format.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid output format. Supported: {[f.value for f in OutputFormat]}"
        )
    
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_file_path = temp_file.name
    
    try:
        logger.info(f"Starting conversion with library: {library}, format: {output_format}")
        # Convert using factory
        result = await factory.convert_async(
            converter_name=library,
            file_path=temp_file_path,
            output_format=format_enum
        )
        
        logger.info(f"Conversion successful with {library}")
        response_data = {
            "success": True,
            "library_used": library,
            "filename": file.filename,
            "format": output_format
        }
        
        if format_enum == OutputFormat.JSON:
            response_data["data"] = result
        else:
            response_data["content"] = result
        
        return JSONResponse(response_data)
    
    except ValueError as e:
        # User-friendly errors (e.g., text-only PDF for DeepSeek-OCR)
        error_msg = str(e)
        logger.warning(f"Conversion rejected: {error_msg}")
        raise HTTPException(status_code=400, detail=error_msg)
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Conversion failed: {error_msg}")
        logger.exception("Full error traceback:")
        raise HTTPException(status_code=500, detail=error_msg)
    
    finally:
        # Clean up temporary file
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

# Catch-all route for React Router (must be after all API routes)
if static_dir.exists():
    @app.get("/{full_path:path}")
    async def serve_react_app(full_path: str):
        """Catch-all route to serve React app for client-side routing"""
        # Don't catch API routes
        if full_path.startswith(("api/", "libraries", "convert", "health", "static")):
            raise HTTPException(status_code=404, detail="Not found")
        index_path = static_dir / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        raise HTTPException(status_code=404, detail="React app not built")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 