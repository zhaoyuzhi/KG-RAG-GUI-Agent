import os
import re
import sys
current_path = os.getcwd()  
print(f"current_path:{current_path}")
sys.path.append(current_path)
from utils import load_json, save_json
from api.internal_qwen import query_intern_vl, query_qwen_vl
from tqdm import tqdm

def get_node_desc(image_path):
    messages = []
    messages.append({
        "role": "system",
        "content": [{'text': "您是一名人工智能助手，负责帮助视觉障碍用户与手机应用程序进行交互并导航以完成特定任务。"}]
    })
    messages.append({
            'role': 'user',
            'content': [
                {
                    'image': image_path
                },
                {
                    'text': 
"""
请详细描述当前屏幕截图，包括布局、可见控件及任何文本或图标。特别强调屏幕上的主要功能和导航线索或互动控件，但不包括最顶部的状态栏，该状态栏包括时间、网络状态、WiFi等信息。请将当前屏幕分为上、中、下三个部分进行分析。不要遗漏任何细节，并列出所有可交互的控件。如果当中出现列表，请把列表里的东西一一列出。

### 输出格式
你的输出应该遵循以下格式：
上部描述: <填写屏幕上部描述>
中部描述: <填写屏幕中部描述>
下部描述: <填写屏幕下部描述>
整体描述: <一句话概括屏幕截图的核心功能>
"""
                },
            ]
            })
    role, content = query_intern_vl(messages, verbose=False)
    content = content.replace("\n", "").replace("：", ":").replace(":", "")
    try:
        top_description = re.search(r'上部描述\s*(.*?)\s*中部描述', content).group(1).strip()
    except:
        top_description = ""
    try:
        mid_description = re.search(r'中部描述\s*(.*?)\s*下部描述', content).group(1).strip()
    except:
        mid_description = ""
    
    try:
        bottom_description = re.search(r'下部描述\s*(.*?)\s*整体描述', content).group(1).strip()
    except:
        bottom_description = ""

    try:
        overall_description = re.search(r'整体描述\s*(.*)', content).group(1).strip()
    except:
        overall_description = ""

    resp = {
        'top': top_description,
        'mid': mid_description,
        'bottom': bottom_description,
        'overall': overall_description
    }

    return resp

if __name__ == "__main__":
    package_names = ['com.ctrip.harmonynext', 'com.dragon.read.next', 'com.netease.cloudmusic.hm', 'com.tencent.hm.qqmusic', 'com.sina.weibo.stage', 'com.vip.hosapp']
    #package_names = ['com.gotokeep.keep'] #['com.alipay.mobile.client']
    graph_dir = "/home/app_agent/RAGGeneration_New/data/oracle_test_app_second_stage/"
    for package_name in package_names:
        path_prefix = os.path.join(graph_dir, package_name, 'graph')
        json_data = os.path.join(path_prefix, f'{package_name}.json')
        screenshot_dir = os.path.join(path_prefix, 'screenshot')
        dist_data = load_json(json_data)
        node_data = dist_data["nodes"]
        node2desc = {}
        for node_id, node in tqdm(node_data.items()):
            filename = node["exactScenes"][0]["img"]
            node2desc[node_id] = get_node_desc(os.path.join(screenshot_dir, filename))

        save_json(node2desc, os.path.join(path_prefix, 'node_desc.json'))