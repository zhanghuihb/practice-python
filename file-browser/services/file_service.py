"""
File Service - 文件操作核心服务
"""
import os
import shutil
import mimetypes
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

import config


class FileService:
    """文件操作服务"""
    
    def __init__(self, root_path: str = None):
        self.root = Path(root_path or config.ROOT_PATH).resolve()
    
    def _resolve_path(self, rel_path: str) -> Optional[Path]:
        """
        解析相对路径为绝对路径，并验证安全性
        防止目录遍历攻击
        """
        if not rel_path:
            return self.root
        
        # 清理路径
        clean_path = rel_path.strip('/').replace('\\', '/')
        full_path = (self.root / clean_path).resolve()
        
        # 安全检查：确保路径在根目录内
        try:
            full_path.relative_to(self.root)
            return full_path
        except ValueError:
            return None
    
    def is_safe_path(self, rel_path: str) -> bool:
        """检查路径是否安全"""
        return self._resolve_path(rel_path) is not None
    
    def get_file_info(self, path: Path) -> Dict[str, Any]:
        """获取文件/目录信息"""
        stat = path.stat()
        name = path.name
        suffix = path.suffix.lower()
        
        # 判断文件类型
        if path.is_dir():
            file_type = "directory"
            icon = "folder"
        elif suffix in config.IMAGE_EXTENSIONS:
            file_type = "image"
            icon = "image"
        elif suffix in {'.pdf'}:
            file_type = "pdf"
            icon = "file-pdf"
        elif suffix in {'.docx', '.doc'}:
            file_type = "document"
            icon = "file-word"
        elif suffix in {'.txt', '.md'}:
            file_type = "text"
            icon = "file-text"
        elif suffix in config.VIDEO_EXTENSIONS:
            file_type = "video"
            icon = "file-video"
        elif suffix in config.AUDIO_EXTENSIONS:
            file_type = "audio"
            icon = "file-audio"
        else:
            file_type = "file"
            icon = "file"
        
        return {
            "name": name,
            "path": str(path.relative_to(self.root)).replace('\\', '/'),
            "type": file_type,
            "icon": icon,
            "size": stat.st_size if path.is_file() else None,
            "size_human": self._format_size(stat.st_size) if path.is_file() else None,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "modified_human": self._format_time(stat.st_mtime),
            "extension": suffix[1:] if suffix else None,
            "is_dir": path.is_dir(),
            "is_image": suffix in config.IMAGE_EXTENSIONS,
            "is_previewable": suffix in config.IMAGE_EXTENSIONS | config.DOCUMENT_EXTENSIONS
        }
    
    def list_directory(self, rel_path: str = "") -> Dict[str, Any]:
        """列出目录内容"""
        path = self._resolve_path(rel_path)
        
        if path is None:
            return {"error": "Invalid path", "code": 400}
        
        if not path.exists():
            return {"error": "Path not found", "code": 404}
        
        if not path.is_dir():
            return {"error": "Not a directory", "code": 400}
        
        items = []
        dirs = []
        files = []
        images = []
        
        try:
            for item in sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
                # 跳过隐藏文件（以.开头）和回收站
                if item.name.startswith('.'):
                    continue
                
                try:
                    info = self.get_file_info(item)
                    items.append(info)
                    
                    if item.is_dir():
                        dirs.append(info)
                    else:
                        files.append(info)
                        if info["is_image"]:
                            images.append(info)
                except (PermissionError, OSError):
                    continue
        except PermissionError:
            return {"error": "Permission denied", "code": 403}
        
        # 生成面包屑导航
        breadcrumbs = self._get_breadcrumbs(rel_path)
        
        # 计算统计信息
        total_size = sum(f["size"] or 0 for f in files)
        
        return {
            "path": rel_path or "",
            "full_path": str(path),
            "items": items,
            "dirs": dirs,
            "files": files,
            "images": images,
            "breadcrumbs": breadcrumbs,
            "stats": {
                "total_items": len(items),
                "dir_count": len(dirs),
                "file_count": len(files),
                "image_count": len(images),
                "total_size": total_size,
                "total_size_human": self._format_size(total_size)
            }
        }
    
    def _get_breadcrumbs(self, rel_path: str) -> List[Dict[str, str]]:
        """生成面包屑导航"""
        breadcrumbs = [{"name": "🏠 Home", "path": ""}]
        
        if not rel_path:
            return breadcrumbs
        
        parts = rel_path.strip('/').split('/')
        current_path = ""
        
        for part in parts:
            if part:
                current_path = f"{current_path}/{part}".lstrip('/')
                breadcrumbs.append({"name": part, "path": current_path})
        
        return breadcrumbs
    
    def copy_file(self, src_rel: str, dst_dir_rel: str) -> Dict[str, Any]:
        """复制文件到目标目录"""
        src_path = self._resolve_path(src_rel)
        dst_dir = self._resolve_path(dst_dir_rel)
        
        if src_path is None or dst_dir is None:
            return {"error": "Invalid path", "code": 400}
        
        if not src_path.exists():
            return {"error": "Source not found", "code": 404}
        
        if not dst_dir.exists():
            return {"error": "Destination directory not found", "code": 404}
        
        if not dst_dir.is_dir():
            return {"error": "Destination is not a directory", "code": 400}
        
        dst_path = dst_dir / src_path.name
        
        # 如果目标已存在，添加后缀
        if dst_path.exists():
            base = dst_path.stem
            ext = dst_path.suffix
            counter = 1
            while dst_path.exists():
                dst_path = dst_dir / f"{base}_{counter}{ext}"
                counter += 1
        
        try:
            if src_path.is_dir():
                shutil.copytree(src_path, dst_path)
            else:
                shutil.copy2(src_path, dst_path)
            
            return {
                "success": True,
                "message": f"Copied to {dst_path.name}",
                "new_path": str(dst_path.relative_to(self.root)).replace('\\', '/')
            }
        except Exception as e:
            return {"error": str(e), "code": 500}
    
    def move_file(self, src_rel: str, dst_dir_rel: str) -> Dict[str, Any]:
        """移动文件到目标目录"""
        src_path = self._resolve_path(src_rel)
        dst_dir = self._resolve_path(dst_dir_rel)
        
        if src_path is None or dst_dir is None:
            return {"error": "Invalid path", "code": 400}
        
        if not src_path.exists():
            return {"error": "Source not found", "code": 404}
        
        if not dst_dir.exists():
            return {"error": "Destination directory not found", "code": 404}
        
        if not dst_dir.is_dir():
            return {"error": "Destination is not a directory", "code": 400}
        
        dst_path = dst_dir / src_path.name
        
        # 如果目标已存在，添加后缀
        if dst_path.exists():
            base = dst_path.stem
            ext = dst_path.suffix
            counter = 1
            while dst_path.exists():
                dst_path = dst_dir / f"{base}_{counter}{ext}"
                counter += 1
        
        try:
            shutil.move(str(src_path), str(dst_path))
            return {
                "success": True,
                "message": f"Moved to {dst_path.name}",
                "new_path": str(dst_path.relative_to(self.root)).replace('\\', '/')
            }
        except Exception as e:
            return {"error": str(e), "code": 500}
    
    def move_to_trash(self, rel_path: str) -> Dict[str, Any]:
        """移动文件到回收站"""
        path = self._resolve_path(rel_path)
        
        if path is None:
            return {"error": "Invalid path", "code": 400}
        
        if not path.exists():
            return {"error": "File not found", "code": 404}
        
        # 创建回收站目录
        trash_dir = self.root / config.TRASH_DIR
        trash_dir.mkdir(exist_ok=True)
        
        # 添加时间戳避免冲突
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        trash_path = trash_dir / f"{timestamp}_{path.name}"
        
        try:
            shutil.move(str(path), str(trash_path))
            return {
                "success": True,
                "message": f"Moved to trash: {path.name}"
            }
        except Exception as e:
            return {"error": str(e), "code": 500}
    
    def create_directory(self, parent_rel: str, name: str) -> Dict[str, Any]:
        """创建新目录"""
        parent = self._resolve_path(parent_rel)
        
        if parent is None:
            return {"error": "Invalid path", "code": 400}
        
        if not parent.exists():
            return {"error": "Parent directory not found", "code": 404}
        
        # 清理目录名
        name = name.strip().replace('/', '').replace('\\', '')
        if not name or name.startswith('.'):
            return {"error": "Invalid directory name", "code": 400}
        
        new_dir = parent / name
        
        if new_dir.exists():
            return {"error": "Directory already exists", "code": 409}
        
        try:
            new_dir.mkdir()
            return {
                "success": True,
                "message": f"Created directory: {name}",
                "path": str(new_dir.relative_to(self.root)).replace('\\', '/')
            }
        except Exception as e:
            return {"error": str(e), "code": 500}
    
    def save_upload(self, rel_path: str, filename: str, content: bytes) -> Dict[str, Any]:
        """保存上传的文件"""
        dir_path = self._resolve_path(rel_path)
        
        if dir_path is None:
            return {"error": "Invalid path", "code": 400}
        
        if not dir_path.exists() or not dir_path.is_dir():
            return {"error": "Directory not found", "code": 404}
        
        # 清理文件名
        safe_name = filename.replace('/', '').replace('\\', '').replace('..', '')
        if not safe_name:
            return {"error": "Invalid filename", "code": 400}
        
        file_path = dir_path / safe_name
        
        # 如果文件已存在，添加后缀
        if file_path.exists():
            base = file_path.stem
            ext = file_path.suffix
            counter = 1
            while file_path.exists():
                file_path = dir_path / f"{base}_{counter}{ext}"
                counter += 1
        
        try:
            file_path.write_bytes(content)
            return {
                "success": True,
                "message": f"Uploaded: {file_path.name}",
                "path": str(file_path.relative_to(self.root)).replace('\\', '/'),
                "file": self.get_file_info(file_path)
            }
        except Exception as e:
            return {"error": str(e), "code": 500}
    
    def get_subdirectories(self, rel_path: str = "") -> List[Dict[str, str]]:
        """获取子目录列表（用于目录选择器）"""
        path = self._resolve_path(rel_path)
        
        if path is None or not path.exists() or not path.is_dir():
            return []
        
        dirs = []
        try:
            for item in sorted(path.iterdir(), key=lambda x: x.name.lower()):
                if item.is_dir() and not item.name.startswith('.'):
                    dirs.append({
                        "name": item.name,
                        "path": str(item.relative_to(self.root)).replace('\\', '/')
                    })
        except PermissionError:
            pass
        
        return dirs
    
    @staticmethod
    def _format_size(size: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.1f} {unit}" if unit != 'B' else f"{size} {unit}"
            size /= 1024
        return f"{size:.1f} PB"
    
    @staticmethod
    def _format_time(timestamp: float) -> str:
        """格式化时间"""
        dt = datetime.fromtimestamp(timestamp)
        now = datetime.now()
        diff = now - dt
        
        if diff.days == 0:
            if diff.seconds < 60:
                return "Just now"
            elif diff.seconds < 3600:
                return f"{diff.seconds // 60} min ago"
            else:
                return f"{diff.seconds // 3600} hours ago"
        elif diff.days == 1:
            return "Yesterday"
        elif diff.days < 7:
            return f"{diff.days} days ago"
        else:
            return dt.strftime("%Y-%m-%d")


# 全局服务实例
file_service = FileService()
