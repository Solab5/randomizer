from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
from pathlib import Path

# Get the absolute path to the base directory
BASE_DIR = Path(__file__).resolve().parent.parent

app = FastAPI()

# Mount static files
static_path = BASE_DIR / "app" / "static"
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Setup templates
templates = Jinja2Templates(directory=str(BASE_DIR / "app" / "templates"))

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    try:
        return templates.TemplateResponse("index.html", {"request": request})
    except Exception as e:
        return HTMLResponse(content=f"Error: {str(e)}", status_code=500)

@app.get("/{path:path}", response_class=HTMLResponse)
async def catch_all(request: Request, path: str):
    try:
        return templates.TemplateResponse("index.html", {"request": request})
    except Exception as e:
        return HTMLResponse(content=f"Error: {str(e)}", status_code=500) 