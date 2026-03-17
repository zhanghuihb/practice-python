"""
Files Router - 文件操作 API
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from services.file_service import file_service
import config

router = APIRouter()


class CopyMoveRequest(BaseModel):
    """复制/移动请求"""
    source: str
    destination: str


class MkdirRequest(BaseModel):
    """创建目录请求"""
    parent: str
    name: str


@router.get("/list")
async def list_files(path: str = ""):
    """列出目录内容"""
    result = file_service.list_directory(path)
    
    if "error" in result:
        raise HTTPException(status_code=result.get("code", 400), detail=result["error"])
    
    return result


@router.get("/info")
async def get_file_info(path: str):
    """获取单个文件/目录信息"""
    if not file_service.is_safe_path(path):
        raise HTTPException(status_code=400, detail="Invalid path")
    
    resolved = file_service._resolve_path(path)
    if resolved is None or not resolved.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return file_service.get_file_info(resolved)


@router.get("/subdirs")
async def get_subdirectories(path: str = ""):
    """获取子目录列表（用于目录选择器）"""
    dirs = file_service.get_subdirectories(path)
    return {"directories": dirs, "path": path}


@router.post("/copy")
async def copy_file(request: CopyMoveRequest):
    """复制文件"""
    result = file_service.copy_file(request.source, request.destination)
    
    if "error" in result:
        raise HTTPException(status_code=result.get("code", 400), detail=result["error"])
    
    return result


@router.post("/move")
async def move_file(request: CopyMoveRequest):
    """移动文件"""
    result = file_service.move_file(request.source, request.destination)
    
    if "error" in result:
        raise HTTPException(status_code=result.get("code", 400), detail=result["error"])
    
    return result


@router.post("/trash")
async def move_to_trash(path: str):
    """移动到回收站"""
    result = file_service.move_to_trash(path)
    
    if "error" in result:
        raise HTTPException(status_code=result.get("code", 400), detail=result["error"])
    
    return result


@router.post("/mkdir")
async def create_directory(request: MkdirRequest):
    """创建新目录"""
    result = file_service.create_directory(request.parent, request.name)
    
    if "error" in result:
        raise HTTPException(status_code=result.get("code", 400), detail=result["error"])
    
    return result


@router.post("/upload")
async def upload_file(
    path: str = Form(""),
    files: List[UploadFile] = File(...)
):
    """上传文件"""
    results = []
    
    for file in files:
        # 检查文件大小
        content = await file.read()
        if len(content) > config.UPLOAD_MAX_SIZE:
            results.append({
                "filename": file.filename,
                "error": "File too large",
                "success": False
            })
            continue
        
        result = file_service.save_upload(path, file.filename, content)
        result["filename"] = file.filename
        result["success"] = "error" not in result
        results.append(result)
    
    return {"uploads": results}


@router.get("/search")
async def search_files(path: str = "", query: str = ""):
    """搜索文件（简单名称匹配）"""
    if not query:
        return {"results": [], "query": query}
    
    result = file_service.list_directory(path)
    if "error" in result:
        raise HTTPException(status_code=result.get("code", 400), detail=result["error"])
    
    query_lower = query.lower()
    matches = [
        item for item in result["items"]
        if query_lower in item["name"].lower()
    ]
    
    return {"results": matches, "query": query}
