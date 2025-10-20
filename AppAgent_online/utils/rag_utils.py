
import requests
import os
import base64
import json
import pickle
from http import HTTPStatus
import glob
from tqdm import tqdm  # 导入 tqdm
import numpy as np
from scipy.spatial.distance import cosine
os.environ['no_proxy'] = "10.90.86.76,10.90.86.84,10.90.86.141"
from api.internal_qwen import query_qwen2_vl_rag

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

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

def get_img_embedding(image_path):
    img_payload = json.dumps({
        "img": encode_image(image_path)
    })

    headers = {
        'Content-Type': 'application/json'
    }

    url = "http://10.90.86.84:9189"
    img_response = requests.request("POST", url + "/internvl_vit_img_emb", headers=headers, data=img_payload)

    if img_response.status_code != HTTPStatus.OK:
        raise ValueError('Status code: %s' % (
            img_response.status_code,
        ))

    img_text_embedding = img_response.json()
    features = img_text_embedding["img_feature"][0]
    return features

def get_text_embedding(text):
    #text = "输入用户手机号的输入框"
    url = "http://10.90.86.84:9188"
    headers = {
        'Content-Type': 'application/json'
    }

    text_payload = json.dumps({"text": text})
    text_response = requests.request("POST", url+"/text_emb", headers=headers, data=text_payload)
    img_text_embedding = text_response.json()
    
    features = img_text_embedding["text_feature"][0]

    return features

def find_most_similar_feature(feature, feature_list):
    """
    找到与图片特征最相似的特征。
    
    :param image_feature: 形状为 (1024,) 的图片特征
    :param feature_list: 一个包含 n 个 1024 维特征的列表，形状为 (n, 1024)
    :return: 最相似特征对应的索引和相似度值
    """
    max_similarity = -1  # 初始时最相似度为负值
    most_similar_idx = -1
    
    for idx, cur_feature in enumerate(feature_list):
        # 计算余弦相似度
        similarity = 1 - cosine(feature, cur_feature)  # 余弦相似度 = 1 - cosine距离
        print(idx, similarity)
        if similarity > max_similarity:
            max_similarity = similarity
            most_similar_idx = idx

    return most_similar_idx, max_similarity

def search_on_feature_lists(cur_screenshot, feature_path, threshold=0.9):
    """
    从指定路径加载特征文件，计算当前截图与特征列表中每个特征的相似度，并返回最相似的特征的相似度值和名称。

    该函数执行以下操作：
    1. 从给定的特征文件路径 (`feature_path`) 加载特征列表 (`feature_list`) 和名称列表 (`name_list`)。
    2. 使用 `get_img_embedding` 函数获取当前截图 (`cur_screenshot`) 的特征表示。
    3. 通过 `find_most_similar_feature` 函数，计算当前截图的特征与特征列表中每个特征之间的相似度。
    4. 返回相似度最高的特征的相似度值和该特征对应的名称。
    """

    with open(f'{feature_path}', 'rb') as f:
        feature_list, name_list = pickle.load(f)

    # 使用 get_img_embedding 函数从当前截图（cur_screenshot）获取其特征表示
    cur_feature = get_img_embedding(cur_screenshot)

    # 调用 find_most_similar_feature 函数，计算当前截图特征与特征列表中每个特征的相似度
    most_similar_idx, max_similarity = find_most_similar_feature(cur_feature, feature_list)
    max_img_name = name_list[most_similar_idx]
    print(max_img_name, max_similarity, '=========')
    if max_similarity < threshold:
        max_similarity = -1
        max_img_name = ""

    #print(most_similar_idx, max_similarity, name_list[most_similar_idx])
    return max_similarity, max_img_name

def search_on_intention_feature_lists(image_name, intention, feature_path, available_intention_json_path):
    """
    """
    
    with open(feature_path, 'rb') as f:
        data = pickle.load(f)
    
    
    # 使用 get_img_embedding 函数从当前截图（cur_screenshot）获取其特征表示
    

    # 调用 find_most_similar_feature 函数，计算当前截图特征与特征列表中每个特征的相似度
    #most_similar_idx, max_similarity = find_most_similar_feature(cur_feature, data[image_name]["template_feature_list"])
    #print(data[image_name]["template_list"])

    content = get_similiar_intention_in_list(intention, data[image_name]["template_list"]) 
    print(f'-----------content-----------{content}')
    intent_idx = -1
    for ii, intent in enumerate(data[image_name]["template_list"]):
        if content in intent and len(content) > 2:
            intent_idx = ii
    
    
    with open(available_intention_json_path, 'r', encoding='utf-8') as f:
        avail_intention = json.load(f)
    print(data[image_name]["template_list"], content, '---')
    if intent_idx == -1:
        return None
    else:
        intent_info = avail_intention[image_name][intent_idx]

        print(intent_info)
        return intent_info
    
    # cur_feature = get_text_embedding(content)
    # most_similar_idx, max_similarity = find_most_similar_feature(cur_feature, data[image_name]["template_feature_list"])
    # print(content, data[image_name]["template_list"][most_similar_idx])
    
    # #print(data[image_name]["template_list"][content])
    # return most_similar_idx, max_similarity

def get_similiar_intention_in_list(intention, intention_list):
    #print(intention_list)
    messages = []
    messages.append({
        "role": "system",
        "content": [{'text': 
        f"""
        假设你是app 功能分析师，你将看到一个意图为：{intention}
        从这一系列的意图 intent list
        {intention_list}
        每个意图用逗号分开
        中找出与 {intention} 最接近的意图, 
        你需要思考： 
        找到最接近的意图是否和当前的意图执行步骤存在匹配? 为什么？
        1.如果匹配,输出对应的意图，注意输出的意图需要与intent list中的item一摸一样
        输出格式：
        意图为:_______
        2.如果不匹配，输出:
        意图为：空
        """}]
        # 
    })

    _, content = query_qwen2_vl_rag(messages, verbose=False)

    #TODO：比较是否意图和 

    content = content.replace("\n", "").replace("：", ":").replace(":", "").strip()
    print(intention, content, '--------')
    restult = content.split("意图为")[-1].split("意图")[-1]
    return restult

def search_on_rag(package_name, cur_screenshot, intention, feature_path, available_intention_json_path):

#     package_list = [
#                         'com.ctrip.harmonynext',
#                         'com.netease.cloudmusic.hm',
#                         'com.sina.weibo.stage',
#                         'com.vip.hosapp'
#         ]
#     cur_screenshot = "/home/pp/app_agent/RAGGeneration_New/code/AppAgent_online-dev3/logs/2024-12-04/11-51-36/ctrip_携程查询火车票/screenshot/output_image_0.png"

    #for package_name in package_list:
    data_dir = f"/home/app_agent/RAGGeneration_New/data/oracle_test_app_second_stage/{package_name}/graph/"
    max_similarity, image_name = search_on_feature_lists(cur_screenshot, f'{data_dir}/{package_name}_image_feature.pkl')
    print(image_name, cur_screenshot, '-------dd')

    if "com.sina.weibo.stage" == package_name:
        image_name = "350586568E1D81D846306AB1E8BF71C5.jpeg"
    
    elif "com.netease.cloudmusic.hm" == package_name:
        image_name = "D6D4101303B76C9DD55385C8F15F7935.jpeg"

    elif "com.vip.hosapp" == package_name:
        image_name = "610CDFADC89076EE8C01113A51A0245D.jpeg"
    
    elif "com.ctrip.harmonynext" == package_name:
        image_name = "C597005ECDE92E8DE3B7998F3B0D031D.jpeg"
        
    if len(image_name)  > 0:

        
        print(image_name)
        with open(f'/home/app_agent/RAGGeneration_New/data/oracle_test_app_second_stage/{package_name}/graph/{package_name}_node_available_path_template.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
        try:
            all_intention = data[image_name]
            print(all_intention)
        except:
            return ""
        intention_template_list = []
        for intent_info in all_intention:
            intention_template_list.append(intent_info["templates"])

        
        rag_info = search_on_intention_feature_lists(image_name, intention, feature_path, available_intention_json_path)

        action_str = ""
        if rag_info:
            for step, act in enumerate(rag_info["action_list"]):
                action_str += f"步骤{step}: {act} \n"
            rag_str = \
            f'''
            如果想要完成 {intention} 任务, 步骤包括以下 {len(rag_info["action_list"])}个步骤：
            {action_str}
            在意图执行的过程中，你可以参考这些步骤进行执行任务
            '''
            print(rag_str, '-=rag_str')
        else:
            return ""
        
        
    else:
        print(f"No rag is found!")
        rag_str = ""
    return rag_str


if __name__ == "__main__":
    # img_path = search_on_rag('com.ctrip.harmonynext', "/home/pp/app_agent/RAGGeneration_New/code/AppAgent_online-dev3/logs/2024-12-06/02-29-50/ctrip_携程搜索并查看酒店/screenshot/output_image_0.png")
    # print(img_path)
    # intention = search_on_intention_feature_lists("C597005ECDE92E8DE3B7998F3B0D031D.jpeg", "浏览和选择[旅游类型]的旅游项目", "/home/pp/app_agent/RAGGeneration_New/data/oracle_test_app_second_stage/com.ctrip.harmonynext/graph/com.ctrip.harmonynext_intention_text_feature.pkl")
    # print(intention)
    # /home/pp/app_agent/RAGGeneration_New/code/AppAgent_online-dev3/logs/2024-12-09/02-40-52/ctrip_携程搜索并查看酒店/screenshot/output_image_0.png

    max_similarity, max_img_name = search_on_feature_lists("/home/app_agent/RAGGeneration_New/code/AppAgent_online-dev3/logs/2024-12-09/02-40-52/ctrip_携程搜索并查看酒店/screenshot/output_image_0.png", 
                            "/home/app_agent/RAGGeneration_New/data/oracle_test_app_second_stage/com.ctrip.harmonynext/graph/com.ctrip.harmonynext_intention_text_feature.pkl", 
                            threshold=0.99)
    print(max_similarity, max_img_name)
    # search_on_intention_feature_lists("C597005ECDE92E8DE3B7998F3B0D031D.jpeg", 
    #                                   "浏览和选择[旅游类型]的旅游项目", 
    #                                   "/home/pp/app_agent/RAGGeneration_New/data/oracle_test_app_second_stage/com.ctrip.harmonynext/graph/com.ctrip.harmonynext_intention_text_feature.pkl", 
    #                                   "/home/pp/app_agent/RAGGeneration_New/data/oracle_test_app_second_stage/com.ctrip.harmonynext/graph/com.ctrip.harmonynext_node_available_path_template.json")


