# YOLOv8 & BERT Cover Detection - 封面检测对比工具

> **一句话总结：** 使用 YOLO 和 BERT 两种模型对文档图片进行封面检测与分类对比，验证不同模型的检测效果差异。

## 功能概述

批量处理目录下的图片文件，先通过 OCR 接口提取图片中的文字，再分别调用 YOLO 和 BERT 模型接口进行封面检测分类（cover/category/first/other），将结果以"检测类型_原文件名"的格式拷贝到结果目录，方便横向对比两种模型的检测效果。

## 核心特性

- 🔍 调用 OCR 接口提取图片文字内容
- 🤖 支持 YOLO 模型检测（`yolo_cover_detection.py`）
- 🧠 支持 BERT 模型检测（`bert_cover_cate_first_detection.py`）
- ⚖️ YOLO vs BERT 对比检测（`cover_detection_contrast.py`）
- 📁 自动递归遍历目录下的所有图片文件
- 📋 结果图片按"模型结果_原文件名"规则重命名，便于对比
- 📊 完整的处理统计（总数、成功数、失败数）
- 💻 支持命令行参数指定图片目录

## 包含脚本

| 脚本 | 说明 |
|------|------|
| `yolo_cover_detection.py` | 仅使用 YOLO 模型进行封面检测 |
| `bert_cover_cate_first_detection.py` | 仅使用 BERT 模型进行封面/类别/首页检测 |
| `cover_detection_contrast.py` | 同时使用 YOLO 和 BERT 进行对比检测 |

## 使用方式

```bash
# 使用 BERT 模型检测
python bert_cover_cate_first_detection.py [图片目录路径]

# 使用 YOLO 模型检测
python yolo_cover_detection.py [图片目录路径]

# YOLO vs BERT 对比检测
python cover_detection_contrast.py [图片目录路径]
```

结果会保存在图片目录下的 `result-bert/`、`result-yolo/` 或 `result/` 子目录中。

## 依赖

- `requests` - HTTP 请求（调用 OCR 和模型接口）
- `Pillow` - 图片处理（可选）
