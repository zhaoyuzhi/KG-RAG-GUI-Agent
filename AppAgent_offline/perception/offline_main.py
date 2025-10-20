import hydra
import os
from utils.basic_utils import load_json, save_json
import dashscope
from dotenv import load_dotenv
from easydict import EasyDict as edict
from utils.draw import setup_logger, color_log
from utils.parseXML import parse, hierarchy_parse, get_all_widget_ids
from utils.get_path_from_kg import get_widget_id_desp_map, get_action_command_map, get_relation_graph_from_edges
from utils.get_path_from_kg import get_new_action_command_map, get_new_relation_graph_from_edges
from collections import defaultdict
from agents import *
import logging
from utils.logging_utils import ColoredFormatter
import time

@hydra.main(version_base=None, config_path='../configs', config_name='configs')
def main(configs):
    logger = logging.getLogger('colored_logger')
    # logger = setup_logger()
    # console_handler = logging.StreamHandler()
    # console_handler.setFormatter(ColoredFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    # logging.getLogger().addHandler(console_handler)
    # logger = setup_logger()
    #file_handler = logging.FileHandler('custom.log', encoding='utf-8')
    #file_handler.setFormatter(red_formatter)
    #logging.getLogger().addHandler(file_handler)

    # ENVIRONMENT VARIABLES
    load_dotenv()
    QWEN_API_TOKEN = os.getenv("QWEN_API_TOKEN")

    # CONFIGURATION
    configs = edict(configs)
    memory_dir = configs.memory_dir
    log_dir = configs.exp_configs.log_dir

    intent = configs.exp_configs.intent
    improved_intent = configs.exp_configs.get('improved_intent', None)
    intent = improved_intent if improved_intent is not None else intent

    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    if not os.path.exists(memory_dir):
        os.makedirs(memory_dir)

    if not os.path.exists("../temp"):
        os.makedirs("../temp")

    # INIT AGENTS
    dashscope.api_key = QWEN_API_TOKEN

    file_data = "com.gotokeep.keep/dist/static/com.gotokeep.keep.json"

    dist_data = load_json(file_data)

    """获取widget_id和控件描述的对应关系"""
    # 'D207CA0F0CA946ACC2235E64AC56F734#40ADFCD68480BF540DCA04F6D581E622': '分享按钮'
    widget_id_desp_map = get_widget_id_desp_map(dist_data["nodes"])

    """获取action_id和操作名称的对应关系"""
    # 'B43165C2917FBFDDB2385D68A6DF8426': "点击'爱玩游戏'的按钮"
    action_command_map = get_action_command_map(dist_data["nodes"], widget_id_desp_map)
    # print(action_command_map["91AE23529C9704FA54FAA31A210FC0E2"])
    # exit(1)

    """
        获得所有页面的带有操作名称的关系图
        relation_graph:
        {
        scene_id1:[{"actionList":["点击推荐按钮"], "to": scene_id2}, {"actionList":["点击我的按钮"], "to": scene_id8}]
        scene_id5:[...]
        }
    """
    #'CBB37C19956E53974B24C8336E53124F':
    # [{'actionList': ['点击点击进入详情页'], 'to': 'F156459EBB2FAA5BE483439C463C2AD8'},
    # {'actionList': ["点击'介绍'的按钮"], 'to': '1BBD4C863978D68FCF19D4576782F14A'},...]
    relation_graph = get_relation_graph_from_edges(dist_data["edges"], action_command_map)
    # print(relation_graph["C1893860D5224DC16D4ED551E76CC753"])
    # exit(1)

    start_node_list = []
    for sid, node in dist_data["nodes"].items():
        if node["exactScenes"][0]["home"]:
            start_node_list.append(sid)

    color_log(f"start_node_list: {start_node_list}",logger)
    # exit(1)
    #
    # start_node = None
    # for sid, node in dist_data["nodes"].items():
    #     if  node["exactScenes"][0]["home"]:
    #         start_node = sid
    #         break

    assert len(start_node_list) > 0, "no homepage"
    #start_node = "804D8228CEADDFAAD8A9FFDCC2A599D4"

    observer = Observer_offline_graph(logger, dist_data)
    reflection = Reflection(logger)
    decision = Decision(logger)

    # MAIN LOOP
    max_n_trials = len(start_node_list)
    max_n_steps = configs.max_n_steps
    color_log(f"任务意图: {intent}", logger, color='cyan')
    max_not_relevant_count = 4

    total_decision_time = 0
    total_reflection_time = 0
    total_step = 0
    total_trial = 0

    # WORKING MEMORY
    history = defaultdict(list)
    total_timer_start = time.time()
    for trial in range(1, max_n_trials + 1):
        trial_timer_start = time.time()
        if trial > 1 and history[trial - 1][-1]['reflection_feedback']['is_complete']:
            color_log("The path is found...", logger, color='cyan')
            break
        total_trial +=1

        step = 0
        start_node = start_node_list[trial - 1]
        history[trial] = []
        color_log(f"exploring start sid: {start_node}", logger, color='cyan')
        current_node = start_node
        not_relevant_count = 0

        while True:

            step += 1

            if step > max_n_steps:
                color_log(
                    "Reach the maximum path length. Fail to generate a path with start node %s" % start_node,
                    logger, color='red')
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
                color_log(
                    f"Trial: {trial} Trial inference time: {time.time() - trial_timer_start}",
                    logger,color='yellow')
                break
            else:
                action_list = relation_graph[current_node]

            step_timer_start = time.time()
            total_step += 1

            if step == 1:
                # OBSERVE
                #layout, screen_id, screen_desc, screen_functions, screenshot = observer(current_node)
                layout, screen_desc, screen_functions, screenshot = observer(current_node)

            decision_timer_start = time.time()

            current_screen_infos = {
                # 'id': next_screen_id,
                'layout': layout,
                'description': screen_desc,
                # 'function_blocks': next_screen_functions,
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
                        #'id': next_screen_id,
                        'layout': next_layout,
                        'description': next_screen_desc,
                        #'function_blocks': next_screen_functions,
                    })
                try:
                    current_complete_reasoning = history[trial][-1]["reflection_feedback"]["reasoning"]
                except:
                    current_complete_reasoning = None

                thought_actions = decision.get_final_decision(intent, current_screen_infos, action_list,
                                                              next_screen_infos, current_complete_reasoning,
                                                              is_use_desp=True)
                thought = thought_actions['reasoning']
                final_action_id = thought_actions['final_action_id']
                is_relevant = thought_actions['is_relevant']
                if is_relevant:
                    not_relevant_count = 0
                else:
                    not_relevant_count += 1
                    if not_relevant_count >= max_not_relevant_count:
                        color_log(
                            "not relevant pages to the intent %d times. Fail to generate a path with start node %s" % (
                            max_not_relevant_count, start_node),
                            logger, color='red')
                        color_log(
                            f"Trial: {trial} Trial inference time: {time.time() - trial_timer_start}",
                            logger)
                        break

                # Next screenshot and layout
                #next_screen_id = next_screen_infos[final_action_id]['id']
                final_action = action_list[final_action_id]["actionList"][0]
                next_node = action_list[final_action_id]["to"]
                next_layout = next_screen_infos[final_action_id]['layout']
                next_screen_desc = next_screen_infos[final_action_id]['description']
                #next_screen_functions = next_screen_infos[final_action_id]['function_blocks']

            elif total_num_actions == 1:
                next_node = action_list[0]["to"]
                final_action = action_list[0]["actionList"][0]
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
                "reflection_feedback": {"reasoning": None, "is_complete": False, "is_trap_in_loop": False},
            })

            # REFLECTION
            feedback = reflection(intent, history[trial], is_use_desp=True)

            # UPDATE
            history[trial][-1]['reflection_feedback'] = feedback

            reflection_time = time.time() - reflection_timer_start
            color_log(f"Trial: {trial}| Step: {step} reflection agent time: {time.time() - reflection_timer_start}", logger,color='yellow')
            total_reflection_time += reflection_time


            #feedback = {}
            if feedback['is_complete']:
                color_log("Task is completed...", logger, color='cyan')
                color_log(f"Current sid: {next_node}", logger)
                history_log_sid_list = [his["node"] for step, his in enumerate(history[trial])]
                history_log_sid_list.append(next_node)
                color_log(f"history_log_sid_list:\n {history_log_sid_list}", logger, color='cyan')
                history_log = "\n".join([f"{step + 1}: {his['action']}" for step, his in enumerate(history[trial])])
                color_log(f"History:\n {history_log}", logger, color='cyan')
                color_log(
                    f"Trial: {trial} Trial inference time: {time.time() - trial_timer_start}",
                    logger,color='yellow')
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
    # if not history[max_n_trials][-1]['reflection_feedback']['is_complete']:
    #     color_log("Reach maximum steps or ...", logger, color='cyan')
    #     #color_log(f"Current sid: {next_node}", logger)
    #     history_log_sid_list = [his["node"] for step, his in enumerate(history[max_n_trials])]
    #     #history_log_sid_list.append(next_node)
    #     color_log(f"history_log_sid_list:\n {history_log_sid_list}", logger, color='cyan')
    #     history_log = "\n".join([f"{step + 1}: {his['action']}" for step, his in enumerate(history[max_n_trials])])
    #     color_log(f"History:\n {history_log}", logger, color='cyan')

if __name__ == '__main__':
    main()
