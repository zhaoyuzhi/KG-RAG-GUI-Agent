import re
import json
from api.internal_qwen import query_qwen2,query_qwen2_int4,query_qwen2dot5_int4
from utils.deicsion_utils import request_rag

class IntentAgent:
    def __init__(self, logger):
        self.logger = logger

    def __call__(self, intent, app_name="",app_desp="",use_rag=False):

        messages = []
        messages.append({
                'role': "system",
                'content': '你是一位帮助用户完成手机应用任务的AI助手。你将获得一个任务意图，你需要将任务进一步分解为子目标，以引导用户按正确顺序完成任务。'
                            })
        #你的任务是分析并将其重写为更清晰明确的意图。此外，你还
        ### 当前任务状态
        # 已经打开相应的APP应用程序，当前处于主页面
        ### 示例 1:
        # 输入: 查看“我的”点赞、收藏记录
        # 输出:
        #
        # ```json
        # {{
        #     "milestones": ["点击个人中心按钮", "点击'收藏'的按钮", "点击'赞过'的按钮"]
        # }}
        # ```
        #
        # ### 示例 2:
        # 输入: 淘宝发送消息
        # 输出:
        #
        # ```json
        # {{
        #     "milestones": ["点击消息通知按钮", "点击点击进入详情页的按钮", "在点击进入详情页的按钮中输入你好",
        #                    "点击发送按钮"]
        # }}
        # ```
        #
        # ### 示例 3:
        # 输入: 浏览首页推荐发现热搜等
        # 输出:
        #
        # ```json
        # {{
        #     "milestones": ["点击'推荐'的按钮", "点击'发现'的按钮", "点击'更多热搜'的按钮"]
        # }}
        # ```
        #
        # ### 示例 4:
        # 输入: 微博搜索查看图片
        # 输出:
        #
        # ```json
        # {{
        #     "milestones": ["点击'发现'的按钮", "点击搜索框",
        #                    "在搜索输入框中输入人民日报"，"点击进入详情页的链接", "点击“图片”的按钮"]
        # }}
        # ```
        #当前APP为：{app_name}。APP描述：{app_desp}
        messages.append({
                'role': "user",
                'content':f"""
### 原始任务意图
{intent}

### 当前任务状态
已经打开APP应用程序，当前处于主页面


分析提供的原始任务意图和检索到的相似示例。确定它是否可以重新编写化为具有具体、清晰和独特完成条件的任务。

### 输出格式
您的输出应遵循以下JSON格式，并确保其可以被Python的`json.loads()`函数解析：
```json
{{ 
"milestones": [<子目标1>, <子目标2>,...]，
}}
```
"""})

        if use_rag:
            most_similar_intention = request_rag(intent)
        else:
            most_similar_intention = None

        if most_similar_intention is not None:
            for idx, item in enumerate(most_similar_intention,start=1):
                messages[-1]["content"] += \
f"""
### 示例 {idx}:
输入: {item["sceneDescription"]}
输出:

```json
{{
    "milestones": {most_similar_intention[0]["actionSequence"]}
}}
```
"""
        else:
            messages[-1]["content"] += \
"""
### 示例 1:
输入: 酷狗音乐查看收藏页面并点击播放全部
输出:

```json
{{
"milestones": ["点击个人中心按钮", "点击'我喜欢'的按钮", "点击播放全部按钮"]
}}
```

### 示例 2:
输入: 今日头条发现页视频浏览
输出:

```json
{{
"milestones": ["点击'发现'的按钮", "点击进入详情页的链接"]
}}
```

### 示例 3:
输入: 京东浏览秒杀和打折团购商品
输出:

```json
{{
"milestones": ["点击京东秒杀按钮", "点击进入商品详情页的按钮", "点击购物车"]
}}
```
"""

        messages[-1]["content"] += \
"""
### 提示
1. 你可以默认已经打开某个应用APP进入主页面，不需要把它作为第一个子目标。
2. 仅使用原始意图中的信息，不要过度解读。
3. 将任务分解为用户必须按顺序完成的子目标，子目标不要过度解读。每个子目标都应包含一个操作(例如：点击、进入)
"""
# ### 示例 1:
# 输入: 酷狗音乐查看收藏页面并点击播放全部
# 输出:
#
#     ```json
# {{
#     "milestones": ["点击个人中心按钮", "点击'我喜欢'的按钮", "点击播放全部按钮"]
# }}  ```
#1. "milestones"：将任务分解为用户必须按顺序完成的子目标或里程碑，以成功完成任务。你必须仅使用原始意图中的信息，不要过度解读。
### 提示
# 1. 不需要要将打开应用作为子目标。
# 2. 仅使用原始意图中的信息，不要过度解读。
# 3.
# 将任务分解为用户必须按顺序完成的子目标。每个子目标都应包含一个操作(例如：点击、进入)。

        # ### 例子
        # 原始任务意图：点击播放按钮开始观看或收听内容
        # ```json
        # {{
        #    "rewritten_intent":
        #    "milestones:
        # }}
        # ```

        #print(messages)
        _, content = query_qwen2dot5_int4(messages, self.logger)
        resp = re.search(r'```json(.*?)```', content, re.DOTALL).group(1)
        try:
            resp = json.loads(resp)
        except:
            messages_2 = []
            messages_2.append({
                'role': "user",
                'content':
                    f"""
原始输出用Python的`json.loads()`函数解析报错，请仔细检查引号并修改保证解析不会报错

### 原始json输出
{resp}

### 输出格式
您的输出应遵循以下JSON格式，并确保其可以被Python的`json.loads()`函数解析：
```json
{{ 
"milestones": [<子目标1>, <子目标2>,...]，
}}
```
"""})
            _, content = query_qwen2(messages_2, self.logger)
            resp = json.loads(resp)

        return intent, resp['milestones']
    