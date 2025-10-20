import time
import re
from http import HTTPStatus
import requests
import json
import base64
#from lmdeploy.serve.openai.api_client import APIClient
import os

os.environ["no_proxy"] = "10.90.86.76"


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def query_intern_vl2(messages, temperature=0., max_tokens=1500):
    intern_messages = []
    for message in messages:
        intern_content = []
        for content in message["content"]:
            
            if "text" in content:
                intern_content.append({
                    "type": "text",
                    "text": content["text"]
                })
            elif "image" in content:
                base64_img = encode_image(messages[1]['content'][0]['image'])
                intern_content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_img}"
                    }
                })
        intern_messages.append({
            "role": message["role"],
            "content": intern_content
        })

    headers = {"Content-Type": "application/json"}
    payload = {
        "model": "internvl2-76b-AWQ",
        "messages": intern_messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    response = requests.post("http://10.90.86.76:10010/v1/chat/completions", headers=headers, json=payload)
    print(response)
    if response.status_code != HTTPStatus.OK:
        raise ValueError('Request id: %s, Status code: %s, error code: %s, error message: %s' % (
            response.request_id, response.status_code,
            response.code, response.message
        ))
    response_output = response.json()
    role, content = response_output['choices'][0]['message']['role'], response_output['choices'][0]['message']['content']

    return role, content

def query_qwen2_vl(messages, temperature=0., max_tokens=1500):
    intern_messages = []
    for message in messages:
        intern_content = []
        for content in message["content"]:
            if "text" in content:
                intern_content.append({
                    "type": "text",
                    "text": content["text"]
                })
            elif "image" in content:
                base64_img = encode_image(messages[1]['content'][0]['image'])
                intern_content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_img}"
                    }
                })
        intern_messages.append({
            "role": message["role"],
            "content": intern_content
        })

    headers = {"Content-Type": "application/json"}
    payload = {
        "model": "Qwen2-72B-Instruct-AWQ",
        "messages": intern_messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    response = requests.post("http://10.90.86.76:9527/v1/chat/completions", headers=headers, json=payload)
    if response.status_code != HTTPStatus.OK:
        raise ValueError('Request id: %s, Status code: %s, error code: %s, error message: %s' % (
            response.request_id, response.status_code,
            response.code, response.message
        ))
    response_output = response.json()
    role, content = response_output['choices'][0]['message']['role'], response_output['choices'][0]['message']['content']

    return role, content

def query_qwen25(messages, temperature=0., max_tokens=1500):
    intern_messages = []
    for message in messages:
        intern_content = []
        for content in message["content"]:
            if "text" in content:
                intern_content.append({
                    "type": "text",
                    "text": content["text"]
                })
        intern_messages.append({
            "role": message["role"],
            "content": intern_content
        })

    headers = {"Content-Type": "application/json"}
    payload = {
        "model": "Qwen2.5-72B",
        "messages": intern_messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    response = requests.post("http://10.90.86.76:5200/v1/chat/completions", headers=headers, json=payload)
    if response.status_code != HTTPStatus.OK:
        raise ValueError('Request id: %s, Status code: %s, error code: %s, error message: %s' % (
            response.request_id, response.status_code,
            response.code, response.message
        ))
    response_output = response.json()
    role, content = response_output['choices'][0]['message']['role'], response_output['choices'][0]['message']['content']

    return role, content

def get_rag_info(app_class="sport"):
    if app_class=="sport":
        exp = \
    """
    1. 浏览推荐动态详情并互动
    2. 关注用户并查看用户详情页
    3. 查看免费直播课程并互动
    4. 浏览全部课程并查看课程详情页
    5. 浏览跑步并开始跑步
    6. 浏览跑步数据
    7. 浏览跑步并开始跑步
    8. 浏览行走详情并行走
    9. 浏览骑行详情并行走
    10. 创建自选课程日程并查看日程详情
    11. 记录饮食并查看饮食详情
    12. 搜索购买会员课程并查看会员课程
    13. 搜索购买畅练卡并继续观看畅练卡专属课
    14. 查看跑步记录详情并分享
    15. 创建训练计划并购买
    1. 切换频道并浏览视频
    2. 搜索视频并观看视频
    3. 观看视频并评论
    4. 下载视频并在本地播放
    5. 收藏视频并从收藏夹中观看视频
    6. 注册并登录账号
    7. 登录老帐号并从浏览历史中继续观看视频
    8. 登录VIP账号并播放VIP视频
    9. 后台播放与通知中心控制
    10. 小窗播放
    11. 购买VIP并播放VIP视频
    12. 购买VIP并播放已下载VIP视频
    13. 播放视频并分享视频
    """
    
    return exp


def single_image_intention_generation(img_path, app_class="sport", model="internvl2"):

    # get rag info
    exp = get_rag_info(app_class)

    # main body
    messages = []
    messages.append({
        "role": "system",
        "content": [{'text': "您是一名人工智能助手，擅长于手机应用程序交互。"}]
    })
    messages.append({
            'role': 'user',
            'content': [
                {
                    'image': img_path
                },
                {
                    'text': 
    """
    ### 任务
    当前图片为一个APP的截图，分析其中的内容，并推理这个APP能够完成的功能。
    """
        },
    ]
    })
    
    messages[-1]["content"][-1]["text"] += \
    """
    ### 输出格式
    您的输出应该遵循以下JSON格式，并确保其可以被Python的`json.loads()`函数解析：
    ```json
    {
        截图内容：<描述屏幕截图显示了什么>
        截图主题：<描述屏幕截图对应的主题>
        功能块：<详细阐述屏幕截图不同板块的功能点>
        APP级意图: [<根据本屏幕截图所提供的信息，创建适用于这个APP的意图1>, <意图2>, <意图3>, ...]
    }
    ```
    """

    messages[-1]["content"][-1]["text"] += \
    f"""
    ### 示例
    您将得到一些适用于这个APP的意图示例：
    {exp}
    """

    messages[-1]["content"][-1]["text"] += \
    """
    ### 提示
    1. 推理得到的“APP级意图”列表的长度通常大于3，但小于9；
    2. “APP级意图”列表中每一条意图应为祈使句，且能够被人理解并在手机上操作，不能含有任何模棱两可的表达；
    3. 请参考提供的示例，编写每一条意图的格式；
    4. 请注意，提供的示例不一定和当前屏幕截图和当前APP匹配，不要抄写提供的示例到“APP级意图”列表中。
    """

    if model=="internvl2":
        role, content = query_intern_vl2(messages, temperature=0., max_tokens=1500)
    if model=="qwen2vl":
        role, content = query_qwen2_vl(messages, temperature=0., max_tokens=1500)
    
    # check format
    resp = re.search(r"```json(.*?)```", content, re.DOTALL).group(1)
    try:
        resp = json.loads(resp)
    except:
        messages_2 = []
        messages_2.append({
            'role': "user",
            'content':
        f"""
        原始输出用Python的`json.loads()`函数解析报错，请仔细检查引号并修改保证解析不会报错

        ### 原始json输出
        {resp}

        ### 输出格式
        您的输出应遵循以下JSON格式，并确保其可以被Python的`json.loads()`函数解析：
        ```json
        {{ 
        "milestones": [<子目标1>, <子目标2>,...]，
        }}
        ```
        """})
        _, content = query_qwen25(messages_2)
        resp = json.loads(resp)

    return resp["APP级意图"]

if __name__ == '__main__':
    
    from glob import glob 

    package_list = [
    #                 'com.app.xt.retouch',
    #                 'com.autohome.main',
    #                 'com.beike.hongmeng',
    #                 'com.cmbchina.harmony',
    #                 'com.ctrip.harmonynext',
    #                 'com.dragon.read.next',
    #                 'com.netease.cloudmusic.hm',
    #                 'com.sina.weibo.stage',
    #                 'com.sinovatech.unicom.ha',
    #                'com.tencent.hm.news',
                    'com.tencent.hm.qqmusic',
                    'com.vip.hosapp', 
                    'com.youku.next', 
                    'com.zhihu.hmos',
                    'me.ele.eleme']
    
    #package_name = "com.sankuai.hmeituan"
    for package_name in package_list:
        img_dir= f"/home/pp/app_agent/RAGGeneration_New/data/oracle_test_app_second_stage/{package_name}/graph/"
        img_list = glob(f"{img_dir}/screenshot/*.jpeg")
        image_data = {}
        for img_path in img_list[:]:
            content = single_image_intention_generation(img_path=img_path, app_class="sport", model="internvl2")
            image_data[os.path.basename(img_path)] = content
            print(img_path, content, flush=True)
        
        with open(f'{img_dir}/{package_name}_intent.json', 'w') as json_file:
            json.dump(image_data, json_file, ensure_ascii=False, indent=4)
