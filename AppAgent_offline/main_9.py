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
import tkinter as tk
from utils.draw import plot_image_flow_old2 as plot_image_flow
from PIL import Image, ImageTk, ImageDraw
import shutil

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

def resize_image_to_height(img, max_height):
    height_ratio = max_height / img.height
    new_width = int(img.width * height_ratio)
    new_height = max_height
    return img.resize((new_width, new_height), Image.LANCZOS)


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

    graph_dir = "/home/app_agent/RAGGeneration_New/data/oracle_test_app_second_stage/"
    path_prefix = os.path.join(graph_dir, package_name, 'graph')

    graph = load_json(os.path.join(path_prefix, 'reformatted_utg_vut.json'))
    metadata_df = pd.read_csv(os.path.join(path_prefix, 'metadata.csv'),
                              names=['node_id', 'img_filename', 'layout_filename'])
    # intent_sequence_list = load_jsonl(os.path.join(path_prefix, 'intent_sequence_pair.jsonl'))
    # start_node = metadata_df[metadata_df['img_filename'] == intent_sequence_list[0]['sceneIdList'][0] + '.jpeg'][
    #     'node_id'].to_list()[0]
    node2img = metadata_df.set_index('node_id')['img_filename'].to_dict()
    img2node = metadata_df.set_index('img_filename')['node_id'].to_dict()

    # plot GT trace
    hydra_cfg = hydra.core.hydra_config.HydraConfig.get()
    # os.path.join("search_private_page", "privacy_data_intent_sequence_list.jsonl")
    # f'data\\intent_sequence_pair.jsonl'
    intent_sequence_list = load_jsonl(os.path.join("search_private_page", "privacy_data_intent_sequence_list.jsonl"))#'data\\intent_sequence_pair.jsonl')
    #os.path.join("search_private_page", "privacy_data_intent_sequence_list.jsonl"))

    edge_dicts = load_json(os.path.join(path_prefix, 'edges.json'))
    intent_sequence_dict = {item["id"]: item for item in intent_sequence_list}

    intent_data = intent_sequence_dict[intent_id]
    gt_img_trace = [os.path.join(path_prefix, 'screenshot', filename ) for filename in
                    intent_data['sceneIdList']] #+ ".jpeg"

    gt_action_trace = [{"actionId": actionId, "actionDesp": command} for command, actionId in
                       zip(intent_data['commandList'], intent_data['actionIdList'])]
    gt_bounding_boxes_list = [edge_dicts[actionId]["bboxes"] for actionId in intent_data['actionIdList']]

    plot_image_flow(gt_img_trace, gt_action_trace, os.path.join(hydra_cfg['runtime']['output_dir'], 'trace_gt.png'),
                    bounding_boxes_list=gt_bounding_boxes_list)
    start_node = img2node[os.path.basename(gt_img_trace[0])]

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
    #intent, milestones = intent_rewriter(intent,use_rag=False)
    milestones = ["点击我的/个人中心按钮", "点击设置按钮", "点击隐私政策链接"]
    #milestones = ["点击我的/个人中心按钮","点击设置按钮", "点击隐私政策链接"]
    total_timer_start = time.time()
    step = 0
    color_log(f"exploring start sid: {start_node}", logger, color='cyan')
    current_node = start_node
    trial_timer_start = time.time()

    # Retrieve online images and measure inference time
    #online_images, inference_time = get_online_image_sources()
    visualization_root = os.path.join(hydra_cfg['runtime']['output_dir'], "visualization")
    os.makedirs(visualization_root, exist_ok=True)
    os.makedirs(os.path.join(visualization_root,"step%02d"%0), exist_ok=True)
    start_img_path = node2img[start_node]
    source_file = os.path.join("utgs", package_name, "screenshot", start_img_path)
    #print(source_file)
    cur_step_visualization_path = os.path.join(visualization_root,"step%02d"%0)
    destination_file = os.path.join(cur_step_visualization_path, "img.jpeg")
    shutil.copy2(source_file, destination_file)

    # Start by displaying offline images
    #update_image(0, cur_step_visualization_path)
    images_list =  [os.path.join(cur_step_visualization_path,_) for _ in os.listdir(cur_step_visualization_path)]
    for index in range(len(images_list)):
        img = Image.open(images_list[index])
        image_queue.put(img)

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
            img_trace = [os.path.join(path_prefix, 'screenshot', filename) for filename in img_filenames]
            pre_bounding_boxes_list = [edge_dicts[item["actionId"]]["bboxes"] for item in action_trace]
            plot_image_flow(img_trace, action_trace,
                            os.path.join(hydra_cfg['runtime']['output_dir'], "visualization",
                                         'trace_step_%d.png' % 0),
                            bounding_boxes_list=pre_bounding_boxes_list)

        incomplete_milestone = history[-1]["incomplete_milestone"]
        progress = None

        bfs_progress_timer_start = time.time()

        res = request_graph_search_server(intent, incomplete_milestone, graph, current_node, 1, 1, 3,
                                          3, 32)

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
            color_log("Decision agent can not find the relevant action trace...", logger, color='red')
            break

        os.makedirs(os.path.join(visualization_root, "step%02d"%step), exist_ok=True)

        chosen_trajectory = possible_trajectories[final_action_id][0]

        node_ids = [chosen_trajectory[0]]
        edge_ids = [] #.append(step[1])
        for _ in chosen_trajectory[1:]:
            node_ids.append(_[0])
            edge_ids.append(_[2])
        img_paths = [ node2img[_] for _ in node_ids]
        #action_trace = edge_ids
        gt_bounding_boxes_list = [edge_dicts[item]["bboxes"] for item in edge_ids]
        num_actions = len(edge_ids)
        cur_step_visualization_path = os.path.join(visualization_root, "step%02d" % step)
        for idx, img_path in enumerate(img_paths):
            source_file = os.path.join("utgs", package_name, "screenshot", img_path)
            destination_file = os.path.join(cur_step_visualization_path, "img_%d.jpeg" % idx)
            shutil.copy2(source_file, destination_file)
            img = Image.open(destination_file)
            if idx < num_actions:
                draw = ImageDraw.Draw(img)
                for box in gt_bounding_boxes_list[idx]:
                    draw.rectangle(box, outline="red", width=8)
                img.save(os.path.join(cur_step_visualization_path, "img_%d_acted.jpeg" % idx))

        # destination_file = os.path.join(cur_step_visualization_path, "img.jpeg")
        # shutil.copy2(source_file, destination_file)
        images_list = [os.path.join(cur_step_visualization_path, _) for _ in os.listdir(cur_step_visualization_path)]
        for index in range(len(images_list)):
            img = Image.open(images_list[index])
            image_queue.put(img)

        #update_image(0, cur_step_visualization_path)

        matched_milestone = [incomplete_milestone[i] for i in range(completed_milestone_index)]
        updated_incomplete_milestone = [ incomplete_milestone[i] for i in range(completed_milestone_index, len(incomplete_milestone))]
        color_log(f"matched_milestone: {matched_milestone}", logger, color='cyan')
        color_log(f"incomplete_milestone: {updated_incomplete_milestone}", logger, color='cyan')

        # WORKING MEMORY
        history.append({
            'node': current_node,
            'trajectory': chosen_trajectory,
            "thought": thought,
            "matched_milestone": matched_milestone,
            "incomplete_milestone": updated_incomplete_milestone,
            'next_node': chosen_trajectory[-1][0],
        })

        history_log_sid_list = [start_node]
        action_trace = []

        for his in history[1:]:
            temp_node_list = [_[0] for _ in his["trajectory"][1:]]
            history_log_sid_list.extend(temp_node_list)
            action_trace.extend([{"actionDesp": _[1], "actionId": _[2]} for _ in his["trajectory"][1:]])

        # save trace
        # sid_trace = [sid for sid in history_log_sid_list]
        # img_filenames = [node2img[sid] for sid in sid_trace if sid in node2img]
        # img_trace = [os.path.join(path_prefix, 'screenshot', filename) for filename in img_filenames]
        # pre_bounding_boxes_list = [edge_dicts[item["actionId"]]["bboxes"] for item in action_trace]
        # plot_image_flow(img_trace, action_trace,
        #                 os.path.join(hydra_cfg['runtime']['output_dir'], "visualization",
        #                              'trace_step_%d.png' % total_step),
        #                 bounding_boxes_list=pre_bounding_boxes_list)

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
    plot_image_flow(img_trace, action_trace,
                    os.path.join(hydra_cfg['runtime']['output_dir'], 'trace_predict.png'),
                    bounding_boxes_list=pre_bounding_boxes_list)

    save_json(history, os.path.join(hydra_cfg['runtime']['output_dir'], 'history.json'))

    temp_dict = {
        "predicted_milestones":milestones,
        "nodeIdList":history_log_sid_list,
        "sceneIdList": img_filenames,
        "action_trace":action_trace,
        "task_is_completed":1,
    }
    save_json(temp_dict, os.path.join(hydra_cfg['runtime']['output_dir'], 'trace_predict.json'))

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
    exit(0)

def update_image():
    try:
        img = image_queue.get_nowait()  # Get image from queue
        img = resize_image_to_height(img, screen_height)
        photo = ImageTk.PhotoImage(img)
        label.config(image=photo)
        label.image = photo
    except queue.Empty:
        pass
    finally:
        root.after(1000, update_image)

# def update_image(index, source):
#     #if source == "offline":
#     images_list =  [os.path.join(source,_) for _ in os.listdir(source)]
#     idx = int(source[-2:])
#     new_source = source[-2:]+"%02d"%(idx+1)
#     #if index < len(images_list):
#     img = Image.open(images_list[index])
#     img = resize_image_to_height(img, screen_height)
#     photo = ImageTk.PhotoImage(img)
#     label.config(image=photo)
#     label.image = photo
#     # Schedule the next update if not the last image
#     if index < len(images_list) - 1:
#         root.after(1000, update_image, index + 1, source)
    # else:
    #     # Switch to online source after displaying offline images
    #     root.after(int(inference_time * 1000), update_image, 0, new_source)
    # elif source == "online":
    #     if index < len(online_images):
    #         img = online_images[index]
    #         img = resize_image_to_height(img, screen_height)
    #         photo = ImageTk.PhotoImage(img)
    #         label.config(image=photo)
    #         label.image = photo
    #         root.after(1000, update_image, index + 1, "online")

def start_gui():
    global root, label, screen_height

    # Create the main window
    root = tk.Tk()
    root.title("Image Viewer")

    # Get screen dimensions
    screen_width = root.winfo_screenwidth()
    screen_height = int(root.winfo_screenheight()*0.95)

    # Set window size and position it on the right side of the screen
    window_width = 750  # Set your desired window width
    window_height = screen_height
    x_position = screen_width - window_width
    y_position = 0

    # Position the window
    root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

    # Create a label to display the image
    label = tk.Label(root)
    label.pack()

    # Start updating images
    update_image()
    # Start by displaying offline images
    # update_image(0, os.path.join("visualization","step00"))

    # Run the Tkinter event loop
    root.mainloop()

if __name__ == '__main__':
    import threading
    import queue
    image_queue = queue.Queue()
    # Start fetching online images in a separate thread
    fetch_thread = threading.Thread(target=main)
    fetch_thread.start()

    # Start the GUI in a separate thread
    gui_thread = threading.Thread(target=start_gui)
    gui_thread.start()

    # Wait for both threads to complete
    fetch_thread.join()
    gui_thread.join()
