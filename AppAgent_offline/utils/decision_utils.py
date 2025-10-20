import requests
import json

def request_rag(goal):
    for _ in range(2):
        try:

            request_data = {
                "packageName": "",
                "content": goal,
                "type": "sceneDescription",
                "topK": 3,
                "similarityAlgorithm": "",
                "appDecisionKnowledgeBaseName": "appDecision2"
            }
            headers = {
                'Content-Type': 'application/json'
            }
            response = requests.post("http://10.108.69.250:8977/textRag/queryTopKQualityAssessmentCenterData", headers=headers, data=json.dumps(request_data))
            print(response.text)
            if response.status_code == 200:
                return response.json()["data"]
        except requests.exceptions.RequestException as e:
            print(f"捕捉异常:{e}")
    else:
        print(f"请求rag服务3次失败，返回None")
    return None

# def intention_planning(intention, most_similar_intention, app_name=None, app_desp=None):
#     user_str = f"""
#     你是一位帮助用户完成手机应用任务的AI助手。你将获得一个任务意图，你的任务是分析并将其重写为更清晰明确的意图。此外，你还需要将任务进一步分解为子目标，以引导用户按正确顺序完成任务。
#     当前APP为：{app_name}。APP描述：{app_desp}
#     分析以下提供的原始任务意图并参考相似意图以及对应的milestones。确定它是否可以重新编写化为具有具体、清晰和独特完成条件的任务。
#
#     ### 原始任务意图
#     {intention}
#
#     ### 相似意图
#     意图:{most_similar_intention[0]["sceneDescription"]}
#     milestones:{most_similar_intention[0]["actionSequence"]}
#
#     意图:{most_similar_intention[1]["sceneDescription"]}
#     milestones:{most_similar_intention[1]["actionSequence"]}
#
#     意图:{most_similar_intention[2]["sceneDescription"]}
#     milestones:{most_similar_intention[2]["actionSequence"]}
#
#     ### 输出格式
#     您的输出应遵循以下JSON格式，并确保其可以被Python的`json.loads()`函数解析：
#     ```json
#     {{
#     "milestones": [<在xxx页面xxx>, <在xxx页面xxx>,...]，
#     }}
#     ```
#
#     ### 提示
#     1. "milestones"：将任务分解为用户从APP首页开始必须按顺序完成的子目标或里程碑，以成功完成任务。仅使用原始意图中的信息和相似意图的信息，不要过度解读。"
#     """
#     print(user_str)
#     res = request_qwen(user_str=user_str, max_new_tokens=1000)
#     return res

if __name__ == '__main__':
    #pass
    intention = "支付宝首页通过扫一扫转账"
    res = request_rag(intention)
    print(res)
    # res = rag_intention_planning(intention)
    # print(f"res:{res}")
