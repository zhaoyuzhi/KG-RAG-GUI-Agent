import base64
import requests

import dashscope
from dashscope import MultiModalConversation

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def inference_chat(chat, model, api_url, token):    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    data = {
        "model": model,
        "messages": [],
        "max_tokens": 2048,
        'temperature': 0.0,
        "seed": 1234
    }

    for role, content in chat:
        data["messages"].append({"role": role, "content": content})

    while True:
        try:
            res = requests.post(api_url, headers=headers, json=data)
            res_json = res.json()
            # res_content = res_json['data']['response']['choices'][0]['message']['content']#['choices'][0]['message']['content']
            res_content = res_json['choices'][0]['message']['content']
        except:
            print("Network Error:")
            try:
                print(res.json())
            except:
                print("Request Failed")
        else:
            break
    
    return res_content

def inference_chat_by_qwen(prompt, image_path_list, model, api_key):
    dashscope.api_key = api_key
    messages = [{
        'role': 'user',
        'content': []
    }]
    for image_path in image_path_list:
        messages[0]['content'].append({
            'image': "file://" + image_path
        })
    messages[0]['content'].append({
        'text': prompt
    })
    if len(image_path_list) > 0:
        response = MultiModalConversation.call(model=model, messages=messages, top_k=0)
        response = response['output']['choices'][0]['message']['content'][0]["text"]
    else:
        response = dashscope.Generation.call(model=model, messages=messages, top_k=0)
        response = response['output']["text"]

    return response