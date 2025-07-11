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

ALLOWED_ORIGINS = [FRONTEND_URL]
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
)

# Health check endpoint
@app.get("/")
async def health_check():
    """Health check endpoint for Digital Ocean."""
    return HTMLResponse(status_code=200)

# Import and include routers
from routes.telegram_routes import router as telegram_router
from routes.openai_route import router as openai_router
from routes.groups_route import router as groups_router
from routes.users_route import router as users_router
from routes.audio_files_route import router as audio_files_router
from routes.meetings_route import router as meetings_router

app.include_router(telegram_router, prefix="/telegram", tags=["Telegram"])
app.include_router(openai_router, prefix="/openai", tags=["OpenAI"])
app.include_router(groups_router, prefix="", tags=["Groups"])
app.include_router(users_router, prefix="", tags=["Users"])
app.include_router(audio_files_router, prefix="", tags=["Audio Files"])
app.include_router(meetings_router, prefix="", tags=["Meetings"])

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))  # Digital Ocean often uses port 8000
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=ENVIRONMENT == 'development'
    ) 