"""
现场照片下载器
从 PostgreSQL 数据库查询 OCR 任务记录，解析 identify_result 字段，
提取 category 为 site_construction_photos 或 equipment_in_place_photo 的照片，
下载到 site_photo 目录。
"""

import json
import logging
import os
import time
from typing import List, Optional, Set

import psycopg2
import requests
from psycopg2.extras import RealDictCursor

# ============================================================
# 日志配置
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ============================================================
# 数据库配置（复用 doc_label_processor.py 的配置）
# ============================================================
DB_CONFIG = {
    "host": "192.168.30.25",
    "port": 5432,
    "database": "apiservice_cpu",
    "user": "postgres",
    "password": "top@123",
}

# 查询 SQL
QUERY_SQL = """
    SELECT ota.identify_result
    FROM ocr_task_accept ota
    WHERE create_time > %s
"""

# 默认查询起始时间
DEFAULT_START_TIME = "2026-02-01 00:00:00"

# 需要提取的照片类别
TARGET_CATEGORIES: Set[str] = {
    "site_construction_photos",
    "equipment_in_place_photo",
}

# 输出目录
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "site_photo")

# 下载超时（秒）
DOWNLOAD_TIMEOUT = 60


# ============================================================
# 数据库操作
# ============================================================
def get_db_connection():
    """创建并返回数据库连接。"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        logger.info("数据库连接成功")
        return conn
    except psycopg2.Error as e:
        logger.error("数据库连接失败: %s", e)
        raise


def fetch_identify_results(conn, start_time: str = DEFAULT_START_TIME) -> List[dict]:
    """
    从数据库查询符合条件的 identify_result 记录。

    Args:
        conn: 数据库连接
        start_time: 查询起始时间

    Returns:
        查询结果列表，每条记录为 dict
    """
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(QUERY_SQL, (start_time,))
            rows = cur.fetchall()
            logger.info("查询到 %d 条记录", len(rows))
            return rows
    except psycopg2.Error as e:
        logger.error("查询失败: %s", e)
        raise


# ============================================================
# JSON 解析
# ============================================================
def parse_identify_result(identify_result_raw) -> Optional[dict]:
    """
    解析 identify_result 字段的 JSON 内容。

    Args:
        identify_result_raw: 原始字段值（可能是 str 或 dict）

    Returns:
        解析后的 dict，解析失败返回 None
    """
    if identify_result_raw is None:
        return None

    if isinstance(identify_result_raw, dict):
        return identify_result_raw

    if isinstance(identify_result_raw, str):
        try:
            return json.loads(identify_result_raw)
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning("JSON 解析失败: %s, 原始值: %.200s", e, identify_result_raw)
            return None

    logger.warning("identify_result 类型不支持: %s", type(identify_result_raw))
    return None


def extract_project_code(parsed_data: dict) -> str:
    """
    从解析后的 JSON 数据中提取 projectCode。

    Args:
        parsed_data: 解析后的 identify_result dict

    Returns:
        projectCode 字符串，默认返回 'UNKNOWN'
    """
    ext_json_data = parsed_data.get("extJsonData")
    if not ext_json_data:
        return "UNKNOWN"

    # extJsonData 可能是字符串，也可能已是 dict
    if isinstance(ext_json_data, str):
        try:
            ext_json_data = json.loads(ext_json_data)
        except (json.JSONDecodeError, TypeError):
            return "UNKNOWN"

    return ext_json_data.get("projectCode", "UNKNOWN")


def extract_target_photos(parsed_data: dict) -> List[dict]:
    """
    从解析后的 JSON 数据中提取目标类别的照片信息。

    Args:
        parsed_data: 解析后的 identify_result dict

    Returns:
        匹配目标类别的照片列表，每项包含 imgUrl 和 imgName
    """
    ocr_result_data = parsed_data.get("ocrResultData", [])
    if not ocr_result_data:
        return []

    target_photos = []
    for item in ocr_result_data:
        if not isinstance(item, dict):
            continue
        category = item.get("category", "")
        if category in TARGET_CATEGORIES:
            img_url = item.get("imgUrl")
            img_name = item.get("imgName")
            if img_url and img_name:
                target_photos.append({
                    "imgUrl": img_url,
                    "imgName": img_name,
                    "category": category,
                })
    return target_photos


# ============================================================
# 图片下载
# ============================================================
def download_photo(img_url: str, save_path: str) -> bool:
    """
    下载单张图片到指定路径。

    Args:
        img_url: 图片下载地址
        save_path: 本地保存路径

    Returns:
        下载是否成功
    """
    try:
        start = time.time()
        resp = requests.get(img_url, timeout=DOWNLOAD_TIMEOUT, stream=True)
        if resp.status_code != 200:
            logger.error("下载失败, HTTP %d: %s", resp.status_code, img_url)
            return False

        with open(save_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)

        elapsed = round(time.time() - start, 2)
        file_size_kb = round(os.path.getsize(save_path) / 1024, 1)
        logger.info("下载成功: %s (%.1f KB, 耗时 %ss)", os.path.basename(save_path), file_size_kb, elapsed)
        return True

    except requests.RequestException as e:
        logger.error("下载异常: %s, URL: %s", e, img_url)
        return False


# ============================================================
# 主处理流程
# ============================================================
def download_site_photos(
    start_time: str = DEFAULT_START_TIME,
    output_dir: str = OUTPUT_DIR,
) -> dict:
    """
    主处理流程：查询 → 解析 → 过滤 → 下载。

    Args:
        start_time: 查询起始时间
        output_dir: 照片保存目录

    Returns:
        统计信息 dict
    """
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    logger.info("照片保存目录: %s", output_dir)

    conn = get_db_connection()

    try:
        rows = fetch_identify_results(conn, start_time)

        stats = {
            "total_records": len(rows),
            "skipped_records": 0,
            "target_photos_found": 0,
            "downloaded": 0,
            "skipped_existing": 0,
            "failed": 0,
        }

        for idx, row in enumerate(rows, start=1):
            identify_result_raw = row.get("identify_result")

            # 1. 解析 JSON
            parsed_data = parse_identify_result(identify_result_raw)
            if parsed_data is None:
                stats["skipped_records"] += 1
                continue

            # 2. 提取 projectCode
            project_code = extract_project_code(parsed_data)

            # 3. 提取目标类别的照片
            target_photos = extract_target_photos(parsed_data)
            if not target_photos:
                continue

            stats["target_photos_found"] += len(target_photos)
            logger.info(
                "第 %d 条记录: projectCode=%s, 找到 %d 张目标照片",
                idx, project_code, len(target_photos),
            )

            # 4. 下载照片
            for photo in target_photos:
                img_name = photo["imgName"]
                img_url = photo["imgUrl"]

                # 文件名格式: {project_code}-{imgName}
                file_name = f"{project_code}-{img_name}"
                save_path = os.path.join(output_dir, file_name)

                # 跳过已存在的文件
                if os.path.exists(save_path):
                    logger.info("文件已存在，跳过: %s", file_name)
                    stats["skipped_existing"] += 1
                    continue

                # 下载
                success = download_photo(img_url, save_path)
                if success:
                    stats["downloaded"] += 1
                else:
                    stats["failed"] += 1

        logger.info(
            "处理完成: 总记录=%d, 跳过解析=%d, 目标照片=%d, "
            "已下载=%d, 已存在跳过=%d, 失败=%d",
            stats["total_records"],
            stats["skipped_records"],
            stats["target_photos_found"],
            stats["downloaded"],
            stats["skipped_existing"],
            stats["failed"],
        )
        return stats

    finally:
        conn.close()
        logger.info("数据库连接已关闭")


# ============================================================
# 入口
# ============================================================
if __name__ == "__main__":
    result = download_site_photos()
    print(f"\n下载统计: {json.dumps(result, ensure_ascii=False, indent=2)}")
