"""FastAPI application stub."""

from fastapi import FastAPI

app = FastAPI(title="[TBD]")


@app.get("/api/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8001, reload=True)