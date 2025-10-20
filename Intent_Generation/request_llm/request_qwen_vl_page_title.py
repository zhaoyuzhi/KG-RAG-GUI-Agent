import requests
import json
import base64

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def request_qwen_vl_page_title(image_base64):
    request_data = {"top_k": 1,
                    "top_p": 0.001,
                    "temperature": 0.001,
                    "max_tokens": 1500,
                    "img": image_base64
                    }
    headers = {
        'Content-Type': 'application/json'
    }
    #
    response = requests.post('http://10.90.86.89:8081/qwen_vl_page_title', data=json.dumps(request_data),
                             headers=headers)

    res = json.loads(response.text)
    print(f"描述模型返回的结果：{res}")

if __name__ == "__main__":
    image_path = "/home/code/intention_generation/4khd/graph_data/抖音/screenshot/6A082AAEC0E0C10F4BBA6E67E23A4537.jpeg"
    image_base64 = encode_image(image_path)
    request_qwen_vl_page_title(image_base64)
