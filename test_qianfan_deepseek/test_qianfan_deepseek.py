import requests
import json

# === 配置区 ===
AK = "your_access_key"  # 替换为你的百度 AK
SK = "your_secret_key"  # 替换为你的百度 SK
MODEL_NAME = "deepseek-v3"  # 确保这是千帆控制台里显示的准确模型名
TOKEN="bce-v3/ALTAK-6YCdh6abSEMtiL2YDzBc4/568835bc2ba03be5eb59bd8d0ca1e26447b6ba34"


# Step 1: 获取 access_token
def get_access_token(ak, sk):
    url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {
        "grant_type": "client_credentials",
        "client_id": ak,
        "client_secret": sk
    }
    response = requests.post(url, params=params)
    result = response.json()
    return result.get("access_token"), result


# Step 2: 调用 DeepSeek 模型
def test_deepseek_on_qianfan(access_token, model_name):
    url = "http://qianfan.baidubce.com/v2/chat/completions"
    headers = {"Content-Type": "application/json"}
    params = {"access_token": access_token}
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": "你好，请回复 'OK'"}],
        "temperature": 0.1,
        "top_p": 0.9,
        "seed": 49,
        "max_output_tokens": 20  # 避免长响应
    }
    response = requests.post(url, headers=headers, json=payload, params=params)
    return response.status_code, response.json()


# 主流程
if __name__ == "__main__":
    if not TOKEN:
        print("🔧 正在获取 access_token...")
        token, auth_res = get_access_token(AK, SK)
        if not token:
            print("❌ 获取 access_token 失败！请检查 AK/SK 是否正确。")
            print("错误详情:", json.dumps(auth_res, indent=2, ensure_ascii=False))
        else:
            TOKEN = token

    print("✅ access_token 获取成功！")
    print("📡 正在调用 DeepSeek 模型...")
    status, result = test_deepseek_on_qianfan(TOKEN, MODEL_NAME)

    if status == 200:
        print("✅ 模型调用成功！AK/SK 有效，模型可用。")
        print("🤖 回复内容:", result["result"])
    elif status == 404 and "model" in str(result).lower():
        print("❌ 模型名称可能错误！请登录千帆控制台确认模型 ID。")
        print("返回:", result)
    elif status == 403:
        print("❌ AK/SK 无权限访问该模型（可能未开通或配额不足）。")
        print("返回:", result)
    else:
        print(f"❌ 调用失败 (HTTP {status}):")
        print(json.dumps(result, indent=2, ensure_ascii=False))