import os
import time
import copy
import hydra
from PIL import Image, ImageDraw
from api.internal_qwen import query_qwen2_vl,query_qwen2dot5_int4 #query_intern_vl,query_qwen2dot5_int4
from MobileAgent.controller import get_screenshot, get_layout, tap, slide, type, back, home
from MobileAgent.controller import check_lock_sreen_state,unlock_screen,open_app,kill_app
from MobileAgent.prompt_original import get_action_prompt, get_reflect_prompt, get_memory_prompt, get_process_prompt
from MobileAgent.chat import init_action_chat, init_reflect_chat, init_memory_chat, add_response, add_response_two_image
from utils.get_vut_desc import get_action_list
import logging
from utils.draw import color_log
####################################### Edit your Setting #########################################
# Your ADB path
adb_path = "D:\\adb\\platform-tools\\adb"

# instruction = "美团外卖页面收藏商家"

# Your GPT-4o API URL
# API_url = "https://api.openai.com/v1/chat/completions"
#
# # Your GPT-4o API Token
# token = "sk-......"
#
# # If you choose the api caption call method, input your Qwen api here
# qwen_api = "sk-......"

# You can add operational knowledge to help Agent operate more accurately.
add_info = "If you want to tap an icon of an app, use the action \"Open app\". If you want to exit an app, use the action \"Home\""
# add_info += "\nWhen the widget you want to interact with spans multiple grid positions, select the position closest to the center of the widget."

# Reflection Setting: If you want to improve the operating speed, you can disable the reflection agent. This may reduce the success rate.
reflection_switch = True

# Memory Setting: If you want to improve the operating speed, you can disable the memory unit. This may reduce the success rate.
memory_switch = False
###################################################################################################


def draw_coordinates_on_image(image_path, coordinates, iter):
    image = Image.open(image_path)
    draw = ImageDraw.Draw(image)
    point_size = 10
    for coord in coordinates:
        draw.ellipse((coord[0] - point_size, coord[1] - point_size, coord[0] + point_size, coord[1] + point_size), fill='red')
    output_image_path = './screenshot/output_image.png'
    image.save(output_image_path)
    
    output_image_path_iter = './screenshot/output_image_' + str(iter) + '.png'
    image.save(output_image_path_iter)
    return output_image_path


@hydra.main(version_base=None, config_path='configs', config_name='configs')
def main(configs):
    logger = logging.getLogger('colored_logger')


    exp_configs = configs.exp_configs
    instruction = exp_configs.intent
    package_name = exp_configs.package_name

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

    iter = 0
    layout_path = "./layout/layout.xml"
    total_decision_time = 0.
    total_planning_time = 0.
    total_reflection_time = 0.
    total_perception_time = 0.
    total_step = 0
    trial_timer_start = time.time()

    is_locked_state = check_lock_sreen_state(adb_path)
    color_log(f"is_locked_state: {is_locked_state}", logger)
    if is_locked_state:
        unlock_screen(adb_path)
    color_log(f"package_name: {package_name}", logger)
    open_app(adb_path,package_name)

    while True:
        start_time = time.time()
        iter += 1

        if iter == 1:
            screenshot_file = "./screenshot/screenshot.jpg"
            get_screenshot(adb_path)
            get_layout(adb_path)
            temp_image = Image.open(screenshot_file)
            width, height = temp_image.size
            perception_infos = []
            perception_start_time = time.time()
            if os.path.exists(layout_path):
                perception_infos = get_action_list(layout_path, screenshot_file)
                os.remove(layout_path)
            output_image_path_iter = os.path.join(hydra_cfg['runtime']['output_dir'],'screenshot','output_image_' + str(0) + '.png')
            temp_image.save(output_image_path_iter)
            perception_time = time.time() - perception_start_time
            total_perception_time += perception_time
            keyboard = True

        decision_timer_start = time.time()

        prompt_action = get_action_prompt(instruction, perception_infos, width, height, keyboard, summary_history, action_history, summary, action, add_info, error_flag, completed_requirements, memory)
        chat_action = init_action_chat()
        chat_action = add_response("user", prompt_action, chat_action, screenshot_file)

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
            output_memory = query_qwen2_vl(chat_action,logger)
            chat_action = add_response("assistant", output_memory, chat_action)
            status = "#" * 50 + " Memory " + "#" * 50
            color_log(f"status: {status}", logger)
            color_log(f"output_memory: {output_memory}", logger)
            color_log('#' * len(status), logger)
            output_memory = output_memory.split("### Important content ###")[-1].split("\n\n")[0].strip() + "\n"
            if "None" not in output_memory and output_memory not in memory:
                memory += output_memory


        if "Tap" in action:
            coordinate = action.split("(")[-1].split(")")[0].split(", ")
            x, y = int(coordinate[0]), int(coordinate[1])
            tap(adb_path, x, y)

        elif "Swipe" in action:
            coordinate1 = action.split("Swipe (")[-1].split("), (")[0].split(", ")
            coordinate2 = action.split("), (")[-1].split(")")[0].split(", ")
            x1, y1 = int(coordinate1[0]), int(coordinate1[1])
            x2, y2 = int(coordinate2[0]), int(coordinate2[1])
            slide(adb_path, x1, y1, x2, y2)

        elif "Type" in action:
            if "(text)" not in action:
                text = action.split("(")[-1].split(")")[0]
            else:
                text = action.split(" \"")[-1].split("\"")[0]
            type(adb_path, text)

        elif "Back" in action:
            back(adb_path)

        elif "Home" in action:
            home(adb_path)

        elif "Stop" in action:
            break

        time.sleep(5)

        # Reflection stage
        last_perception_infos = copy.deepcopy(perception_infos)
        last_screenshot_file = "./screenshot/last_screenshot.jpg"
        last_keyboard = keyboard
        if os.path.exists(last_screenshot_file):
            os.remove(last_screenshot_file)
        os.rename(screenshot_file, last_screenshot_file)

        get_screenshot(adb_path)
        get_layout(adb_path)
        temp_image = Image.open(screenshot_file)
        width, height = temp_image.size
        perception_infos = []
        if os.path.exists(layout_path):
            perception_infos = get_action_list(layout_path, screenshot_file)
            #center_list = [metadata["coordinates"] for metadata in perception_infos]
            os.remove(layout_path)

        keyboard = True

        # Reflection
        if reflection_switch:
            prompt_reflect = get_reflect_prompt(instruction, last_perception_infos, perception_infos, width, height, last_keyboard, keyboard, summary, action, add_info)
            chat_reflect = init_reflect_chat()
            chat_reflect = add_response_two_image("user", prompt_reflect, chat_reflect, [last_screenshot_file, screenshot_file])


            output_reflect = query_qwen2_vl(chat_reflect,logger)
            reflect = output_reflect[1].split("### Answer ###")[-1].replace("\n", " ").strip()
            chat_reflect = add_response("assistant", output_reflect, chat_reflect)
            status = "#" * 50 + " Reflection " + "#" * 50
            color_log(f"status: {status}", logger)
            color_log(f"output_reflect: {output_reflect}", logger)
            color_log('#' * len(status), logger)

            if 'A' in reflect:
                output_image_path_iter = os.path.join(hydra_cfg['runtime']['output_dir'], 'screenshot',
                                                      'output_image_' + str(0) + '.png')
                temp_image.save(output_image_path_iter)
                thought_history.append(thought)
                summary_history.append(summary)
                action_history.append(action)

                prompt_planning = get_process_prompt(instruction, thought_history, summary_history, action_history, completed_requirements, add_info)
                chat_planning = init_memory_chat()
                chat_planning = add_response("user", prompt_planning, chat_planning)
                output_planning = query_qwen2_vl(chat_planning,logger)
                chat_planning = add_response("assistant", output_planning, chat_planning)
                status = "#" * 50 + " Planning " + "#" * 50
                color_log(status, logger)
                color_log(output_planning, logger)
                color_log('#' * len(status), logger)
                completed_requirements = output_planning[1].split("### Completed contents ###")[-1].replace("\n", " ").strip()

                error_flag = False

            elif 'B' in reflect:
                error_flag = True
                back(adb_path)

            elif 'C' in reflect:
                error_flag = True

        else:
            output_image_path_iter = os.path.join(hydra_cfg['runtime']['output_dir'], 'screenshot',
                                                  'output_image_' + str(0) + '.png')
            temp_image.save(output_image_path_iter)
            thought_history.append(thought)
            summary_history.append(summary)
            action_history.append(action)

            prompt_planning = get_process_prompt(instruction, thought_history, summary_history, action_history, completed_requirements, add_info)
            chat_planning = init_memory_chat()
            chat_planning = add_response("user", prompt_planning, chat_planning)
            output_planning = query_qwen2dot5_int4(chat_planning,logger)
            chat_planning = add_response("assistant", output_planning, chat_planning)
            status = "#" * 50 + " Planning " + "#" * 50
            color_log(status,logger)
            color_log(output_planning,logger)
            color_log('#' * len(status),logger)
            completed_requirements = output_planning[1].split("### Completed contents ###")[-1].replace("\n", " ").strip()

        os.remove(last_screenshot_file)
        step_time = time.time() - start_time
        total_step += step_time
        color_log(f"Iter: {iter} total time: {step_time}", logger, color='yellow')

    kill_app(adb_path,package_name)
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
