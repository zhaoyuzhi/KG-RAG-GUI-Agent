import os
import json
import time

import dashscope
from dashscope import MultiModalConversation
from parseXML import parse, hierarchy_parse
from get_path_from_kg import *
import shutil

dashscope.api_key = "sk-......"

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

def reformat_layout(xml_path):
    xml = open(xml_path, 'r', encoding="utf8").read()
    parsed_xml = parse(xml)
    formatted_xml = hierarchy_parse(parsed_xml)
    # formatted_xml_path = xml_path.replace('.xml', '_formatted.xml')
    formatted_xml_path = 'a.xml'
    open(formatted_xml_path, 'w', encoding="utf8").write(formatted_xml)
    return formatted_xml

def chat_with_mllm(user_text, user_image_path, system_text="", model="qwen-vl-max"):
    messages = [
        {
            'role': 'system',
            'content': [
                {
                    'text': system_text
                }
            ]
        },
        {
            'role': 'user',
            'content': [
                {
                    'image': user_image_path
                },
                {
                    'text': user_text
                },
            ]
        }
    ]
    for _ in range(3):
        response = MultiModalConversation.call(model=model, messages=messages)
        if response:
            if "choices" in response:
                break
        time.sleep(5)
    return response['output']['choices'][0]['message']['content'][0]['text']

def chat_with_llm(user_text, system_text="", model="qwen2-72b-instruct"):
    messages = [
        {
            'role': 'system',
            'content': [
                {
                    'text': system_text
                }
            ]
        },
        {
            'role': 'user',
            'content': [
                {
                    'text': user_text
                },
            ]
        }
    ]

    for _ in range(3):
        response = dashscope.Generation.call(
            model,
            messages=messages,
            result_format='message',
            top_k=1
        )
        if response:
            if "choices" in response:
                break
    return response['output']['choices'][0]['message']['content']

def get_path_info(dist_data_path, start_point=None, end_point=None):
    dist_data = load_json(dist_data_path)
    widget_id_desp_map = get_widget_id_desp_map(dist_data["nodes"])
    action_command_map = get_action_command_map(dist_data["nodes"], widget_id_desp_map)
    relation_graph = get_relation_graph_from_edges(dist_data["edges"], action_command_map)
    relation_graph_for_shortestpath = get_relation_graph_for_shortestpath(relation_graph)

    all_path_list = get_random_path(relation_graph_for_shortestpath, start_point, end_point)
    all_jpeg_list = []
    all_layout_list = []
    all_command_list = []
    all_ui_desp_list = []

    for path_list in all_path_list:
        jpeg_list, layout_list = get_path_jpeg_xml_name(dist_data["nodes"], path_list)
        command_list = convert_path_to_command(path_list, relation_graph)
        ui_desp_list = get_path_ui_desp(path_list, dist_data["nodes"])
        all_jpeg_list.append(jpeg_list)
        all_layout_list.append(layout_list)
        all_command_list.append(command_list)
        all_ui_desp_list.append(ui_desp_list)

    return all_path_list, all_command_list, all_jpeg_list, all_layout_list, all_ui_desp_list


if __name__ == '__main__':
    dist_data_path = "/home/code/intention_generation/4khd/graph_data/番茄小说/番茄小说.json"

    # 获取路径相关信息
    # 如果不传递start_point和end_point，获取的是从出度最多的节点到所有其他节点的路径
    all_path_list, all_command_list, all_jpeg_list, all_layout_list, all_ui_desp_list = \
        get_path_info(dist_data_path, start_point="2490BBBB6578CFE0833F1B54A838D6D0", end_point="22D3423AD2673049B0356E043B2ED623")

    # 只生成一条路径时index为0，生成多条时选择相应下标
    index = 0
    jpeg_list = all_jpeg_list[index]
    layout_list = all_layout_list[index]
    command_list = all_command_list[index]
    path_list = all_path_list[index]
    ui_desp_list = all_ui_desp_list[index]
    print(command_list)
    print(ui_desp_list)
    num_graph = len(command_list) + 1

    # 获取当前路径的action_sequence
    action_sequence = ""
    for index, ui_desp_item in enumerate(ui_desp_list):
        if index < len(command_list):
            action_sequence += f"{index + 1}、在{ui_desp_item}中{command_list[index]}"
        # else:
        #     action_sequence += f"{index + 1}、最终抵达{ui_desp_item}"
    print(action_sequence)

    # 请求prompt
    system_text = '您是一名人工智能助手，负责帮助视觉障碍用户与手机应用程序进行交互并导航以完成特定任务。'
    multi_graph_prompt = f"例子：\n" \
                         f"截图序列：首页，推荐频道页面，新闻详情页，评论页面" \
                         f"操作序列：在首页点击“推荐”按钮，在推荐频道页面点击进入详情页，在新闻详情页”点击“评论”按钮\n" \
                         f"测试意图：在首页进入推荐频道，查看一篇新闻详情，在新闻详情页发表评论\n" \
                         f"你会得到连续的{num_graph}张的截图跳转的操作序列\n" \
                         f"截图序列：{ui_desp_list}" \
                         f"操作序列：{action_sequence} \n" \
                         f"请根据以下格式输出" \
                         f"<测试意图>：请根据例子，用最简短的祈使句总结一条顺序正确的测试意图，只输出测试意图"

    intention = chat_with_llm(system_text, multi_graph_prompt)
    print(intention)
