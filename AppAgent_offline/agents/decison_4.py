import re
from api.internal_qwen import query_qwen2dot5_int4

class Decision:
    def __init__(self, logger):
        self.logger = logger


    def get_final_decision(self,
                               intent,
                               graph,
                               possible_trajectories,
                               start_node,
                               progress="",
                               incomplete_milestones=[]):
        messages = []
        messages.append({
            "role": "system",
            'content': "您是一名人工智能助手，负责帮助用户导航手机应用程序并完成特定任务。我们将向您提供当前任务的意图和推理，以及一系列操作及其相应的结果（下一个屏幕截图的描述）。请分析这些信息并选择最合适的操作来完成任务。"
        })
        milestones_text = ""
        for i, milestone in enumerate(incomplete_milestones,start=1):
            milestones_text += \
                f"""* 里程碑 {i}: {milestone} """


        if progress != "":
            content = f"""
### 当前任务意图：{intent}
### 当前屏幕截图的描述：{ graph[start_node]['full_desc']}
### 以下是未完成的里程碑，请按顺序把他们完成: {milestones_text}

### 操作列表:
    """
        else:
            content = f"""
### 当前任务意图：{intent}
### 当前屏幕截图的描述：{graph[start_node]['full_desc']}

### 操作列表:
"""
        messages.append({
            'role': 'user',
            'content': content
        })
        for tid, (trajectory, coarse_score, fine_score) in enumerate(possible_trajectories):
            edge_descs = []
            node_ids = [trajectory[0]]
            for step in trajectory[1:]:
                node_ids.append(step[0])
                edge_descs.append(step[1])
            description = graph[node_ids[-1]]['full_desc']
            action_desp_sequence = ", ".join(edge_descs)
            action_desp_len = len(edge_descs)
            messages[-1]['content'] += \
                        f"""
* 操作序列{tid+1}:
    * 操作名称序列 : {action_desp_sequence}
    * 执行后的屏幕截图的描述: {description}
                        """
#    * 操作名称长度 : {action_desp_len}
        messages[-1]['content'] += \
        f"""\n根据当前任务意图，屏幕截图和未完成里程碑，你的反思应该关注操作名称序列以及执行后的屏幕截图描述。

### 输出格式
你的输出应该遵循以下格式：
* 对操作序列1的反思: <操作1按从里程碑1开始的顺序完成了哪些未完成里程碑，推进了怎样地任务进展>

* 对操作序列2的反思: ... 

观察：<根据上面对每个操作反思，记录你观察到的信息>
最终决策: <几号操作/0>
对应的里程碑列表: [1,...] 


### 提示
1. 最终决策: 该操作按按从里程碑1开始的顺序完成了最多的未完成里程碑，并且执行步骤更少。如果全部操作序列选项都没推进至少一个里程碑的进展，输出0。
2. 对应的里程碑列表: 如果执行最终决策操作后，能够按顺序完成里程碑1和2，则输出[1,2]。如果某个里程碑只有部分完成，则不算完成这个里程碑。
"""
#该操作能够最大化任务进展，按顺序完成了最多的未完成里程碑。
#推进了怎样地任务进展，即完成了按从里程碑1开始顺序执行的哪些里程碑
#以便决定哪种操作完成了最多的哪些未完成里程碑和推进了任务进展
#以便决定哪种操作完成了按从里程碑1顺序执行的最多里程碑和最大化推进了任务进展
        _, content = query_qwen2dot5_int4(messages, logger=self.logger)
        content = content.replace("：", "").replace(":", "").replace("\n", "").replace(" ", "")
        final_action_id = int(re.search(r"最终决策.*?(\d+).*?对应的里程碑列表", content).group(1))
        reasoning_pattern = re.compile(r'对操作序列%s的反思\s*(.*?)\s*(\*对操作|观察)' % final_action_id, re.DOTALL)
        reasoning_match = reasoning_pattern.search(content)
        reasoning = reasoning_match.group(1).strip() if reasoning_match else ''


        if final_action_id != 0:
            # Regular expression pattern to match any list of integers inside square brackets after the phrase "对应的里程碑列表"
            number_pattern = r"对应的里程碑列表\s*.*\[\s*(-?\d+(?:\s*,\s*-?\d+)*)\s*\]"

            # Find the first match
            match = re.search(number_pattern, content)

            # Extract the number list part (the first captured group)
            numbers = match.group(1)
            # Convert the string of numbers to an actual list of integers
            number_list = [int(n) for n in re.findall(r"-?\d+", numbers)]
            #print(number_list)
            print(f" number_list: {number_list}")
            # max_index = 0
            # for index in range(1,len(incomplete_milestones)+1):
            #     if index in number_list:
            #         max_index = index
            #     else:
            #         break
            max_index = min(max(number_list),len(incomplete_milestones))
            completed_milestone_index_list = number_list
        else:
            max_index = len(incomplete_milestones)
            completed_milestone_index_list = []
        #is_irrelevant =  re.search(r'无关操作\s*(.*)', content).group(1)[:4] == "true"

        resp = {
            'reasoning': reasoning,
            'final_action_id': final_action_id - 1,
            "completed_milestone_index": max_index ,
            "completed_milestone_index_list": completed_milestone_index_list,
        }

        return resp
        # if final_action_id != 404 else 404


    # def get_action_feedback(self, action, next_screen_infos, history):
    #     """
    #     i. whether an action is correctly executed
    #     ii. whether the outcome matches the expectation
    #     """
    #     if action['type'] == 'finish':
    #         history[-2]['description']
    #
    #     return None
    #
    # def get_final_decision(self, intent, layout, thought_actions, next_feedbacks, progress, completion_rate, is_trap_in_loop=False):
    #     resp = self._get_planning_feedback(intent, layout, thought_actions, next_feedbacks, progress, completion_rate, is_trap_in_loop=is_trap_in_loop)
    #     return resp