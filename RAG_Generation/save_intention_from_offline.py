import os
import json
import pickle
from utils import query_qwen25
import re

def load_json_file(file_path):
    """
    读取 JSON 文件并返回解析后的数据。
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_img_from_node(node_id, harmonynext_data):
    """
    从 com.ctrip.harmonynext.json 文件中获取指定 node_id 的 img 信息。
    """
    nodes = harmonynext_data.get("nodes", {})
    node = nodes.get(node_id, {})
    
    # 检查 node 是否存在，确保返回正确的 img 信息
    if node:
        exact_scenes = node.get("exactScenes", [])
        if exact_scenes:
            return exact_scenes[0].get("img", "")
    return None

def process_history_files(root_dir, graph_data):
    """
    处理指定路径下的所有子目录中的 history.json 文件，
    获取每个历史记录中的 node 并提取对应的 img 和 action 信息。
    """
    results_all = {}
    # 遍历所有子目录

    '''
    {'image_id': 
        {'intention1':
            {'node_list': 
                'action_list':
                }
            'intention2':,
            ....
                    }
    '''

    for subdir, _, files in os.walk(root_dir):
        for file in files:
            if file == "history.json":
                history_path = os.path.join(subdir, file)
                history_data = load_json_file(history_path)
                
                intention_name = os.path.basename(subdir)
                #print(intention_name)
                #intention[intention_name] = {}

                image_list = []
                action_list = []
                print(subdir+'/history.json')

                if len(history_data) > 1:
                    trajectory = history_data[1].get("trajectory", [])
                    
                    node_id = trajectory[0]  # 从 trajectory 中获取节点 ID
                    img1 = get_img_from_node(node_id, graph_data)

                    if img1 not in results_all:
                        results_all[img1] = []
                    if img1:
                        image_list.append(img1)
                    print(len(history_data))
                    for history_item in history_data[1:]:
                        

                        trajectory = history_item.get("trajectory", [])
                        for t in trajectory[1:]:
                        # 处理 history.json 中的每一项（跳过第一个）
                            
                            img2 = get_img_from_node(t[0], graph_data)
                            image_list.append(img2)

                            action_list.append(t[1])

                    action_contents = ""
                    for act in action_list:
                        action_contents += act +"\t"
                    intention = intention_name
                    output_planning = summary_available_path(action_contents, intention)
                    sing_result = { 
                                    "intention": intention_name,
                                    "img_list": image_list,
                                    "action_list": action_list,
                                    "templates": output_planning}
                    
                    results_all[img1].append(sing_result)
                
    return results_all

def summary_available_path(action_contents, intention, model="internvl2"):

    # main body
    messages = []
    messages.append({
        "role": "system",
        "content": [{'text': "您是一名人工智能助手，擅长于手机应用程序交互。"}]
    })
    messages.append({
            'role': 'user',
            'content': [
                {
                    'text': 
    f"""
    ### 任务
    给定一个意图:{intention}，
    然后根据这个意图, 手机自动执行了一些操作:
    {action_contents}，
    请帮我总结一下这些操作能够实现的意图;
    意图里面有些描述可以作为参数被替换成其他变量，比如：地点、人名、物品名称等名词
    ```
    播放周杰伦的歌曲
    这里的周杰伦是变量，可以被替换为林俊杰
    ```
    如果发现存在这种变量将这些变量用"[]"括起来,并总结"[]"内部用一个类别名词
    """
        },
    ]
    })
    
    messages[-1]["content"][-1]["text"] += \
    """
    ### 输出格式
    意图为: _______   

    注意：不需要解释，只需要输出意图 
    """

    role, content = query_qwen25(messages, temperature=0., max_tokens=1500)
    # check format
    #print(intention, action_contents, content)
    print(content)
    content_ = content.split('\n')[0].split("意图为: ")[-1]
    print(content_)

    return content_

def main():
    # 设置根目录路径

    package_list = [
        #'com.ctrip.harmonynext',
        #'com.netease.cloudmusic.hm',
        #'com.sina.weibo.stage',
        #'com.vip.hosapp'
        #'com.dragon.read.next',
        'com.tencent.hm.qqmusic'
    ]

    package = package_list[0]
    base_dir = f"/home/app_agent/RAGGeneration_New/data/oracle_test_app_second_stage/{package}/graph/"
    root_dir = f"{base_dir}/intention_path/" 
    graph_path = f"{base_dir}/{package}.json"

    # 读取 haronynext.json 文件
    graph_data = load_json_file(graph_path)


    # 处理 history.json 文件并提取 img 和 action 信息
    results_all = process_history_files(root_dir, graph_data)
    
    with open(f'{base_dir}/{package}_node_available_path_template.json', 'w', encoding='utf-8') as f:
        json.dump(results_all, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    main()
