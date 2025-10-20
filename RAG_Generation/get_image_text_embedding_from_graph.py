import requests
import os
import base64
import json
import pickle
from http import HTTPStatus
import glob
from tqdm import tqdm  # 导入 tqdm
from utils import get_img_embedding, get_text_embedding

os.environ['no_proxy'] = "10.90.86.84,10.90.86.141"

def get_img_feature_list():
    feature_list = []
    name_list = []  

    package_list = [
        # 'com.ctrip.harmonynext',
        # 'com.netease.cloudmusic.hm',
        # 'com.sina.weibo.stage',
        # 'com.vip.hosapp'
        'com.dragon.read.next',
        'com.tencent.hm.qqmusic'
    ]

    for package_name in package_list:
        data_dir = f"/home/app_agent/RAGGeneration_New/data/oracle_test_app_second_stage/{package_name}/graph/"
        img_path_list = glob.glob(f'{data_dir}/screenshot/*.jpeg')

        for image_path in tqdm(img_path_list, desc=f"Processing {package_name}", unit="image"):
            
            features = get_img_embedding(image_path)
            
            feature_list.append(features)
            name_list.append(os.path.basename(image_path))

        with open(f'{data_dir}/{package_name}_image_feature.pkl', 'wb') as f:
            pickle.dump((feature_list, name_list), f)



def get_text_feature_list():

    package_list = [
    # #    'com.ctrip.harmonynext',
    #      'com.netease.cloudmusic.hm',
    #      'com.sina.weibo.stage',
    #     'com.vip.hosapp',
    # 
    #    'com.dragon.read.next',
        'com.tencent.hm.qqmusic'
    ]

    for package_name in package_list:
        json_file = f"/home/pp/app_agent/RAGGeneration_New/data/oracle_test_app_second_stage/{package_name}/graph/{package_name}_node_available_path_template.json"
        output_file = f"/home/pp/app_agent/RAGGeneration_New/data/oracle_test_app_second_stage/{package_name}/graph/{package_name}_intention_text_feature.pkl"
          
        with open(json_file, 'r', encoding='utf-8') as f:
            result = json.load(f)

        # 初始化一个字典来存储结果
        result_all = {}
        #
        # 遍历 JSON 数据并提取 template 和生成 feature
        for img_key, template_data in result.items():
            template_list = []
            feature_list = []

            # 遍历每个条目，提取 template 和计算 feature
            for entry in template_data:
                template = entry.get('templates', '')  # 提取 tempolate 字段
                template_list.append(template)  # 将 template 添加到 list
                feature = get_text_embedding(template)  # 获取对应的 feature
                feature_list.append(feature)  # 将 feature 添加到 list
                print(img_key, template, len(feature))

            # 将该图片的结果保存到字典中
            result_all[img_key] = {
                'template_list': template_list,
                'template_feature_list': feature_list
            }
            print(template_list)

        with open(output_file, 'wb') as f:  # Open in binary mode for pickle
            pickle.dump(result_all, f)  # Dump the result as a pickle object
get_img_feature_list()
get_text_feature_list()