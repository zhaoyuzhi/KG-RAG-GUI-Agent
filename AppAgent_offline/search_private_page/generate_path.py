from utils.get_path_from_kg import get_widget_id_desp_map,get_action_command_map,get_relation_graph_from_edges,get_relation_graph_for_shortestpath
from utils.get_path_from_kg import get_random_path,get_action_command_map,get_path_jpeg_xml_name,get_new_relation_graph_from_edges,convert_path_to_action
from utils.basic_utils import load_json,save_jsonl
from utils.draw import plot_image_flow,plot_image_flow_old
import os

#"group-o-587e01af828a4b71932444596ba2734f.jpeg",
package2end ={
# "com.hexin.plat.android":["group-o-5f43d74f2a18440fb51d31d65f5c198a.jpeg",
#                           "group-o-706ae46cb79746c6b4e6f5381cf6634c.jpeg"],
# "com.gotokeep.keep":["group-o-80b1c8f5a4324cdbb72549f83802b74f.jpeg"],
# "com.ss.android.article.news":["group-o-32f7c0114e9946a7ac56680ea34348ad.jpeg",
#                                "group-o-698d86a382a947c095cc2dfbb98d024b.jpeg",
#                                "group-o-8d4211d820764912a931c9f4cfda5235.jpeg"],
"com.feeyo.variflight":["554CBD9B7A96B112731548E62357F104.jpeg","33AA5FAE6FC942E5EC827733889A7DF5.jpeg","3474F0863339B83F8FC85524F436065D.jpeg","D1321CA72AB53813F3B98FE06C10B593.jpeg"],
"com.xingin.xhs_hos":["C0B5AA358176A0E61592442343BB2302.jpeg"],
"com.ximalaya.ting.xmharmony":["05AB88FB98453F3A811B785145662131.jpeg","D48D4E4D93BCA099111F24B5341FFEF8.jpeg","DB8F96A44A57DDBB323C2621B7C8034C.jpeg"],
"com.ximalaya.ting.xmharmony.":["C0B5AA358176A0E61592442343BB2302.jpeg"]
}

package2abbr ={
"com.feeyo.variflight":"variflight",
"com.hexin.plat.android":"tonghuashun",
"com.gotokeep.keep":"keep",
"com.ss.android.article.news":"toutiao",
"com.xingin.xhs_hos":"xhs",
"com.ximalaya.ting.xmharmony":"ximalaya",
"com.taobao.taobao4hmos":"taobao",
}

package2abbr_zh ={
"com.hexin.plat.android":"同花顺",
"com.gotokeep.keep":"keep",
"com.ss.android.article.news":"今日头条",
"com.xingin.xhs_hos":"小红书",
"com.ximalaya.ting.xmharmony":"喜玛拉雅",
"com.taobao.taobao4hmos":"淘宝",
"com.feeyo.variflight":"飞常准",
}


if __name__ == "__main__":

    # 加载图谱json
    package = "com.feeyo.variflight"#"com.ximalaya.ting.xmharmony"#"com.gotokeep.keep"#"com.ss.android.article.news" #com.hexin.plat.android
    #end_node = "D0B7114140F90AD861E6361B5900F7B5"
    end_point_img_list = package2end[package]
    #["group-o-5f43d74f2a18440fb51d31d65f5c198a.jpeg","group-o-706ae46cb79746c6b4e6f5381cf6634c.jpeg"]

    #root = os.path.join(package, "dist", "static")
    root = os.path.join("graph_data",package)
    screen_path = os.path.join(root, "screenshot")
    dist_data_path = os.path.join(root, "%s.json"%package)

    dist_data = load_json(dist_data_path)
    widget_id_desp_map = get_widget_id_desp_map(dist_data["nodes"])

    action_command_map = get_action_command_map(dist_data["nodes"], widget_id_desp_map)
    relation_graph = get_relation_graph_from_edges(dist_data["edges"], action_command_map)
    new_relation_graph = get_new_relation_graph_from_edges(dist_data["edges"], action_command_map)
    relation_graph_for_shortestpath = get_relation_graph_for_shortestpath(relation_graph)

    start_node_list = []
    end_node_list = []
    for sid, node in dist_data["nodes"].items():
        if node["exactScenes"][0]["home"]:
            start_node_list.append(sid)
        if node["exactScenes"][0]["img"] in end_point_img_list:
            end_node_list.append(sid)
    abbr_package = package2abbr[package]
    abbr_zh_package = package2abbr_zh[package]
    print("start_node_list: ",start_node_list)
    print("end_node_list: ", end_node_list)
    idx = 0
    intent_sequence_list = []
    for start_node in start_node_list:
        for end_node in end_node_list:
            print(f"start_node:{start_node}, end_node:{end_node}")
            # 获取从起始点开始到所有节点的路径
            all_path_list = get_random_path(relation_graph_for_shortestpath,start_point=start_node,end_point=end_node)
            # ,start_point="804D8228CEADDFAAD8A9FFDCC2A599D4"
            #eid start_point="27919883ACAF85908D8B1726FBE7831F",end_point="B8EBB7D02CB088A01AE99584F32CC287"
            # all_path_list = get_random_path(relation_graph_for_shortestpath, start_point="98F0C598C9001222235B035B3BE81E7B", end_point="22D3423AD2673049B0356E043B2ED623")
            print(f"生成{len(all_path_list)}条路径")
            if len(all_path_list) == 0:
                continue
            #获取所有路径对应的图片名称、xml名称、操作序列
            all_jpeg_list = []
            all_layout_list = []
            all_command_list = []
            all_actionid_list = []
            for path_list in all_path_list:
                jpeg_list, layout_list = get_path_jpeg_xml_name(dist_data["nodes"], path_list)
                all_jpeg_list.append(jpeg_list)
                all_layout_list.append(layout_list)
                command_list, actionid_list = convert_path_to_action(path_list, new_relation_graph)
                #command_list = convert_path_to_command(path_list, relation_graph)
                all_command_list.append(command_list)
                all_actionid_list.append(actionid_list)

            # print(all_jpeg_list[0])
            # print(all_path_list[0])
            # print(all_command_list[0])
            # print(all_command_list[0])

            # save trace
            sid_trace = all_path_list[0]
            # selected_rows = observer_agent.df[observer_agent.df['sid'].isin(sid_trace)]
            # sid_to_img = dict(zip(selected_rows['sid'], selected_rows['img']))
            img_filenames = all_jpeg_list[0]
            img_trace = [os.path.join(root, 'screenshot', filename) for filename in img_filenames]
            #pre_bounding_boxes_list = [edge_dicts[item["actionId"]]["bboxes"] for item in action_trace]
            # plot_image_flow_old(img_trace, all_command_list[0],
            #                 os.path.join(root, 'trace_start_with_%s_end_with_%s.png'%(start_node,end_node)))
            temp_dict = {"id": "%s%02d"%(abbr_package,idx),
                     "intent": "查看并浏览%sapp的隐私政策"%(abbr_zh_package),
                     "NodeList": sid_trace,
                     "sceneIdList": all_jpeg_list[0],
                     "actionIdList": all_actionid_list[0],
                     "commandList": all_command_list[0],
                     "package": package}
            intent_sequence_list.append(temp_dict)
            idx+=1
    save_jsonl(intent_sequence_list, os.path.join(root,"intent_sequence_list.jsonl"))