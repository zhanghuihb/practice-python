import os
import requests
from flask import Flask, request, jsonify
from typing import List, Set, Dict, Optional
import mimetypes

# 假设这些变量已经在环境变量中设置或已经定义
# OCR_HOST = "http://your-ocr-service"
# HEADERS = {"Content-Type": "application/json"}

# 全局配置（可以从环境变量读取）
OCR_HOST = os.environ.get("OCR_HOST", "http://192.168.30.25:8867")
HEADERS = {"Content-Type": "application/json"}

# 支持的图片扩展名
SUPPORTED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp'}

app = Flask(__name__)

def ocr_predict(image_list):
    """
    调用OCR接口识别图片内容
    """
    # image_list = {'image': [{"imgPath": "/home"}]}
    try:
        result = requests.post(
            url=f"{OCR_HOST}/rest/ocr/v1/general",
            headers=HEADERS,
            json=image_list,
            timeout=500
        )

        if result.status_code != 200:
            raise Exception(f"OCR服务请求异常，状态码：{result.status_code}，响应：{result.text}")

        result_json = result.json()
        print(result_json)
        if result_json.get("code") != "00000":
            raise Exception(f"OCR服务返回异常：{result_json.get('msg')}")

        return result_json.get("data", [])

    except requests.exceptions.RequestException as e:
        raise Exception(f"OCR服务连接失败：{str(e)}")
    except Exception as e:
        raise Exception(f"OCR处理失败：{str(e)}")

def is_image_file(file_path: str) -> bool:
    """
    检查文件是否为图片文件
    """
    # 检查扩展名
    ext = os.path.splitext(file_path)[1].lower()
    if ext in SUPPORTED_IMAGE_EXTENSIONS:
        return True

    # 额外通过MIME类型检查
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type and mime_type.startswith('image/'):
        return True

    return False

def process_images_in_directory(directory_path: str, keywords: List[str]) -> Dict:
    """
    处理目录中的图片，检查是否包含关键词
    """
    if not os.path.exists(directory_path):
        return {"error": f"目录不存在：{directory_path}"}

    if not os.path.isdir(directory_path):
        return {"error": f"路径不是目录：{directory_path}"}

    # 获取目录下的所有文件（不递归）
    try:
        all_files = os.listdir(directory_path)
    except PermissionError:
        return {"error": f"没有权限访问目录：{directory_path}"}
    except Exception as e:
        return {"error": f"读取目录失败：{str(e)}"}

    # 过滤出有效的图片文件
    image_files = []
    for filename in all_files:
        # 过滤以"."开头的文件
        if filename.startswith('.'):
            continue

        file_path = os.path.join(directory_path, filename)

        # 检查是否为文件
        if not os.path.isfile(file_path):
            continue

        # 检查是否为图片
        if not is_image_file(file_path):
            continue

        image_files.append(file_path)

    if not image_files:
        return {"message": "目录中没有找到有效的图片文件", "unmatched_images": []}

    # 准备OCR请求数据
    # image_list = {
    #     "image": [{"imgPath": img_path} for img_path in image_files]
    # }
    image_list = {
        "image": [{"imgUrl": "http://192.168.30.34:30015/top_repository/outer/downloadFile?userFileId=2000823033910935552&userId=999&shareType=1"}]
    }
    try:
        # 调用OCR接口
        ocr_results = ocr_predict(image_list)

        # 处理OCR结果
        unmatched_images = []

        # 如果OCR返回的结果数量与图片数量不一致
        if len(ocr_results) != len(image_files):
            print(f"警告：OCR返回结果数量({len(ocr_results)})与图片数量({len(image_files)})不一致")

        # 检查每个图片的OCR结果是否包含关键词
        for i, image_path in enumerate(image_files):
            # 获取对应图片的OCR结果
            ocr_text = ""
            if i < len(ocr_results):
                # 根据实际的OCR响应结构调整，这里假设每个结果有'text'字段
                ocr_result = ocr_results[i]
                # 尝试获取文本内容，具体字段名可能需要根据实际响应调整

                ocr_text = "".join([word["words"] for word in ocr_result["ocr"]["words_result"]])

            # 检查是否包含任何关键词
            found_keyword = False
            for keyword in keywords:
                if keyword.lower() in ocr_text:
                    found_keyword = True
                    break

            # 如果没有找到任何关键词，添加到未匹配列表中
            if not found_keyword and ocr_text:  # 只有有OCR文本且没匹配到关键词才记录
                unmatched_images.append(image_path)
            elif not ocr_text:  # 如果没有OCR文本，也认为是未匹配
                print(f"警告：图片 {image_path} OCR识别结果为空")
                unmatched_images.append(image_path)

        return {
            "total_images": len(image_files),
            "processed_images": len(ocr_results),
            "unmatched_images": unmatched_images,
            "unmatched_count": len(unmatched_images)
        }

    except Exception as e:
        return {"error": f"OCR处理过程出错：{str(e)}"}

@app.route('/api/check_images', methods=['POST'])
def check_images_api():
    """
    API接口：检查目录中的图片是否包含关键词
    请求体示例：
    {
        "directory_path": "/path/to/images",
        "keywords": ["发票", "收据", "账单"]
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "请求体不能为空"}), 400

        directory_path = data.get('directory_path')
        keywords = data.get('keywords')

        if not directory_path:
            return jsonify({"error": "directory_path 参数不能为空"}), 400

        if not keywords or not isinstance(keywords, list):
            return jsonify({"error": "keywords 参数必须是非空列表"}), 400

        # 处理图片
        result = process_images_in_directory(directory_path, keywords)

        if "error" in result:
            return jsonify(result), 500

        # 输出没有命中任何关键词的图片路径
        if result["unmatched_images"]:
            print("\n以下图片没有命中任何关键词：")
            for img_path in result["unmatched_images"]:
                print(img_path)
        else:
            print(f"\n所有图片都命中了至少一个关键词。共处理 {result['total_images']} 张图片。")

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": f"服务器内部错误：{str(e)}"}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """
    健康检查接口
    """
    return jsonify({"status": "healthy", "service": "image-keyword-checker"})

if __name__ == '__main__':
    # 从环境变量获取配置
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 8625))
    debug = os.environ.get('DEBUG', 'false').lower() == 'true'

    print(f"启动图片关键词检查服务...")
    print(f"监听地址：{host}:{port}")
    print(f"OCR服务地址：{OCR_HOST}")
    print(f"API接口：POST /api/check_images")
    print(f"健康检查：GET /api/health")

    app.run(host=host, port=port, debug=debug)