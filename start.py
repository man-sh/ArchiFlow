#!/usr/bin/env python3
"""
Startup script for the SDD Generator application.
Run this after ensuring vLLM server is running.
"""
import subprocess
import sys
import os

def check_vllm_server(url: str = "http://localhost:8000") -> bool:
    """Check if vLLM server is running."""
    import httpx
    try:
        response = httpx.get(f"{url}/v1/models", timeout=5.0)
        return response.status_code == 200
    except:
        return False

def main():
    print("🚀 SDD Generator Startup")
    print("=" * 50)
    
    # Check vLLM server
    print("\n📡 Checking vLLM server...")
    if check_vllm_server():
        print("✅ vLLM server is running")
    else:
        print("⚠️  vLLM server is not responding")
        print("   Please start vLLM server first:")
        print("   python -m vllm.entrypoints.api_server --model <your-model> --host 0.0.0.0 --port 8000")
        print("\n   Continuing anyway (API calls will fail until vLLM is started)...")
    
    # Change to backend directory
    os.chdir(os.path.join(os.path.dirname(__file__), 'backend'))
    
    # Start FastAPI server
    print("\n🔧 Starting FastAPI server...")
    print("   Access the application at: http://localhost:8080/static/index.html")
    print("   API documentation at: http://localhost:8080/docs")
    print("\n" + "=" * 50)
    
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "main:app", 
            "--host", "0.0.0.0", 
            "--port", "8080",
            "--reload"
        ], check=True)
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
