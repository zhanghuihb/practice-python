import os
import glob
import re


def get_next_output_filename(base_name, ext='.txt'):
    """
    根据已有文件自动生成递增的文件名。
    例如: filing_results_1.txt, filing_results_2.txt, ...
    
    参数:
    base_name (str): 文件名前缀，如 'filing_results'
    ext (str): 文件扩展名，默认 '.txt'
    
    返回:
    str: 下一个可用的文件名
    """
    pattern = f"{base_name}_*{ext}"
    existing_files = glob.glob(pattern)
    
    max_num = 0
    num_pattern = re.compile(rf'{re.escape(base_name)}_(\d+){re.escape(ext)}$')
    for f in existing_files:
        match = num_pattern.search(f)
        if match:
            max_num = max(max_num, int(match.group(1)))
    
    return f"{base_name}_{max_num + 1}{ext}"


def filter_document_filing(input_file_path, output_file_path, exclude_keywords=None):
    """
    遍历输入文件，将标记结果中含有 'document_filing' 的行输出到新文件中。
    如果某行包含排除关键词列表中的任意关键词，则跳过该行。
    
    参数:
    input_file_path (str): 输入 txt 文件的路径
    output_file_path (str): 输出 txt 文件的路径
    exclude_keywords (list): 排除关键词列表，包含这些关键词的行会被过滤掉
    """
    if exclude_keywords is None:
        exclude_keywords = ["备案"]
    
    matched_lines = []
    excluded_count = 0
    
    try:
        # 读取输入文件
        with open(input_file_path, 'r', encoding='utf-8') as f_in:
            for line in f_in:
                line = line.strip()
                
                # 跳过空行
                if not line:
                    continue
                
                # 检查该行是否包含 'document_filing'
                if 'document_filing' not in line:
                    continue
                
                # 检查是否包含排除关键词
                if any(keyword in line for keyword in exclude_keywords):
                    excluded_count += 1
                    continue
                
                matched_lines.append(line)
        
        # 写入输出文件
        with open(output_file_path, 'w', encoding='utf-8') as f_out:
            for line in matched_lines:
                f_out.write(line + '\n')
                
        print(f"处理完成！共找到 {len(matched_lines)} 条包含 'document_filing' 的记录。")
        if exclude_keywords:
            print(f"因包含排除关键词而过滤掉 {excluded_count} 条记录。")
        print(f"结果已保存至: {output_file_path}")
        
    except FileNotFoundError:
        print(f"错误：找不到文件 '{input_file_path}'，请检查路径是否正确。")
    except Exception as e:
        print(f"发生未知错误: {e}")


# --- 使用示例 ---
if __name__ == "__main__":
    input_filename = 'train.txt'
    
    # 自动生成递增的输出文件名
    output_filename = get_next_output_filename('filing_results')
    
    # 排除关键词列表：包含这些关键词的行会被过滤掉
    exclude_list = ["备案"]

    # 调用函数
    filter_document_filing(input_filename, output_filename, exclude_keywords=exclude_list)
    
    # 打印输出文件内容供查看
    print(f"\n--- 输出文件内容预览 ({output_filename}) ---")
    with open(output_filename, 'r', encoding='utf-8') as f:
        print(f.read())