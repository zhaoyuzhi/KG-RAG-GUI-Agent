import os
import json

import sys
current_path = os.getcwd()  
print(f"current_path:{current_path}")
sys.path.append(current_path)

from utils import load_jsonl_as_dict, load_json, save_json

def build_graph(edge_connections, node_desc, edge_desc):
    graph = {}

    for node_id, desc in node_desc.items():
        graph[node_id] = {
            'desc': desc['overall'],
            'full_desc': desc,
            'to': {}  # To store outgoing edges
        }

    # Add edges and their descriptions based on connections
    for edge_id, connection in edge_connections.items():
        try:
            from_node = connection['from']
            to_node = connection['to']

            # Ensure from_node exists in the graph
            if from_node not in graph:
                continue

            # Ensure outgoing edge structure exists for from_node
            if to_node not in graph[from_node]['to']:
                graph[from_node]['to'][to_node] = {}

            graph[from_node]['to'][to_node][edge_id] = edge_desc[edge_id]#["summary"]
        except:
            continue

    return graph

if __name__ == "__main__":
    # package_names = ['com.alipay.mobile.client','com.qiyi.video.hmy', 'com.sankuai.hmeituan', 'com.ss.hm.ugc.aweme']
    # package_names = ['com.jd.hm.mall', 'com.ss.hm.article.news' ,'com.kugou.hmmusic']
    # package_names = ['com.kugou.hmmusic'] #'com.kugou.hmmusic',
    # extra_path_prefix = "edge_des_new"
    package_names = ['com.ctrip.harmonynext', 'com.dragon.read.next', 'com.netease.cloudmusic.hm', 'com.tencent.hm.qqmusic', 'com.sina.weibo.stage', 'com.vip.hosapp']
    #package_names = ['com.gotokeep.keep'] #['com.alipay.mobile.client']
    graph_dir = "/home/app_agent/RAGGeneration_New/data/oracle_test_app_second_stage/"
    for package_name in package_names:
        path_prefix = os.path.join(graph_dir, package_name, 'graph')
   
        node_desc = load_json(os.path.join(path_prefix, 'node_desc.json'))
        # vut_edge_desc = load_jsonl_as_dict(os.path.join(path_prefix, 'vut_desc.jsonl'))
        # print(len(vut_edge_desc))
        edge_desc = load_jsonl_as_dict(os.path.join(path_prefix, 'edge_desc.jsonl'))
        print(len(edge_desc))
        # edge_desc_ping = load_json(os.path.join(extra_path_prefix,'%s_edge_des_final_ex_unlimited.json'%package_name)) #'%s_edge_des_final_ex_unlimited.json'%package_name)
        # print(len(edge_desc_ping)) #"com.alipay.mobile.client_edge_des_final_ex_unlimited.json"
        # edge_desc_ping_new = {key:value for key,value in edge_desc_ping.items() if value["summary"]!=""}
        # print(len(edge_desc_ping_new))
        edge_connections = load_json(os.path.join(path_prefix, 'edges.json'))  # Contains edge connections between nodes

        graph = build_graph(edge_connections, node_desc, edge_desc)
        save_json(graph, os.path.join(path_prefix, 'reformatted_utg_vut.json'))
