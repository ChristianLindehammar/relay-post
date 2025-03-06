"""
Direct execution script for the FastAPI application.
Run with: python run.py
"""

import uvicorn
import sys
import os

# Add the current directory to path if needed
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Try to import the FastAPI app
    try:
        # When in standard directory structure
        from app.main import app
    except ImportError:
        # Alternative import path
        from main import app
    
    if __name__ == "__main__":
        print("Starting FastAPI server on http://0.0.0.0:8000")
        uvicorn.run(app, host="0.0.0.0", port=8000)
        
except Exception as e:
    print(f"Error starting application: {e}")
    sys.exit(1)