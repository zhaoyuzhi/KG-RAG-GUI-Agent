import copy
from MobileAgent.api import encode_image


def init_action_chat():
    operation_history = []
    system_prompt = f"""你是一个擅长操作智能手机的AI助手。用户会说明他希望达成的操作意图并给你两张图片，第一张为手机当前界面的截图，第二张则在其基础上标注了控件的编号。你需要帮助用户确定接下来的单步操作。"""
    # system_prompt = f"""你是一个擅长操作智能手机的AI助手。用户会说明他希望达成的操作意图并给你三张图片，第一张为手机当前界面的截图，第二张在其基础上标注了控件的编号，第三张则在其基础上加了坐标线。你需要根据这三张截图和用户要求来确定接下来的单步操作。"""
    operation_history.append(["system", [{"type": "text", "text": system_prompt}]])
    return operation_history


def init_description_chat():
    operation_history = []
    # system_prompt = f"""你是一个擅长描述智能手机界面的AI助手。用户会给你一张手机界面的截图，你需要根据用户的要求从多个方面描述这张截图的内容。"""
    system_prompt = f"""你是一个专注于智能手机界面描述的AI助手。用户会提供一张手机界面的截图，你需要根据用户的要求从应用类型、页面性质、页面布局和页面功能四个方面进行描述。你的描述应避免包含具体的实时数据，聚焦于页面结构和功能性方面。

请特别注意以下几点：
1. 忽略页面顶部的状态栏或任何实时变化的内容。
2. 描述内容应尽可能泛化，避免提及具体应用或特定内容，集中于类似页面的共性。
3. 确保描述清晰、有条理，便于理解和分析。

你的描述应能帮助用户理解页面的结构和功能，而无需了解具体的实时信息或应用名称。"""
    operation_history.append(["system", [{"type": "text", "text": system_prompt}]])
    return operation_history


# def init_reference_chat(final=False):
#     operation_history = []
#     system_prompt = "你是一个专注于智能手机操作描述和理解的AI助手。"
#     if not final:
#         # system_prompt += f"""用户会提供两张手机界面的截图，并告知你为了完成某个操作意图，领域专家会在第一张截图中的界面如何操作，从而去往第二张截图的界面。你需要根据用户的要求描述第一张截图呈现的初始界面，并根据操作意图和两张截图描述用户的操作、解释该操作的逻辑原因和操作后实现的效果。
#         # system_prompt += f"""你是一个专注于智能手机操作描述和理解的AI助手。用户会提供两张手机界面的截图，并告知你为了完成某个操作意图，领域专家会在第一张截图中的界面如何操作，从而去往第二张截图的界面。你的任务是根据用户的要求，详细描述页面，分析并理解领域专家的操作。
#         system_prompt += f"""你是一个专注于智能手机操作描述和理解的AI助手。用户会提供两张手机界面的截图，并告知你为了完成某个操作意图，领域专家会在第一张截图中的界面如何操作，从而去往第二张截图的界面。你的任务是根据用户的要求，详细描述页面，分析并理解领域专家的操作。
#
# 请特别注意以下几点：
# 1. 用户可能会在第一张截图中画框来指明领域专家的操作，但你在描述页面或操作时应假定用户画的框不存在，不要提及它们。
# 2. 注意区分用户画的框和实际被选中的控件，避免混淆。
# 3. 如果页面的顶部有状态栏或底部有“ADB Keyboard {"ON"}”的字样，请忽略这些部分，描述时不需要提及。
# 4. 描述时应重点关注与操作意图和领域专家的操作逻辑相关的信息，可能包括页面的性质、功能，以及标签或复选框的选中情况等。
# 5. 在描述操作或结果时，避免使用“第一张截图”或“第二张截图”等字眼，而是直接描述操作和结果。
# 6. 描述效果时，不要使用将来时，而是以操作完成后的口吻进行描述。"""
#     else:
#         # system_prompt += "用户会提供一张手机界面的截图，它是人类操作者完成某个操作意图后达到的最终页面。你需要描述截图中呈现的界面，并着重于和操作意图有逻辑关联的信息，可能包括页面的性质、功能，以及标签或复选框的选中情况等。"
#         system_prompt += "用户会提供一张手机界面的截图，它是领域专家完成某个操作意图后达到的最终页面。你需要根据用户的要求描述页面。请注意，描述时应重点关注与操作意图逻辑相关的信息，可能包括页面的性质、功能，以及标签或复选框的选中情况等。"
#     operation_history.append(["system", [{"type": "text", "text": system_prompt}]])
#     return operation_history


def init_reference_chat(final=False):
    operation_history = []
    system_prompt = "你是一个专注于智能手机操作描述和理解的AI助手。用户会给你一张或多张手机界面的截图，并告诉你领域专家为了达成某一意图时的单步操作。你需要根据用户的要求准确的描述页面和领域专家的操作，并分析领域专家的推理过程。"

    system_prompt += """请特别注意以下几点：
1. 如果页面的顶部有状态栏或底部有“ADB Keyboard {ON}”的字样，请忽略这些部分，描述时不需要提及。
2. 描述页面时应重点关注与操作意图和领域专家的操作逻辑相关的信息，可能包括页面的性质、功能，以及标签或复选框的选中情况等。
3. 在描述操作时，避免使用“第一张截图”或“第二张截图”等字眼，而是直接描述操作。
4. 如果用户借由画框来指示操作，你在描述时应当忽略此类框，而是描述实际的操作。"""

    operation_history.append(["system", [{"type": "text", "text": system_prompt}]])
    return operation_history


def init_reference_summary_chat():
    operation_history = []
    # system_prompt = "你是一个专注于分析理解领域专家对智能手机应用操作并归纳操作文档的AI助手。"
    system_prompt = "你是一个专注于分析和归纳领域专家在使用智能手机应用时操作步骤并形成操作文档的AI助手。"
    # system_prompt += "用户会提供领域专家在完成某一操作意图时经历的页面和执行的操作，并描述领域专家对每一步操作的思考过程。你的任务是基于这些信息，提取出通用的操作文档，帮助不熟悉该App或类似App操作逻辑的用户顺利实现类似的操作意图。请注意，你的文档应当将操作意图和流程泛化，不仅限于领域专家操作时的初始页面或唯一的操作意图，而是应引导用户熟悉操作逻辑以实现所有相似的意图。\n\n"
    # system_prompt += "用户会提供领域专家在完成某一操作意图时经历的页面和执行的操作，并描述领域专家对每一步操作的思考过程。你的任务是基于这些信息，提取出通用的操作文档，帮助不熟悉该App或类似App操作逻辑的用户顺利实现类似的操作意图。请注意，你的文档应当将操作意图和流程泛化，不仅限于领域专家操作时的初始页面或唯一的操作意图，而是应引导用户熟悉操作逻辑以实现所有相似的意图。你的文档应注重帮助用户理解操作背后的逻辑，以便他们能举一反三，适应其他相关操作。\n\n"
    # system_prompt += "用户会提供领域专家在完成某一操作意图时经历的页面和执行的操作，并描述领域专家对每一步操作的思考过程。你的任务是基于这些信息，提取出通用的操作文档，帮助不熟悉该App或类似App操作逻辑的用户顺利实现类似的操作意图。请注意，你的文档应当将操作意图和流程泛化，不仅限于领域专家操作时的初始页面或唯一的操作意图，也不应该以特定操作意图举例，而是应引导用户熟悉操作逻辑以实现所有相似的意图。你的文档应注重帮助用户理解操作背后的逻辑，以便他们能举一反三，适应其他相关操作。\n\n"
    # system_prompt += "用户会提供领域专家在完成某一操作意图时经历的页面和执行的操作，并描述领域专家对每一步操作的思考过程。你的任务是基于这些信息，提取出通用的操作文档，帮助不熟悉该App或类似App操作逻辑的用户顺利实现类似的操作意图。\n\n"
    system_prompt += "用户会提供领域专家在实现某个操作意图时经过的页面、执行的操作步骤及其思考过程。你的任务是根据这些信息提取出适用于一般用户的通用操作文档，帮助他们在不熟悉该App或类似App操作逻辑的情况下顺利完成类似操作。\n\n"

#     system_prompt += """请特别注意以下几点：
# 1. 操作意图和流程应该是泛化的，不应该局限于领域专家操作时的意图，而是应该能适应所有类似的意图。
# 2. 页面描述不应提及那些看起来是个性化的、实时的推荐内容或标签。无论任何用户在任何时间开启该页面，你的描述都应该适用。
# 3. 你的文档应注重帮助用户理解操作背后的逻辑，以便他们能举一反三，适应其他相关操作。"""

    system_prompt += """请特别注意以下几点：
1. 操作意图和流程应具有泛化性，不应该局限于领域专家操作时的意图，而是应该能适应所有类似的意图。
2. 页面描述中出现的实时或个性化内容及控件应被抽象处理，以便任何用户在任何时间查看时都能适用。
3. 文档应注重解释操作背后的逻辑和原因，帮助用户理解并能够在类似情况下举一反三。"""

# 你的文档应注重帮助用户理解操作背后的逻辑，以便他们能举一反三，适应其他相关操作。请提供详细的操作步骤和解释，并以JSON格式输出，确保格式规范并便于解析。"""

    operation_history.append(["system", [{"type": "text", "text": system_prompt}]])
    return operation_history


def init_reflect_chat():
    operation_history = []
    sysetm_prompt = "You are a helpful AI mobile phone operating assistant."
    operation_history.append(["system", [{"type": "text", "text": sysetm_prompt}]])
    return operation_history


def init_memory_chat():
    operation_history = []
    sysetm_prompt = "You are a helpful AI mobile phone operating assistant."
    operation_history.append(["system", [{"type": "text", "text": sysetm_prompt}]])
    return operation_history


def add_response(role, prompt, chat_history, image=None):
    new_chat_history = copy.deepcopy(chat_history)
    if image:
        base64_image = encode_image(image)
        content = [
            {
                "type": "text", 
                "text": prompt
            },
            {
                "type": "image_url", 
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}"
                }
            },
        ]
    else:
        content = [
            {
            "type": "text", 
            "text": prompt
            },
        ]
    new_chat_history.append([role, content])
    return new_chat_history


def add_response_two_image(role, prompt, chat_history, image):
    new_chat_history = copy.deepcopy(chat_history)

    base64_image1 = encode_image(image[0])
    base64_image2 = encode_image(image[1])
    content = [
        {
            "type": "text", 
            "text": prompt
        },
        {
            "type": "image_url", 
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image1}"
            }
        },
        {
            "type": "image_url", 
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image2}"
            }
        },
    ]

    new_chat_history.append([role, content])
    return new_chat_history


def print_status(chat_history):
    print("*"*100)
    for chat in chat_history:
        print("role:", chat[0])
        print(chat[1][0]["text"] + "<image>"*(len(chat[1])-1) + "\n")
    print("*"*100)