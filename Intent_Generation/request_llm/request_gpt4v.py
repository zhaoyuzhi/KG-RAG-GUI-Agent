import time
import threading
import requests
import base64
import os
import json

TOTAL_COUNT = 0

APP_DESP_MAP = {"汽车": "cars", "新闻阅读": "News reading", "商务办公": "Business and Office", "影音娱乐": "Audio and Visual entertainment",
                "出行导航": "Mobility and Navigation", "社交通讯": "Social communications", "购物比价": "Shopping", "实用工具": "Utilities",
                "金融理财": "Finance", "教育幼教": "Education", "拍摄美化": "Photographing", "便捷生活": "Portable Life"
}

def dump_json(data_=None, tar_=None, indent_=None, ensure_ascii=False):
    with open(tar_, 'w', encoding='utf-8') as f:
        if indent_ is not None:
            json.dump(data_, f, indent=indent_, ensure_ascii=ensure_ascii)
        else:
            json.dump(data_, f, ensure_ascii=ensure_ascii)
    f.close()

def load_json(src_=None):
    with open(src_, 'r', encoding='utf-8') as f:
        data_ = json.load(f)
    f.close()
    return data_

def encode_image(image_path):
    """将图片编码为base64格式"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def call_openai_api(prompt, api_key, model="gpt-4o", temperature=0.7, max_tokens=1024):
    """调用GPT-4o API，传入图片和文本提示"""
    
    # 构建请求内容
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": model,
        "messages": prompt,
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    
    # 发送请求
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        data=json.dumps(payload)
    )
    
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        raise Exception(f"API请求失败: {response.status_code}\n{response.text}")

class ChatGPT:
  def __init__(self):
      # 前置内容-设定角色
      self.messages = []

  def ask_gpt(self, question):
      # 记录问题
      self.messages.append({"role": "user",
                            "content": question}
                            )
      # 发送请求
      api_key = 'sk-......'

      for _ in range(5):
        response = call_openai_api(self.messages, api_key, "gpt-4-vision-preview", 1e-5, 3000)
        if "choices" in response.text:
            break
        
      print(type(response), response.text)
      response_json = json.loads(response.text)
      answer = response_json["choices"][0]["message"]["content"]

      # 记录回答
      self.messages.append({"role": "assistant", "content": answer})

      return answer

if __name__ == "__main__":

    image_path = "/home/cropped_Top225_sample/group-o-1c43d0f2e5fe4c43ae70b1bb20b0ef63.jpeg" # cars
    image_path = "/home/cropped_Top225_sample/group-o-0803d112505348ffb42fd5911c770e7b.jpeg" # Mobility and Navigation
    image_path = "/home/cropped_Top225_sample/group-o-5abe27b879e940909e8b307e7e4f3424.jpeg" # Education

    base64_image = encode_image(image_path)
    prompt_first_round = [
        {
            "type": "text",
            "text": "You are an agent that is trained to perform some basic tasks on a smartphone. This is an App about Education"
                    "Now, given the screenshot of an APP, you need to perceive this page.\n"
                    "Your output should include six parts in the given format:\n"
                    "Observation in parts: <Split the screen to upper, middle and lower parts. Describe the each part in detail, in Chinese>\n"
                    "Observation: <Generalize the screenshot in detail, in Chinese>\n"
                    "Title: <Summarize the function of the screenshot, in one sentence and in Chinese>\n"
                    "Function Blocks: <Summarize the functions provided by several blocks of the screenshot, in numeric order and in Chinese>\n"
                    "Intention: <For each intention, please combine what page you need to enter into based on Title and what task you can complete based on Observation and Function Blocks in one short imperative sentences and in Chinese.>\n"
                    "App-level Intention: <Given you are already in this App, based on the answer above, please generate a general app-level intention according to the information on this page, in one short imperative sentence and in Chinese>"
        },
        {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image}"}
        }
    ]
    
    chat = ChatGPT()
    chat.ask_gpt(question=prompt_first_round)
    # chat.ask_gpt(question=prompt_second_round)
