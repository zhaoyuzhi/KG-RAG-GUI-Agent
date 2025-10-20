from glob import glob 

import os
import json
from api.internal_qwen import query_qwen2_vl

import json
def get_summary_for_intention(intention, milestone_list, succeed_milestone):
    messages = []
    messages.append({
        "role": "system",
        "content": [{'text': 
f"""
假设你是app 功能分析师，你将看到一个意图为：{intention}
我们分析出执行这个意图需要的步骤为：{milestone_list}。
但是我们在实际操作中发现，由于操作控件和信息的缺失，我们只能执行部分操作，这是我们执行的操作：{succeed_milestone}.
这就导致执行过程和意图不是很匹配，我希望你能根据已经执行的操作重新总结一下当前操作的意图.
输出格式：子意图为:_______. 
"""}]
    })

    _, content = query_qwen2_vl(messages, verbose=False)
    edge_desc = content.replace("\n", "").replace("：", ":").replace(":", "").strip()
    return edge_desc

def get_template_for_intention(intention_list):
   
    messages = []
    messages.append({
        "role": "system",
        "content": [{'text': 

f"""
以下的内容是所有的意图列表, 帮我将一下item根据功能进行聚类,每个功能能抽象出一个模板：
{intention_list}
每个item：
id： subintention
帮我将意图聚类，对每个类总结出不同的模板
"""
        }]
    })

    messages[-1]["content"][-1]["text"] += \
"""
注意：
需要对相同的意图聚类，抽象出一个template，参数用[]替代，

template: 意图模板
parameter：
{
    id. subintention
}
### 输出格式
您的输出应该遵循以下JSON格式，并确保其可以被Python的`json.loads()`函数解析：
```json
{
   "搜索[]":
   [
        {
            1: 在搜索框中输入“电子医保”
        },
        {
            3. 搜索“交通卡”
        }
    ],
    "购买[]商品":
   [
        {
            7: 购买三国演义书籍
        },
        {
            8. 购买可乐
        }
    ]
}
```
把所有结果都罗列出来
"""
    
    _, content = query_qwen2_vl(messages, verbose=False)
    #template_des = content.replace("\n", "").replace("：", ":").replace(":", "").strip()
    return content

# 获取所有的subintention
def get_all_subintention(intent_list, file_dir, package_name, all_intention_num):
    succeed_intention_num = 0
    intention_dict = {}

    for intent_file in intent_list:
        # try:
        if os.path.exists(f"{intent_file}/history.json"):
            with open(f"{intent_file}/history.json", 'r', encoding='utf-8') as file:
                data = json.load(file) 
                #for item_ in data: 
                ll =  len(data) 
                
                    #print(os.path.basename(intent_file), len(data[1]["trajectory"]))
                for ii in range(1, ll):
                    data_item = data[ii]
                    succeed_intention_num += 1

                    # 主意图
                    intention = os.path.basename(intent_file)

                    milestones_all_list = data[0]["incomplete_milestone"]

                    # 子路径
                    node_list = []
                    action_list = []
                    milestone_list = []
                    for ii, item in enumerate(data_item["trajectory"]):
                        if ii == 0:
                            node_list.append(item)
                        else:
                            node_list.append(item[0])
                            milestone_list.append(item[1])
                            action_list.append(item[-1])
                    
                    subintention = get_summary_for_intention(intention, milestones_all_list, milestone_list)
                    subintention = subintention.split('子意图为')[-1]
                    print(intention, milestones_all_list, milestone_list)
                    print(subintention)
                    intention_dict[succeed_intention_num] = {
                                                "intention": intention,
                                                "milestones_list": milestones_all_list,
                                                "succeed_milestone_list": milestone_list,
                                                "subintention": subintention,
                                                "node_list": node_list,
                                                "action_list": action_list}

    print(f"The percentage of succeed intention: {succeed_intention_num}/{all_intention_num}")
    with open(f"{file_dir}/{package_name}_subintention.json", 'w', encoding='utf-8') as file:
        json.dump(intention_dict, file, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    package_list = [
                    #  'com.ctrip.harmonynext',
                    #  'com.netease.cloudmusic.hm',
                    #  'com.sina.weibo.stage',
                    #'com.vip.hosapp'
                    'com.dragon.read.next',
                    'com.tencent.hm.qqmusic'
    ]
    
    # package_name = "com.sankuai.hmeituan"
    for package_name in package_list:
        file_dir= f"/home/app_agent/RAGGeneration_New/data/oracle_test_app_second_stage/{package_name}/graph/"
            
        intent_list = glob(f"{file_dir}/intention_path/*")
        all_intention_num = len(intent_list)
        
        get_all_subintention(intent_list, file_dir, package_name, all_intention_num)
