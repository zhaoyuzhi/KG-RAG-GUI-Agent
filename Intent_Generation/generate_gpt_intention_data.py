import time
import threading
import requests
import base64
import os
import json

TOTAL_COUNT = 0

APP_DESP_MAP = {"汽车": "cars", "新闻阅读": "News reading", "新闻阅读电子书": "E-book reading", "新闻阅读新闻垂类": "News reading", "商务办公": "Business and Office", "影音娱乐": "Audio and Visual entertainment",
                "出行导航": "Mobility and Navigation", "社交通讯": "Social communications", "购物比价": "Shopping", "实用工具": "Utilities",
                "金融理财": "Finance", "教育幼教": "Education", "拍摄美化": "Photographing", "剪辑类": "Photograph clipping", "美化类": "Photograph retouching", "拍摄类": "Photographing", "便捷生活": "Portable Life"
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

# save a dictionary object to a json file
def json_save(json_content, json_file):
    with open(json_file, 'a') as fp:
        json.dump(json_content, fp, indent=4)

# read a json file, return the json_content
def json_read(json_file):
    with open(json_file, 'r') as f:
        # json_content = json.load(f)
        json_content = json.loads(f.read())
        return json_content

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

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

      for _ in range(10):
        response = call_openai_api(self.messages, api_key, "gpt-4-vision-preview", 1e-5, 3000)
        if "choices" in response.text:
            break

      print(type(response), response.text)
      response_json = json.loads(response.text)
      answer = response_json["choices"][0]["message"]["content"]
      
      # 记录回答
      self.messages.append({"role": "assistant", "content": answer})

      return answer

def thread_get_gpt_answer(save_dir_path, data_dir_path, dirname_list, threading_lock_):
    global TOTAL_COUNT
    for dirname in dirname_list:
        new_data_dir_path = data_dir_path + "/" + dirname
        walk_dir = os.walk(new_data_dir_path)
        for path, d, filelist in walk_dir:
            for filename in filelist:
                if not filename.endswith("jpeg"):
                    continue
                cur_file_path = path + "/" + filename
                save_file_dir = save_dir_path + path.replace("/home/dataset/top225/Top225_type/", "").replace("/dist/static/screenshot", "")
                os.makedirs(save_file_dir, exist_ok=True)
                if filename.replace("jpeg", "json") in os.listdir(save_file_dir):
                    continue
                save_file_path = save_file_dir + "/" + filename.replace("jpeg", "json")
                dirname_type = save_file_path.split("/")[-3]
                if dirname_type.startswith("影音娱乐"):
                    dirname_type = "影音娱乐"
                dirname_type_chinese = APP_DESP_MAP[dirname_type]
                base64_image = encode_image(cur_file_path)
                prompt_first_round = [
                    {
                        "type": "text",
                        "text": f"You are an agent that is trained to perform some basic tasks on a smartphone. This is an App about {dirname_type_chinese}"
                                "Now, given the screenshot of an APP, you need to perceive this page.\n"
                                "Your output should include four parts in the given format:\n"
                                "Observation: <Describe the screenshot in detail, in Chinese>\n"
                                "Title: <Summarize the function of the screenshot, in one sentence and in Chinese>\n"
                                "Function Blocks: <Summarize the functions provided by several blocks of the screenshot"
                                ", in Chinese>\n"
                                "Intention: <Based on the information above, please generalize what page you need to enter into and what task you can complete, give your answer in one short imperative sentence and in Chinese>\n"
                                "App-level Intention: <Given you are already in this App, based on the answer above, please generate a general app-level intention according to the information on this page, in one short imperative sentence and in Chinese>"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"}
                    }
                ]
                chat = ChatGPT()
                answer = chat.ask_gpt(question=prompt_first_round)

                threading_lock_.acquire()
                json_save(answer, save_file_path)
                TOTAL_COUNT += 1
                print(f"当前完成个数:{TOTAL_COUNT}")
                threading_lock_.release()

if __name__ == "__main__":

    # 先不生成：未确认，商务办公
    # 有subtype的类，后生成
    black_dirname_list = ["未确认", "商务办公"]
    have_sub_type_dirname_list = ["新闻阅读", "影音娱乐", "拍摄美化"]
    save_dir_path = "/home/code/data/Top225_type/"
    data_dir_path = "/home/dataset/top225/Top225_type/"
    cnt = 0
    valid_dirname_list = [x for x in os.listdir(data_dir_path) if x not in black_dirname_list]
    len_valid_dirname_list = len(valid_dirname_list)
    print(len_valid_dirname_list)
    dirname_list_1 = valid_dirname_list[:3]
    dirname_list_2 = valid_dirname_list[3:6]
    dirname_list_3 = valid_dirname_list[6:9]
    dirname_list_4 = valid_dirname_list[9:11]
    dirname_list_5 = valid_dirname_list[11:]
    threading_list_ = list()
    threading_lock_ = threading.Lock()
    threading_list_.append(threading.Thread(target=thread_get_gpt_answer,
                                            args=(save_dir_path, data_dir_path, dirname_list_1, threading_lock_),
                                            daemon=True))
    threading_list_.append(threading.Thread(target=thread_get_gpt_answer,
                                            args=(save_dir_path, data_dir_path, dirname_list_2, threading_lock_),
                                            daemon=True))
    threading_list_.append(threading.Thread(target=thread_get_gpt_answer,
                                            args=(save_dir_path, data_dir_path, dirname_list_3, threading_lock_),
                                            daemon=True))
    threading_list_.append(threading.Thread(target=thread_get_gpt_answer,
                                            args=(save_dir_path, data_dir_path, dirname_list_4, threading_lock_),
                                            daemon=True))
    threading_list_.append(threading.Thread(target=thread_get_gpt_answer,
                                            args=(save_dir_path, data_dir_path, dirname_list_5, threading_lock_),
                                            daemon=True))
    for t_ in threading_list_:
        t_.start()
    for t_ in threading_list_:
        t_.join()
