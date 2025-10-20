import re
import json
from api.internal_qwen import query_qwen2

class IntentRewriter:
    def __init__(self, logger):
        self.logger = logger

    def __call__(self, intent):
        messages = []
        messages.append({
                'role': "system",
                'content': '你是一位帮助用户完成手机应用任务的AI助手。你将获得一个任务意图，你的任务是分析并将其重写为更清晰明确的意图。此外，你还需要将任务进一步分解为子目标，以引导用户按正确顺序完成任务。'
                            })
        messages.append({
                'role': "user",
                'content': 
f"""
分析以下提供的原始任务意图。确定它是否可以重新编写化为具有具体、清晰和独特完成条件的任务。

### 原始任务意图
{intent}

### 输出格式
您的输出应遵循以下JSON格式，并确保其可以被Python的`json.loads()`函数解析：
```json
{{ 
"rewritten_intent": <重新编写后任务意图>, 
"milestones": [<子目标1>, <子目标2>,...]，
}}
```

### 提示
1. "rewritten_intent"：将任务意图重写为更清晰明确的表述，不要含糊不清。尽量紧贴原始意图，不要过度解读。
2. "milestones"：将任务分解为用户必须按顺序完成的子目标或里程碑，以成功完成任务。仅使用原始意图中的信息，不要过度解读。"
"""

        # ### 例子
        # 原始任务意图：点击播放按钮开始观看或收听内容
        # ```json
        # {{
        #    "rewritten_intent": 
        #    "milestones:
        # }}
        # ```
                            })
        _, content = query_qwen2(messages, self.logger)
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
"rewritten_intent": <重新编写后任务意图>, 
"milestones": [<子目标1>, <子目标2>,...]，
}}
```
"""})
            _, content = query_qwen2(messages_2, self.logger)
            resp = json.loads(resp)

        return resp['rewritten_intent'], resp['milestones']
    