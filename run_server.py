"""
Uvicorn startup script with Windows event loop policy fix.
"""
import sys
import asyncio

# Set Windows Proactor event loop policy BEFORE importing anything else
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    print("✓ Windows Proactor event loop policy set")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="127.0.0.1",
        port=8000,
        log_level="info"
    )
