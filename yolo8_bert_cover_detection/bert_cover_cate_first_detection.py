import os
import requests
import shutil
from pathlib import Path
from typing import Optional, Dict

# ===================== 核心配置项（请根据实际情况修改） =====================
# 原始图片根目录（可通过命令行传参覆盖）
TARGET_DIR = "/data/ocr/zhh/bert_cover_cate_first_detection/data/cover"
# 结果输出目录（会自动创建在TARGET_DIR下）
RESULT_DIR_NAME = "result-bert"
# YOLO模型和BERT模型对比接口地址
API_URL = "http://192.168.30.25:8017/rest/classify/v1/cover_detection_contrast"
# 支持的图片后缀（小写）
SUPPORTED_SUFFIX = (".png", ".jpg", ".jpeg", ".bmp", ".webp", ".tiff", ".gif")
# 接口超时时间（秒）
API_TIMEOUT = 30
HEADERS = {"Content-Type": "application/json"}
# ===========================================================================


def ocr_predict(image_list):
    """
    调用OCR接口识别图片内容
    """
    # image_list = {'image': [{"imgPath": "/home"}]}
    try:
        result = requests.post(
            url="http://192.168.30.25:8867/rest/ocr/v1/general",
            headers=HEADERS,
            json=image_list,
            timeout=500
        )

        if result.status_code != 200:
            raise Exception(f"OCR服务请求异常，状态码：{result.status_code}，响应：{result.text}")

        result_json = result.json()
        # print(f"OCR服务请求结果：{result_json}")
        if result_json.get("code") != "00000":
            raise Exception(f"OCR服务返回异常：{result_json.get('msg')}")

        return result_json.get("data", [])

    except requests.exceptions.RequestException as e:
        raise Exception(f"OCR服务连接失败：{str(e)}")
    except Exception as e:
        raise Exception(f"OCR处理失败：{str(e)}")

def init_result_dir(target_dir: str) -> Optional[str]:
    """
    初始化结果目录（TARGET_DIR/result），确保目录存在
    :param target_dir: 原始图片根目录
    :return: 结果目录完整路径，失败返回None
    """
    try:
        result_dir = os.path.join(target_dir, RESULT_DIR_NAME)
        os.makedirs(result_dir, exist_ok=True)  # 不存在则创建，存在则忽略
        print(f"结果目录已初始化：{result_dir}")
        return result_dir
    except Exception as e:
        print(f"初始化结果目录失败：{str(e)}")
        return None

def call_model_api(api_url: str, image_path: str) -> Optional[Dict]:
    """
    调用模型接口，获取检测结果（cover/category/first/other）
    :param api_url: 模型接口地址
    :param image_path: 图片本地路径
    :return: 合法检测类型/None
    """
    # 校验图片文件是否存在
    if not os.path.exists(image_path):
        print(f"图片文件不存在：{image_path}")
        return None

    try:
        # 1. 调用ocr获取图片内容接口
        image_list = {
            "image": [{"imgPath": image_path}]
        }
        # 调用OCR接口
        ocr_results = ocr_predict(image_list)
        # 获取对应图片的OCR结果
        ocr_result = ocr_results[0]
        # 尝试获取文本内容，具体字段名可能需要根据实际响应调整
        image_text = "".join([word["words"] for word in ocr_result["ocr"]["words_result"]])
        # 2. 调用 yolo模型和bert模型进行封面检测 接口接收图片路径字符串（若模型部署在同一服务器，可启用）
        # 2.1 构造表单参数（x-www-form-urlencoded 格式）
        params = {
            "image_path": "",
            "image_text": image_text
        }

        response = requests.post(
            api_url,
            params=params,
            headers=HEADERS,
            timeout=API_TIMEOUT
        )

        # 校验接口响应状态
        if response.status_code != 200:
            print(f"接口请求失败 [{api_url}]，状态码：{response.status_code} | 图片：{image_path}")
            return None

        # 解析响应结果
        result = response.json()
        print(f"接口请求 [{api_url}] 成功，图片：{image_path} | 返回结果：{result} ")

        return result.get("data", {})


    except requests.exceptions.RequestException as e:
        print(f"接口网络异常 [{api_url}]：{str(e)} | 图片：{image_path}")
        return None
    except Exception as e:
        print(f"接口解析异常 [{api_url}]：{str(e)} | 图片：{image_path}")
        return None

def copy_and_rename_image(
    src_image_path: str,
    dest_dir: str,
    bert_type: str
) -> Optional[str]:
    """
    将图片拷贝到结果目录，并按规则重命名（yolo_type_bert_type_原文件名）
    重名时直接覆盖目标文件
    :param src_image_path: 原始图片路径
    :param dest_dir: 目标结果目录
    :param yolo_type: YOLO检测结果
    :param bert_type: BERT检测结果
    :return: 新文件路径/None
    """
    try:
        src_path = Path(src_image_path)
        # 构造新文件名：bert类型_原文件名（无数字后缀）
        new_name = f"{bert_type}_{src_path.name}"
        dest_path = Path(dest_dir) / new_name

        # 拷贝图片并覆盖同名文件（copy2保留元数据，shutil.copy默认覆盖）
        shutil.copy2(src_path, dest_path)  # 若存在同名文件会直接覆盖
        print(f"拷贝并重命名成功（覆盖同名文件）：{src_path.name} -> {new_name}")
        return str(dest_path)

    except Exception as e:
        print(f"拷贝重命名失败：{str(e)} | 图片：{src_image_path}")
        return None

def get_parent_dirname(image_path: str) -> str:
    """
    提取图片的直接父级目录名（核心简化逻辑）
    示例：/xxx/cover/aaa.png → 返回 cover
    """
    try:
        parent_dir = Path(image_path).parent
        dirname = parent_dir.name
        print(f"✅ 提取父级目录名：{dirname}（图片：{image_path}）")
        return dirname
    except Exception as e:
        print(f"❌ 提取父级目录名失败：{str(e)} | 图片：{image_path}")
        return "unknown"  # 兜底值

def traverse_and_process_images(root_dir: str, result_dir: str):
    """
    递归遍历根目录下所有图片，调用双模型并处理拷贝重命名
    :param root_dir: 原始图片根目录
    :param result_dir: 结果输出目录
    """
    # 统计变量
    total_count = 0
    success_count = 0
    fail_count = 0

    print(f"\n开始递归遍历目录：{root_dir}")
    # 递归遍历所有子目录
    for root, dirs, files in os.walk(root_dir):
        # 跳过结果目录，避免处理已生成的文件
        if RESULT_DIR_NAME in root:
            continue

        for filename in files:
            # 统一转为小写，判断是否为支持的图片格式
            file_suffix = Path(filename).suffix.lower()
            if file_suffix not in SUPPORTED_SUFFIX:
                continue

            total_count += 1
            src_image_path = os.path.join(root, filename)
            print(f"\n===== 处理第 {total_count} 张图片：{src_image_path} =====")

            # 1. 调用YOLO模型和BERT模型对比及恶口
            result = call_model_api(API_URL, src_image_path)
            bert_result = result.get('bert_result', None)

            # 3. 拷贝并重命名图片到结果目录
            if copy_and_rename_image(src_image_path, result_dir, bert_result):
                success_count += 1
            else:
                fail_count += 1

    # 输出统计结果
    print("\n" + "="*50)
    print(f"处理完成！统计结果：")
    print(f"总图片数：{total_count}")
    print(f"成功数：{success_count}")
    print(f"失败数：{fail_count}")
    print(f"结果目录：{result_dir}")
    print("="*50)

if __name__ == "__main__":
    # 支持命令行传参（优先级高于配置项）
    import sys
    if len(sys.argv) > 1:
        TARGET_DIR = sys.argv[1].strip()

    # 校验原始目录是否存在
    if not os.path.exists(TARGET_DIR):
        print(f"错误：原始图片目录不存在 -> {TARGET_DIR}")
        sys.exit(1)

    # 初始化结果目录
    result_dir = init_result_dir(TARGET_DIR)
    if not result_dir:
        sys.exit(1)

    # 开始处理
    traverse_and_process_images(TARGET_DIR, result_dir)
    sys.exit(0)
