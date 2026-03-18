# Test Qianfan DeepSeek - 百度千帆 DeepSeek 模型测试

> **一句话总结：** 测试百度千帆平台 DeepSeek-V3 大模型 API 的连通性，验证 AK/SK 鉴权和模型调用是否正常。

## 功能概述

一个简单的测试脚本，用于验证百度智能云千帆大模型平台的 DeepSeek-V3 模型是否正常可用。包含：获取 `access_token` → 调用 DeepSeek 模型 → 检查返回结果，并对常见错误（鉴权失败、模型不存在、权限不足等）给出友好提示。

## 核心特性

- 🔑 支持通过 AK/SK 获取 `access_token`，也支持直接配置 Token
- 🤖 调用千帆平台 DeepSeek-V3 模型的聊天补全接口
- ✅ 多种错误场景的友好提示（404 模型不存在、403 权限不足等）
- ⚙️ 可配置 `temperature`、`top_p`、`seed`、`max_output_tokens` 等生成参数

## 使用方式

1. 修改脚本中的 AK/SK 或 TOKEN 配置
2. 运行测试：

```bash
python test_qianfan_deepseek.py
```

## 依赖

- `requests` - HTTP 请求
