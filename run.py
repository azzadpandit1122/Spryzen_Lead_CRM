import uvicorn
import os
import sys

def main():
    print("==========================================================")
    print("               CLINETHUB STARTER UTILITY                  ")
    print("==========================================================")
    print("FastAPI Backend & static Frontend will run on:")
    print("Local URL: http://localhost:8000")
    print("Default Admin Account Credentials:")
    print("- Username: admin")
    print("- Password: admin123")
    print("==========================================================")
    
    try:
        uvicorn.run(
            "backend.main:app", 
            host="0.0.0.0", 
            port=8000, 
            reload=True
        )
    except KeyboardInterrupt:
        print("\nShutdown signal received. Stopping server...")
    except Exception as e:
        print(f"\nError starting server: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
