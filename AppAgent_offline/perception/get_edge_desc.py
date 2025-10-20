import os 
from tqdm import tqdm
import pandas as pd
import json
from PIL import Image, ImageDraw
import sys
current_path = os.getcwd()  
print(f"current_path:{current_path}")
sys.path.append(current_path)

from utils import load_json, load_jsonl
from api.internal_qwen import query_intern_vl

ACTION_TYPE_MAP = {
    "click": "点击",
    "swipe up": "向上滑动",
    "swipe down": "向下滑动",
    "swipe right": "向右滑动",
    "swipe left": "向左滑动",
    "edit": "输入",
    "checkable": "勾选",
    "long_click": "长按"
}

def get_edge_desc(edge_img_path, action_types):
    messages = []
    messages.append({
        "role": "system",
        "content": [{'text': 
"""你是一个帮助用户完成手机应用任务的AI助手。你将看到一张包含多个屏幕截图的图像(通常是两个)，代表连续的多个操作步骤（从左到右）。每个截图（除最右侧的截图外）都有一个红色边框标出一个可操作部件，并提供每个步骤操作类型（包括：[点击、滑动、编辑、可检查、长按]）。请用一句话概括整个操作序列。

### 示例
- 示例 1: 点击导航栏中的主页选项卡
- 示例 2: 使用搜索栏搜索“xxx”
- 示例 3: 在设置菜单中选择“账户管理”选项
- 示例 4: 向下滑动音乐列表刷新内容
- 示例 5: 长按列表中的项目以查看更多选项
- 示例 6: 通过侧边栏访问“帮助与支持”页面
- 示例 7: 在弹出窗口中点击“确认”按钮
- 示例 8: 使用导航栏中的“消息”选项卡查看新消息
- 示例 9: 点击“更多”按钮查看详细信息
- 示例 10: 在输入框中输入电子邮件地址，然后点击登录按钮

### 注意
1. 如果屏幕截图无法正确反映操作后的状态（例如，保持不变），请专注于前一个截图和对应的操作类型。
2. 请提供简洁而精准的操作序列描述，避免使用编号列表。
"""}]
    })


    messages.append({
            'role': 'user',
            'content': [{'image': edge_img_path}]
            })

    if len(action_types) > 1:
        action_prompt = "\n".join(
            [f"操作类型{i}: {ACTION_TYPE_MAP[action_type]}" for i, action_type in enumerate(action_types)]
        )
    else:
        action_prompt = f"\n操作类型: {ACTION_TYPE_MAP[action_types[0]]}"

    messages[-1]['content'].append({'text': action_prompt})

    _, content = query_intern_vl(messages, verbose=False, max_tokens=50)
    edge_desc = content.replace("\n", "").replace("：", ":").replace(":", "").strip()
    return edge_desc


def make_edge_img(from_img_path, to_img_path, bboxes, save_path):
    combined_images = []

    for bbox in bboxes:
        from_img = Image.open(from_img_path)
        draw = ImageDraw.Draw(from_img)
        draw.rectangle(bbox, outline="red", width=3)  # Annotate with bounding box
        combined_images.append(from_img)

    combined_images.append(Image.open(to_img_path))

    # Determine the combined width and the maximum height
    total_width = sum(img.size[0] for img in combined_images)
    max_height = max(img.size[1] for img in combined_images)

    # Create a new blank image with the combined width and max height
    edge_img = Image.new('RGB', (total_width, max_height), (255, 255, 255))

    # Paste each image into the combined image
    current_x = 0
    for img in combined_images:
        edge_img.paste(img, (current_x, 0))
        current_x += img.size[0]

    # Save the final combined image
    edge_img.save(save_path)

if __name__ == "__main__":
    package_names = ['com.ctrip.harmonynext', 'com.dragon.read.next', 'com.netease.cloudmusic.hm', 'com.tencent.hm.qqmusic', 'com.sina.weibo.stage', 'com.vip.hosapp']
    #package_names = ['com.gotokeep.keep'] #['com.alipay.mobile.client']
    graph_dir = "/home/app_agent/RAGGeneration_New/data/oracle_test_app_second_stage/"
    for package_name in package_names:
        path_prefix = os.path.join(graph_dir, package_name, 'graph')
        screenshot_dir = os.path.join(path_prefix, 'screenshot')
        node2img = pd.read_csv(os.path.join(path_prefix, 'metadata.csv'), names=['node_id', 'img', 'layout'], index_col='node_id')['img'].to_dict()

        if not os.path.exists(os.path.join(path_prefix, 'edge')):
            os.makedirs(os.path.join(path_prefix, 'edge'))

        edge_dicts = load_json(os.path.join(path_prefix, 'edges.json'))
        print(f'No. of edges: {len(edge_dicts)}')

        edge_desc_file_path = os.path.join(path_prefix, 'edge_desc.jsonl')
        is_file_exist = os.path.exists(edge_desc_file_path)
        existing_edge_desc = {}
        if is_file_exist: 
            existing_edge_desc_list = load_jsonl(edge_desc_file_path)
            for edge_dict in existing_edge_desc_list:
                existing_edge_desc.update(edge_dict)

        with open(edge_desc_file_path, "a" if is_file_exist else "w", encoding="utf-8") as f:
            for edge_id, edge in tqdm(edge_dicts.items()):
                if edge_id in existing_edge_desc:
                    continue
                try:
                    from_img_path = os.path.join(screenshot_dir, node2img[edge['from']])
                    to_img_path = os.path.join(screenshot_dir, node2img[edge['to']])
                    edge_img_path = os.path.join(path_prefix, 'edge', f'{edge_id}.jpeg')
                    if not os.path.exists(edge_img_path):
                        make_edge_img(from_img_path, to_img_path, edge['bboxes'], edge_img_path)
                    edge_desc_dict = {edge_id: get_edge_desc(edge_img_path, edge['action_types'])}
                    print(edge_desc_dict)
                    f.write(json.dumps(edge_desc_dict, ensure_ascii=False) + '\n')
                except:
                    continue