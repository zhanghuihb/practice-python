# Image Keyword Checker - 图片关键词检查服务

> **一句话总结：** 基于 Flask 的 Web 服务，通过 OCR 识别目录下图片中的文字，检查是否包含指定关键词，输出未命中的图片列表。

## 功能概述

提供 REST API 接口，接收图片目录路径和关键词列表，自动扫描目录下的所有图片文件，调用 OCR 服务识别图片中的文字内容，检查是否包含指定关键词，返回未命中任何关键词的图片列表。

## 核心特性

- 🔍 自动扫描目录下的图片文件（支持 jpg、png、bmp、gif、tiff、webp 等格式）
- 🤖 调用 OCR 服务识别图片中的文字
- 🏷️ 支持自定义关键词列表进行匹配检查
- 📋 返回未命中关键词的图片路径列表
- 🐳 支持 Docker 部署
- ❤️ 内置健康检查接口

## API 接口

### POST `/api/check_images` - 检查图片关键词

```json
{
    "directory_path": "/path/to/images",
    "keywords": ["发票", "收据", "合同"]
}
```

### GET `/api/health` - 健康检查

## 安装依赖

```bash
pip install -r requirements.txt
```

## 运行服务

```bash
export OCR_HOST="http://your-ocr-service:port"
export HOST="0.0.0.0"
export PORT=8625
python image-keyword-checker.py
```

## Docker 部署

```bash
docker build -t image-keyword-checker .
docker run -p 8625:8625 -e OCR_HOST=http://your-ocr-host image-keyword-checker
```

## 依赖

- `Flask` - Web 框架
- `requests` - HTTP 请求（调用 OCR 服务）