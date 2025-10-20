import copy
import hydra
from PIL import Image
from api.internal_qwen import query_qwen2_vl,query_qwen2dot5_int4,query_intern_vl
from MobileAgent.prompt_polished_1 import get_action_prompt, get_reflect_prompt, get_memory_prompt, get_process_prompt
from MobileAgent.chat import init_action_chat, init_reflect_chat, init_memory_chat, add_response, add_response_two_image
from utils.get_server_deploy_new import init_pack_router, save_image, save_layout, get_action_list, execute_action, get_scene, init_router
import time
import os

import logging
import shutil
from utils.draw import color_log,add_swipe_visualization,draw_coordinates_and_bounding_boxes,draw_bounding_boxes_wtype,draw_tag_wtype

from utils.basic_utils import save_jsonl
from utils.rag_utils import search_on_rag


####################################### Edit your Setting #########################################
# You can add operational knowledge to help Agent operate more accurately.
#add_info = "If you want to browse more, normally use the action swipe down."
# Reflection Setting: If you want to improve the operating speed, you can disable the reflection agent. This may reduce the success rate.
reflection_switch = True

# Memory Setting: If you want to improve the operating speed, you can disable the memory unit. This may reduce the success rate.
memory_switch = False
###################################################################################################

@hydra.main(version_base=None, config_path='configs', config_name='configs')
def main(configs):
    logger = logging.getLogger('colored_logger')
    exp_configs = configs.exp_configs
    app_name = exp_configs.app_name
    package_name = exp_configs.package_name
    instruction = exp_configs.intent

    thought_history = []
    summary_history = []
    action_history = []

    summary = ""
    action = ""
    completed_requirements = ""
    memory = ""
    insight = ""
    if not os.path.exists("screenshot"):
        os.mkdir("screenshot")
    if not os.path.exists("layout"):
        os.mkdir("layout")

    error_flag = False
    hydra_cfg = hydra.core.hydra_config.HydraConfig.get()
    os.makedirs(os.path.join(hydra_cfg['runtime']['output_dir'], "screenshot"), exist_ok=True)
    os.makedirs(os.path.join(hydra_cfg['runtime']['output_dir'], "layout"), exist_ok=True)
    os.makedirs(os.path.join(hydra_cfg['runtime']['output_dir'], "perception"), exist_ok=True)
    os.makedirs(os.path.join(hydra_cfg['runtime']['output_dir'], "img_plus_bbox"), exist_ok=True)
    os.makedirs(os.path.join(hydra_cfg['runtime']['output_dir'], "img_plus_som"), exist_ok=True)

    iter = 0
    total_decision_time = 0.
    total_planning_time = 0.
    total_reflection_time = 0.
    total_perception_time = 0.
    total_step = 0
    trial_timer_start = time.time()

    # perception of the first time
    sent_aibrain_param = {
        "packageName": package_name,
        "productDescription": "接口测试",
        "taskId": "test",
        "target": instruction,# 执行目标
        "appName": app_name,
    }

    feature_path = f"/home/pp/app_agent/RAGGeneration_New/data/oracle_test_app_second_stage/{package_name}/graph/{package_name}_intention_text_feature.pkl"
    available_intention_json_path = f"/home/pp/app_agent/RAGGeneration_New/data/oracle_test_app_second_stage/{package_name}/graph/{package_name}_node_available_path_template.json"


    perception_start_time = time.time()

    screenshot_file = os.path.join(hydra_cfg['runtime']['output_dir'], 'screenshot', 'output_image_' + str(0) + '.png')  # "./screenshot/screenshot.jpg"

    layout_path = os.path.join(hydra_cfg['runtime']['output_dir'], 'layout', 'output_layout_' + str(0) + '.json')

    perception_file = os.path.join(hydra_cfg['runtime']['output_dir'], 'perception',
                                   'output_perception_' + str(0) + '.jsonl')
    img_plus_bbox_file = os.path.join(hydra_cfg['runtime']['output_dir'], 'img_plus_bbox',
                                        'output_img_plus_bbox_' + str(iter) + '.png')
    img_plus_som_file = os.path.join(hydra_cfg['runtime']['output_dir'], 'img_plus_som',
                                        'output_img_plus_som_' + str(iter) + '.png')

    # 模拟执行器发起调用
    init_pack_value = init_pack_router(sent_aibrain_param)

    # 调用action的 init接口,此处才是工程化的开始接口
    init_value = init_router()

    product_description = init_value["productDescription"]
    prompt_target = init_value["promptTarget"]
    # 执行完init后，调用getScene方法，获取场景信息
    #time.sleep(100)
    temp_value = get_scene()

    # 参数key值不变
    # 将actionId作为key值构建map
    save_image(temp_value["img"], screenshot_file)
    save_layout(temp_value["layout"], layout_path)
    del temp_value["img"]
    del temp_value["layout"]

    perception_time = time.time() - perception_start_time
    total_perception_time += perception_time
    color_log(f"Iter: {iter} perception agent time: {perception_time}", logger, color='yellow')


    perception_dict, perception_infos = get_action_list(temp_value["widgetList"])
    save_jsonl(perception_infos, perception_file)

    draw_bounding_boxes_wtype(screenshot_file, perception_dict, img_plus_bbox_file)
    draw_tag_wtype(screenshot_file, perception_dict, img_plus_som_file)

    width, height = Image.open(screenshot_file).size

    keyboard = True

    add_info = search_on_rag(package_name, screenshot_file, instruction, feature_path, available_intention_json_path)
    
    while True:
        start_time = time.time()
        if iter > 8:
            break
        iter += 1

        decision_timer_start = time.time()
        #add_info = ""
        print(add_info, '---')
        color_log(f"RAG_info: {add_info}", logger)
        #add_info = ""
        prompt_action = get_action_prompt(instruction, perception_infos, width, height, keyboard, summary_history, action_history, summary, action, add_info, error_flag, completed_requirements, memory)
        chat_action = init_action_chat()
        chat_action = add_response("user", prompt_action, chat_action, screenshot_file)

        # output_action = inference_chat(chat_action, 'gpt-4o', API_url, token)
        output_action = query_qwen2_vl(chat_action,logger)

        thought = output_action[1].split("### Thought ###")[-1].split("### Action ###")[0].replace("\n", " ").replace(":", "").replace("  ", " ").strip()
        summary = output_action[1].split("### Operation ###")[-1].replace("\n", " ").replace("  ", " ").strip()
        action = output_action[1].split("### Action ###")[-1].split("### Operation ###")[0].replace("\n", " ").replace("  ", " ").strip()
        chat_action = add_response("assistant", output_action, chat_action)
        status = "#" * 50 + " Decision " + "#" * 50
        color_log(f"status: {status}", logger)
        color_log(f"output_action: {output_action}", logger)
        color_log('#' * len(status), logger)

        decision_time = time.time() - decision_timer_start
        total_decision_time += decision_time
        color_log(f"Iter: {iter} decision agent time: {decision_time}", logger, color='yellow')

        if memory_switch:
            prompt_memory = get_memory_prompt(insight)
            chat_action = add_response("user", prompt_memory, chat_action)
            # output_memory = inference_chat(chat_action, 'gpt-4o', API_url, token)
            output_memory = query_qwen2_vl(chat_action,logger)
            # chat_action = add_response("assistant", output_memory, chat_action)
            status = "#" * 50 + " Memory " + "#" * 50
            color_log(f"status: {status}", logger)
            color_log(f"output_memory: {output_memory}", logger)
            color_log('#' * len(status), logger)
            output_memory = output_memory.split("### Important content ###")[-1].split("\n\n")[0].strip() + "\n"
            if "None" not in output_memory and output_memory not in memory:
                memory += output_memory

        save_img_with_action_path = os.path.join(hydra_cfg['runtime']['output_dir'], 'screenshot',
                                            'output_image_action_' + str(iter - 1) + '.png')

        #当前支持 WAIT, CLICK, INPUT, SWIPE_UP, SWIPE_DOWN, SWIPE_LEFT, SWIPE_RIGHT, BACK, BACK_HOME
        actionType = "CLICK"
        inputText  = ""
        x,y = 0,0
        widgetId = None
        swipe_type = None
        if "Tap" in action:
            index = int(action.split("(")[-1].split(")")[0])
            #print(perception_infos, index, '====')
            meta_info = perception_infos[index]
            x, y = meta_info["coordinates"]
            draw_coordinates_and_bounding_boxes(screenshot_file, [[x, y]], [meta_info["bbox"]], save_img_with_action_path)
            widgetId = meta_info["widgetId"]

        elif "Swipe" in action:
            action_output = action.split("(")[-1].split(")")[0].split(", ")
            index = int(action_output[0])
            meta_info = perception_infos[index]
            x, y = meta_info["coordinates"]
            widgetId = meta_info["widgetId"]
            draw_coordinates_and_bounding_boxes(screenshot_file, [[x, y]], [meta_info["bbox"]],
                                                save_img_with_action_path)

            swipe_direction = action_output[1]
            actionType = "SWIPE"
            if "up" in swipe_direction:
                x2, y2 = x, y + 600
                swipe_type = "SwipeUp"
            elif "down" in swipe_direction:
                x2, y2 = x, y - 600
                swipe_type = "SwipeDown"
            elif "left" in swipe_direction:
                x2, y2 = x + 300, y
                swipe_type = "SwipeLeft"
            elif "right" in swipe_direction:
                x2, y2 = x - 300, y
                swipe_type = "SwipeRight"
            else:
                color_log("Invalid swipe direction, swipe down by default", logger)
                x2, y2 = x, y - 600
                swipe_type = "SwipeDown"

            add_swipe_visualization(screenshot_file, save_img_with_action_path,(x, y),(x2, y2))


        elif "Type" in action:
            action_output = action.split("(")[-1].split(")")[0].split(", ")
            index = int(action_output[0])
            meta_info = perception_infos[index]
            x, y = meta_info["coordinates"]
            widgetId = meta_info["widgetId"]
            draw_coordinates_and_bounding_boxes(screenshot_file, [[x, y]], [meta_info["bbox"]],
                                                save_img_with_action_path)

            inputText = action_output[1]
            actionType = "INPUT"

        elif "Back" in action:
            actionType = "BACK"

        elif "Stop" in action:
            break

        perception_start_time = time.time()

        action_list_parm = {
            "actionList":[
                { "action": actionType,
                    "swipe_type": swipe_type,
                    "content": inputText,
                    "widgetId": widgetId,
                }
            ]
        }
        execute_aibrain_param = {
            "sceneId": temp_value["sceneId"], "exactSceneSequence": action_list_parm, "code": 0, "sleepTime":1000
        }

        temp_value = execute_action(execute_aibrain_param)
        print(execute_aibrain_param, temp_value, '----------------------d---')
        # Reflection stage
        last_perception_infos = copy.deepcopy(perception_infos)
        last_screenshot_file = "./screenshot/last_screenshot.jpg"
        last_keyboard = keyboard
        if screenshot_file != last_screenshot_file:
            if os.path.exists(last_screenshot_file):
                os.remove(last_screenshot_file)
            shutil.copy(screenshot_file, last_screenshot_file)

        screenshot_file =  os.path.join(hydra_cfg['runtime']['output_dir'], 'screenshot',
                                              'output_image_' + str(iter) + '.png')
        layout_path = os.path.join(hydra_cfg['runtime']['output_dir'], 'layout', 'output_layout_' + str(iter) + '.json')
        perception_file = os.path.join(hydra_cfg['runtime']['output_dir'], 'perception',
                                       'output_perception_' + str(iter) + '.jsonl')
        img_plus_bbox_file = os.path.join(hydra_cfg['runtime']['output_dir'], 'img_plus_bbox',
                                          'output_img_plus_bbox_' + str(iter) + '.png')
        img_plus_som_file = os.path.join(hydra_cfg['runtime']['output_dir'], 'img_plus_som',
                                         'output_img_plus_som_' + str(iter) + '.png')

        save_image(temp_value["img"], screenshot_file)
        save_layout(temp_value["layout"], layout_path)

        perception_dict, perception_infos = get_action_list(temp_value["widgetList"])
        save_jsonl(perception_infos, perception_file)
        draw_bounding_boxes_wtype(screenshot_file, perception_dict, img_plus_bbox_file)
        draw_tag_wtype(screenshot_file, perception_dict, img_plus_som_file)

        width, height = Image.open(screenshot_file).size

        keyboard = True

        perception_time = time.time() - perception_start_time
        total_perception_time += perception_time
        color_log(f"Iter: {iter} perception agent time: {perception_time}", logger, color='yellow')


        # Reflection
        if reflection_switch:

            reflection_timer_start = time.time()
            prompt_reflect = get_reflect_prompt(instruction, last_perception_infos, perception_infos, width, height, last_keyboard, keyboard, summary, action, thought)
            chat_reflect = init_reflect_chat()
            chat_reflect = add_response_two_image("user", prompt_reflect, chat_reflect, [last_screenshot_file, screenshot_file])

            # output_reflect = inference_chat(chat_reflect, 'gpt-4o', API_url, token)
            output_reflect = query_qwen2_vl(chat_reflect,logger)
            reflect = output_reflect[1].split("### Answer ###")[-1].replace("\n", " ").strip()
            chat_reflect = add_response("assistant", output_reflect, chat_reflect)
            status = "#" * 50 + " Reflection " + "#" * 50
            color_log(f"status: {status}", logger)
            color_log(f"output_reflect: {output_reflect}", logger)
            color_log('#' * len(status), logger)
            reflection_time = time.time() - reflection_timer_start
            total_reflection_time += reflection_time
            color_log(f"Iter: {iter} reflection agent time: {reflection_time}", logger, color='yellow')

            if 'A' in reflect:
                planning_timer_start = time.time()
                thought_history.append(thought)
                summary_history.append(summary)
                action_history.append(action)

                prompt_planning = get_process_prompt(instruction, thought_history, summary_history, action_history, completed_requirements, add_info)
                chat_planning = init_memory_chat()
                chat_planning = add_response("user", prompt_planning, chat_planning)
                # output_planning = inference_chat(chat_planning, 'gpt-4-turbo', API_url, token)
                output_planning = query_qwen2dot5_int4(chat_planning,logger)
                chat_planning = add_response("assistant", output_planning, chat_planning)
                status = "#" * 50 + " Planning " + "#" * 50
                color_log(status, logger)
                color_log(output_planning, logger)
                color_log('#' * len(status), logger)
                completed_requirements = output_planning[1].split("### Completed contents ###")[-1].replace("\n", " ").strip()
                error_flag = False
                #decision_time = time.time() - decision_timer_start
                planning_time = time.time() - planning_timer_start
                total_planning_time += planning_time
                color_log(f"Iter: {iter} planning agent time: {planning_time}", logger, color='yellow')


            elif 'B' in reflect:
                error_flag = True
                color_log("Return Back to previous page", logger)


                perception_start_time = time.time()
                action_list_parm = {
                    "actionList":
                       [
                           {"action": "BACK",
                            "swipe_type": None,
                            "content": None,
                            "widgetId": None}
                       ]
                }

                execute_aibrain_param = {
                    "sceneId": temp_value["sceneId"], "exactSceneSequence": action_list_parm, "code": 0
                }

                #print("execute_aibrain_param: ",execute_aibrain_param)

                temp_value =  execute_action(execute_aibrain_param)

                screenshot_file = os.path.join(hydra_cfg['runtime']['output_dir'], 'screenshot',
                                               'output_image_back_' + str(iter) + '.png')
                layout_path = os.path.join(hydra_cfg['runtime']['output_dir'], 'layout',
                                           'output_layout_back_' + str(iter) + '.json')
                perception_file = os.path.join(hydra_cfg['runtime']['output_dir'], 'perception',
                                               'output_perception_back_' + str(iter) + '.jsonl')
                img_plus_bbox_file = os.path.join(hydra_cfg['runtime']['output_dir'], 'img_plus_bbox',
                                                  'output_img_plus_bbox_back_' + str(iter) + '.png')
                img_plus_som_file = os.path.join(hydra_cfg['runtime']['output_dir'], 'img_plus_som',
                                                 'output_img_plus_som_back_' + str(iter) + '.png')
                save_image(temp_value["img"], screenshot_file)
                save_layout(temp_value["layout"], layout_path)
                perception_dict, perception_infos = get_action_list(temp_value["widgetList"])
                save_jsonl(perception_infos, perception_file)
                draw_bounding_boxes_wtype(screenshot_file, perception_dict, img_plus_bbox_file)
                draw_tag_wtype(screenshot_file, perception_dict, img_plus_som_file)
                width, height = Image.open(screenshot_file).size
                keyboard = True
                perception_time = time.time() - perception_start_time
                total_perception_time += perception_time
                color_log(f"Iter: {iter} perception agent time: {perception_time}", logger, color='yellow')


            elif 'C' in reflect:
                error_flag = True
                color_log("No change", logger)

        else:

            planning_timer_start = time.time()
            thought_history.append(thought)
            summary_history.append(summary)
            action_history.append(action)

            prompt_planning = get_process_prompt(instruction, thought_history, summary_history, action_history, completed_requirements, add_info)
            chat_planning = init_memory_chat()
            chat_planning = add_response("user", prompt_planning, chat_planning)
            # output_planning = inference_chat(chat_planning, 'gpt-4-turbo', API_url, token)
            output_planning = query_qwen2dot5_int4(chat_planning,logger)
            chat_planning = add_response("assistant", output_planning, chat_planning)
            status = "#" * 50 + " Planning " + "#" * 50
            color_log(status,logger)
            color_log(output_planning,logger)
            color_log('#' * len(status),logger)
            completed_requirements = output_planning[1].split("### Completed contents ###")[-1].replace("\n", " ").strip()
            planning_time = time.time() - planning_timer_start
            total_planning_time += planning_time
            color_log(f"Iter: {iter} planning agent time: {planning_time}", logger, color='yellow')


        step_time = time.time() - start_time
        total_step += step_time
        color_log(f"Iter: {iter} total time: {step_time}", logger, color='yellow')

    total_inference_time = time.time() - trial_timer_start
    color_log(
        f"total perception time: {total_perception_time}",
        logger, color='yellow')
    color_log(
        f"total planning time: {total_planning_time}",
        logger, color='yellow')
    color_log(
        f"total decision time: {total_decision_time}",
        logger, color='yellow')
    color_log(
        f"total reflection time: {total_reflection_time}",
        logger, color='yellow')
    color_log(
        f"total inference time: {total_inference_time}",
        logger, color='yellow')


if __name__ == '__main__':
    main()