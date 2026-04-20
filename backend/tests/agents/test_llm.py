import requests

url = "https://dungvq1234-my-llm-agent.hf.space/generate"
payload = {
    "prompt": "Thủ tục đăng ký học phần online như thế nào?",
    "max_tokens": 50
}

try:
    response = requests.post(url, json=payload, timeout=120)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")