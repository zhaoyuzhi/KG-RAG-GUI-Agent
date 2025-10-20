import cv2
import imageio
import os
import numpy as np
from PIL import Image
from utils.basic_utils import load_json
# img_path = "D:\\PycharmProjects\\AppAgent_offline-dev2\\logs\\aqiyi04_浏览综艺频道视频并播放\\visualization\\trace_step_0.png"
# print(img_path)
# img = cv2.imread(img_path)
# print(img)
# exit(0)

# 图片路径
# image_folder = 'logs\\aqiyi04_浏览综艺频道视频并播放\\visualization'  # 替换为你的图片文件夹路径
# images = [img for img in os.listdir(image_folder)][:10] # if img.endswith(".png") or img.endswith(".jpg")
# images.sort()  # 根据文件名排序
# print(images)
# # 创建GIF
# gif_images = []
# for i in range(1, len(images) + 1):
#     img_path = os.path.join(image_folder, images[i-1])
#     print(img_path)
#     if not os.path.exists(img_path):
#         print(f"Error: The file path {img_path} does not exist.")
#     else:
#         print("File path is correct.")
#     #img = cv2.imread(img_path)
#     img = Image.open(img_path)
#     img = img.convert('RGB')
#     if img is None:
#         print("Error: Image not loaded correctly.")
#     else:
#         print("Image loaded successfully.")
#     print(img)
#     gif_images.append(img)  # 转换为RGB格式
# print(gif_images)
#
# # 保存为GIF
# imageio.mimsave('output3.gif', gif_images, fps=1)  # 设置每帧持续时间
import shutil
from PIL import Image, ImageDraw, ImageFont
import tqdm

# Function to resize images to the nearest size divisible by 16
def resize_image(image, size=(1280, 2720)):
    return image.resize(size)

if __name__ == '__main__':

    #pre_root = os.path.join("logs", "aqiyi04_浏览综艺频道视频并播放")
    #pre_root = os.path.join("logs","2024-10-08","13-07-53") #"zhangduo_data"
    pre_root = os.path.join("logs", "2024-10-14", "15-13-03")
    new_data_root = "demo_privacy_data_2"
    for package_data in tqdm.tqdm(os.listdir(pre_root)):
        intent = package_data.split("_")[1]
        os.makedirs(os.path.join(new_data_root, package_data), exist_ok=True)
        final_output_path = os.path.join(new_data_root, package_data,'%s.gif'%intent)
        if os.path.exists(final_output_path):
            continue

        pre_root_ = os.path.join(pre_root, package_data)
        data = load_json( os.path.join(pre_root_, "trace_predict.json"))
        temp_folder = os.path.join(pre_root_, "temp")
        package = data["package"]
        if not os.path.exists(temp_folder):
            os.makedirs(temp_folder, exist_ok=True)
            img_list = data["sceneIdList"]
            action_trace = data["action_trace"]
            #root = os.path.join("utgs","com.qiyi.video.hmy")
            root = os.path.join("utgs", package)
            edge_dicts = load_json(os.path.join(root, 'edges.json'))
            gt_bounding_boxes_list = [edge_dicts[item["actionId"]]["bboxes"] for item in action_trace]
            num_actions = len(action_trace)
            for idx, img_path in enumerate(img_list):
                source_file = os.path.join(root,"screenshot",img_path)
                destination_file = os.path.join(temp_folder, "img_%d.jpeg" % idx)
                shutil.copy2(source_file, destination_file)
                img = Image.open(destination_file)
                if idx < num_actions:
                    draw = ImageDraw.Draw(img)
                    for box in gt_bounding_boxes_list[idx]:
                        draw.rectangle(box, outline="red", width=8)
                    img.save(os.path.join(temp_folder, "img_%d_acted.jpeg" % idx))

        images = [img for img in os.listdir(temp_folder)] # if img.endswith(".png") or img.endswith(".jpg")
        images.sort()  # 根据文件名排序
        #print(images)
        # 创建GIF
        frames  = []
        for i in range(1, len(images) + 1):
            img_path = os.path.join(temp_folder, images[i-1])
            img = Image.open(img_path)
            # img = resize_image(img)
            # frames.append(np.array(img))
            img = img.convert('RGB')
            frames.append(img)  # 转换为RGB格式
        #print(frames)

        #imageio.mimsave(final_output_path, frames, fps=1)

        # 保存为GIF
        try:
            imageio.mimsave(final_output_path, frames, fps=0.5)  # 设置每帧持续时间
        except:
            print(package_data)
            pass
        