import os 
import re
import time
import jpype
import subprocess
from PIL import Image
from utils.draw import color_log

"""
get layout & screenshot
prompt llm/vlm to obtain action list
"""

ACTION_TYPE_MAP = {
    "click": "点击",
    "swipe": "滑动",
    "edit": "输入",
    "checkable": "勾选",
    "long_click": "长按"
}

class PerceptionAgent:
    def __init__(self, logger, adb_path, layout_analyst, screenshot_path='temp/screenshot.jpg', layout_path='temp/layout.xml'):
        self.logger = logger
        self.adb_path = adb_path
        self.screenshot_path = screenshot_path
        self.layout_path = layout_path
        self.layout_analyst = layout_analyst

    def get_layout(self):
        color_log("Extracting layout...", self.logger)
        xml_device_path = "/sdcard/window_dump.xml"
        subprocess.run([self.adb_path, "shell", "uiautomator", "dump", xml_device_path])
        subprocess.run([self.adb_path, "pull", xml_device_path, self.layout_path])
        subprocess.run([self.adb_path, "shell", "rm", xml_device_path])

    def get_screenshot(self):
        color_log("Capturing screenshot...", self.logger)
        command = self.adb_path + " shell rm /sdcard/screenshot.png"
        subprocess.run(command, capture_output=True, text=True, shell=True)
        time.sleep(0.5)
        command = self.adb_path + " shell screencap -p /sdcard/screenshot.png"
        subprocess.run(command, capture_output=True, text=True, shell=True)
        time.sleep(0.5)
        command = self.adb_path + " pull /sdcard/screenshot.png temp"
        subprocess.run(command, capture_output=True, text=True, shell=True)

        # convert png to jpg
        image_path = os.path.join("temp", "screenshot.png")
        image = Image.open(image_path)
        image.convert("RGB").save(self.screenshot_path, "JPEG")
        os.remove(image_path)       

    def get_action_list(self):
        """
        from layout & screenshot to widget_list: [action_type, bbox, desc] 
        """
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

        layout_result = self.layout_analyst.getGraphWidgetsInfo(self.layout_path, self.screenshot_path)
        layout_result_dict = {entry.getKey(): entry.getValue() for entry in layout_result.entrySet()}

        widget_list = {}

        for edge_id, java_widget_info in layout_result_dict.items():
            widget = {
                'xpath': _convert_java_to_python(java_widget_info.getXpath()),
                'actions': _convert_java_to_python(java_widget_info.getActions()),
                'bounds': _convert_java_to_python(java_widget_info.getBounds()),
                'text': _convert_java_to_python(java_widget_info.getText()),
                'img': self.screenshot_path
            }
            widget_list[str(edge_id.split('#')[1])] = widget

        sent_aibrain_param = {
            "img": get_base64(self.screenshot_path),
            "layout": get_file_content(self.layout_path),
            "widgetList": widget_list
        }

        vut_result = request_vut(sent_aibrain_param)

        # print(vut_result.keys())
        # for key, value in vut_result.items():
        #     if key not in ['img', 'layout']:
        #         print(key, value)
        # exit(1)
        action_list  =[]
        for edge_id, widget_info in widget_list['widgetList'].items():
            bounds = widget_info['bounds'].replace('][', ',').replace('[', '').replace(']', '')
            bbox = list(map(int, bounds.split(','))) 

            desc = widget_info.get('widgetDescription', '')
            if not desc: # may not have description
                desc = ACTION_TYPE_MAP[widget_info['actions'][-1].lower()]

            action_list.append(
                dict(    
                action_type=widget_info['actions'][-1],
                bbox=bbox,
                desc=desc,
                )
            )

        return action_list

#     def get_node_desc(self):
#         messages = []
#         messages.append({
#             "role": "system",
#             "content": [{'text': "您是一名人工智能助手，负责帮助视觉障碍用户与手机应用程序进行交互并导航以完成特定任务。"}]
#         })
#         messages.append({
#                 'role': 'user',
#                 'content': [
#                     {
#                         'image': self.screenshot_path
#                     },
#                     {
#                         'text':
# """
# 请详细描述当前屏幕截图，包括布局、可见控件及任何文本或图标。特别强调屏幕上的主要功能和导航线索或互动控件，但不包括最顶部的状态栏，该状态栏包括时间、网络状态、WiFi等信息。请将当前屏幕分为上、中、下三个部分进行分析。不要遗漏任何细节，并列出所有可交互的控件。如果当中出现列表，请把列表里的东西一一列出。
#
# ### 输出格式
# 你的输出应该遵循以下格式：
# 上部描述: <填写屏幕上部描述>
# 中部描述: <填写屏幕中部描述>
# 下部描述: <填写屏幕下部描述>
# 整体描述: <一句话概括屏幕截图的核心功能>
# """
#                 },
#             ]
#             })
#         _, content = query_intern_vl(messages, verbose=False)
#         content = content.replace("\n", "").replace("：", ":").replace(":", "")
#         top_description = re.search(r'上部描述\s*(.*?)\s*中部描述', content).group(1).strip()
#         mid_description = re.search(r'中部描述\s*(.*?)\s*下部描述', content).group(1).strip()
#         bottom_description = re.search(r'下部描述\s*(.*?)\s*整体描述', content).group(1).strip()
#         overall_description = re.search(r'整体描述\s*(.*)', content).group(1).strip()
#
#         resp = {
#             'top': top_description,
#             'mid': mid_description,
#             'bottom': bottom_description,
#             'overall': overall_description
#         }
#
#         return resp