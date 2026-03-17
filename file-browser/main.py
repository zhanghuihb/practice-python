"""
File Browser - Main Application
文件浏览器主入口
"""
import argparse
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import uvicorn

import config
from routers import files, preview

# 创建 FastAPI 应用
app = FastAPI(
    title="File Browser",
    description="A lightweight file browser for Linux servers",
    version="1.0.0"
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory=config.STATIC_DIR), name="static")

# 配置模板引擎
templates = Jinja2Templates(directory=config.TEMPLATES_DIR)

# 注册路由
app.include_router(files.router, prefix="/api/files", tags=["files"])
app.include_router(preview.router, prefix="/api/preview", tags=["preview"])


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """主页面"""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "root_path": config.ROOT_PATH,
        "title": "File Browser"
    })


@app.get("/browse/{path:path}", response_class=HTMLResponse)
async def browse(request: Request, path: str = ""):
    """浏览指定路径"""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "root_path": config.ROOT_PATH,
        "current_path": path,
        "title": "File Browser"
    })


def main():
    """启动服务器"""
    parser = argparse.ArgumentParser(description="File Browser Server")
    parser.add_argument("--host", default=config.HOST, help="Host to bind")
    parser.add_argument("--port", type=int, default=config.PORT, help="Port to bind")
    parser.add_argument("--root", default=config.ROOT_PATH, help="Root directory to browse")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    
    args = parser.parse_args()
    
    # 更新配置
    if args.root:
        config.ROOT_PATH = args.root
    
    print(f"File Browser starting...")
    print(f"Root directory: {config.ROOT_PATH}")
    print(f"Server: http://{args.host}:{args.port}")
    
    uvicorn.run(
        "main:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )


if __name__ == "__main__":
    main()
