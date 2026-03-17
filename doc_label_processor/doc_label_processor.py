"""
文档打标处理器
从 PostgreSQL 数据库查询 OCR 任务记录，解析 JSON 字段提取文档名称列表，
调用打标方法获取每个文档的打标结果，并输出到文本文件。
"""

import json
import logging
import time

import requests
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple

import psycopg2
from psycopg2.extras import RealDictCursor

# 常量定义
KEYWORD_MAP: Dict[str, List[str]] = {
    "contract": ["施工总承包","合同"],
    "feasibility_report": ["可研报告","可行性研究报告"],
    "project_approval_documents": ["备案", "批复", "立项文件","审批文件"],
    "site_photo": ["现场照片","施工图片","施工现场图片"]
}

VALID_LABELS: Set[str] = {"contract", "feasibility_report", "project_approval_documents", "site_photo", "other"}

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
# 数据库配置
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

# 输出文件路径
OUTPUT_FILE = "doc_label_results.txt"


# ============================================================
# 分类接口（占位 —— 请替换为真实实现）
# ============================================================
def classify_by_file_names(filename):
    ''''
    根据文件名进行分类
    '''
    filename_clas_url = f"http://192.168.30.25:8867/rest/classify/v1/filename"
    if isinstance(filename, str):
        if not filename:
            return False, "filename is null"
        filenames = [filename]
    elif isinstance(filename, list):
        filenames = filename
    else:
        logger.error("filename is error")
        return False, "filename is error,must str or list"
    start = time.time()
    resp = requests.post(filename_clas_url, json={"text": filenames})
    end = time.time()
    logger.info(f"调用s14按文件名分类服务 {len(filenames)} 耗时：{round(end - start, 3)}")
    if resp.status_code != 200:
        logger.error(f"调用文件名分类模型错误:{resp.status_code}")
        return False, f"调用文件名分类模型错误:{resp.status_code}"
    response_data = resp.json()
    if response_data.get("code") != "00000":
        logger.error(f"调用文件名分类模型错误:{response_data.get('msg')}")
        return False, f"调用文件名分类模型错误:{response_data.get('msg')}"
    result = response_data.get("result", [])
    return True, result


# ============================================================
# 核心处理逻辑
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


def extract_doc_info(parsed_data: dict) -> tuple:
    """
    从解析后的 JSON 数据中提取 projectCode 和文档名称列表。

    Args:
        parsed_data: 解析后的 JSON dict

    Returns:
        (project_code, doc_names) 元组
    """
    ext_json_data = parsed_data.get("extJsonData")
    if not ext_json_data:
        logger.warning("缺少 extJsonData 字段")
        return None, []

    # extJsonData 可能是字符串，也可能已是 dict
    if isinstance(ext_json_data, str):
        try:
            ext_json_data = json.loads(ext_json_data)
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning("extJsonData 解析失败: %s", e)
            return None, []

    project_code = ext_json_data.get("projectCode", "UNKNOWN")

    doc_fils = ext_json_data.get("docFils", [])
    if not doc_fils:
        logger.warning("projectCode=%s 的 docFils 为空", project_code)
        return project_code, []

    doc_names = [
        item.get("fileName", "")
        for item in doc_fils
        if isinstance(item, dict) and item.get("fileName")
    ]

    logger.info("projectCode=%s, 提取到 %d 个文档名称", project_code, len(doc_names))
    return project_code, doc_names


def process_and_label(
    start_time: str = DEFAULT_START_TIME,
    output_file: str = OUTPUT_FILE,
) -> str:
    """
    主处理流程：查询 → 解析 → 打标 → 输出。

    Args:
        start_time: 查询起始时间
        output_file: 输出文件路径

    Returns:
        输出文件路径
    """
    conn = get_db_connection()

    try:
        rows = fetch_identify_results(conn, start_time)

        results: List[str] = []
        total_docs = 0
        skipped_rows = 0

        for idx, row in enumerate(rows, start=1):
            identify_result_raw = row.get("identify_result")

            # 1. 解析 JSON
            parsed_data = parse_identify_result(identify_result_raw)
            if parsed_data is None:
                skipped_rows += 1
                logger.warning("第 %d 条记录: identify_result 解析失败，跳过", idx)
                continue

            # 2. 提取 projectCode 和文档名称列表
            project_code, doc_names = extract_doc_info(parsed_data)
            if not doc_names:
                skipped_rows += 1
                logger.warning("第 %d 条记录: 未提取到文档名称，跳过", idx)
                continue

            # 3. 遍历文档名称，调用打标方法
            for doc_name in doc_names:
                try:
                    final_label, original_label = validate_and_correct_label(doc_name, doc_names)
                except Exception as e:
                    logger.error(
                        "打标失败: projectCode=%s, docName=%s, error=%s",
                        project_code, doc_name, e,
                    )
                    final_label, original_label = f"ERROR: {e}", f"ERROR: {e}"

                if final_label != original_label:
                    line = f"{project_code}/{doc_name}/{final_label}/{original_label} =====================================修正==================================="
                else:
                    line = f"{project_code}/{doc_name}/{final_label}/{original_label}"
                results.append(line)
                total_docs += 1

        # 4. 写入输出文件
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(results))
            if results:
                f.write("\n")  # 末尾换行

        logger.info(
            "处理完成: 总记录=%d, 跳过=%d, 文档打标=%d, 输出文件=%s",
            len(rows), skipped_rows, total_docs, output_file,
        )
        return output_file

    finally:
        conn.close()
        logger.info("数据库连接已关闭")



def validate_and_correct_label(current_doc_name: str, all_doc_names: List[str]) -> str:
    """
    文档分类结果校验与修正的核心逻辑方法。

    Args:
        current_doc_name: 当前正在处理的文档名称
        all_doc_names: 同批次所有的文档名称列表

    Returns:
        str: 当前文档最终确定的分类打标结果,原始分类
    """
    # ---------------- 边界检查 ----------------
    if not current_doc_name or not all_doc_names:
        logging.warning("入参为空，返回默认类别 'other'")
        return "other","other"

    # ---------------- 步骤1：关键词提取与统计 ----------------
    current_doc_keywords: Set[str] = set()
    matched_category_count = 0
    for category_key, category_keywords in KEYWORD_MAP.items():
        category_matched = False
        for keyword in category_keywords:
            if keyword in current_doc_name:
                current_doc_keywords.add(keyword)
                category_matched = True
        if category_matched:
            matched_category_count += 1

    keyword_count = matched_category_count
    logging.info(f"文档 [{current_doc_name}] 匹配到 {keyword_count} 个分类类别, 具体关键词: {current_doc_keywords}")

    # ---------------- 步骤2：调用分类接口 ----------------
    try:
        status, results = classify_by_file_names(all_doc_names)
        if not status:
            logging.error(f"根据文件名分类错误:{results}")
            return "other","other" # 接口失败时降级为 other
        else:
            logging.info(f"根据文件名分类结果:{results}")
    except Exception as e:
        logging.exception(f"调用分类接口发生未知异常: {e}")
        return "other","other" # 发生网络或解析异常时降级为 other

    # 解析接口结果，构建 mapping: {doc_name: predicted_label}
    doc_to_label_map: Dict[str, str] = {}
    for item in results:
        doc_name = item.get("text_a")
        predictions: Dict[str, float] = item.get("predictions", {})
        if doc_name and predictions:
            # 提取置信度最高的类别作为该文档的 preliminary label
            best_label = max(predictions.items(), key=lambda x: x[1])[0]
            doc_to_label_map[doc_name] = best_label

    # 检查当前文档是否在接口返回结果中
    if current_doc_name not in doc_to_label_map:
        logging.warning(f"接口未返回当前文档 [{current_doc_name}] 的分类结果")
        return "other","other"
        
    label_a = doc_to_label_map[current_doc_name]

    # ---------------- 步骤3：单关键词/无关键词分支 ----------------
    if keyword_count <= 1:
        logging.info(f"命中单关键词/无关键词分支，直接返回接口初步结果: {label_a}")
        return label_a,label_a

    # ---------------- 步骤4：多关键词分支 ----------------
    logging.info(f"命中多关键词分支，当前初步结果 Label_A 为: {label_a}")
    
    # 遍历检查其余文档（非当前文档）的打标结果
    for other_doc_name, label_b in doc_to_label_map.items():
        if other_doc_name == current_doc_name:
            continue
            
        # 获取 Label_B 对应的关键词列表。如果 label_b 是 "other" 或不在字典中，这里安全返回空列表 []
        label_b_keywords = KEYWORD_MAP.get(label_b, [])
        
        # 判定规则：检查 Label_B 对应的关键词列表中，是否有任何一个词存在于当前文档的提取关键词集合中
        # 只要存在交集，即满足条件
        has_intersection = any(kw in current_doc_keywords for kw in label_b_keywords)
        
        if has_intersection:
            logging.info(f"规则匹配成功！其他文档 [{other_doc_name}] 的标签 [{label_b}] "
                         f"包含在当前文档提取的关键词中。维持原判: {label_a}")
            return label_a,label_a

    # 如果遍历完所有其他文档，都不满足判定条件，则修改当前文档结果为 "other"
    logging.info("所有其他文档均不满足交叉验证条件，修正打标结果为: 'other'")
    return "other",label_a

# ============================================================
# 入口
# ============================================================
if __name__ == "__main__":
    output = process_and_label()
    print(f"结果已输出到: {output}")
