"""
Preview Service - 文档和图片预览服务
"""
import io
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple

from PIL import Image

import config


class PreviewService:
    """预览服务"""
    
    def __init__(self, root_path: str = None):
        self.root = Path(root_path or config.ROOT_PATH).resolve()
    
    def _resolve_path(self, rel_path: str) -> Optional[Path]:
        """解析并验证路径"""
        if not rel_path:
            return None
        
        clean_path = rel_path.strip('/').replace('\\', '/')
        full_path = (self.root / clean_path).resolve()
        
        try:
            full_path.relative_to(self.root)
            return full_path if full_path.exists() and full_path.is_file() else None
        except ValueError:
            return None
    
    def get_image(self, rel_path: str) -> Optional[Tuple[bytes, str]]:
        """获取图片内容"""
        path = self._resolve_path(rel_path)
        if path is None:
            return None
        
        suffix = path.suffix.lower()
        if suffix not in config.IMAGE_EXTENSIONS:
            return None
        
        # 确定 MIME 类型
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.bmp': 'image/bmp',
            '.svg': 'image/svg+xml',
            '.ico': 'image/x-icon'
        }
        
        mime_type = mime_types.get(suffix, 'application/octet-stream')
        
        try:
            return path.read_bytes(), mime_type
        except Exception:
            return None
    
    def get_thumbnail(self, rel_path: str, size: Tuple[int, int] = None) -> Optional[bytes]:
        """生成缩略图"""
        path = self._resolve_path(rel_path)
        if path is None:
            return None
        
        if size is None:
            size = config.THUMBNAIL_SIZE
        
        suffix = path.suffix.lower()
        if suffix not in config.IMAGE_EXTENSIONS or suffix == '.svg':
            return None
        
        try:
            with Image.open(path) as img:
                # 转换为 RGB（处理 RGBA、P 等模式）
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                
                # 生成缩略图
                img.thumbnail(size, Image.Resampling.LANCZOS)
                
                # 保存到内存
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=config.THUMBNAIL_QUALITY)
                return buffer.getvalue()
        except Exception:
            return None
    
    def get_text_content(self, rel_path: str, max_size: int = 1024 * 1024) -> Optional[str]:
        """获取文本文件内容"""
        path = self._resolve_path(rel_path)
        if path is None:
            return None
        
        # 限制文件大小
        if path.stat().st_size > max_size:
            content = path.read_bytes()[:max_size]
            try:
                return content.decode('utf-8', errors='replace') + "\n\n... (truncated)"
            except Exception:
                return None
        
        # 尝试多种编码
        for encoding in ['utf-8', 'gbk', 'gb2312', 'latin-1']:
            try:
                return path.read_text(encoding=encoding)
            except (UnicodeDecodeError, LookupError):
                continue
        
        return None
    
    def get_pdf_content(self, rel_path: str) -> Optional[bytes]:
        """获取 PDF 文件内容"""
        path = self._resolve_path(rel_path)
        if path is None:
            return None
        
        if path.suffix.lower() != '.pdf':
            return None
        
        try:
            return path.read_bytes()
        except Exception:
            return None
    
    def get_docx_html(self, rel_path: str) -> Optional[str]:
        """将 DOCX 转换为 HTML"""
        path = self._resolve_path(rel_path)
        if path is None:
            return None
        
        if path.suffix.lower() != '.docx':
            return None
        
        try:
            import mammoth
            
            with open(path, 'rb') as f:
                result = mammoth.convert_to_html(f)
                html = result.value
                
                # 添加基本样式
                styled_html = f"""
                <div class="docx-preview">
                    <style>
                        .docx-preview {{
                            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                            line-height: 1.6;
                            padding: 20px;
                            max-width: 800px;
                            margin: 0 auto;
                        }}
                        .docx-preview h1 {{ font-size: 2em; margin: 0.67em 0; }}
                        .docx-preview h2 {{ font-size: 1.5em; margin: 0.75em 0; }}
                        .docx-preview h3 {{ font-size: 1.17em; margin: 0.83em 0; }}
                        .docx-preview p {{ margin: 1em 0; }}
                        .docx-preview table {{
                            border-collapse: collapse;
                            width: 100%;
                            margin: 1em 0;
                        }}
                        .docx-preview th, .docx-preview td {{
                            border: 1px solid #ddd;
                            padding: 8px;
                            text-align: left;
                        }}
                        .docx-preview img {{ max-width: 100%; height: auto; }}
                    </style>
                    {html}
                </div>
                """
                return styled_html
        except ImportError:
            return "<p>mammoth library not installed</p>"
        except Exception as e:
            return f"<p>Error converting document: {str(e)}</p>"
    
    def get_doc_text(self, rel_path: str) -> Optional[str]:
        """
        获取 DOC 文件内容（需要 antiword）
        """
        path = self._resolve_path(rel_path)
        if path is None:
            return None
        
        if path.suffix.lower() != '.doc':
            return None
        
        try:
            # 尝试使用 antiword
            result = subprocess.run(
                ['antiword', str(path)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return result.stdout
            
            # antiword 失败，尝试其他方法
            return self._doc_fallback(path)
        
        except FileNotFoundError:
            # antiword 未安装
            return self._doc_fallback(path)
        except subprocess.TimeoutExpired:
            return "Error: Document processing timeout"
        except Exception as e:
            return f"Error reading document: {str(e)}"
    
    def _doc_fallback(self, path: Path) -> str:
        """DOC 文件备用处理方法"""
        try:
            # 尝试使用 libreoffice
            with tempfile.TemporaryDirectory() as tmpdir:
                result = subprocess.run(
                    ['libreoffice', '--headless', '--convert-to', 'txt', '--outdir', tmpdir, str(path)],
                    capture_output=True,
                    timeout=60
                )
                
                if result.returncode == 0:
                    txt_file = Path(tmpdir) / (path.stem + '.txt')
                    if txt_file.exists():
                        return txt_file.read_text(encoding='utf-8', errors='replace')
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        except Exception:
            pass
        
        return "Unable to preview DOC file. Please install 'antiword' or 'libreoffice' on the server."


# 全局服务实例
preview_service = PreviewService()
