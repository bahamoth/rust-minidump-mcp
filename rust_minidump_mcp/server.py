"""FastMCP server entry point."""

from fastapi import FastAPI

app = FastAPI(title="Rust Minidump MCP")


@app.get("/healthz")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
