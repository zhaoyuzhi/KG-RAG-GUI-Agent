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

    file_dir = "/home/app_agent/RAGDataset/"
    #package = "com.alipay.mobile.client"
    package = "com.sankuai.hmeituan"
    file_ = f"{file_dir}/{package}/{package}_subintention.json"
    with open(file_, 'r') as file:
        data = json.load(file)

    # 用于存储相同 (node_list, action_list) 的条目ID
    clustered_entries = defaultdict(list)

    # 遍历 JSON 数据
    for key, value in data.items():
        key_tuple = (tuple(value["node_list"]), tuple(value["action_list"]))
        clustered_entries[key_tuple].append(key)

    list_all = 0

    intention_item = {}
    # 输出聚类结果
    for key_tuple, ids in clustered_entries.items():

        print(f"相同 node_list 和 action_list 的条目: {ids}")

        intention_list = []
        intention_str = ""
        print(f"Items with same node_list {key_tuple}: {ids}")
        if len(ids) > 1: 
            for item  in ids:
                intention_list.append(data[item]["subintention"])
                intention_str += data[item]["subintention"] + "\n"
            print(intention_list)
        else:
            print(ids)
            intention_list.append(data[ids[0]]["subintention"])
            intention_str += data[ids[0]]["subintention"] + "\n"
        

        content = get_template_for_intention(intention_str)
        print(content, '-----')
        intention_item[data[ids[0]]["subintention"]] = {
            "node_list": data[ids[0]]["node_list"],
            "action_list": data[ids[0]]["action_list"],
            "subintention_list": intention_list
        }
        list_all += 1

    with open(f"{file_dir}/{package}/{package}_clustered_intention.json", "w", encoding='utf-8') as f:
        json.dump(intention_item, f, ensure_ascii=False, indent=4)
        
    print(list_all)
