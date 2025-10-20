import hydra
import os
from utils.basic_utils import load_json, load_jsonl
from dotenv import load_dotenv
from easydict import EasyDict as edict
from utils.draw import color_log, plot_image_flow
from agents import Decision, IntentRewriter, Progress, IntentAgent
import time
import logging
import math
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
    data_dir = configs.data_dir
    log_dir = configs.log_dir
    exp_configs = configs.exp_configs

    app_name = exp_configs.app_name
    package_name = exp_configs.package_name
    intent = exp_configs.intent
    intent_id = exp_configs.id

    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    path_prefix = os.path.join('utgs', package_name)
    # trajectory_dir = os.path.join(path_prefix, 'trajectory')
    # if not os.path.exists(trajectory_dir):
    #     os.makedirs(trajectory_dir)

    graph = load_json(os.path.join(path_prefix, 'reformatted_utg_vut.json'))
    metadata_df = pd.read_csv(os.path.join(path_prefix, 'metadata.csv'),
                              names=['node_id', 'img_filename', 'layout_filename'])
    intent_sequence_list = load_jsonl(os.path.join(path_prefix, 'intent_sequence_pair.jsonl'))
    start_node = metadata_df[metadata_df['img_filename'] == intent_sequence_list[0]['sceneIdList'][0] + '.jpeg'][
        'node_id'].to_list()[0]
    node2img = metadata_df.set_index('node_id')['img_filename'].to_dict()

    # plot GT trace
    hydra_cfg = hydra.core.hydra_config.HydraConfig.get()
    intent_sequence_list = load_jsonl(f'data\\intent_sequence_pair.jsonl')

    edge_dicts = load_json(os.path.join(path_prefix, 'edges.json'))
    intent_sequence_dict = {item["id"]: item for item in intent_sequence_list}

    intent_data = intent_sequence_dict[intent_id]
    gt_img_trace = [os.path.join(path_prefix, 'screenshot', filename + '.jpeg') for filename in
                    intent_data['sceneIdList']]

    gt_action_trace = [{"actionId": actionId, "actionDesp": command} for command, actionId in
                       zip(intent_data['commandList'], intent_data['actionIdList'])]
    gt_bounding_boxes_list = [edge_dicts[actionId]["bboxes"] for actionId in intent_data['actionIdList']]

    plot_image_flow(gt_img_trace, gt_action_trace, os.path.join(hydra_cfg['runtime']['output_dir'], 'trace_gt.png'),
                    bounding_boxes_list=gt_bounding_boxes_list)

    progress_agent = Progress(logger)
    decision_agent = Decision(logger)
    intent_rewriter = IntentAgent(logger)

    # MAIN LOOP
    max_n_trials = configs.max_n_trials
    max_n_steps = configs.max_n_steps
    color_log(f"任务意图: {intent}", logger, color='cyan')

    total_decision_time = 0.
    total_reflection_time = 0.
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
            color_log(
                "Reach the maximum path length. Fail to generate a path with start node %s" % start_node,
                logger, color='red')
            color_log("Ending Task...", logger, color='cyan')
            history_log_sid_list = [start_node]
            action_desp_trace = []
            action_trace = []
            for his in history[1:]:
                history_log_sid_list.extend([_[0] for _ in his["trajectory"][1:]])
                action_desp_trace.extend([_[1] for _ in his["trajectory"][1:]])
                action_trace.extend([{"actionDesp":_[1],"actionId":_[2]} for _ in his["trajectory"][1:]])
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
            plot_image_flow(img_trace, action_trace,
                            os.path.join(hydra_cfg['runtime']['output_dir'], 'trace_predict.png'),
                            bounding_boxes_list=pre_bounding_boxes_list)
            break

        color_log(f" Step: {step}/{max_n_steps}", logger, color='cyan')
        color_log(f"Current sid: {current_node}", logger)

        if not len(graph[current_node]["to"]):
            color_log("Ending Task...", logger, color='cyan')
            history_log_sid_list = [start_node]
            action_desp_trace = []
            action_trace=[]
            for his in history[1:]:
                history_log_sid_list.extend([ _[0] for _ in his["trajectory"][1:]])
                action_desp_trace.extend([ _[1] for _ in his["trajectory"][1:]])
                action_trace.extend([{"actionDesp": _[1], "actionId": _[2]} for _ in his["trajectory"][1:]])
            color_log(f"history_log_sid_list:\n {history_log_sid_list}", logger, color='cyan')
            history_log = "\n".join([f"{step + 1}: { action_desp}" for step,  action_desp in enumerate(action_desp_trace)])
            color_log(f"History:\n {history_log}", logger, color='cyan')
            color_log(
                f" Trial inference time: {time.time() - trial_timer_start}",
                logger, color='yellow')

            # save trace
            sid_trace = [sid for sid in history_log_sid_list]
            img_filenames = [node2img[sid] for sid in sid_trace if sid in node2img]
            img_trace = [os.path.join(path_prefix, 'screenshot', filename) for filename in img_filenames]
            pre_bounding_boxes_list = [edge_dicts[item["actionId"]]["bboxes"] for item in action_trace]
            plot_image_flow(img_trace, action_trace,
                            os.path.join(hydra_cfg['runtime']['output_dir'], 'trace_predict.png'),
                            bounding_boxes_list=pre_bounding_boxes_list)
            break

        step_timer_start = time.time()
        total_step += 1

        if step == 1:
            history.append({
                "last_progress": None,
                'node': None,
                'trajectory':None,
                "thought": None,
                "progress": "尚未开始执行任务",
                "matched_milestone": [],
                "incomplete_milestone": milestones,
                'next_node': current_node,
            })

        incomplete_milestone = history[-1]["incomplete_milestone"]
        progress = history[-1]["progress"]

        bfs_progress_timer_start = time.time()

        res = request_graph_search_server(intent, incomplete_milestone, graph, current_node, 1, 1, 3,
                                          3, 32)
        bfs_progress_time = time.time() - bfs_progress_timer_start

        possible_trajectories = res["data"]

        color_log(f"Step: {step} bfs_progress agent time: {bfs_progress_time}", logger, color='yellow')

        if possible_trajectories is None:
            color_log("possible_trajectories is None...", logger, color='cyan')
            color_log("Ending Task...", logger, color='cyan')
            history_log_sid_list = [start_node]
            action_desp_trace = []
            action_trace = []
            for his in history[1:]:
                history_log_sid_list.extend([_[0] for _ in his["trajectory"][1:]])
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
            plot_image_flow(img_trace, action_trace,
                            os.path.join(hydra_cfg['runtime']['output_dir'], 'trace_predict.png'),
                            bounding_boxes_list=pre_bounding_boxes_list)
            break

        for possible_trajectory in possible_trajectories:
            color_log(possible_trajectory, logger)

        decision_timer_start = time.time()

        thought_actions = decision_agent.get_final_decision(intent, graph, possible_trajectories, current_node,
                                                            progress, incomplete_milestone)

        decision_time = time.time() - decision_timer_start
        color_log(f"Step: {step} decision agent time: {decision_time}", logger, color='yellow')
        total_decision_time += decision_time

        thought = thought_actions['reasoning']
        final_action_id = thought_actions['final_action_id']
        completed_milestone_index = thought_actions['completed_milestone_index']
        color_log(
            f" completed_milestone_index: {completed_milestone_index}",
            logger, color='yellow')


        if final_action_id == -1 :
            color_log("Ending Task...", logger, color='cyan')
            history_log_sid_list = [start_node]
            action_desp_trace = []
            action_trace = []
            for his in history[1:]:
                history_log_sid_list.extend([_[0] for _ in his["trajectory"][1:]])
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
            plot_image_flow(img_trace, action_trace,
                            os.path.join(hydra_cfg['runtime']['output_dir'], 'trace_predict.png'),
                            bounding_boxes_list=pre_bounding_boxes_list)
            break

        # if completed_milestone_index < 0:
        #     matched_milestone = []
        #     incomplete_milestone = incomplete_milestone
        # else:
        #     matched_milestone = incomplete_milestone[:completed_milestone_index],
        #     incomplete_milestone = incomplete_milestone[completed_milestone_index + 1:],
        matched_milestone = [ incomplete_milestone[i] for i in range(completed_milestone_index)]
        updated_incomplete_milestone = [ incomplete_milestone[i] for i in range(completed_milestone_index, len(incomplete_milestone))]
        color_log(f"matched_milestone: {matched_milestone}", logger, color='cyan')
        color_log(f"incomplete_milestone: {updated_incomplete_milestone}", logger, color='cyan')
        #matched_milestone

        # WORKING MEMORY
        history.append({
            "last_progress": progress,
            'node': current_node,
            'trajectory': possible_trajectories[final_action_id][0],
            "thought": thought,
            "matched_milestone": matched_milestone,
            "incomplete_milestone": updated_incomplete_milestone,
            "progress": None,
            'next_node': possible_trajectories[final_action_id][0][-1][0],
        })

        if len(updated_incomplete_milestone) == 0:
            color_log("Ending Task...", logger, color='cyan')
            history_log_sid_list = [start_node]
            action_desp_trace = []
            action_trace = []
            for his in history[1:]:
                history_log_sid_list.extend([_[0] for _ in his["trajectory"][1:]])
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
            plot_image_flow(img_trace, action_trace,
                            os.path.join(hydra_cfg['runtime']['output_dir'], 'trace_predict.png'),
                            bounding_boxes_list=pre_bounding_boxes_list)
            break

        progress_timer_start = time.time()
        feedback = progress_agent(intent, milestones, graph, history)

        progress_time = time.time() - progress_timer_start
        color_log(f"Step: {step} progress agent time: {time.time() - progress_timer_start}", logger, color='yellow')
        total_reflection_time += progress_time

        history[-1]["progress"] = feedback
        # completion_rate = history[-1]["progress"]["completion_rate"]
        # float_number, float_den = completion_rate.split('/')
        # complete_milestone_number, _ = int(float_number), int(float_den)
        # incomplete_milestone = milestones[complete_milestone_number:]

        # UPDATE
        current_node = history[-1]["next_node"]

        color_log(
            f" Step: {step}  step time: {time.time() - step_timer_start}",
            logger, color='yellow')

    total_inference_time = time.time() - total_timer_start
    color_log(
        f"total inference time: {total_inference_time}",
        logger, color='yellow')
    # color_log(
    #     f"inference time per trial: {total_inference_time} / {total_trial} = {total_inference_time/total_trial}",
    #     logger, color='yellow')
    color_log(
        f"inference time per step: {total_inference_time} / {total_step} = {total_inference_time / total_step}",
        logger, color='yellow')
    color_log(
        f"inference time of decision agent per step: {total_decision_time} / {total_step} = {total_decision_time / total_step}",
        logger, color='yellow')
    color_log(
        f"inference time of reflection agent per step: {total_reflection_time} / {total_step} = {total_reflection_time / total_step}",
        logger, color='yellow')

if __name__ == '__main__':
    main()
