import os
import json
from MobileAgent.api import inference_chat, inference_chat_by_qwen
from MobileAgent.chat import add_response, init_reference_summary_chat
from MobileAgent.prompt import get_reference_summary_prompt
from termcolor import colored

API_url = "https://api.openai.com/v1/chat/completions"
token = "sk-......"
qwen_api = "sk-......"

def reformulate_output(documentation):
    # 按自然语言的段落格式重新组织描述信息
    n_steps = len([documentation[key] for key in documentation if '步骤' in key])

    reformulated_documentation = ""
    reformulated_documentation += f"--- 操作文档：如何{documentation['操作意图']} ---\n"
    reformulated_documentation += f"* 起始页面：{documentation['起始页面']}\n"
    reformulated_documentation += f"* 操作步骤：\n"
    for i in range(1, n_steps + 1):
        reformulated_documentation += f"  步骤{i}：\n"
        reformulated_documentation += f"  - 页面：{documentation[f'步骤{i}']['页面']}\n"
        reformulated_documentation += f"  - 操作：{documentation[f'步骤{i}']['操作']}\n"
        reformulated_documentation += f"  - 解释：{documentation[f'步骤{i}']['解释']}\n"
    reformulated_documentation += f"{documentation['总结']}"

    return reformulated_documentation

# steps_path = '/Users/jinpeng/Desktop/gaode/steps.txt'
# documenation_path = '/Users/jinpeng/Desktop/gaode/documentation.txt'
# instruction = "使用账号‘cjp990528’和密码‘123456’登录高德地图"

# steps_path = '/Users/jinpeng/Desktop/weibo/steps.txt'
# documenation_path = '/Users/jinpeng/Desktop/weibo/documentation.txt'
# instruction = "查看微博热搜的第一名"

# steps_path = '/Users/jinpeng/Desktop/用华为音乐播放富士山下/steps.txt'
# documenation_path = '/Users/jinpeng/Desktop/用华为音乐播放富士山下/documentation.txt'
# instruction = "用华为音乐播放富士山下"

# steps_path = '/Users/jinpeng/Desktop/导航到背景音提取页面/steps.txt'
# documenation_path = '/Users/jinpeng/Desktop/导航到背景音提取页面/documentation.txt'
# instruction = "导航到背景音提取页面"

steps_path = '/Users/Desktop/创建一个新的歌单/steps.txt'
documenation_path = '/Users/Desktop/创建一个新的歌单/documentation.txt'
instruction = "创建一个新的歌单"

with open(steps_path, 'r') as f:
    steps = f.read()

prompt_reference_summary = get_reference_summary_prompt(instruction, steps)

# GPT-4o
chat_reference_summary = init_reference_summary_chat()

print(colored(chat_reference_summary[0][1][0]['text'], 'yellow'))
print(colored(prompt_reference_summary, 'green'))

chat_description = add_response(
    "user", prompt_reference_summary, chat_reference_summary)
documentation = inference_chat(chat_description, 'gpt-4o', API_url, token)

# # Qwen2
# documentation = inference_chat_by_qwen(prompt_reference_summary, [], 'qwen2-72b-instruct', qwen_api)

print(colored(documentation, 'blue'))

documentation = documentation.split("```json")[1].split("```")[0]
documentation = reformulate_output(json.loads(documentation))

print(documentation)

with open(documenation_path, 'w') as f:
    f.write(documentation)
    