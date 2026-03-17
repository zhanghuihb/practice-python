

## 安装依赖
1. 创建 requirements.txt 文件
```txt
Flask>=2.0.0
requests>=2.25.0
```
2. 安装依赖
```txt
pip install -r requirements.txt
```
## 运行服务
```bash
# 设置环境变量并运行
export OCR_HOST="http://your-ocr-service:port"
export HOST="0.0.0.0"
export PORT=5000
python your_script_name.py
```
## 调用API接口
使用curl测试API
```bash
curl -X POST http://localhost:5000/api/check_images \
-H "Content-Type: application/json" \
-d '{
"directory_path": "/path/to/your/images",
"keywords": ["发票", "收据", "合同"]
}'
```

## Docker部署（可选）
1. 创建 Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV OCR_HOST=http://ocr-service:8080
ENV HOST=0.0.0.0
ENV PORT=5000

EXPOSE 5000

CMD ["python", "app.py"]
```
2. 构建和运行
```bash
docker build -t image-keyword-checker .
docker run -p 5000:5000 -e OCR_HOST=http://your-ocr-host image-keyword-checker
```