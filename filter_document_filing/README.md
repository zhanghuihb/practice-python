# Filter Document Filing - 文档归档过滤器

> **一句话总结：** 从打标结果文件中筛选出包含 `document_filing` 标签的记录，并支持按关键词排除不需要的行。

## 功能概述

读取文档打标结果文本文件，过滤出所有标记为 `document_filing`（文档归档）的行，同时支持通过排除关键词列表（如"备案"）跳过特定记录，将筛选结果输出到自动递增编号的新文件中。

## 核心特性

- 📄 逐行扫描输入文件，精确匹配 `document_filing` 标签
- 🚫 支持自定义排除关键词列表，过滤包含特定关键词的行
- 📊 自动统计匹配数量和被排除数量
- 📁 输出文件名自动递增（如 `filing_results_1.txt`、`filing_results_2.txt`）
- 🔍 运行后自动预览输出文件内容

## 使用方式

```bash
python filter_document_filing.py
```

默认从 `train.txt` 读取输入，排除包含"备案"的行，结果自动保存到递增编号文件。

## 自定义配置

在脚本中修改以下参数：

```python
input_filename = 'train.txt'          # 输入文件
exclude_list = ["备案"]               # 排除关键词列表
```
