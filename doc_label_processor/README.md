# Doc Label Processor - 文档打标处理器

> **一句话总结：** 从数据库查询 OCR 任务记录，根据文件名关键词和分类模型对文档进行自动打标分类，并输出结果到文件。

## 功能概述

从 PostgreSQL 数据库查询 OCR 任务记录（`ocr_task_accept` 表），解析 `identify_result` JSON 字段提取文档名称列表，通过**关键词匹配**和**远程分类模型接口**两种方式对文档进行分类打标，最终将打标结果输出到文本文件。

## 核心特性

- 🗄️ 连接 PostgreSQL 数据库，按时间范围查询 OCR 任务记录
- 📋 解析嵌套 JSON 字段，提取 `projectCode` 和文档名称列表
- 🏷️ 支持多种文档分类标签：`contract`（合同）、`feasibility_report`（可研报告）、`project_approval_documents`（审批文件）、`site_photo`（现场照片）、`other`（其他）
- 🔑 基于关键词映射表进行初步分类匹配
- 🤖 调用远程文件名分类服务（`/rest/classify/v1/filename`）进行模型分类
- ✅ 多关键词场景下的交叉验证修正机制
- 📝 输出格式：`projectCode/docName/finalLabel/originalLabel`

## 使用方式

```bash
python doc_label_processor.py
```

运行后会自动连接数据库、查询记录、处理打标，并将结果写入 `doc_label_results.txt`。

## 依赖

- `psycopg2` - PostgreSQL 数据库驱动
- `requests` - HTTP 请求（调用分类模型接口）
