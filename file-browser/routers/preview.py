"""
Preview Router - 预览 API
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response, HTMLResponse, PlainTextResponse

from services.preview_service import preview_service

router = APIRouter()


@router.get("/image/{path:path}")
async def preview_image(path: str):
    """预览图片原图"""
    result = preview_service.get_image(path)
    
    if result is None:
        raise HTTPException(status_code=404, detail="Image not found")
    
    content, mime_type = result
    return Response(content=content, media_type=mime_type)


@router.get("/thumb/{path:path}")
async def preview_thumbnail(path: str, size: int = 200):
    """获取图片缩略图"""
    thumb = preview_service.get_thumbnail(path, (size, size))
    
    if thumb is None:
        raise HTTPException(status_code=404, detail="Cannot generate thumbnail")
    
    return Response(content=thumb, media_type="image/jpeg")


@router.get("/pdf/{path:path}")
async def preview_pdf(path: str):
    """获取 PDF 文件"""
    content = preview_service.get_pdf_content(path)
    
    if content is None:
        raise HTTPException(status_code=404, detail="PDF not found")
    
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": "inline"}
    )


@router.get("/text/{path:path}")
async def preview_text(path: str):
    """预览文本文件"""
    content = preview_service.get_text_content(path)
    
    if content is None:
        raise HTTPException(status_code=404, detail="Text file not found")
    
    return PlainTextResponse(content=content)


@router.get("/docx/{path:path}")
async def preview_docx(path: str):
    """预览 DOCX 文件（转换为 HTML）"""
    html = preview_service.get_docx_html(path)
    
    if html is None:
        raise HTTPException(status_code=404, detail="DOCX file not found")
    
    return HTMLResponse(content=html)


@router.get("/doc/{path:path}")
async def preview_doc(path: str):
    """预览 DOC 文件（转换为文本）"""
    text = preview_service.get_doc_text(path)
    
    if text is None:
        raise HTTPException(status_code=404, detail="DOC file not found")
    
    # 将文本包装为 HTML
    html = f"""
    <div class="doc-preview" style="
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        line-height: 1.6;
        padding: 20px;
        max-width: 800px;
        margin: 0 auto;
        white-space: pre-wrap;
        word-wrap: break-word;
    ">
{text}
    </div>
    """
    
    return HTMLResponse(content=html)


@router.get("/download/{path:path}")
async def download_file(path: str):
    """下载文件"""
    from pathlib import Path
    from services.file_service import file_service
    
    resolved = file_service._resolve_path(path)
    if resolved is None or not resolved.exists() or not resolved.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    
    content = resolved.read_bytes()
    filename = resolved.name
    
    return Response(
        content=content,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )
