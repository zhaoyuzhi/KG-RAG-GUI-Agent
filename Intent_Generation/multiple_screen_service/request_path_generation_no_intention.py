import requests
import json

def load_json(src_=None):
    with open(src_, 'r', encoding='utf-8') as f:
        data_ = json.load(f)
    f.close()
    return data_

def get_path_result(graph_id, kg_data, use_extend_random_path=False, use_detour_extend_random_path=False,
                    use_inpage_extend_random_path=False, use_loop_extend_random_path=False, num_random_path=20, len_random_path=2,
                    url="http://10.247.162.249:5005/sim_decision_maker"):
    """
    :param graph_id: 图谱唯一id，用于日志存储，可自行定义
    :param kg_data: 图谱数据
    :param use_extend_random_path: 是否开启路径延长策略
    :param use_detour_extend_random_path: 是否开启绕路延长策略
    :param use_inpage_extend_random_path: 是否开启页面内延长策略
    :param use_loop_extend_random_path: 是否开启环路延长策略
    :param num_random_path: 生成的路径最大数量
    :param len_random_path: 生成的路径最短长度
    """
    payload = {"appId": graph_id, "graphId": graph_id, "kgData": kg_data, "promptTargetList": [],
               "homeNodeList": ["A23BBEFCFD921AD3FE11000FEC7164F6"],
               "numRandomPath": num_random_path, "lenRandomPath": len_random_path,
               "use_extend_random_path": use_extend_random_path, "use_detour_extend_random_path": use_detour_extend_random_path,
               "use_inpage_extend_random_path": use_inpage_extend_random_path, "use_loop_extend_random_path": use_loop_extend_random_path
               }
    response = requests.request("POST", url, json=payload)
    print(response.text)


if __name__ == "__main__":
    graph_id = 710
    json_path = f'/home/project/SimDecision_no_baseline/data_sim_decision/{graph_id}/cur_data_{graph_id}.json'
    kg_data = load_json(src_=json_path)
    kg_data = json.dumps(kg_data)
    get_path_result(graph_id, kg_data, use_extend_random_path=False)