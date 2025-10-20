import os
import json
import jpype
import base64
import requests
from collections import OrderedDict,defaultdict

ACTION_TYPE_MAP = {
    "click": "点击",
    "swipe": "滑动",
    "edit": "输入",
    "checkable": "勾选",
    "long_click": "长按"
}

os.environ['JAVA_HOME'] = "C:\Program Files\Huawei\jdk1.8.0_332" #'C:\Program Files\Huawei\jdk1.8.0_332'
jar_path = "apptester-engine-1.4.27-SNAPSHOT-shaded.jar"
java_path = jpype.getDefaultJVMPath()
jpype.startJVM(java_path, "-ea", "-XX:+CreateMinidumpOnCrash", classpath=[jar_path])
layout_analyst = jpype.JClass('com.huawei.hitest.apptester.engine.utils.WindowUtil')


def get_base64(path):
    with open(path, 'rb') as file:
        img_data = file.read()
    encoded_data = base64.b64encode(img_data)
    encoded_string = encoded_data.decode('utf-8')
    return encoded_string


def get_json(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        c = f.read()
    return json.loads(c)


def get_file_content(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        c = f.read()
    return c

from http import HTTPStatus
def request_vut(params):
    url = "http://10.90.86.165:7787/excute_2"
    payload = json.dumps(params)
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    if response.status_code != HTTPStatus.OK:
        raise ValueError(' Status code: %s' % (
            response.status_code,
        ))

    #print("response: ", response.text)
    return response.json()

def get_json(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    return json.loads(content)

def get_file_content(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        c = f.read()
    return c

def get_base64(path):
    # 读取图像文件并转换为二进制数据
    with open(path, 'rb') as file:
        img_data = file.read()
    # 对图像数据进行Base64编码
    encoded_data = base64.b64encode(img_data)
    # 将编码后的数据转换为字符串
    encoded_string = encoded_data.decode('utf-8')
    return encoded_string


def _convert_java_to_python(java_obj):
    if isinstance(java_obj, jpype.JString):
        return str(java_obj)
    elif isinstance(java_obj, jpype.JInt):
        return int(java_obj)
    elif isinstance(java_obj, jpype.JFloat):
        return float(java_obj)
    elif java_obj.getClass().getName() == "java.util.ArrayList":
        return [_convert_java_to_python(item) for item in java_obj]  #
    return java_obj  # Default case

def get_widget_list(layout_path, screenshot_path):
    layout_result = layout_analyst.getGraphWidgetsInfo(layout_path, screenshot_path)
    #print(type(layout_result))
    layout_result_dict = {entry.getKey(): entry.getValue() for entry in layout_result.entrySet()}

    widget_list = {}

    for edge_id, java_widget_info in layout_result_dict.items():
        widget = {
            'xpath': _convert_java_to_python(java_widget_info.getXpath()),
            'actions': _convert_java_to_python(java_widget_info.getActions()),
            'bounds': _convert_java_to_python(java_widget_info.getBounds()),
            'text': _convert_java_to_python(java_widget_info.getText()),
            'img': screenshot_path
        }
        widget_list[str(edge_id.split('#')[1])] = widget

    return widget_list

def get_action_list(layout_path, screenshot_path):
    """
    from layout & screenshot to perception data
    """

    # get the widget_list
    widget_list = get_widget_list(layout_path, screenshot_path)
    print("widget_list", widget_list)
    sent_aibrain_param = {
        "img": get_base64(screenshot_path),
        "layout": get_file_content(layout_path),
        "widgetList": widget_list
    }

    # get the widget description from vut model
    vut_result = request_vut(sent_aibrain_param)
    print("vut_result", vut_result.keys())
    print("vut_widgetList_result", vut_result['widgetList'])

    action_list  = []
    for edge_id, widget_info in vut_result['widgetList'].items():
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

    print("action_list", action_list)

    ## remove duplicated bounding boxes
    action_list = cluster_and_filter(action_list)

    sorted_action_list = sorted(action_list, key=lambda x: x['coordinates'])

    ## generate perception dict based on action type
    perception_dict = convert_perception_list2dict_2(sorted_action_list)

    ## generate perception list
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
