"""
File Browser Configuration
"""
import os
from pathlib import Path

# 可浏览的根目录
ROOT_PATH = os.environ.get("FILE_BROWSER_ROOT", "/data")

# 服务器配置
HOST = os.environ.get("FILE_BROWSER_HOST", "0.0.0.0")
PORT = int(os.environ.get("FILE_BROWSER_PORT", "8625"))

# 上传配置
UPLOAD_MAX_SIZE = 100 * 1024 * 1024  # 100MB

# 支持的文件类型
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg', '.ico'}
DOCUMENT_EXTENSIONS = {'.pdf', '.txt', '.docx', '.doc', '.md', '.json', '.xml', '.html', '.css', '.js', '.py'}
VIDEO_EXTENSIONS = {'.mp4', '.webm', '.avi', '.mov', '.mkv'}
AUDIO_EXTENSIONS = {'.mp3', '.wav', '.ogg', '.flac', '.aac'}

# 缩略图配置
THUMBNAIL_SIZE = (200, 200)
THUMBNAIL_QUALITY = 85

# 回收站目录（相对于根目录）
TRASH_DIR = ".file-browser-trash"

# 应用目录
APP_DIR = Path(__file__).parent
TEMPLATES_DIR = APP_DIR / "templates"
STATIC_DIR = APP_DIR / "static"
