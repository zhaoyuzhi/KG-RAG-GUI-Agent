import re
import json
from api.internal_qwen import  query_qwen2_int4, query_qwen2dot5_int4
from utils.draw import color_log

class Reflection:
    def __init__(self, logger):
        self.logger = logger

    def __call__(self, intent, milestones, history):
        color_log("Reflection...", self.logger)
        messages = []
        messages.append({
            "role": "system",
            'content': "你是一位帮助用户完成手机应用任务的AI助手。你的任务是总结当前进度并判断任务是否完成。你将获得以下信息：当前任务意图、所有先前操作及其对应的结果（截图描述）。此外，你还会获得一系列里程碑，用于判断任务进度。只有当所有里程碑都达成时，任务才被视为完成。你的任务是总结所有之前的操作，确定哪些里程碑已经达成，哪些尚未达成，并评估整体任务进度。"
        })

        messages.append({
            'role': 'user',
            'content': 
f"""
### 当前任务意图：{intent}
### 以下是需要达成的里程碑，以真正完成任务:
"""
            })

        for i, milestone in enumerate(milestones):
            messages[-1]['content'] += \
f"""
* 里程碑 {i}: {milestone}
"""

        messages[-1]['content'] += \
"""
### 以下是已执行的交互操作和相应的思考过程:
"""

        for step, his in enumerate(history):
            actionDesp = his['action']["actionDesp"]
            thought = his['thought']
            description = his['description']
            messages[-1]['content'] += \
    f"""
* 已执行操作序列 (t={step + 1})
    * 操作名称 : {actionDesp}
    * 操作推理 : {thought}
    * 屏幕截图描述: {description}

"""

        messages[-1]['content'] += \
    f"""
### 当前页面 
    * 当前屏幕截图描述: {history[-1]["next_description"]}
"""

        messages[-1]['content'] += \
"""
### 输出格式
您的输出应遵循以下JSON格式，并确保其可以被Python的`json.loads()`函数解析：
```json
{
  "progress": "<基于之前的操作总结当前的进度>",
  "completion_rate": "<根据已成功完成的里程碑数量计算完成率。例如，如果4个里程碑中有2个达成，完成率应为"2/4">"
  "is_trap_in_loop": <用户是否被困在一个循环中，例如反复执行相同的操作, 如果被困循环，返回true；如果未被困，返回false>,
}
```
"""
#   "is_complete": "<根据任务的当前进度和已定义的结束条件，判断任务是否已完成。如果任务已完成，返回true；如果未完成，返回false>"

        _, content = query_qwen2dot5_int4(messages, self.logger)

        resp_json = re.search(r'```json(.*?)```', content, re.DOTALL).group(1)
        try:
            feedback = json.loads(resp_json)
        except:
            print(resp_json)
            print(type(resp_json))
            feedback = json.loads(resp_json)

        return feedback