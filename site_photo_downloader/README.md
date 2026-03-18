# Site Photo Downloader - 现场照片下载器

> **一句话总结：** 从数据库查询 OCR 任务记录，自动提取并下载施工现场照片和设备到位照片到本地目录。

## 功能概述

连接 PostgreSQL 数据库查询 OCR 任务记录，解析 `identify_result` JSON 字段中的 `ocrResultData`，提取 category 为 `site_construction_photos`（施工现场照片）和 `equipment_in_place_photo`（设备到位照片）的图片，通过 `imgUrl` 下载到本地 `site_photo` 目录。

## 核心特性

- 🗄️ 连接 PostgreSQL 数据库，按时间范围查询记录
- 🔍 自动过滤目标类别照片（施工现场照片、设备到位照片）
- 📥 流式下载图片，支持超时控制（60 秒）
- 📝 文件命名规则：`{projectCode}-{imgName}`
- ⏭️ 自动跳过已存在的文件，支持断点续下
- 📊 完整的下载统计（总记录、已下载、已跳过、失败数）

## 使用方式

```bash
python site_photo_downloader.py
```

运行后自动查询数据库、下载目标照片到 `site_photo/` 目录，并输出统计信息。

## 依赖

- `psycopg2` - PostgreSQL 数据库驱动
- `requests` - HTTP 图片下载
