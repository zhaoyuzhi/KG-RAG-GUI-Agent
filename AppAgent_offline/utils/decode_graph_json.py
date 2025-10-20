# encoding: utf-8
from dataclasses import dataclass, field
from typing import Dict, List, Set, Type
import re
import numpy as np
import json

ACTION_TYPE_MAP = {
    "CLICK": "点击",
    "SWIPE": "滑动",
    "EDIT": "输入",
    "CHECKABLE": "勾选",
    "LONG_CLICK": "长按"
}

REMOVE_RE = re.compile(r'[·’!"\#$%&\'()＃！（）*+,-./:;<=>?\@，：?￥★、…．＞【】［］《》？“”‘’\[\\\]^_`{|}~]+')

def load_json(src_=None):
    with open(src_, 'r', encoding='utf-8') as f:
        data_ = json.load(f)
    f.close()
    return data_

def remove_rt_desp(widget_desp):
    if not widget_desp:
        return
    if "\r" in widget_desp:
        widget_desp.replace("\r", "")
    if "\t" in widget_desp:
        widget_desp.replace("\t", "")
    widget_desp_filtered = widget_desp.strip()
    return widget_desp_filtered

class Widget:
    def __init__(self, widget_id, widget_text, widget_description, widget_label, widget_block_id):
        self.widget_id = widget_id
        self.widget_text = widget_text
        self.widget_description = widget_description
        self.widget_label = widget_label
        self.widget_block_id = widget_block_id

class Block:
    def __init__(self, widget_block_id, widget_label):
        self.widget_block_id = widget_block_id
        self.widget_label = widget_label

class Action:
    def __init__(self, scene_id, action_id, action_description, action_list,
                 combined_action_description=None, widget_id=None, action_type=None):
        self.from_id = scene_id
        self.action_id = action_id
        self.action_description = action_description
        self.action_list = action_list
        self.combined_action_description = combined_action_description
        self.widget_id = widget_id
        self.action_type = action_type

    def get_combined_action_description(self, widget_dict:  Dict[str, Widget]):
        if any(x["action"] == "EDIT" for x in self.action_list):
            for action_item in self.action_list[::-1]:
                cur_widget_id = action_item["widgetId"]
                action_type = action_item["action"]
                if action_type != "EDIT":
                    continue
                content = action_item.get("content", "")
                for widget_id, widget_info in widget_dict.items():
                    if widget_id != cur_widget_id:
                        continue
                    widget_description = widget_info.widget_description
                    if not widget_description:
                        continue
                    command = None
                    if action_type == "EDIT":
                        command = f"在{widget_description.strip()}中{ACTION_TYPE_MAP[action_type]}{content}"
                    else:
                        if action_type in ACTION_TYPE_MAP:
                            command = ACTION_TYPE_MAP[action_type] + widget_description
                    if command:
                        self.combined_action_description = command
                    else:
                        self.combined_action_description = ""
                    self.widget_id = widget_id
                    self.action_type = action_type
                    break
                else:
                    continue
                break
        else:
            for action_item in self.action_list[::-1]:
                cur_widget_id = action_item["widgetId"]
                action_type = action_item["action"]
                content = action_item.get("content", "")
                for widget_id, widget_info in widget_dict.items():
                    if widget_id != cur_widget_id:
                        continue
                    widget_description = widget_info.widget_description
                    if not widget_description:
                        continue
                    command = None
                    if action_type == "EDIT":
                        command = f"在{widget_description.strip()}中{ACTION_TYPE_MAP[action_type]}{content}"
                    else:
                        if action_type in ACTION_TYPE_MAP:
                            command = ACTION_TYPE_MAP[action_type] + widget_description
                    if command:
                        self.combined_action_description = command
                    else:
                        self.combined_action_description = ""
                    self.widget_id = widget_id
                    self.action_type = action_type
                    break
                else:
                    continue
                break

@dataclass
class SceneDescription:
    page_desp: str
    scene_id: str
    exact_scene_id: str
    scene_img: str
    scene_layout: str
    raw_info: field(default_factory=dict)
    widget_dict: Dict[str, Widget] = field(default_factory=dict)
    scene_action_dict: Dict[str, Action] = field(default_factory=dict)
    block_dict: Dict[str, Block] = field(default_factory=dict)
    operated_widgets: Set[str] = field(default_factory=set)
    desp_vec: np.ndarray = field(default=None)

    @staticmethod
    def make_from_scene_raw_info(scene_info):
        raw_info = scene_info
        scene_id = scene_info["sceneId"]
        exact_scene_id = scene_info["exactSceneId"]
        # page_desp = scene_info["uiDescription"] if scene_info.get("uiDescription") is not None else ""
        page_desp = scene_info["uiDescription"] if scene_info.get("uiDescription") is not None else \
            scene_info.get("label", "")
        scene_img = scene_info['img']
        scene_layout = scene_info['layout']
        desp_obj = SceneDescription(page_desp, scene_id, exact_scene_id, scene_img, scene_layout, raw_info)
        desp_obj.desp_vec = np.array(scene_info["uiDescriptionVector"]) \
            if scene_info.get("uiDescriptionVector") is not None else None

        for widget_id, widget_info in scene_info["widgetList"].items():
            widget_description = remove_rt_desp(widget_info.get("widgetDescription", ""))
            widget_text = widget_info.get("text", "")
            widget_label = widget_info.get("widgetLabel", "")
            widget_block_id = widget_info.get("widgetBlockId")
            desp_obj.widget_dict[widget_id] = Widget(widget_id,
                                                     widget_text,
                                                     widget_description,
                                                     widget_label,
                                                     widget_block_id
                                                     )

        for scene_action_item in scene_info["sceneActionList"]:
            action_description = scene_action_item.get("actionDescription", "")
            action_id = scene_action_item.get("actionId")
            action_list = scene_action_item.get("actionList")
            if not action_id or not action_list:
                continue
            action_obj = Action(scene_id, action_id, action_description, action_list)
            action_obj.get_combined_action_description(desp_obj.widget_dict)
            desp_obj.scene_action_dict[action_id] = action_obj
        return desp_obj

class SpecificKg:
    def __init__(self, kg_data_all):
        self.kg_data_all = kg_data_all
        self.data_nodes = self.kg_data_all["nodes"]
        self.data_edges = self.kg_data_all["edges"]
        self.scenes_desp = {}

    def get_scene_desp_dict(self):
        for scene_id, info in self.data_nodes.items():
            desp_obj = SceneDescription.make_from_scene_raw_info(info["exactScenes"][0])
            if desp_obj:  # 判断是否desp_obj为空
                self.scenes_desp[scene_id] = desp_obj

    def fill_scene_action_list_in_desp_obj(self):
        for edges_item in self.data_edges:
            from_scene_id = edges_item.get("from")
            to_scene_id = edges_item.get("to")
            if not from_scene_id or not to_scene_id:
                continue
            if from_scene_id not in self.scenes_desp.keys():
                continue
            from_scene_obj = self.scenes_desp[from_scene_id]
            for event_item in edges_item["events"]:
                cur_event_action_id = event_item.get("actionId")
                if not cur_event_action_id:
                    continue
                for action_id, action_info in from_scene_obj.scene_action_dict.items():
                    if cur_event_action_id != action_id:
                        continue
                    self.scenes_desp[from_scene_id].scene_action_dict[action_id].to_id = to_scene_id

if __name__ == "__main__":
    json_path = "com.gotokeep.keep/dist/static/com.gotokeep.keep.json"
    kg_data = load_json(src_=json_path)
    kg_obj = SpecificKg(kg_data)
    kg_obj.get_scene_desp_dict()
    kg_obj.fill_scene_action_list_in_desp_obj()
    for key, value in kg_obj.scenes_desp["C1893860D5224DC16D4ED551E76CC753"].scene_action_dict.items():
        print(key, value.get_combined_action_description)
        