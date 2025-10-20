import hydra
import os
import tqdm
from utils.basic_utils import load_json,save_json
import dashscope
from dotenv import load_dotenv
from easydict import EasyDict as edict
from utils.draw import setup_logger, color_log
from agents import *

@hydra.main(version_base=None, config_path='../configs', config_name='configs')
def main(configs):
    logger = setup_logger()

    # ENVIRONMENT VARIABLES
    load_dotenv()
    QWEN_API_TOKEN = os.getenv("QWEN_API_TOKEN")

    # CONFIGURATION
    configs = edict(configs)
    # memory_dir = configs.memory_dir
    # log_dir = configs.exp_configs.log_dir
    #
    # intent = configs.exp_configs.intent
    # improved_intent = configs.exp_configs.get('improved_intent', None)
    # intent = improved_intent if improved_intent is not None else intent


    # if not os.path.exists(log_dir):
    #     os.makedirs(log_dir)
    #
    # if not os.path.exists(memory_dir):
    #     os.makedirs(memory_dir)

    if not os.path.exists("../temp"):
        os.makedirs("../temp")


    # INIT AGENTS
    dashscope.api_key = QWEN_API_TOKEN

    homepage = "data"
    selected_package_list = ["com.sankuai.hmeituan"]
    #selected_package_list:#
    for package_name in selected_package_list: #tqdm.tqdm(selected_package_list):
        if package_name.startswith("com"):
            root = os.path.join(homepage, package_name)
            if os.path.exists(os.path.join(root,"sid2desc.json")):
                temp = load_json(os.path.join(root, "sid2desc.json"))
                if len(temp) > 0:
                    print("existing {}".format(os.path.join(root, "sid2desc.json")))
                    continue
            file_data = os.path.join(root, package_name + ".json")
            print(file_data)
            try:
                dist_data = load_json(file_data)
            except:
                print("skipping package 2 {}".format(package_name))
                continue
            try:
                observer = Observer(logger,dist_data, path_prefix = root)
            except:
                print("skipping package 3 {}".format(package_name))
                continue
            col_sid_list = observer.df['sid'].tolist()
            print("num of sid: ", len(col_sid_list))
            sid2desc = {}
            print("num of sid2desc: ", len(sid2desc))

            for idx, current_node in tqdm.tqdm(enumerate(col_sid_list)):
                # OBSERVE
                screenshot, screenshot_path = observer.get_screenshot(current_node)
                screen_desc = observer.get_screen_description(screenshot_path)
                # try:
                #     screen_desc = observer.get_screen_description(screenshot_path)
                # except:
                #     print(current_node)
                #     continue
                sid2desc[current_node] = screen_desc

            save_json(sid2desc, os.path.join(root,"sid2desc.json"))


if __name__ == '__main__':
    # root = "true_path_data"
    # for package in os.listdir(root):
    #     if package.startswith("com"):
    main()
