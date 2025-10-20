import os 
import re
import json
import time
import subprocess
from PIL import Image
from api.internal_qwen import query_intern_vl, query_qwen2
import pandas as pd
from utils import load_json, color_log, parse, hierarchy_parse, get_all_widget_ids

class Observer:
    def __init__(self, logger, dist_data, path_prefix="dist/static"):
        self.logger = logger
        self.path_prefix = path_prefix
        self.dist_data = dist_data
        self.init_get_metadata()
        self.init_get_desc()

    def init_get_metadata(self):
        if not os.path.exists(os.path.join(self.path_prefix, 'metadata.csv')):
            metadata_list = []
            node_data = self.dist_data["nodes"]
            for sid, node in node_data.items():
                metadata = node["exactScenes"][0]
                img_path = metadata["img"]
                layout_path = metadata["layout"]
                metadata_list.append([sid, img_path, layout_path])
            my_df = pd.DataFrame(metadata_list)
            my_df.to_csv(os.path.join(self.path_prefix, 'metadata.csv'), index=False, header=False)
        self.df = pd.read_csv(os.path.join(self.path_prefix, 'metadata.csv'), names=["sid", "img", "layout"])

    def init_get_desc(self):
        if os.path.exists(os.path.join(self.path_prefix,"sid2desc.json")):
            self.sid2desc = load_json(os.path.join(self.path_prefix,"sid2desc.json"))
        else:
            self.sid2desc = None

    def _reformat_layout(self, xml):
        color_log("Reformatting layout...", self.logger)
        parsed_xml = parse(xml)
        formatted_xml = hierarchy_parse(parsed_xml)
        return formatted_xml

    def get_layout(self, sid):
        # color_log("Getting layout...", self.logger)
        layout_path = self.df.loc[self.df['sid'] == sid].iloc[0]["layout"]
        xml = open(os.path.join(self.path_prefix, "layout", layout_path), 'r', encoding='utf8').read()
        # formatted_layout = self._reformat_layout(xml)
        return xml

    def get_screenshot(self,sid):
        # color_log("Capturing screenshot...", self.logger)
        img_path = self.df.loc[self.df['sid'] == sid].iloc[0]["img"]
        image = Image.open(os.path.join(self.path_prefix, "screenshot", img_path))
        return image, os.path.join(self.path_prefix, "screenshot", img_path)

    def get_screen_description(self, screenshot_path):
        color_log("Generating screenshot description...", self.logger)
        messages = []
        messages.append({
            "role": "system",
            "content": [
                {'text': "您是一名人工智能助手，负责帮助视觉障碍用户与手机应用程序进行交互并导航以完成特定任务。"}]
        })
        messages.append({
            'role': 'user',
            'content': [
                {
                    'image': screenshot_path
                },
                {
                    'text':
"""
请详细描述当前屏幕截图，包括布局、可见控件及任何文本或图标。特别强调屏幕上的主要功能和导航线索或互动控件，但不包括最顶部的状态栏，该状态栏包括时间、网络状态、WiFi等信息。请将当前屏幕分为上、中、下三个部分进行分析。不要遗漏任何细节，并列出所有可交互的控件。如果当中出现列表，请把列表里的东西一一列出。

### 输出格式
你的输出应该遵循以下格式：
上部描述: <填写屏幕上部描述>
中部描述: <填写屏幕中部描述>
下部描述: <填写屏幕下部描述>
整体描述: <一句话概括屏幕截图的核心功能>
"""
                },
            ]
        })
        role, content = query_intern_vl(messages, self.logger)
        # screen_desc_json = re.search(r'```json(.*?)```', content, re.DOTALL).group(1)
        # resp = json.loads(screen_desc_json)

        # messages.append({
        #     'role': role,
        #      'content': [{'text': content}]
        # })

        # messages.append({
        #     'role': 'user',
        #     'content': [{'text': "根据您之前的描述，检查是否遗漏了一些细节。尝试补充缺失的信息，并确保遵循相同的输出格式。"}]
        # })
        # _, content = query_qwen_vl(messages, self.logger)

        content = content.replace("\n", "").replace("：", ":").replace(":", "")

        try:
            top_desciption = re.search(r'上部描述\s*(.*?)\s*中部描述', content).group(1).strip()
        except:
            top_desciption = ""
        try:
            mid_desciption = re.search(r'中部描述\s*(.*?)\s*下部描述', content).group(1).strip()
        except:
            mid_desciption = ""
        try:
            bottom_desciption = re.search(r'下部描述\s*(.*?)\s*整体描述', content).group(1).strip()
        except:
            bottom_desciption = ""
        try:
            total_desciption = re.search(r'整体描述\s*(.*)', content).group(1).strip()  # [:4] == "True"
        except:
            total_desciption = ""

        resp = {
            'top': top_desciption,
            'mid': mid_desciption,
            'bottom': bottom_desciption,
            'overall': total_desciption
        }
        # resp = {
        #     'top': re.search(r'上部描述\s*(.*?)\s*中部描述', content).group(1).strip(),
        #     'mid': re.search(r'中部描述\s*(.*?)\s*下部描述', content).group(1).strip(),
        #     'bottom': re.search(r'下部描述\s*(.*?)\s*ADB', content).group(1).strip(),
        #     'keyboard': re.search(r'ADB Keyboard\s*(.*)', content).group(1)[:4] == "True"
        # }

        return resp

    def get_function_blocks(self, screen_desc, formatted_layout):
        color_log("Generating screenshot function blocks...", self.logger)
        messages = []
        messages.append({
                'role': "system",
                'content': "您是一名人工智能助手，负责帮助用户导航手机应用程序并完成特定任务。"})

        messages.append({
                'role': "user",
                'content': 
f"""
以下是一个类似HTML的文件(包含在<screen></screen>标签中），该文件展示了当前屏幕截图的简化布局。请整合所有可用信息，并列出当前屏幕上所有的功能区域，例如：搜索功能区域、导航栏等。

### 当前屏幕截图的HTML简化布局：
<screen>{formatted_layout}</screen>

### 输出格式
您的输出应遵循以下JSON格式，并确保其可以被Python的`json.loads()`函数解析：
```json
[{{ "name": <功能区域名称>, "description": <功能区域描述>, 
    "widget_list": [{{"widget_id": <控件id>, 
                      "widget_name": <控件名称>, 
                      "action_types": [<行动类型>, ...], 
                      "checked": <true/false/null>}}, ...]
    }}, ...]
```

### 提示
1. widget_list: 在每个功能区域下，请仅列出可交互的控件。不需要显示非交互元素。
2. widget_id：返回在HTML布局中找到的ID或null。
3. widget_name：请提供控件的名称，尽量简化（例如：‘取消按钮’、‘更多选项按钮’、‘发送按钮’等）。如果控件本身包含文本，请直接返回该文本（例如，'首页'图标应返回'首页'）。
4. action_types：从"checkable", "clickable", "scrollable", "long-clickable", "input"中选一个，可以是多个。
5. checked: 如果控件是"checkable"，返回true/false；否则返回null。
""" 
                            })
        role, content = query_qwen2(messages, self.logger)

        messages.append({'role': role, 'content': content})        

        messages.append({'role': 'user', 'content':
f"""
以下是另一位人工智能助手提供的屏幕截图描述，将描述作为布局的补充信息，把布局中未包括的功能区域和控件加到您之前的功能区域描述里，并确保遵循相同的输出格式。

### 当前屏幕描述：
上部描述: {screen_desc['top']}
中部描述: {screen_desc['mid']}
下部描述: {screen_desc['bottom']}
正在输入: {str(screen_desc['keyboard'])}  


### 提示
1. widget_id：布局中未包括控件返回null
2. action_types: 从描述中猜测最可能的行动类型。
"""
                        })

        _, content = query_qwen2(messages, self.logger)
        screen_function_json = re.search(r'```json(.*?)```', content, re.DOTALL).group(1)
        resp = json.loads(screen_function_json)

        # verify to prevent hallucination
        valid_widget_ids = get_all_widget_ids(formatted_layout)        

        # change all string "null" to null
        for block in resp:
            valid_widget_list = []
            for widget in block['widget_list']:
                if widget['widget_id'] in valid_widget_ids:
                    valid_widget_list.append(widget)
                
                if widget['widget_id'] == "null" or widget['widget_id'] == "N/A" or widget['widget_id'] is None:
                    widget['widget_id'] = None
                    valid_widget_list.append(widget)

            block['widget_list'] = valid_widget_list

        # remove function blocks with empty widget_list
        resp = [block for block in resp if block['widget_list']]
        return resp

        
    def __call__(self, sid, is_screen_desc=True, is_screen_functions=False):
        layout = self.get_layout(sid)
        screenshot, screenshot_path = self.get_screenshot(sid)
        if is_screen_desc:
            if self.sid2desc is None:
                screen_desc = self.get_screen_description(screenshot_path)
            else:
                screen_desc = self.sid2desc[sid]
            if is_screen_functions:
                screen_functions = self.get_function_blocks(screen_desc,
                                                            layout)  ## Polish xml layout to get widget_list
                return layout, screen_desc, screen_functions, screenshot
            else:
                return layout, screen_desc, None, screenshot
        else:
            return layout, None, None, screenshot
        