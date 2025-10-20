import os
import json
import jpype
import base64
import requests
import ast
from utils.basic_utils import save_json
from collections import defaultdict
from http import HTTPStatus

os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)
ACTION_TYPE_MAP = {
    "click": "点击",
    "swipe": "滑动",
    "edit": "输入",
    "checkable": "勾选",
    "long_click": "长按"
}

# 初始化参数，开发环境使用，仅用于模拟执行器发起任务的动作
def init_pack_router(params):
    url = "......"
    payload = json.dumps(params)
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    result = response.json()

    temp_result = result["data"]

    return temp_result

def init_router():
    url = "......"
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers)

    if response.status_code != HTTPStatus.OK:
        raise ValueError(' Status code: %s' % (
            response.status_code,
        ))

    result = response.json()

    temp_result = result["data"]

    return temp_result

def get_scene():
    url = "......"
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers)

    if response.status_code != HTTPStatus.OK:
        raise ValueError(' Status code: %s' % (
            response.status_code,
        ))

    result = response.json()

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


    if response.status_code != HTTPStatus.OK:
        raise ValueError(' Status code: %s' % (
            response.status_code,
        ))

    result = response.json()

    temp_result = result["data"]["productAndScenes"]["exactSceneInfoMap"]

    temp_value = list(temp_result.values())[0]

    return temp_value



def save_image(image_base64, screenshot_file):
    # Decode the Base64 string
    image_data = base64.b64decode(image_base64)

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
        if not desc:  # may not have description
            desc = ACTION_TYPE_MAP[widget_info['actions'][-1].lower()]

        action_list.append(
            dict(
                action_type=widget_info['actions'][-1],
                bbox=bbox,
                desc=desc,
                coordinates=coordinates,
                widgetId=edge_id,
            )
        )

    action_list = cluster_and_filter(action_list)

    sorted_action_list = sorted(action_list, key=lambda x: x['coordinates'])

    perception_dict = convert_perception_list2dict_2(sorted_action_list)

    perception_list = []
    index = 0
    for action_type, item_list in perception_dict.items():
        for item in item_list:
            item["index"] = index
            perception_list.append(item)
            index += 1

    return perception_dict, perception_list

def calculate_iou(box1, box2):
    # Calculate the intersection area
    x_left = max(box1[0], box2[0])
    y_top = max(box1[1], box2[1])
    x_right = min(box1[2], box2[2])
    y_bottom = min(box1[3], box2[3])

    if x_right < x_left or y_bottom < y_top:
        return 0.0

    intersection_area = (x_right - x_left) * (y_bottom - y_top)

    # Calculate the areas of the individual boxes
    box1_area = (box1[2] - box1[0]) * (box1[3] - box1[1])
    box2_area = (box2[2] - box2[0]) * (box2[3] - box2[1])

    # Calculate the union area
    union_area = box1_area + box2_area - intersection_area

    # Calculate IOU
    iou = intersection_area / union_area
    return iou

def cluster_and_filter(data):
    # Group by 'desc'
    clusters = defaultdict(list)
    for item in data:
        clusters[(item['desc'],item["action_type"])].append(item)

    # Filter out duplicates with IOU > 0.5
    result = []
    for _, items in clusters.items():
        filtered_items = []
        for item in items:
            bbox1 = item['bbox']
            is_duplicate = False
            for other_item in filtered_items:
                bbox2 = other_item['bbox']
                if calculate_iou(bbox1, bbox2) > 0.5:
                    is_duplicate = True
                    break
            if not is_duplicate:
                filtered_items.append(item)
        result.extend(filtered_items)

    return result

def convert_perception_list2dict_2(perception_infos):
    perception_dict = defaultdict(list)
    for idx, meta_info in enumerate(perception_infos):
        if meta_info['desc'] == "" or meta_info['coordinates'] == (0, 0):
            continue
        if meta_info['action_type'] == "CLICK":  perception_dict["clickable_info"].append(meta_info)
        elif meta_info['action_type'] == "SWIPE":   perception_dict["slideable_info"].append(meta_info)
        elif meta_info['action_type'] == "EDIT": perception_dict["editable_info"].append(meta_info)
        # elif meta_info['action_type'] == "SWIPE": perception_dict["checkable_info"].append(meta_info)
        # elif meta_info['action_type'] == "EDIT": perception_dict["editable_info"].append(meta_info)
            #perception_dict["slideable_info"].append(meta_info)

    return perception_dict

def convert_perception_list2dict(perception_infos):
    perception_dict = defaultdict(list)
    for idx, clickable_info in enumerate(perception_infos):
        if clickable_info['action_type'] == "CLICK" and clickable_info['desc'] != "" and clickable_info['coordinates'] != (0, 0):
            perception_dict["clickable_info"].append(clickable_info)

    for idx, slideable_info in enumerate(perception_infos):
        if slideable_info['action_type'] == "SWIPE" and slideable_info['desc'] != "" and slideable_info['coordinates'] != (0, 0):
            perception_dict["slideable_info"].append(slideable_info)

    return perception_dict
