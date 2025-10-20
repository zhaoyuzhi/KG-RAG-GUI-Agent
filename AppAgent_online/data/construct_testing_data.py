import os
import json
from utils.basic_utils import save_jsonl
from utils.draw import plot_image_flow
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

    configs_root = "configs/exp_configs"
    intent_sequence_pair_list = []
    for _package in os.listdir(root):  #selected_package_list:#selected_package_list:#os.listdir(root):

        if not os.path.isdir(os.path.join(root, _package)):
           continue
        zh_package, package, _ = _package.split("---")

        package_list = package.split(".")
        abbr_package = package_list[1]
        if abbr_package == "tencent":
            abbr_package = package_list[3]

        #if package in selected_package_list:
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
                #intent = item['sceneDescription']
            sceneIdList = ast.literal_eval(item['sceneIdList'])
            actionIdList = ast.literal_eval(item['actionIdList'])
            action_trace = item['intention'].split("，")

            #exit(1)
            json_data = {"id": "%s%02d" % (abbr_package, idx), "intent": intent, "sceneIdList": sceneIdList,
                         "actionIdList": actionIdList, "commandList": action_trace, "package": package, "zh_package":zh_package}
            intent_sequence_pair_list.append(json_data)
            temp_intent_sequence_pair_list.append(json_data)
            number +=1
            # if idx != 5:
            #     continue
            # print(item)
            # exit(1)
            # print("intent: ",intent)
            # intent = intent.replace("/", "").replace("\n", "").replace("\"", "")
            # print("after intent: ", intent)
            # img_trace = [os.path.join(package_path, 'screenshot', filename+".jpeg") for filename in sceneIdList]
            # plot_image_flow(img_trace, action_trace,
            #                 os.path.join(package_path, f'%s_img_trace_%02d.png' % (intent, idx)))
            #hydra_cfg = hydra.core.hydra_config.HydraConfig.get()
            # try:
            #     plot_image_flow(img_trace, action_trace,
            #                     os.path.join(package_path, f'%s_img_trace_%02d.png'%(intent,idx)))
            # except:
            #     continue

            json2yaml_data = {"app_name": abbr_package, "package_name": package, "intent": intent,
                              "id": "%s%02d" % (abbr_package, idx)}

            configs_save_path = os.path.join(configs_root, "%s%02d.yaml" % (
            abbr_package, idx))

            with open(configs_save_path, 'w', encoding="utf8") as file:
                yaml.dump(json2yaml_data, file, default_flow_style=False, allow_unicode=True)

        save_jsonl(temp_intent_sequence_pair_list,
                   os.path.join(package_path, "%s_intent_sequence_pair_1125.jsonl" % package))
        package2length[(zh_package,package)] = number
    save_jsonl(intent_sequence_pair_list,
               os.path.join(root, "intent_sequence_pair_1125.jsonl"))  #""%s_intent_sequence_pair.jsonl"%package))

    sorted_dict = dict(sorted(package2length.items(), key=lambda item: item[1],reverse=True))

    for k  in sorted_dict:
        print(k)
    #print(sorted_dict)  # Output: {'b': 1, 'c': 2, 'a': 3}



    #         print(package, len(data_))
    #         if len(data_) > 5:
    #             number += len(data_)
    #             selected_package_list.append(package)

    # print(selected_package_list)
    # print(number)
