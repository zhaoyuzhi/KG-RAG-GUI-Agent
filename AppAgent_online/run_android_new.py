import os
import time
import copy
import hydra
from PIL import Image, ImageDraw
from api.internal_qwen import query_qwen2_vl,query_qwen2dot5_int4,query_intern_vl
from MobileAgent.prompt_polished_1 import get_action_prompt, get_reflect_prompt, get_memory_prompt, get_process_prompt
from MobileAgent.controller import get_screenshot, get_layout, tap, slide, type, back, home, check_lock_screen_state
from MobileAgent.controller import unlock_screen,open_app,kill_app
from MobileAgent.chat import init_action_chat, init_reflect_chat, init_memory_chat, add_response, add_response_two_image
import time
import os

import logging
import shutil
from utils.draw import color_log,add_swipe_visualization,draw_coordinates_and_bounding_boxes,draw_bounding_boxes_wtype,draw_tag_wtype
from utils.get_vut_desc import get_action_list
from utils.basic_utils import save_jsonl,save_json
####################################### Edit your Setting #########################################
# Your ADB path
adb_path = "adb"

# You can add operational knowledge to help Agent operate more accurately.
# add_info = "If you want to tap an icon of an app, use the action \"Open app\". If you want to exit an app, use the action \"Home\""
# add_info += "\nWhen the widget you want to interact with spans multiple grid positions, select the position closest to the center of the widget."
add_info = "If you want to browse more, normally use the action swipe down. "
#add_info += "If the current screenshot does not show any direct link or button to complete the task, choose the optimal action which can move forward the task."
#add_info = "To view the privacy policy details on the some apps, the user need to first navigate my page, and then go to the settings or help section to find the privacy policy."

# Reflection Setting: If you want to improve the operating speed, you can disable the reflection agent. This may reduce the success rate.
reflection_switch = True

# Memory Setting: If you want to improve the operating speed, you can disable the memory unit. This may reduce the success rate.
memory_switch = False
###################################################################################################

@hydra.main(version_base=None, config_path='configs', config_name='configs')
def main(configs):
    logger = logging.getLogger('colored_logger')

    # get the config variables
    exp_configs = configs.exp_configs
    app_name = exp_configs.app_name
    package_name = exp_configs.package_name
    instruction = exp_configs.intent

    # record the immediate variable
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

    ## check whether phone is loked and wake up
    is_locked_state = check_lock_screen_state(adb_path)
    color_log(f"is_locked_state: {is_locked_state}", logger)
    if is_locked_state:
        unlock_screen(adb_path)
    color_log(f"package_name: {package_name}", logger)
    ## kill & open app
    kill_app(adb_path, package_name)
    time.sleep(0.5)
    open_app(adb_path, package_name)
    time.sleep(5)

    ## get perception of the first time
    perception_start_time = time.time()
    screenshot_file = os.path.join(hydra_cfg['runtime']['output_dir'], 'screenshot', 'output_image_' + str(0) + '.png')

    layout_path = os.path.join(hydra_cfg['runtime']['output_dir'], 'layout', 'output_layout_' + str(0) + '.xml')

    perception_file = os.path.join(hydra_cfg['runtime']['output_dir'], 'perception',
                                   'output_perception_' + str(0) + '.jsonl')
    img_plus_bbox_file = os.path.join(hydra_cfg['runtime']['output_dir'], 'img_plus_bbox',
                                        'output_img_plus_bbox_' + str(iter) + '.png')
    img_plus_som_file = os.path.join(hydra_cfg['runtime']['output_dir'], 'img_plus_som',
                                        'output_img_plus_som_' + str(iter) + '.png')

    get_screenshot(adb_path,save_path=screenshot_file)
    get_layout(adb_path,save_path=layout_path)
    width, height = Image.open(screenshot_file).size
    ##
    # 1. get widget description from the vut model. 2. reformat perception data.
    ##
    perception_dict, perception_infos = get_action_list(layout_path, screenshot_file)
    save_jsonl(perception_infos, perception_file)
    perception_time = time.time() - perception_start_time
    total_perception_time += perception_time
    color_log(f"Iter: {iter} perception agent time: {perception_time}", logger, color='yellow')
    ## visualization
    draw_bounding_boxes_wtype(screenshot_file, perception_dict, img_plus_bbox_file)
    draw_tag_wtype(screenshot_file, perception_dict, img_plus_som_file)

    keyboard = True

    while True:
        start_time = time.time()
        if iter > 8:
            break
        iter += 1

        decision_timer_start = time.time()

        ## get the prompt of decision agent
        prompt_action = get_action_prompt(instruction, perception_infos, width, height, keyboard, summary_history, action_history, summary, action, add_info, error_flag, completed_requirements, memory)
        chat_action = init_action_chat()
        chat_action = add_response("user", prompt_action, chat_action, screenshot_file)

        ## conduct decision agent
        output_action = query_qwen2_vl(chat_action,logger)

        ## analysis the output of the decision agent
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
            output_memory = query_qwen2_vl(chat_action,logger)
            status = "#" * 50 + " Memory " + "#" * 50
            color_log(f"status: {status}", logger)
            color_log(f"output_memory: {output_memory}", logger)
            color_log('#' * len(status), logger)
            output_memory = output_memory.split("### Important content ###")[-1].split("\n\n")[0].strip() + "\n"
            if "None" not in output_memory and output_memory not in memory:
                memory += output_memory

        ## visualize the conductd action in the image
        save_img_with_action_path = os.path.join(hydra_cfg['runtime']['output_dir'], 'screenshot',
                                            'output_image_action_' + str(iter - 1) + '.png')

        # Action:  Click a widget
        if "Tap" in action:
            index = int(action.split("(")[-1].split(")")[0])
            meta_info = perception_infos[index]
            x, y = meta_info["coordinates"]
            tap(adb_path, x, y)
            draw_coordinates_and_bounding_boxes(screenshot_file, [[x, y]], [meta_info["bbox"]], save_img_with_action_path)

        # Action:  Swipe a widget
        elif "Swipe" in action:

            action_output = action.split("(")[-1].split(")")[0].split(", ")
            index = int(action_output[0])
            meta_info = perception_infos[index]
            x, y = meta_info["coordinates"]
            draw_coordinates_and_bounding_boxes(screenshot_file, [[x, y]], [meta_info["bbox"]],
                                                save_img_with_action_path)
            swipe_direction = action_output[1]

            if "up" in swipe_direction:
                x2, y2 = x, y + 600
            elif "down" in swipe_direction:
                x2, y2 = x, y - 600
            elif "left" in swipe_direction:
                x2, y2 = x + 300, y
            elif "right" in swipe_direction:
                x2, y2 = x - 300, y
            else:
                color_log("Invalid swipe direction, swipe down by default", logger)
                x2, y2 = x, y - 600

            slide(adb_path, x, y, x2, y2)
            add_swipe_visualization(screenshot_file, save_img_with_action_path,(x, y),(x2, y2))

        # Action: Input something
        elif "Type" in action:
            if "(text)" not in action:
                action_output = action.split("(")[-1].split(")")[0]
            else:
                action_output = action.split(" \"")[-1].split("\"")[0]
            index_string, text = action_output.split(", ")
            index = int(index_string)
            meta_info = perception_infos[index]
            x, y = meta_info["coordinates"]
            tap(adb_path, x, y)
            type(adb_path, text)

        elif "Back" in action:
            back(adb_path)

        elif "Stop" in action:
            break

        #  sleep 5 seconds after conducting a action
        time.sleep(5)

        # Reflection stage
        perception_start_time = time.time()
        last_perception_dict = copy.deepcopy(perception_dict)
        last_perception_infos = copy.deepcopy(perception_infos)
        last_screenshot_file = "./screenshot/last_screenshot.jpg"
        last_keyboard = keyboard
        if screenshot_file != last_screenshot_file:
            if os.path.exists(last_screenshot_file):
                os.remove(last_screenshot_file)
            shutil.copy(screenshot_file, last_screenshot_file)

        screenshot_file =  os.path.join(hydra_cfg['runtime']['output_dir'], 'screenshot',
                                              'output_image_' + str(iter) + '.png')
        layout_path = os.path.join(hydra_cfg['runtime']['output_dir'], 'layout', 'output_layout_' + str(iter) + '.xml')
        perception_file = os.path.join(hydra_cfg['runtime']['output_dir'], 'perception',
                                       'output_perception_' + str(iter) + '.jsonl')
        img_plus_bbox_file = os.path.join(hydra_cfg['runtime']['output_dir'], 'img_plus_bbox',
                                          'output_img_plus_bbox_' + str(iter) + '.png')
        img_plus_som_file = os.path.join(hydra_cfg['runtime']['output_dir'], 'img_plus_som',
                                         'output_img_plus_som_' + str(iter) + '.png')

        get_screenshot(adb_path, screenshot_file)
        get_layout(adb_path, layout_path)

        perception_dict, perception_infos = get_action_list(layout_path, screenshot_file)

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
            output_reflect = query_qwen2_vl(chat_reflect,logger)

            # analysis the output of the reflection agent
            reflect = output_reflect[1].split("### Answer ###")[-1].replace("\n", " ").strip()
            chat_reflect = add_response("assistant", output_reflect, chat_reflect)
            status = "#" * 50 + " Reflection " + "#" * 50
            color_log(f"status: {status}", logger)
            color_log(f"output_reflect: {output_reflect}", logger)
            color_log('#' * len(status), logger)
            reflection_time = time.time() - reflection_timer_start
            total_reflection_time += reflection_time
            color_log(f"Iter: {iter} reflection agent time: {reflection_time}", logger, color='yellow')

            # Reflection Output : success
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


            # Reflection Output : wrong page
            elif 'B' in reflect:
                error_flag = True
                color_log("Return Back to previous page", logger)
                back(adb_path)

                width, height = Image.open(last_screenshot_file).size
                screenshot_file = last_screenshot_file
                perception_infos = last_perception_infos
                perception_dict = last_perception_dict

            # Reflection Output : no change
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