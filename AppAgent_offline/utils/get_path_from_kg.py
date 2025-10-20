from utils.basic_utils import load_json
from collections import defaultdict

ACTION_TYPE_MAP = {
    "CLICK": "点击",
    "SWIPE": "滑动",
    "EDIT": "输入",
    "CHECKABLE": "勾选"
}

def remove_rt_desp(widget_desp):
    if not widget_desp:
        return
    if "\r" in widget_desp:
        widget_desp.replace("\r", "")
    if "\t" in widget_desp:
        widget_desp.replace("\t", "")
    widget_desp_filtered = widget_desp.strip()
    return widget_desp_filtered

def get_widget_id_desp_map(data_nodes):
    """
    获取widget_id和控件描述的对应关系
    """
    widget_id_desp_map = {}
    for scene_id, info in data_nodes.items():
        specific_id_data = info["exactScenes"][0]
        for widget_id, widget_info in specific_id_data["widgetList"].items():
            if widget_id in widget_id_desp_map.keys():
                continue
            if "widgetDescription" not in widget_info:
                continue
            if widget_info["widgetDescription"] and "未知" not in widget_info["widgetDescription"] and \
                    "其它" not in widget_info["widgetDescription"]:
                widget_id_desp_map[widget_id] = remove_rt_desp(widget_info["widgetDescription"])
    return widget_id_desp_map

def get_action_command_map(data_nodes, widget_id_desp_map):
    """
    获取action_id和操作名称的对应关系
    """
    action_command_map = {}
    for scene_id, info in data_nodes.items():
        specific_id_data = info["exactScenes"][0]
        for item in specific_id_data["sceneActionList"]:
            action_id = item["actionId"]
            for list_item in item["actionList"][::-1]:
                if list_item["widgetId"] not in widget_id_desp_map:
                    continue
                widget_desp = widget_id_desp_map[list_item["widgetId"]]
                action_type = list_item["action"]
                if action_type == "EDIT":
                    try:
                        content = list_item["content"]
                    except:
                        content = ""
                    command = f"在{widget_desp.strip()}中{ACTION_TYPE_MAP[action_type]}{content}"
                else:
                    if action_type in ACTION_TYPE_MAP:
                        command = ACTION_TYPE_MAP[action_type] + widget_desp
                if command:
                    action_command_map[action_id] = command
                break
    return action_command_map

def get_relation_graph_from_edges(edges_list, action_command_map):
    """
    获得所有页面的带有操作名称的关系图
    relation_graph:
    {
    scene_id1:[{"actionList":["点击推荐按钮"], "to": scene_id2}, {"actionList":["点击我的按钮"], "to": scene_id8}]
    scene_id5:[...]
    }
    """
    relation_graph = {}
    for items in edges_list:
        sub_action_list = []
        for item in items["events"]:
            if item["actionId"] in action_command_map.keys():  # 如果actionId有相应的action_desp，则存储
                command = action_command_map[item["actionId"]]
                if command not in sub_action_list:  # command去重
                    sub_action_list.append(command)
        if sub_action_list:
            if items["from"] not in relation_graph:
                relation_graph[items["from"]] = [{"actionList": sub_action_list, "to": items["to"]}]
            else:
                update = True
                for graph_item in relation_graph[items["from"]]:
                    if items["to"] == graph_item["to"] and sub_action_list == graph_item["actionList"]:
                        update = False
                if update:
                    relation_graph[items["from"]].append({"actionList": sub_action_list, "to": items["to"]})
    return relation_graph

def get_new_relation_graph_from_edges(edges_list, action_command_map):
    """
    获得所有页面的带有操作名称的关系图
    relation_graph:
    {
    scene_id1:[{"actionId":01854CB306B0F72D5F35A4E38674742F, "actiondesp":"点击推荐按钮", "to": scene_id2},...]
    scene_id2:[...]
    }
    """
    relation_graph = defaultdict(list)
    for items in edges_list:
        for item in items["events"]:
            if item["actionId"] in action_command_map.keys():
                actionDesp  = action_command_map[item["actionId"]]
                relation_graph[items["from"]].append({"actionId": item["actionId"], "actionDesp": actionDesp, "to": items["to"]})
        #     if item["actionId"] in action_command_map.keys():  # 如果actionId有相应的action_desp，则存储
        #         command = action_command_map[item["actionId"]]
        #         if command not in sub_action_list:  # command去重
        #             sub_action_list.append(command)
        # if sub_action_list:
        #     if items["from"] not in relation_graph:
        #         relation_graph[items["from"]] = [{"actionList": sub_action_list, "to": items["to"]}]
        #     else:
        #         update = True
        #         for graph_item in relation_graph[items["from"]]:
        #             if items["to"] == graph_item["to"] and sub_action_list == graph_item["actionList"]:
        #                 update = False
        #         if update:
        #             relation_graph[items["from"]].append({"actionList": sub_action_list, "to": items["to"]})
    return relation_graph

def get_relation_graph_for_shortestpath(relation_graph):
    """
    获取bfs算法需求的关系图格式
    """
    relation_graph_for_shortest_path = {}
    for scene_id, item in relation_graph.items():
        to_list = []
        for list_item in item:
            if list_item["to"] not in to_list:
                to_list.append(list_item["to"])
        if scene_id not in relation_graph_for_shortest_path.keys():
            relation_graph_for_shortest_path[scene_id] = to_list
        else:
            relation_graph_for_shortest_path[scene_id].extend(to_list)
        for node in to_list:
            if node not in relation_graph_for_shortest_path.keys():
                relation_graph_for_shortest_path[node] = []
    return relation_graph_for_shortest_path

def convert_path_to_command(path_list, relation_graph):
    """
    获得path_list对应的command_list
    """
    command_list = []
    for i in range(len(path_list) - 1):
        from_id = path_list[i]
        to_id = path_list[i + 1]
        if from_id in relation_graph.keys():
            all_list = relation_graph[from_id]
            for item in all_list:
                if to_id == item["to"]:
                    command = item["actionList"][0]
                    command_list.append(command)
    return command_list

def get_path_ui_desp(path_list, data_nodes):
    ui_desp_list = []
    for path_item in path_list:
        for scene_id, info in data_nodes.items():
            if scene_id != path_item:
                continue
            specific_id_data = info["exactScenes"][0]
            ui_desp = specific_id_data["uiDescription"]
            ui_desp_list.append(ui_desp)
    return ui_desp_list


def get_path_jpeg_xml_name(data_nodes, path_list):
    """
    获取path对应的jpeg、xml名称
    """
    jpeg_list = []
    layout_list = []
    for node in path_list:
        for sid, info in data_nodes.items():
            if node != sid:
                continue
            img = info['exactScenes'][0]['img']
            layout = info['exactScenes'][0]['layout']
            jpeg_list.append(img)
            layout_list.append(layout)
    return jpeg_list, layout_list

def bfs(graph, start, end, except_scene_id_list=[]):
    path = []
    queue = []
    queue.append(start)
    seen = set()
    parent = {}
    parent[start] = None
    while queue:
        cur_node = queue.pop(0)
        if cur_node not in seen and cur_node not in except_scene_id_list:
            if cur_node != end:
                if cur_node not in graph:
                    continue
                neighbor_nodes = graph[cur_node]
                for node in neighbor_nodes:
                    queue.append(node)
                    if node not in parent.keys():
                        parent[node] = cur_node
                seen.add(cur_node)
            else:
                while end:
                    path.append(end)
                    end = parent[end]
                path.reverse()
                return path
    return None

def get_random_path(relation_graph_for_shortestpath, start_point=None, end_point=None):
    nodes_num_edges_dict = {}
    all_path_list = []
    for node, out_edges in relation_graph_for_shortestpath.items():
        nodes_num_edges_dict[node] = len(out_edges)
    sorted_nodes_num_edges_list = sorted(nodes_num_edges_dict.items(), key=lambda k: k[1], reverse=True)
    # 如果没有指定起始点，用出度最多的点当起始点
    if not start_point:
        start_point = sorted_nodes_num_edges_list[0][0]
        print(f"start_point:{start_point}")
    # 如果没有指定终点，获得起始点到所有节点的最短路径
    if not end_point:
        for end_node in sorted_nodes_num_edges_list[::-1]:
            end_node = end_node[0]
            cur_path = bfs(relation_graph_for_shortestpath, start_point, end_node)
            if cur_path:
                all_path_list.append(cur_path)
    # 如果指定了起始点和终点，输出最短路径
    elif start_point and end_point:
        cur_path = bfs(relation_graph_for_shortestpath, start_point, end_point)
        if cur_path:
            all_path_list.append(cur_path)
    return all_path_list

def get_path_info(kg_json_path, start_point=None, end_point=None):
    dist_data = load_json(kg_json_path)
    """获取widget_id和控件描述的对应关系"""
    widget_id_desp_map = get_widget_id_desp_map(dist_data["nodes"])
    """获取action_id和操作名称的对应关系"""
    action_command_map = get_action_command_map(dist_data["nodes"], widget_id_desp_map)
    """
        获得所有页面的带有操作名称的关系图
        relation_graph:
        {
        scene_id1:[{"actionList":["点击推荐按钮"], "to": scene_id2}, {"actionList":["点击我的按钮"], "to": scene_id8}]
        scene_id5:[...]
        }
    """
    relation_graph = get_relation_graph_from_edges(dist_data["edges"], action_command_map)
    """not dive into the details"""
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

if __name__ == "__main__":
    # 加载图谱json
    dist_data_path = "dist/static/com.android.mediacenter.json"
    dist_data = load_json(dist_data_path)
    widget_id_desp_map = get_widget_id_desp_map(dist_data["nodes"])

    action_command_map = get_action_command_map(dist_data["nodes"], widget_id_desp_map)
    relation_graph = get_relation_graph_from_edges(dist_data["edges"], action_command_map)
    relation_graph_for_shortestpath = get_relation_graph_for_shortestpath(relation_graph)

    # 获取从起始点开始到所有节点的路径
    all_path_list = get_random_path(relation_graph_for_shortestpath,start_point="804D8228CEADDFAAD8A9FFDCC2A599D4")
    # ,start_point="804D8228CEADDFAAD8A9FFDCC2A599D4"
    #eid start_point="27919883ACAF85908D8B1726FBE7831F",end_point="B8EBB7D02CB088A01AE99584F32CC287"
    # all_path_list = get_random_path(relation_graph_for_shortestpath, start_point="98F0C598C9001222235B035B3BE81E7B", end_point="22D3423AD2673049B0356E043B2ED623")
    print(f"生成{len(all_path_list)}条路径")

    # 获取所有路径对应的图片名称、xml名称、操作序列
    all_jpeg_list = []
    all_layout_list = []
    all_command_list = []
    for path_list in all_path_list:
        jpeg_list, layout_list = get_path_jpeg_xml_name(dist_data["nodes"], path_list)
        all_jpeg_list.append(jpeg_list)
        all_layout_list.append(layout_list)

        command_list = convert_path_to_command(path_list, relation_graph)
        all_command_list.append(command_list)

    print(all_jpeg_list[0])
    print(all_path_list[0])
    print(all_command_list[0])
