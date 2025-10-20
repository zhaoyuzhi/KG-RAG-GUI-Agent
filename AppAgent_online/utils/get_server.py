import os
import json
import jpype
import base64
import requests
import ast
from utils.basic_utils import save_json

ACTION_TYPE_MAP = {
    "click": "点击",
    "swipe": "滑动",
    "edit": "输入",
    "checkable": "勾选",
    "long_click": "长按"
}

def init_router(params):
    url = "......"
    payload = json.dumps(params)
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    result =  response.json()

    temp_result = result["data"]["productAndScenes"]["exactSceneInfoMap"]

    temp_value = list(temp_result.values())[0]

    return temp_value

def execute_action(params):
    url = "......"

    payload = json.dumps(params)
    headers = {
      'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    result = response.json()

    temp_result = result["data"]["productAndScenes"]["exactSceneInfoMap"]

    temp_value = list(temp_result.values())[0]

    return temp_value

def save_image(image_base64, screenshot_file):
    # Decode the Base64 string
    image_data = base64.b64decode(image_base64)

    # screenshot_file = os.path.join(hydra_cfg['runtime']['output_dir'], 'screenshot',
    #                                'output_image_' + str(0) + '.png')  # "./screenshot/screenshot.jpg"

    with open(screenshot_file, "wb") as file:
        file.write(image_data)

def save_layout(layout_string, layout_path):
    dictionary = ast.literal_eval(layout_string)
    save_json(dictionary, layout_path)

def get_action_list(widgetList):
    """
    from layout & screenshot to widget_list: [action_type, bbox, desc]
    """

    action_list  =[]
    for edge_id, widget_info in widgetList.items():
        bounds = widget_info['bounds'].replace('][', ',').replace('[', '').replace(']', '')
        bbox = list(map(int, bounds.split(',')))
        coordinates = [int((bbox[0] + bbox[2]) / 2), int((bbox[1] + bbox[3]) / 2)]
        desc = widget_info.get('widgetDescription', '')
        if not desc: # may not have description
            desc = ACTION_TYPE_MAP[widget_info['actions'][-1].lower()]

        action_list.append(
            dict(
            action_type=widget_info['actions'][-1],
            bbox=bbox,
            desc=desc,
            coordinates = coordinates,
            )
        )

    sorted_action_list = sorted(action_list, key=lambda x: x['bbox'])

    return sorted_action_list
