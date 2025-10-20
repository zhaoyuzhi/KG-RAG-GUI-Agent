import time
from http import HTTPStatus
import requests
import json
import base64
from lmdeploy.serve.openai.api_client import APIClient

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def query_intern_vl2(messages, temperature=0., max_tokens=1500):
    intern_messages = []
    for message in messages:
        intern_content = []
        for content in message["content"]:
            if "text" in content:
                intern_content.append({
                    "type": "text",
                    "text": content["text"]
                })
            elif "image" in content:
                base64_img = encode_image(messages[1]['content'][0]['image'])
                intern_content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_img}"
                    }
                })
        intern_messages.append({
            "role": message["role"],
            "content": intern_content
        })

    headers = {"Content-Type": "application/json"}
    payload = {
        "model": "internvl2-76b-AWQ",
        "messages": intern_messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    response = requests.post("http://10.90.86.76:10090/v1/chat/completions", headers=headers, json=payload)
    if response.status_code != HTTPStatus.OK:
        raise ValueError('Request id: %s, Status code: %s, error code: %s, error message: %s' % (
            response.request_id, response.status_code,
            response.code, response.message
        ))
    response_output = response.json()
    print(response_output)
    role, content = response_output['choices'][0]['message']['role'], response_output['choices'][0]['message']['content']

    return role, content

def query_qwen2_vl(messages, temperature=0., max_tokens=1500):
    intern_messages = []
    for message in messages:
        intern_content = []
        for content in message["content"]:
            if "text" in content:
                intern_content.append({
                    "type": "text",
                    "text": content["text"]
                })
            elif "image" in content:
                base64_img = encode_image(messages[1]['content'][0]['image'])
                intern_content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_img}"
                    }
                })
        intern_messages.append({
            "role": message["role"],
            "content": intern_content
        })

    headers = {"Content-Type": "application/json"}
    payload = {
        "model": "Qwen2-72B-Instruct-AWQ",
        "messages": intern_messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    response = requests.post("http://10.90.86.76:9527/v1/chat/completions", headers=headers, json=payload)
    if response.status_code != HTTPStatus.OK:
        raise ValueError('Request id: %s, Status code: %s, error code: %s, error message: %s' % (
            response.request_id, response.status_code,
            response.code, response.message
        ))
    response_output = response.json()
    role, content = response_output['choices'][0]['message']['role'], response_output['choices'][0]['message']['content']

    return role, content

def query_qwen25(messages, temperature=0., max_tokens=1500):
    intern_messages = []
    for message in messages:
        intern_content = []
        for content in message["content"]:
            if "text" in content:
                intern_content.append({
                    "type": "text",
                    "text": content["text"]
                })
        intern_messages.append({
            "role": message["role"],
            "content": intern_content
        })

    headers = {"Content-Type": "application/json"}
    payload = {
        "model": "Qwen2.5-72B",
        "messages": intern_messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    response = requests.post("http://10.90.86.76:5200/v1/chat/completions", headers=headers, json=payload)
    if response.status_code != HTTPStatus.OK:
        raise ValueError('Request id: %s, Status code: %s, error code: %s, error message: %s' % (
            response.request_id, response.status_code,
            response.code, response.message
        ))
    response_output = response.json()
    role, content = response_output['choices'][0]['message']['role'], response_output['choices'][0]['message']['content']

    return role, content

if __name__ == '__main__':
    
    img_path = 'group-o-00e7f0c836e744c5bb9acb423908ca22.jpeg'
    
    messages = []
    messages.append({
        "role": "system",
        "content": [{'text': "您是一名人工智能助手，负责帮助视觉障碍用户与手机应用程序进行交互并导航以完成特定任务。"}]
    })
    messages.append({
            'role': 'user',
            'content': [
                {
                    'image': img_path
                },
                {
                    'text': 
    """
    请详细描述当前屏幕截图，包括布局、可见控件及任何文本或图标。特别强调屏幕上的主要功能和导航线索或互动控件，但不包括最顶部的状态栏，该状态栏包括时间、网络状态、WiFi等信息。请将当前屏幕分为上、中、下三个部分进行分析。不要遗漏任何细节，并列出所有可交互的控件。如果当中出现列表，请把列表里的东西一一列出。
    若屏幕上显示有\"ADB Keyboard {{ON}}\"，请回复:\"True\"。若无，请回复:\"False\"。

    ### 输出格式
    你的输出应该遵循以下格式：
    上部描述: <填写屏幕上部描述>
    中部描述: <填写屏幕中部描述>
    下部描述: <填写屏幕下部描述>
    ADB Keyboard: <True/False>
    """
        },
    ]
    })

    role, content = query_intern_vl2(messages, temperature=0., max_tokens=1500)
    print(role, content)

    # -------------------------------------------------------
    
    '''
    messages = []
    messages.append({
        "role": "system",
        "content": [{'text': "您是一名人工智能助手，负责帮助视觉障碍用户与手机应用程序进行交互并导航以完成特定任务。"}]
    })
    messages.append({
            'role': 'user',
            'content': [
                {
                    'text': 
    """
    你好
    """
        },
    ]
    })

    role, content = query_qwen25(messages, temperature=0., max_tokens=1500)
    print(role, content)
    '''
