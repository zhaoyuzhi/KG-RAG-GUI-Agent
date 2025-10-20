import os
import json
from MobileAgent.api import inference_chat, inference_chat_by_qwen
from MobileAgent.chat import add_response, add_response_two_image, init_reference_chat
from MobileAgent.prompt import get_reference_prompt, get_reference_prompt_qwen
from termcolor import colored

API_url = "https://api.openai.com/v1/chat/completions"
token = "sk-......"
qwen_api = "sk-......"

def reformulate_output(description, ind, final=False):
    # 按自然语言的段落格式重新组织描述信息
    if not final:
        reformulated_description = ""
        reformulated_description += f"* 页面{ind}：{description['页面']}\n"
        reformulated_description += f"- 操作：{description['操作']}\n"
        reformulated_description += f"- 思考：{description['思考']}"
    else:
        reformulated_description = f"* 页面{ind}：{description['页面']}"
    return reformulated_description


def process_images(input_dir, img_list, ind, instruction, operation="", final=False):

    # GPT-4o
    prompt_description = get_reference_prompt(instruction, operation, final=final)
    chat_description = init_reference_chat(final=final)

    print(colored(chat_description[0][1][0]['text'], 'yellow'))
    print(colored(prompt_description, 'green'))

    if not final:
        chat_description = add_response_two_image(
            "user", prompt_description, chat_description,
            [os.path.join(input_dir, img_list[0]), os.path.join(input_dir, img_list[1])])
    else:
        chat_description = add_response(
            "user", prompt_description, chat_description, os.path.join(input_dir, img_list[0]))

    description = inference_chat(chat_description, 'gpt-4o', API_url, token)

    # # Qwen-VL
    # prompt_description = get_reference_prompt_qwen(instruction, operation, final=final)
    # print(colored(prompt_description, 'green'))
    # if not final:
    #     description = inference_chat_by_qwen(
    #         prompt_description,
    #         [os.path.join(input_dir, img_list[0]), os.path.join(input_dir, img_list[1])],
    #         'qwen-vl-max',
    #         qwen_api
    #     )
    # else:
    #     description = inference_chat_by_qwen(
    #         prompt_description,
    #         [os.path.join(input_dir, img_list[0])],
    #         'qwen-vl-max',
    #         qwen_api
    #     )

    print(colored(description, 'blue'))

    # 使用json.loads()将字符串转换为字典
    description = description.strip().strip('`').strip('json')
    description = json.loads(description)
    description = reformulate_output(description, ind, final=final)

    return description


# input_dir = '/Users/jinpeng/Desktop/gaode'
# instruction = "使用账号‘cjp990528’和密码‘123456’登录高德地图"
# operation_list = [
#     "点击第二张截图里用红框标记的控件",
#     "点击第二张截图里用红框标记的控件",
#     "点击第二张截图里用红框标记的控件",
#     "在第二张截图里用红框标记的控件中输入“cjp990528”",
#     "在第二张截图里用红框标记的控件中输入“123456”",
#     "点击第二张截图里用红框标记的控件",
#     "点击第二张截图里用红框标记的控件",
# ]

# input_dir = '/Users/jinpeng/Desktop/weibo'
# instruction = "查看微博热搜的第一名"
# operation_list = [
#     "点击第二张截图里用红框标记的控件",
#     "点击第二张截图里用红框标记的控件",
#     "点击第二张截图里用红框标记的控件",
#     "点击第二张截图里用红框标记的控件",
# ]

# input_dir = '/Users/jinpeng/Desktop/用华为音乐播放富士山下'
# instruction = "用华为音乐播放富士山下"
# operation_list = [
#     "点击第二张截图里用红框标记的控件",
#     "在第二张截图里用红框标记的控件中输入“富士山下”",
#     "点击第二张截图里用红框标记的控件",
#     "点击第二张截图里用红框标记的控件",
# ]

# input_dir = '/Users/jinpeng/Desktop/导航到背景音提取页面'
# instruction = "导航到背景音提取页面"
# operation_list = [
#     "点击第二张截图里用红框标记的控件",
#     "点击第二张截图里用红框标记的控件",
# ]

input_dir = '/Users/jinpeng/Desktop/创建一个新的歌单'
instruction = "创建一个新的歌单"
operation_list = [
    "点击第二张截图里用红框标记的控件",
    "左滑第二张截图里用红框标记的控件",
    "点击第二张截图里用红框标记的控件",
    "点击第二张截图里用红框标记的控件",
    "点击第二张截图里用红框标记的控件",
]

all_descriptions = []

for i in range(len(operation_list) + 1):
    if i < len(operation_list):
        img_list = [f"{i + 1}.jpg", f"{i + 1}_w_box.jpg"]
        description = process_images(
            input_dir, img_list, i + 1, instruction, operation_list[i], final=False)
    else:
        img_list = [f"{i + 1}.jpg"]
        description = process_images(
            input_dir, img_list, i + 1, instruction, "", final=True)
    all_descriptions.append(description)

all_descriptions = '\n'.join(all_descriptions)
print(all_descriptions)
with open(os.path.join(input_dir, 'steps.txt'), 'w') as f:
    f.write(all_descriptions)
