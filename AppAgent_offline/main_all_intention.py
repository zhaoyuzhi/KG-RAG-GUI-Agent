import hydra
import os
from utils.basic_utils import load_json, load_jsonl, save_json
from easydict import EasyDict as edict
from utils.draw import color_log, plot_image_flow
from agents import Decision, Progress, IntentAgent
import time
import logging
import pandas as pd
import requests
import json

def request_graph_search_server(intent, milestones, graph, start_node, accept_threshold, step_size, max_depth,
                                topk, max_batch_size):
    try:
        url = "http://10.90.86.76:5125/graph_search"
        payload = {"intent": intent, "milestones": milestones, "graph": graph, "start_node": start_node,
                   "accept_threshold": accept_threshold, "step_size": step_size, "max_depth": max_depth, "topk": topk,
                   "max_batch_size": max_batch_size}
        headers = {
            'Content-Type': 'application/json'
        }
        response = requests.request("POST", url, headers=headers, data=json.dumps(payload))
    except requests.exceptions.RequestException as e:
        print(f"捕捉异常:{e}")
    return response.json()

@hydra.main(version_base=None, config_path='configs', config_name='configs')
def main(configs):
    logger = logging.getLogger('colored_logger')

    # CONFIGURATION
    configs = edict(configs)
    #data_dir = configs.data_dir
    log_dir = configs.log_dir
    #exp_configs = configs.exp_configs
    #package_name = "com.ctrip.harmonynext"

    for package_name in ["com.tencent.hm.qqmusic", "com.dragon.read.next", "com.netease.cloudmusic.hm", "com.sina.weibo.stage", "com.vip.hosapp"]:
    #for package_name in ["com.vip.hosapp"]:
        # D:\Appagent\RAGGeneration_New\data\oracle_test_app_second_stage\com.ctrip.harmonynext\graph\com.ctrip.harmonynext_intent.json
        json_path = f"/home/app_agent/RAGGeneration_New/data/oracle_test_app_second_stage/{package_name}/graph/{package_name}_intent.json"
        print(json_path)
        with open(json_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        #intention_list = []
        for key, intentions in data.items():
            print(key, intentions)
            for intent in intentions:
                print(intent, '====')
                if package_name == "com.ctrip.harmonynext":
                    start_node = "3198487835ECC4F7A4F0A71A4B3C2B26" 
                elif package_name == 'com.netease.cloudmusic.hm':
                    start_node = "DFB579022A71DBC6EF156617506156BC"
                elif package_name == 'com.sina.weibo.stage':
                    start_node = "B7EAA640775C1F8DF49E924D709B8240"
                elif package_name == 'com.vip.hosapp':
                    start_node = "2E61A7175054BAD131EDE3D1141AF3A1"
                elif package_name == 'com.dragon.read.next':
                    start_node = "2F5BBD43C78B3C627AD3133515D0284D"
                elif package_name == "com.tencent.hm.qqmusic":
                    start_node = "89EB0BC915B74D0FDA29E9EAA66F450C"
                
                if not os.path.exists(log_dir):
                    os.makedirs(log_dir)

                graph_dir = "/home/pp/app_agent/RAGGeneration_New/data/oracle_test_app_second_stage/"
                path_prefix = os.path.join(graph_dir, package_name, 'graph')

                save_path = os.path.join(graph_dir, package_name, 'graph', 'intention_path', intent)
                os.makedirs(save_path, exist_ok=True)

                
                if os.path.exists(os.path.join(save_path, 'trace_predict.json')):
                    print(os.path.join(save_path, 'trace_predict.json'), '---------')
                    continue
                
                graph = load_json(os.path.join(path_prefix, 'reformatted_utg_vut.json'))
                metadata_df = pd.read_csv(os.path.join(path_prefix, 'metadata.csv'), names=['node_id', 'img_filename', 'layout_filename'])

                # intent_sequence_list = load_jsonl(os.path.join(path_prefix, 'intent_sequence_pair.jsonl'))
                # start_node = metadata_df[metadata_df['img_filename'] == intent_sequence_list[0]['sceneIdList'][0] + '.jpeg'][
                #     'node_id'].to_list()[0]
                node2img = metadata_df.set_index('node_id')['img_filename'].to_dict()
                # img2node = metadata_df.set_index('img_filename')['node_id'].to_dict()

                # plot GT trace
                hydra_cfg = hydra.core.hydra_config.HydraConfig.get()

                edge_dicts = load_json(os.path.join(path_prefix, 'edges.json'))
                
                #progress_agent = Progress(logger)
                decision_agent = Decision(logger)
                intent_rewriter = IntentAgent(logger)

                # MAIN LOOP
                max_n_trials = configs.max_n_trials
                max_n_steps = configs.max_n_steps
                color_log(f"任务意图: {intent}", logger, color='cyan')

                total_decision_time = 0.
                total_reflection_time = 0.
                total_bfs_search_time = 0.
                total_step = 0

                # WORKING MEMORY
                history = list()

                # Intent Rewrite
                intent, milestones = intent_rewriter(intent)

                total_timer_start = time.time()
                step = 0
                color_log(f"exploring start sid: {start_node}", logger, color='cyan')
                current_node = start_node
                trial_timer_start = time.time()

                while True:
                    step += 1

                    if step > max_n_steps:
                        color_log("Ending Task...", logger, color='cyan')
                        color_log(
                            "Reach the maximum path length. Fail to generate a path with start node %s" % start_node,
                            logger, color='red')
                        break

                    color_log(f" Step: {step}/{max_n_steps}", logger, color='cyan')
                    color_log(f"Current sid: {current_node}", logger)

                    if not len(graph[current_node]["to"]):
                        color_log("Ending Task...", logger, color='cyan')
                        color_log(
                            "Enter the node with no outward edge. ",logger, color='red')
                        break

                    step_timer_start = time.time()
                    total_step += 1

                    if step == 1:
                        history.append({
                            'node': None,
                            'trajectory':None,
                            "thought": None,
                            "matched_milestone": [],
                            "incomplete_milestone": milestones,
                            'next_node': current_node,
                        })
                        history_log_sid_list = [start_node]
                        action_trace = []

                        # save trace
                        sid_trace = [sid for sid in history_log_sid_list]
                        img_filenames = [node2img[sid] for sid in sid_trace if sid in node2img]
                        #img_trace = [os.path.join(path_prefix, 'screenshot', filename) for filename in img_filenames]
                        #pre_bounding_boxes_list = [edge_dicts[item["actionId"]]["bboxes"] for item in action_trace]
                        # plot_image_flow(img_trace, action_trace,
                        #                 os.path.join(hydra_cfg['runtime']['output_dir'], "visualization",
                        #                             'trace_step_%d.png' % 0),
                        #                 bounding_boxes_list=pre_bounding_boxes_list)

                    incomplete_milestone = history[-1]["incomplete_milestone"]
                    progress = None

                    bfs_progress_timer_start = time.time()

                    res = request_graph_search_server(intent, incomplete_milestone, graph, current_node, 1, 1, 3,
                                                    3, 20)

                    bfs_progress_time = time.time() - bfs_progress_timer_start
                    total_bfs_search_time += bfs_progress_time

                    possible_trajectories = res["data"]

                    color_log(f"Step: {step} bfs_progress agent time: {bfs_progress_time}", logger, color='yellow')

                    if possible_trajectories is None:
                        color_log("Ending Task...", logger, color='cyan')
                        color_log("possible_trajectories is None...", logger, color='red')
                        break

                    for possible_trajectory in possible_trajectories:
                        color_log(possible_trajectory, logger)

                    decision_timer_start = time.time()
                    
                    try:
                        thought_actions = decision_agent.get_final_decision(intent, graph, possible_trajectories, current_node, progress, incomplete_milestone)
                        thought = thought_actions['reasoning']
                        final_action_id = thought_actions['final_action_id']
                        completed_milestone_index = thought_actions['completed_milestone_index']
                        completed_milestone_index_list = thought_actions['completed_milestone_index_list']
                        
                    except:
                        thought = ""
                        final_action_id = -1
                        completed_milestone_index = -1
                        completed_milestone_index_list = -1    

                    decision_time = time.time() - decision_timer_start
                    color_log(f"Step: {step} decision agent time: {decision_time}", logger, color='yellow')
                    total_decision_time += decision_time
                    color_log(f" completed_milestone_index: {completed_milestone_index}", logger, color='yellow')

                    if final_action_id == -1 :
                        color_log("Ending Task...", logger, color='cyan')
                        color_log("Decision agent can not find the relevant action trace...", logger, color='red')
                        break

                    matched_milestone = [ incomplete_milestone[i-1] for i in completed_milestone_index_list]
                    updated_incomplete_milestone = [ incomplete_milestone[i] for i in range(completed_milestone_index, len(incomplete_milestone))]
                    color_log(f"matched_milestone: {matched_milestone}", logger, color='cyan')
                    color_log(f"incomplete_milestone: {updated_incomplete_milestone}", logger, color='cyan')

                    # WORKING MEMORY
                    history.append({
                        'node': current_node,
                        'trajectory': possible_trajectories[final_action_id][0],
                        "thought": thought,
                        "matched_milestone": matched_milestone,
                        "incomplete_milestone": updated_incomplete_milestone,
                        'next_node': possible_trajectories[final_action_id][0][-1][0],
                    })

                    history_log_sid_list = [start_node]
                    action_trace = []

                    for his in history[1:]:
                        temp_node_list = [_[0] for _ in his["trajectory"][1:]]
                        history_log_sid_list.extend(temp_node_list)
                        action_trace.extend([{"actionDesp": _[1], "actionId": _[2]} for _ in his["trajectory"][1:]])

                    # save trace
                    sid_trace = [sid for sid in history_log_sid_list]
                    img_filenames = [node2img[sid] for sid in sid_trace if sid in node2img]
                    img_trace = [os.path.join(path_prefix, 'screenshot', filename) for filename in img_filenames]
                    pre_bounding_boxes_list = [edge_dicts[item["actionId"]]["bboxes"] for item in action_trace]

                    if len(updated_incomplete_milestone) == 0:
                        _incomplete_milestone_flag = True
                        color_log("Ending Task...", logger, color='cyan')
                        color_log("Decision agent match all uncompleted milestones...", logger, color='red')
                        break

                    # UPDATE
                    current_node = history[-1]["next_node"]

                    color_log(
                        f" Step: {step}  step time: {time.time() - step_timer_start}",
                        logger, color='yellow')

                history_log_sid_list = [start_node]
                action_desp_trace = []
                action_trace = []

                for his in history[1:]:
                    temp_node_list = [_[0] for _ in his["trajectory"][1:]]
                    history_log_sid_list.extend(temp_node_list)
                    action_desp_trace.extend([_[1] for _ in his["trajectory"][1:]])
                    action_trace.extend([{"actionDesp": _[1], "actionId": _[2]} for _ in his["trajectory"][1:]])

                color_log(f"history_log_sid_list:\n {history_log_sid_list}", logger, color='cyan')
                history_log = "\n".join(
                    [f"{step + 1}: {action_desp}" for step, action_desp in enumerate(action_desp_trace)])
                color_log(f"History:\n {history_log}", logger, color='cyan')
                color_log(
                    f" Trial inference time: {time.time() - trial_timer_start}",
                    logger, color='yellow')

                # save trace
                sid_trace = [sid for sid in history_log_sid_list]
                img_filenames = [node2img[sid] for sid in sid_trace if sid in node2img]
                img_trace = [os.path.join(path_prefix, 'screenshot', filename) for filename in img_filenames]
                pre_bounding_boxes_list = [edge_dicts[item["actionId"]]["bboxes"] for item in action_trace]

                save_json(history, os.path.join(save_path, 'history.json'))

                temp_dict = {
                    "predicted_milestones":milestones,
                    "nodeIdList":history_log_sid_list,
                    "sceneIdList": img_filenames,
                    "action_trace":action_trace,
                    "task_is_completed":1,
                }
                save_json(temp_dict, os.path.join(save_path, 'trace_predict.json'))

                total_inference_time = time.time() - total_timer_start
                color_log(
                    f"total inference time: {total_inference_time}",
                    logger, color='yellow')
                color_log(
                    f"inference time per step: {total_inference_time} / {total_step} = {total_inference_time / total_step}",
                    logger, color='yellow')
                color_log(
                    f"BFS progress search time per step: {total_bfs_search_time} / {total_step} = {total_bfs_search_time / total_step}",
                    logger, color='yellow')
                color_log(
                    f"inference time of decision agent per step: {total_decision_time} / {total_step} = {total_decision_time / total_step}",
                    logger, color='yellow')
                color_log(
                    f"inference time of reflection agent per step: {total_reflection_time} / {total_step} = {total_reflection_time / total_step}",
                    logger, color='yellow')

if __name__ == '__main__':
    main()
    