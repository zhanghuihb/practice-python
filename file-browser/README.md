# File Browser - 文件浏览器

一个轻量级的文件浏览器 Web 应用，可部署到 Linux 服务器上浏览图片和文档。

## 功能特性

- 📁 目录浏览（手动输入路径 + 逐级点击）
- 🖼️ 图片管理：预览、上传、复制、移动
- 📄 文档预览：PDF、TXT、DOCX、DOC
- 🖼️ 相册模式：上一张/下一张切换
- 🌙 深色/浅色主题切换
- 📱 响应式布局

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 启动服务

```bash
python main.py
# 访问 http://localhost:8000
```

### 配置

编辑 `config.py` 修改配置：

```python
ROOT_PATH = "/home"  # 可浏览的根目录
HOST = "0.0.0.0"     # 监听地址
PORT = 8000          # 端口
```

## Linux 部署

### 直接运行

```bash
cd /opt/file-browser
pip install -r requirements.txt
python main.py --host 0.0.0.0 --port 8080
```

### Systemd 服务

```bash
sudo cp file-browser.service /etc/systemd/system/
sudo systemctl enable file-browser
sudo systemctl start file-browser
```

## DOC 文件支持

预览 DOC 文件需要安装 antiword：

```bash
# Debian/Ubuntu
sudo apt-get install antiword

# CentOS/RHEL
sudo yum install antiword
```

## 技术栈

- FastAPI + Uvicorn
- Jinja2 模板
- Pillow (图片处理)
- python-docx + mammoth (DOCX 预览)
- PDF.js (PDF 预览)
