import json
from collections import defaultdict
import json
from api.internal_qwen import query_intern_vl

def get_template_for_intention(intention_list):
   
    messages = []
    messages.append({
        "role": "system",
        "content": [{'text': 

f"""
以下的内容是所有的意图列表, 帮我这些意图总结出一个主要的意图：
{intention_list}

输出格式: 意图
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
    
    #package_name = "com.sankuai.hmeituan"
    for package_name in package_list:
        file_dir= f"/home/app_agent/RAGGeneration_New/data/oracle_test_app_second_stage/{package_name}/graph/"
            
        file_ = f"{file_dir}/{package_name}_clustered_intention.json"
        with open(file_, 'r') as file:
            data = json.load(file)


        node_id_dict = defaultdict(list)

        for key, value in data.items():
            node_id = value['node_list'][0]
            print(key, node_id)
            node_id_dict[node_id].append({
                'intention': key,
                'node_list': value['node_list'],
                'action_list': value['action_list'],
                'subintention_list': value['subintention_list']
            })

        formatted_data = dict(node_id_dict)
        print(formatted_data)
        print(f"{file_dir}/{package_name}_clustered_intention_node_id.json")
        with open(f"{file_dir}/{package_name}_clustered_intention_node_id.json", "w", encoding='utf-8') as f:
            json.dump(formatted_data, f, ensure_ascii=False, indent=4)
