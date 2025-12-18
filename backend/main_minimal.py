"""
Minimal FastAPI backend for Railway deployment
This bypasses all optional dependencies and just runs a basic server
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Shopify AI Backend", version="1.0.0")

# CORS - Configure for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with your Streamlit URL after deployment
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "service": "Shopify AI Backend",
        "status": "running",
        "version": "1.0.0",
        "mode": "minimal"
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "shopify-ai-backend"
    }

@app.get("/ready")
def ready():
    return {
        "status": "ready",
        "checks": {
            "api": "ok"
        }
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
