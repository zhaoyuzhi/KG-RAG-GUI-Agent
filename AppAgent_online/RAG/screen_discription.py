import os
import json
from MobileAgent.api import inference_chat
from MobileAgent.chat import add_response, init_description_chat
from MobileAgent.prompt import get_description_prompt

API_url = "https://api.openai.com/v1/chat/completions"
token = "sk-......"

def save_description(description, output_path):
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(description)


def reformulate_description(description):
    # 按自然语言的段落格式重新组织描述信息
    reformulated_description = ""
    reformulated_description += f"应用类型：{description['应用类型']}\n"
    reformulated_description += f"页面性质：{description['页面性质']}\n"
    reformulated_description += "页面布局：\n"
    for key, value in description['页面布局'].items():
        reformulated_description += f"  * {key}：{value}\n"
    reformulated_description += "页面功能：\n"
    for key, value in description['页面功能'].items():
        reformulated_description += f"  * {key}：{value}\n"
    return reformulated_description


def process_image(image_path):
    prompt_description = get_description_prompt()
    chat_description = init_description_chat()
    chat_description = add_response("user", prompt_description, chat_description, image_path)
    description = inference_chat(chat_description, 'gpt-4o', API_url, token)

    # 使用json.loads()将字符串转换为字典
    description = description.strip().strip('`').strip('json')
    description = json.loads(description)
    description = reformulate_description(description)

    return description


def process_images(input_dir, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    img_list = os.listdir(input_dir)
    img_list.sort()

    i = 0
    while i < len(img_list):
        filename = img_list[i]
        try:
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                image_path = os.path.join(input_dir, filename)

                # prompt_description = get_description_prompt()
                # chat_description = init_description_chat()
                # chat_description = add_response("user", prompt_description, chat_description, image_path)
                # description = inference_chat(chat_description, 'gpt-4o', API_url, token)
                #
                # # 使用json.loads()将字符串转换为字典
                # description = description.strip().strip('`').strip('json')
                # description = json.loads(description)
                # description = reformulate_description(description)

                description = process_image(image_path)

                output_path = os.path.join(output_dir, os.path.splitext(filename)[0] + '.txt')
                save_description(description, output_path)
                print(f'已处理: {filename}, {i + 1}/{len(img_list)}')
            i += 1
        except:
            print(f'处理失败: {filename}')
            i += 1


# # 使用示例
# input_directory = r'E:\Datasets\AppTestAgent\0624HuaweiMusic\all_nodes'
# output_directory = r'E:\Datasets\AppTestAgent\0624HuaweiMusic\all_nodes\descriptions'
#
# process_images(input_directory, output_directory)
