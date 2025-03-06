import os
import sys

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(__file__))

"""
Passenger WSGI adapter for shared hosting environments.
Converts the FastAPI (ASGI) application to WSGI.
"""

try:
    # Try to import the FastAPI app
    try:
        # When in standard directory structure
        from app.main import app as fastapi_app
    except ImportError:
        # Alternative import path
        from main import app as fastapi_app
    
    # Convert ASGI app to WSGI
    from asgiref.wsgi import ASGIToWSGIAdapter
    application = ASGIToWSGIAdapter(fastapi_app)
    
except Exception as e:
    # Fallback error handler if imports fail
    def application(environ, start_response):
        status = '500 Internal Server Error'
        response_headers = [('Content-type', 'text/plain')]
        start_response(status, response_headers)
        error_message = f"Failed to initialize application: {str(e)}"
        return [error_message.encode('utf-8')]