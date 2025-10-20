import re
from api.internal_qwen import query_qwen2dot5_int4

class Decision:
    def __init__(self, logger):
        self.logger = logger


    def _get_planning_feedback(self, 
                               intent,
                               current_screen_infos, 
                               thought_actions, 
                               next_screen_infos,
                               progress, 
                               completion_rate,
                               is_trap_in_loop=False):
        messages = []
        messages.append({
            "role": "system",
            'content': "您是一名人工智能助手，负责帮助用户导航手机应用程序并完成特定任务。我们将向您提供当前任务的意图和推理，以及一系列操作及其相应的结果（下一个屏幕截图的描述）。请分析这些信息并选择最合适的操作来完成任务。"
        })

        content = f"""
### 当前任务意图：{intent}
### 当前屏幕截图的描述：{current_screen_infos["description"]}
### 当前任务进度：{progress}
### 当前任务完成率：{completion_rate}

### 操作列表:
"""
        messages.append({
            'role': 'user',
            'content': content
        })

        action_count = 0
        for screen_id, screen_info in enumerate(next_screen_infos):
            #for action_desp in thought_actions[screen_id]['actionList']:
                #action_count+=1
            action_desp = thought_actions[screen_id]['actionDesp']
            layout = screen_info['layout']
            total_description = screen_info['description']['whole']
            description = screen_info['description']
            messages[-1]['content'] += \
                        f"""
* 操作{screen_id+1}:
    * 操作名称 : {action_desp}
    * 下一个屏幕截图的描述: {description}
                        """

        messages[-1]['content'] += \
        f"""\n你的反思应该关注操作的结果（屏幕截图描述），以便决定哪种做法是合适的。

### 输出格式
你的输出应该遵循以下格式：
* 对操作1的反思: <填写操作1的反思>

* 对操作2的反思: ... 

最终决策: <几号操作>
理由: <填写最终决策理由>
无关操作: <true/false>

### 提示
1. 最终决策: 你必须从提供的操作列表中选择一个操作。如果没有一个操作选项看起来是理想的，请选择在当前情况下相对合适的那个。
2. 理由: 如果你发现操作列表中没有好的选项，并且在没有正当理由的情况下被迫做出选择，请使用“相对合适”作为你的理由。
3. 无关操作: 如果你必须选择一个相对合适的最终操作，但该操作与当前任务无关，返回true；否则返回false。
"""
        _, content = query_qwen2dot5_int4(messages, logger=self.logger)
        content = content.replace("：", "").replace(":", "").replace("\n", "").replace(" ", "")
        final_action_id = int(re.search(r"最终决策.*?(\d+).*?理由", content).group(1))
        reasoning_pattern = re.compile(r'对操作%s的反思\s*(.*?)\s*(\*对操作|最终决策)' % final_action_id, re.DOTALL)
        reasoning_match = reasoning_pattern.search(content)
        reasoning = reasoning_match.group(1).strip() if reasoning_match else ''
        is_irrelevant =  re.search(r'无关操作\s*(.*)', content).group(1)[:4] == "true"

        resp = {
            'reasoning': reasoning,
            'final_action_id': final_action_id - 1,
            "is_irrelevant": is_irrelevant
        }

        return resp
        # if final_action_id != 404 else 404


    def get_action_feedback(self, action, next_screen_infos, history):
        """
        i. whether an action is correctly executed
        ii. whether the outcome matches the expectation
        """
        if action['type'] == 'finish':
            history[-2]['description']

        return None

    def get_final_decision(self, intent, layout, thought_actions, next_feedbacks, progress, completion_rate, is_trap_in_loop=False):
        resp = self._get_planning_feedback(intent, layout, thought_actions, next_feedbacks, progress, completion_rate, is_trap_in_loop=is_trap_in_loop)
        return resp