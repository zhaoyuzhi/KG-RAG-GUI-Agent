import hydra
import os
from utils.basic_utils import load_json, load_jsonl
import dashscope
from dotenv import load_dotenv
from easydict import EasyDict as edict
from utils.draw import color_log, plot_image_flow
from utils.get_path_from_kg import    get_new_relation_graph_from_edges
from collections import defaultdict
from agents import Observer, Reflection, Decision, IntentRewriter
import time
import logging
import math

@hydra.main(version_base=None, config_path='configs', config_name='configs')
def main(configs):
    logger = logging.getLogger('colored_logger')

    # ENVIRONMENT VARIABLES
    load_dotenv()
    QWEN_API_TOKEN = os.getenv("QWEN_API_TOKEN")

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

    # INIT AGENTS
    dashscope.api_key = QWEN_API_TOKEN

    path_prefix = os.path.join(data_dir, package_name)
    dist_data = load_json(os.path.join(path_prefix, f"{package_name}.json"))

    # plot GT trace
    hydra_cfg = hydra.core.hydra_config.HydraConfig.get()
    intent_sequence_list = load_jsonl(f'data\\intent_sequence_pair.jsonl')

    edge_dicts = load_json(os.path.join(data_dir, package_name, 'edges.json'))
    intent_sequence_dict = { item["id"]: item for item in intent_sequence_list}

    intent_data = intent_sequence_dict[intent_id]
    gt_img_trace = [os.path.join(path_prefix, 'screenshot', filename + '.jpeg') for filename in intent_data['sceneIdList']]

    gt_action_trace = [{"actionId": actionId, "actionDesp": command} for command,actionId in zip(intent_data['commandList'], intent_data['actionIdList'])]
    gt_bounding_boxes_list = [edge_dicts[actionId]["bboxes"] for actionId in intent_data['actionIdList']]
    # print(bounding_boxes_list)
    # print(intent_data['actionIdList'])
    # assert len(bounding_boxes_list) == len(intent_data['actionIdList'])
    plot_image_flow(gt_img_trace, gt_action_trace, os.path.join(hydra_cfg['runtime']['output_dir'], 'trace_gt.png'),bounding_boxes_list=gt_bounding_boxes_list)

    """获取widget_id和控件描述的对应关系"""
    # 'D207CA0F0CA946ACC2235E64AC56F734#40ADFCD68480BF540DCA04F6D581E622': '分享按钮'
    # widget_id_desp_map = get_widget_id_desp_map(dist_data["nodes"])
    #
    # """获取action_id和操作名称的对应关系"""
    # # 'B43165C2917FBFDDB2385D68A6DF8426': "点击'爱玩游戏'的按钮"
    # action_command_map = get_action_command_map(dist_data["nodes"], widget_id_desp_map)

    action_command_list = load_jsonl(os.path.join(data_dir, package_name, 'edge_desc.jsonl')) #f'data\{package_name}\\edge_desc.jsonl'
    action_command_map = {}
    for item in action_command_list:
        action_command_map.update(item)
    # """
    #     获得所有页面的带有操作名称的关系图
    #     relation_graph:
    #     {
    #     scene_id1:[{"actionList":["点击推荐按钮"], "to": scene_id2}, {"actionList":["点击我的按钮"], "to": scene_id8}]
    #     scene_id5:[...]
    #     }
    # """
    #'CBB37C19956E53974B24C8336E53124F':
    # [{'actionList': ['点击点击进入详情页'], 'to': 'F156459EBB2FAA5BE483439C463C2AD8'},
    # {'actionList': ["点击'介绍'的按钮"], 'to': '1BBD4C863978D68FCF19D4576782F14A'},...]
    relation_graph = get_new_relation_graph_from_edges(dist_data["edges"], action_command_map)

    img_to_sid_map = {node['exactScenes'][0]['img']: sid for sid, node in dist_data["nodes"].items()}
    start_node = img_to_sid_map[os.path.basename(gt_img_trace[0])]

    observer = Observer(logger, dist_data, path_prefix)
    reflection = Reflection(logger)
    decision = Decision(logger)
    intent_rewriter = IntentRewriter(logger)

    # MAIN LOOP
    max_n_trials = configs.max_n_trials
    max_n_steps = configs.max_n_steps
    color_log(f"任务意图: {intent}", logger, color='cyan')
    max_consecutive_irrelevant_count = 3

    total_decision_time = 0.
    total_reflection_time = 0.
    total_step = 0
    total_trial = 0

    # WORKING MEMORY
    history = defaultdict(list)

    # Intent Rewrite    
    intent, milestones = intent_rewriter(intent)

    total_timer_start = time.time()
    for trial in range(1, max_n_trials + 1):
        trial_timer_start = time.time()
        if trial > 1 and math.floor(eval(history[trial - 1][-1]['reflection_feedback']['completion_rate'])):
            color_log("The path is found...", logger, color='cyan')
            break
        total_trial +=1

        step = 0
        history[trial] = []
        color_log(f"exploring start sid: {start_node}", logger, color='cyan')
        current_node = start_node
        consecutive_irrelevant_count = 0

        while True:

            step += 1
            if step > max_n_steps:
                color_log(
                    "Reach the maximum path length. Fail to generate a path with start node %s" % start_node,
                    logger, color='red')
                color_log("Ending Task...", logger, color='cyan')
                next_node = history[trial][-1]["next_node"]
                history_log_sid_list = [his["node"] for step, his in enumerate(history[trial])]
                history_log_sid_list.append(next_node)
                color_log(f"history_log_sid_list:\n {history_log_sid_list}", logger, color='cyan')
                action_trace = [his['action'] for his in history[trial]]
                history_log = "\n".join([f"{step + 1}: {his['action']}" for step, his in enumerate(history[trial])])
                color_log(f"History:\n {history_log}", logger, color='cyan')
                color_log(
                    f"Trial: {trial} Trial inference time: {time.time() - trial_timer_start}",
                    logger, color='yellow')

                # save trace
                sid_trace = [sid for sid in history_log_sid_list]
                selected_rows = observer.df[observer.df['sid'].isin(sid_trace)]
                sid_to_img = dict(zip(selected_rows['sid'], selected_rows['img']))
                img_filenames = [sid_to_img[sid] for sid in sid_trace if sid in sid_to_img]
                img_trace = [os.path.join(path_prefix, 'screenshot', filename) for filename in img_filenames]
                pre_bounding_boxes_list = [edge_dicts[item["actionId"]]["bboxes"] for item in action_trace]
                plot_image_flow(img_trace, action_trace,
                                os.path.join(hydra_cfg['runtime']['output_dir'], 'trace_predict.png'),
                                bounding_boxes_list=pre_bounding_boxes_list)

                color_log(
                    f"Trial: {trial} Trial inference time: {time.time() - trial_timer_start}",
                    logger,color='yellow')
                break
            color_log(f"Trial: {trial}/{max_n_trials} | Step: {step}/{max_n_steps}", logger, color='cyan')
            color_log(f"Current sid: {current_node}", logger)

            if current_node not in relation_graph:
                color_log(
                    "Enter the node with no outward edge. Fail to generate a path with start node %s" % start_node,
                    logger, color='red')
                color_log("Ending Task...", logger, color='cyan')
                next_node = history[trial][-1]["next_node"]
                history_log_sid_list = [his["node"] for step, his in enumerate(history[trial])]
                history_log_sid_list.append(next_node)
                color_log(f"history_log_sid_list:\n {history_log_sid_list}", logger, color='cyan')
                action_trace = [his['action'] for his in history[trial]]
                history_log = "\n".join([f"{step + 1}: {his['action']}" for step, his in enumerate(history[trial])])
                color_log(f"History:\n {history_log}", logger, color='cyan')
                color_log(
                    f"Trial: {trial} Trial inference time: {time.time() - trial_timer_start}",
                    logger,color='yellow')

                # save trace
                sid_trace = [sid for sid in history_log_sid_list]
                selected_rows = observer.df[observer.df['sid'].isin(sid_trace)]
                sid_to_img = dict(zip(selected_rows['sid'], selected_rows['img']))
                img_filenames = [sid_to_img[sid] for sid in sid_trace if sid in sid_to_img]
                img_trace = [os.path.join(path_prefix, 'screenshot', filename) for filename in img_filenames]
                pre_bounding_boxes_list = [edge_dicts[item["actionId"]]["bboxes"] for item in action_trace]
                plot_image_flow(img_trace, action_trace,
                                os.path.join(hydra_cfg['runtime']['output_dir'], 'trace_predict.png'),
                                bounding_boxes_list=pre_bounding_boxes_list)
                #plot_image_flow(img_trace, action_trace, os.path.join(hydra_cfg['runtime']['output_dir'], 'trace_predict.png'))
                break
            else:
                action_list = relation_graph[current_node]

            step_timer_start = time.time()
            total_step += 1

            if step == 1:
                # OBSERVE
                layout, screen_desc, screen_functions, screenshot = observer(current_node)

            decision_timer_start = time.time()

            current_screen_infos = {
                'layout': layout,
                'description': screen_desc
            }

            total_num_actions = len(action_list)

            if total_num_actions > 1:
                next_screen_infos = []
                for action_id, action in enumerate(action_list):
                    color_log(f"Exploring action {action_id + 1}/{total_num_actions}...", logger)
                    next_sid = action["to"]
                    # Get next screenshot and layout
                    next_layout, next_screen_desc, next_screen_functions, next_screenshot = observer(next_sid)

                    next_screen_infos.append({
                        'layout': next_layout,
                        'description': next_screen_desc
                    })
                try:
                    progress = history[trial][-1]["reflection_feedback"]["progress"]
                    completion_rate = history[trial][-1]["reflection_feedback"]["completion_rate"]
                    is_trap_in_loop = history[trial][-1]["reflection_feedback"]["is_trap_in_loop"]
                except:
                    progress = ""
                    completion_rate = f"0/{len(milestones)}"
                    is_trap_in_loop = False

                thought_actions = decision.get_final_decision(intent, current_screen_infos, action_list, next_screen_infos, progress, completion_rate, is_trap_in_loop)

                thought = thought_actions['reasoning']
                final_action_id = thought_actions['final_action_id']
                is_irrelevant = thought_actions['is_irrelevant']

                if is_irrelevant:
                    consecutive_irrelevant_count += 1
                    if consecutive_irrelevant_count >= max_consecutive_irrelevant_count:
                        color_log(
                            "Reach the maximum irrelevant operation counts (i.e. %d times). Fail to generate a path with start node %s" % (
                            max_consecutive_irrelevant_count, start_node),
                            logger, color='red')
                        color_log("Ending Task...", logger, color='cyan')
                        next_node = history[trial][-1]["next_node"]
                        history_log_sid_list = [his["node"] for step, his in enumerate(history[trial])]
                        history_log_sid_list.append(next_node)
                        color_log(f"history_log_sid_list:\n {history_log_sid_list}", logger, color='cyan')
                        action_trace = [his['action'] for his in history[trial]]
                        history_log = "\n".join(
                            [f"{step + 1}: {his['action']}" for step, his in enumerate(history[trial])])
                        color_log(f"History:\n {history_log}", logger, color='cyan')
                        color_log(
                            f"Trial: {trial} Trial inference time: {time.time() - trial_timer_start}",
                            logger, color='yellow')

                        # save trace
                        sid_trace = [sid for sid in history_log_sid_list]
                        selected_rows = observer.df[observer.df['sid'].isin(sid_trace)]
                        sid_to_img = dict(zip(selected_rows['sid'], selected_rows['img']))
                        img_filenames = [sid_to_img[sid] for sid in sid_trace if sid in sid_to_img]
                        img_trace = [os.path.join(path_prefix, 'screenshot', filename) for filename in img_filenames]
                        pre_bounding_boxes_list = [edge_dicts[item["actionId"]]["bboxes"] for item in action_trace]
                        plot_image_flow(img_trace, action_trace,
                                        os.path.join(hydra_cfg['runtime']['output_dir'], 'trace_predict.png'),
                                        bounding_boxes_list=pre_bounding_boxes_list)
                        # plot_image_flow(img_trace, action_trace,
                        #                 os.path.join(hydra_cfg['runtime']['output_dir'], 'trace_predict.png'))

                        color_log(
                            f"Trial: {trial} Trial inference time: {time.time() - trial_timer_start}",
                            logger)
                        break
                else:
                    consecutive_irrelevant_count = 0

                # Next screenshot and layout
                #next_screen_id = next_screen_infos[final_action_id]['id']

                #len(actionlist）can be larger than one
                #final_action = action_list[final_action_id]["actionList"][0]
                final_action = action_list[final_action_id]
                next_node = action_list[final_action_id]["to"]
                next_layout = next_screen_infos[final_action_id]['layout']
                next_screen_desc = next_screen_infos[final_action_id]['description']
                #next_screen_functions = next_screen_infos[final_action_id]['function_blocks']

            elif total_num_actions == 1:
                next_node = action_list[0]["to"]
                final_action = action_list[0]#["actionList"][0]
                thought = None
                next_layout, next_screen_desc, next_screen_functions, next_screenshot = observer(action_list[0]["to"])
            # else:
            #     color_log("Fail to generate a path. enter the node with no outward edge", logger)
            #     break
            decision_time = time.time() - decision_timer_start
            color_log(f"Trial: {trial} | Step: {step} decision agent time: {decision_time}", logger,color='yellow')
            total_decision_time += decision_time
            reflection_timer_start = time.time()

            # WORKING MEMORY
            history[trial].append({
                'node': current_node,
                'action': final_action,
                'layout': layout,
                "thought": thought,
                'next_node': next_node,
                'description': screen_desc,
                'next_layout': next_layout,
                'next_description': next_screen_desc,
                "reflection_feedback": {"progress": "", "completion_rate": f"0/{len(milestones)}", "is_trap_in_loop": False},
            })

            # REFLECTION
            feedback = reflection(intent, milestones, history[trial])

            # UPDATE
            history[trial][-1]['reflection_feedback'] = feedback

            reflection_time = time.time() - reflection_timer_start
            color_log(f"Trial: {trial}| Step: {step} reflection agent time: {time.time() - reflection_timer_start}", logger,color='yellow')
            total_reflection_time += reflection_time


            if math.floor(eval(feedback['completion_rate'])) or step == max_n_steps:
                color_log("Ending Task...", logger, color='cyan')
                color_log(f"Current sid: {next_node}", logger)
                history_log_sid_list = [his["node"] for step, his in enumerate(history[trial])]
                history_log_sid_list.append(next_node)
                color_log(f"history_log_sid_list:\n {history_log_sid_list}", logger, color='cyan')
                action_trace = [his['action'] for his in history[trial]]
                history_log = "\n".join([f"{step + 1}: {his['action']}" for step, his in enumerate(history[trial])])
                color_log(f"History:\n {history_log}", logger, color='cyan')
                color_log(
                    f"Trial: {trial} Trial inference time: {time.time() - trial_timer_start}",
                    logger,color='yellow')

                # save trace
                sid_trace = [sid for sid in history_log_sid_list]
                selected_rows = observer.df[observer.df['sid'].isin(sid_trace)]
                sid_to_img = dict(zip(selected_rows['sid'], selected_rows['img']))
                img_filenames = [sid_to_img[sid] for sid in sid_trace if sid in sid_to_img]
                img_trace = [os.path.join(path_prefix, 'screenshot', filename) for filename in img_filenames]
                pre_bounding_boxes_list = [edge_dicts[item["actionId"]]["bboxes"] for item in action_trace]
                plot_image_flow(img_trace, action_trace,
                                os.path.join(hydra_cfg['runtime']['output_dir'], 'trace_predict.png'),
                                bounding_boxes_list=pre_bounding_boxes_list)
                #plot_image_flow(img_trace, action_trace, os.path.join(hydra_cfg['runtime']['output_dir'], 'trace_predict.png'))
                break

            # UPDATE
            #history[trial][-1]['reflection_feedback'] = feedback
            screen_desc = next_screen_desc
            layout = next_layout
            current_node = next_node

            color_log(
                f"Trial: {trial}| Step: {step}  step time: {time.time() - step_timer_start}",
                logger,color='yellow')

    total_inference_time = time.time() - total_timer_start
    color_log(
        f"total inference time: {total_inference_time}",
        logger,color='yellow')
    color_log(
        f"inference time per trial: {total_inference_time} / {total_trial} = {total_inference_time/total_trial}",
        logger, color='yellow')
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
