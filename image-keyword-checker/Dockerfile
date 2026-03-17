# python:3.9-slim 是Python 官方 Docker 镜像的一个变体，专为减少镜像体积而设计，适用于资源受限或注重效率的部署场景
FROM python:3.9-slim

WORKDIR /image-keyword-checker

# Alpine 需要先安装依赖
# RUN apk add --no-cache gcc musl-dev linux-headers

# 设置清华源（比阿里云可能更快）
# RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple/

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV OCR_HOST=http://localhost:8867
ENV HOST=0.0.0.0
ENV PORT=8625

EXPOSE 8625

CMD ["python", "image-keyword-checker.py"]


# 构建和运行
# docker build -t image-keyword-checker .
# docker run -d --network host -p 8625:8625 --name image-checker -v /data/zhh:/data/zhh image-keyword-checker
