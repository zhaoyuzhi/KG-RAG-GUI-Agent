import os
import json
from utils.basic_utils import save_jsonl
from utils.draw import plot_image_flow
import json
import yaml

def load_json(src_=None):
    with open(src_, 'r', encoding='utf-8') as f:
        data_ = json.load(f)
    f.close()
    return data_
# com.alipay.mobile.client 7
# com.chinamobile.cmcc 0
# com.chinarailway.ticketingHM 2
# com.ctrip.harmonynext 4
# com.jd.hm.mall 5
# com.kuaishou.hmapp 1
# com.kugou.hmmusic 5
# com.qiyi.video.hmy 6
# com.sankuai.hmeituan 8
# com.sina.weibo.stage 3
# com.ss.hm.article.news 5
# com.ss.hm.ugc.aweme 6
# com.taobao.taobao4hmos 4
# com.tencent.mtthm 4
# com.tencent.videohm 1
# com.ximalaya.ting.xmharmony 2
# com.xingin.xhs_hos 3

mapping = \
    {
        "com.ss.hm.article.news": "toutiao",
        "com.kugou.hmmusic": "kugou",
        "com.jd.hm.mall" : "jd",
        "com.sankuai.hmeituan": "meituan",
'com.ss.hm.ugc.aweme':"douyin",
"com.alipay.mobile.client": "alipay",
"com.qiyi.video.hmy":"aqiyi",
    }

if __name__ == '__main__':
    # selected_package_list = []
    # root = "true_path_data"
    # for package in os.listdir(root):
    #     if package.startswith("com"):


    number = 0
    root = "data"
    selected_package_list = ['com.qiyi.video.hmy', 'com.sankuai.hmeituan', 'com.ss.hm.ugc.aweme',"com.alipay.mobile.client",'com.ss.hm.article.news','com.kugou.hmmusic', 'com.jd.hm.mall']
    #,'com.kugou.hmmusic', 'com.jd.hm.mall'
    # ['com.ss.hm.article.news','com.kugou.hmmusic', 'com.jd.hm.mall']#,
    #, 'com.qiyi.video.hmy', 'com.sankuai.hmeituan', 'com.ss.hm.ugc.aweme',"com.alipay.mobile.client"
    #, 'com.sankuai.hmeituan', 'com.ss.hm.ugc.aweme',"com.alipay.mobile.client","com.qiyi.video.hmy"

    configs_root = "configs/exp_configs"
    intent_sequence_pair_list = []
    for package in selected_package_list:#selected_package_list:#os.listdir(root):
        # if not package.startswith("com"):
        #     continue

        try:
            abbr_package = mapping[package]
        except:
            abbr_package =  package
        # configs_path = os.path.join(configs_root, abbr_package)
        #
        # if not os.path.exists(configs_path):
        #    os.makedirs(configs_path)

        #if package in selected_package_list:
        package_path = os.path.join(root, package)
        info_path = os.path.join(package_path, "filtered_%s.txt"%package)
        try:
            data_ = load_json(info_path)
        except:
            continue
        for idx, item in enumerate(data_,start=0):
            try:
                intent = item['sceneDescription']
            except:
                print(item)
                print(package)
                continue
                #intent = item['sceneDescription']
            sceneIdList = item['sceneIdList']
            actionIdList = item['actionIdList']
            action_trace = item['commandList']
            # for key, value in item.items():
            #     print(key, value)
            #exit(1)
            json_data = {"id":"%s%02d"%(abbr_package,idx),"intent": intent, "sceneIdList": sceneIdList,"actionIdList":actionIdList,"commandList": action_trace, "package": package}
            intent_sequence_pair_list.append(json_data)
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

            json2yaml_data = {"app_name": abbr_package, "package_name": package, "intent": intent, "id":"%s%02d"%(abbr_package,idx)}
            #configs_save_path = os.path.join(configs_root, abbr_package)
            configs_save_path = os.path.join(configs_root,"%s%02d.yaml"%(abbr_package,idx)) #os.path.join(configs_root, abbr_package)

            with open(configs_save_path, 'w', encoding="utf8") as file:
                yaml.dump(json2yaml_data, file, default_flow_style=False, allow_unicode=True)

                # yaml.dump(json2yaml_data, ff, allow_unicode=True)
                # for key, value in item.items():
                #     print(key, value)
        save_jsonl(intent_sequence_pair_list, os.path.join(root, package, "%s_intent_sequence_pair.jsonl"%package))
    save_jsonl(intent_sequence_pair_list, os.path.join(root, "intent_sequence_pair.jsonl"))#""%s_intent_sequence_pair.jsonl"%package))

    #         print(package, len(data_))
    #         if len(data_) > 5:
    #             number += len(data_)
    #             selected_package_list.append(package)


    # print(selected_package_list)
    # print(number)