from http import HTTPStatus
import requests
# from utils import color_print
import json
import base64
# from utils.draw import color_log
import os

os.environ["no_proxy"] = "10.90.86.76,7.185.125.184"

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def query_intern_vl(messages, verbose=True, temperature=0., max_tokens=1500):
    intern_messages = []
    for message in messages:
        intern_content = []
        for content in message["content"]:
            if "text" in content:
                # if verbose:
                #     color_print(content["text"], 'green')
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
    response = requests.post("http://10.90.86.76:10010/v1/chat/completions", headers=headers, json=payload)
    if response.status_code != HTTPStatus.OK:
        raise ValueError('Request id: %s, Status code: %s, error code: %s, error message: %s' % (
            response.request_id, response.status_code,
            response.code, response.message
        ))
    response_output = response.json()
    role, content = response_output['choices'][0]['message']['role'], response_output['choices'][0]['message'][
        'content']

    # if verbose:
    #     color_print(content, 'blue')

    return role, content

def query_qwen2_vl(messages, verbose=True, temperature=0., max_tokens=1500):
    # print(" messages: ", messages)
    intern_messages = []
    for message in messages:
        intern_content = []
        for content in message["content"]:
            if "text" in content:
                # if verbose:
                #     color_print(content["text"], 'green')
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
        "temperature":temperature,
        "max_tokens": max_tokens
    }
    response = requests.post("http://10.90.86.76:10013/v1/chat/completions", headers=headers, json=payload)
    if response.status_code != HTTPStatus.OK:
        raise ValueError('Request id: %s, Status code: %s, error code: %s, error message: %s' % (
            response.request_id, response.status_code,
            response.code, response.message
        ))
    response_output = response.json()
    role, content = response_output['choices'][0]['message']['role'], response_output['choices'][0]['message'][
        'content']
    
    return role, content

def query_qwen_vl(messages, verbose=True):
    def remove_file_url_prefix(file_url):
        if file_url.startswith('file://'):
            return file_url[len('file://'):]
        return file_url


    # if verbose:
    #     for message in messages:
    #         color_print(message["content"], 'green')

    url = "......"
    headers = {
        "csb-token": "......",
    }

    image_path =  remove_file_url_prefix(messages[1]["content"][0]["image"])

    with open( image_path, "rb") as image_file:
        image_data = base64.b64encode(image_file.read()).decode('utf-8')

    # 文本数据
    text_data = messages[1]["content"][1]["text"]

    data = {
        "image": image_data,
        "text": text_data
    }

    response = requests.post(url, headers=headers, data=data)


    if not response.ok:
        print(f"request qwen server error! response status: {response.status_code}")
        exit(1)

    response_data = json.loads(response.text)

    role, content = response_data['choices'][0]['message']['role'], response_data['choices'][0]['message']['content']
    # if verbose:
    #     color_print(content, 'blue')

    return role, content

def query_qwen2(messages, logger, model_name="Qwen2-72B-Instruct-MLOPS"):
    # max_tokens=1024, logprobs=False, top_logprobs=None , verbose=False
    # for message in messages:
    #     color_log(message["content"],logger, 'green')

    headers = {
        'Authorization': 'Bearer sk-......',
        'Content-Type': 'application/json'
    }
    #print(messages)
    json_data = {
        "model": model_name,
        "messages": messages,
        "temperature": 1e-6,
        #"max_tokens": max_tokens,
        # "logprobs": logprobs,
        # "top_logprobs": top_logprobs
    }

    url = "......"

    response = requests.post(url=url, headers=headers, json=json_data, verify=False)
    if not response.ok:
        print(f"request qwen server error! response status: {response.status_code}")
        exit(1)
    if not response.text:
        print('empty resp')
    response_data = json.loads(response.text)

    # if logprobs:
    #     role, content, logprobs = response_data['choices'][0]['message']['role'], response_data['choices'][0]['message']['content'], response_data['choices'][0]['logprobs']
    #     if verbose:
    #         color_print(content, 'blue')
    #         color_print(logprobs, 'blue')
    #
    #     return role, content, logprobs

    role, content = response_data['choices'][0]['message']['role'], response_data['choices'][0]['message']['content']

    #color_log(content, logger, 'blue')
    return role, content
