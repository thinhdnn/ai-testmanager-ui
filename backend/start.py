#!/usr/bin/env python3
"""
Startup script for AI Test Manager Backend
"""

import uvicorn
import os
import sys

if __name__ == "__main__":
    # Add the current directory to Python path
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    # Run the application
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 