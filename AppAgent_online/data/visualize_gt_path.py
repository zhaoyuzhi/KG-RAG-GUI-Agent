import os
import json
from utils.basic_utils import save_jsonl
from utils.draw import plot_image_flow,plot_image_flow_2
import json
import yaml
import ast
from collections import defaultdict

def load_json(src_=None):
    with open(src_, 'r', encoding='utf-8') as f:
        data_ = json.load(f)
    f.close()
    return data_

if __name__ == '__main__':

    number = 0
    root = "oracle_test_app_second_stage"
    package2length = dict()

    selected_package_list = ["网易云音乐---com.netease.cloudmusic.hm---0515版本"]

    intent_sequence_pair_list = []
    for _package in selected_package_list:#os.listdir(root):
        if not os.path.isdir(os.path.join(root, _package)):
           continue
        zh_package, package, _ = _package.split("---")

        package_list = package.split(".")
        abbr_package = package_list[1]
        if abbr_package == "tencent":
            abbr_package = package_list[3]

        package_path = os.path.join(root, _package,"graph")
        info_path = os.path.join(package_path, "path.json")
        try:
            data_ = load_json(info_path)["paths"]
        except:
            print(f"{info_path} is skipping.")
            continue

        number = 0
        temp_intent_sequence_pair_list  = []
        for idx, item in enumerate(data_, start=0):
            try:
                intent = item['sceneDescription']
            except:
                print(item)
                print(package)
                continue
            sceneIdList = ast.literal_eval(item['sceneIdList'])
            actionIdList = ast.literal_eval(item['actionIdList'])
            action_trace = item['intention'].split("，")

            json_data = {"id": "%s%02d" % (abbr_package, idx), "intent": intent, "sceneIdList": sceneIdList,
                         "actionIdList": actionIdList, "commandList": action_trace, "package": package, "zh_package":zh_package}

            number +=1

            img_trace = [os.path.join(package_path, 'screenshot', filename+".jpeg") for filename in sceneIdList]

            plot_image_flow_2(img_trace, action_trace,
                            os.path.join(package_path, f'%s.png' % (intent)))
