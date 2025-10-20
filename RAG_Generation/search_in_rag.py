import json
from collections import defaultdict
import json
from api.internal_qwen import query_intern_vl
import pickle

def search_for_intention(query_intention, intention_list):
   
    messages = []
    messages.append({
        "role": "system",
        "content": [{'text': 

f"""
你将看到一系列aap可以执行的指令集:
{intention_list}

现在我想要执行的指令为：{query_intention}

请问这个指令可以与哪些可执行指令集匹配，帮我输出匹配度最高的3个可执行指令。

输出格式: 指令1, 指令2, 指令3


"""
        }]})
    
    _, content = query_intern_vl(messages, verbose=False)
    #template_des = content.replace("\n", "").replace("：", ":").replace(":", "").strip()
    return content

if __name__ == '__main__':


    package_list = [
        'com.ctrip.harmonynext',
        'com.netease.cloudmusic.hm',
        'com.sina.weibo.stage',
        'com.vip.hosapp'
    ]

    for package_name in package_list:
        data_dir = f"/home/app_agent/RAG_Generation/data/oracle_test_app_second_stage/{package_name}/graph/"
        with open(f"{data_dir}/{package_name}_image_feature.pkl", 'rb') as f:
            feature_list, name_list = pickle.load(f)

    file_dir = "/home/app_agent/RAGDataset/"
    package = "com.alipay.mobile.client"
    query_intention = "进入消费圈页面"
    file_ = f"{file_dir}/{package}/{package}_clustered_intention.json"
    with open(file_, 'r') as file:
        data = json.load(file)

    intention_list = ""
    for intention in data:
        intention_list += intention + '\n'
    print(intention_list)
    content = search_for_intention(query_intention, intention_list)
    
    print(content)
    