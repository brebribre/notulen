import os
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import uvicorn

load_dotenv()

# Environment configuration
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:5173')

ALLOWED_ORIGINS = [
    FRONTEND_URL,
    'http://127.0.0.1:8000',
    'http://localhost:8000'
]
if ENVIRONMENT == 'production':
    ALLOWED_ORIGINS.append('https://www.google.com')  # TODO: Change to the production URL

app = FastAPI(
    title="SaaS API",
    description="API for SaaS application",
    version="1.0.0",
    docs_url="/api/v1/docs",
    openapi_url="/apispec.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Health check endpoint
@app.get("/")
async def health_check():
    """Health check endpoint for Digital Ocean."""
    return {"status": "ok", "message": "API is running"}

# Import and include routers
from routes.audio_workers import router as audio_workers_router

app.include_router(audio_workers_router, prefix="", tags=["Audio Workers"])

# Handle OPTIONS requests for CORS preflight
@app.options("/{rest_of_path:path}")
async def preflight_handler(request: Request, rest_of_path: str):
    """Handle CORS preflight requests"""
    response = JSONResponse(content={})
    return response

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))  # Digital Ocean often uses port 8000
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=ENVIRONMENT == 'development'
    ) 