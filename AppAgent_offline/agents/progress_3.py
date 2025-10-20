import re
import json
from api.internal_qwen import  query_qwen2_int4,query_qwen2, query_qwen2dot5_int4
from utils.draw import color_log

class Progress:
    def __init__(self, logger):
        self.logger = logger

    def __call__(self, intent, milestones, graph, history):
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
        if len(history) <= 1:
            messages[-1]['content'] += f"""暂无执行记录
                   """

        for step_id, his in enumerate(history[1:]):
            thought = his['thought']
            trajectory = his['trajectory']
            # progress = his['progress']
            edge_descs = []
            node_ids = [trajectory[0]]
            for step in trajectory[1:]:
                node_ids.append(step[0])
                edge_descs.append(step[1])
            action_desp_sequence = ", ".join(edge_descs)
            last_progress = his['last_progress']
            messages[-1]['content'] += \
    f"""
* 已执行操作序列 (t={step_id + 1})
    * 执行操作之前意图完成进度: {last_progress}
    * 屏幕截图全局描述: {graph[node_ids[0]]['desc']}
    * 操作名称 : {action_desp_sequence}
    * 操作推理 : {thought}
"""

#         messages[-1]['content'] += \
#     f"""
# ### 当前页面
#     * 当前屏幕截图全局描述: {graph[history[-1]["next_node"]]["desc"]}
# """

        messages[-1]['content'] += \
    f"""
### 输出格式
任务执行进度: <基于之前的操作历史和当前页面以及你的观察，总结当前的任务执行进度>
"""
# 已经完成的里程碑: < 基于之前的操作历史，当前页面，你的观察和进度总结，列出按照顺序执行的已经完成的里程碑。你必须按数字大小顺序一步一步执行，不能发生跳跃中间的步骤。比如，如果里程碑2未完成，则不能完成里程碑2之后的里程碑 >
# 完成里程碑的总数目: < 输出一个int整数 >

        _, content = query_qwen2dot5_int4(messages, self.logger)

        content = content.replace("：", "").replace(":", "").replace("\n", "").replace(" ", "").replace("-", "")

        # if len(history) <= 1:
        #     progress = re.search(r"任务执行进度\s*(.*)", content).group(1)
        #     return {'progress': progress, "completion_rate": "%d/%d" % (0, len(milestones)) }
        # else:
        feedback = re.search(r"任务执行进度\s*(.*)", content).group(1) #\s*已经完成的里程碑
        # completion_number = int(re.search(r"完成里程碑的总数目\s*(\d+)\s*", content).group(1))  # (.*)\s*已经完成的里程碑
        # completion_rate = "%d/%d" % (completion_number, len(milestones))
        # feedback = {
        #     'progress': progress,
        #     "completion_rate": completion_rate,
        # }
        return feedback