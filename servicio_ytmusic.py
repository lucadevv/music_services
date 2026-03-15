"""Main entry point for YouTube Music Service."""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0", 
        port=8000,
        workers=4,
        log_level="warning",
        access_log=False,
        limit_concurrency=2000,
        limit_max_requests=10000,
        timeout_keep_alive=30,
        backlog=4096,
    )
