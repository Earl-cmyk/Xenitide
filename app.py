#!/usr/bin/env python3
"""
Xenitide Backend Application Runner
Simple entry point for running the FastAPI application
"""

import uvicorn
import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

def main():
    """Main application entry point"""
    
    # Check if .env file exists
    env_file = Path(__file__).parent / ".env"
    if not env_file.exists():
        print("❌ .env file not found!")
        print("Please copy .env.example to .env and fill in your credentials")
        print("Run: cp .env.example .env")
        return
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv(env_file)
    
    # Check required environment variables
    required_vars = ["SUPABASE_URL", "SUPABASE_KEY", "JWT_SECRET_KEY"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please check your .env file")
        return
    
    print("🚀 Starting Xenitide Backend...")
    print(f"📍 Environment: {'Development' if os.getenv('DEBUG', 'false').lower() == 'true' else 'Production'}")
    print(f"🌐 API Documentation: http://localhost:8000/docs")
    print(f"🏥 Health Check: http://localhost:8000/health")
    print(f"📊 API Root: http://localhost:8000/")
    print("="*60)
    
    try:
        # Import and run the FastAPI app
        from app.main import app
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            reload=os.getenv("DEBUG", "false").lower() == "true",
            log_level="info"
        )
        
    except ImportError as e:
        print(f"❌ Failed to import application: {e}")
        print("Make sure you're in the project root directory")
        print("Install dependencies: pip install -r backend/requirements.txt")
        
    except Exception as e:
        print(f"❌ Failed to start application: {e}")

if __name__ == "__main__":
    main()
