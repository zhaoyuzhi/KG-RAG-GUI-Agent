from PIL import Image, ImageDraw, ImageFont
from termcolor import colored
import logging
import colorlog
import matplotlib.pyplot as plt
#from pyvis.network import Network
import math

# Set up the logger with color support
def setup_logger():
    logger = logging.getLogger('colored_logger')
    logger.setLevel(logging.INFO)
    logger.propagate = False  # Prevent propagation to the root logger

    # Check if handlers are already added to avoid duplicate logs
    if not logger.handlers:
        handler = colorlog.StreamHandler()
        handler.setLevel(logging.INFO)

        formatter = colorlog.ColoredFormatter(
            "%(message)s",
            secondary_log_colors={},
        )

        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

def color_log(msg, logger, color='white'):
    # Define a custom logging level based on the color
    level = logging.INFO
    log_colors = {
        'white': '\033[0m',    # reset to default color
        'red': '\033[31m',     # red
        'green': '\033[32m',   # green
        'yellow': '\033[33m',  # yellow
        'blue': '\033[34m',    # blue
        'magenta': '\033[35m', # magenta
        'cyan': '\033[36m',    # cyan
        'black': '\033[30m',   # black
    }

    color_code = log_colors.get(color.lower(), '\033[0m')
    colored_msg = f"{color_code}{msg}\033[0m"
    logger.log(level, colored_msg)

def color_print(msg, color='white'):
    if not color:
        print(msg)
        return

    colored_log = colored(msg, color, attrs=['bold'])
    print(colored_log)

def draw_bounding_boxes(image_path, bounds_list, save_path):
    image = Image.open(image_path)
    draw = ImageDraw.Draw(image)
    
    for bounds in bounds_list:
        draw.rectangle(bounds, outline="red", width=3)
    
    image.save(save_path)


def draw_bounding_boxes_wtype(image_path, perception_dict, save_path):
    image = Image.open(image_path)
    draw = ImageDraw.Draw(image)

    mapping = {
        "clickable_info" : "red",
        "slideable_info" : "blue",
        "editable_info": "green",
    }

    for action_type, item_list in perception_dict.items():
        color = mapping[action_type]

        for item in item_list:
            draw.rectangle(item["bbox"], outline=color, width=3)

    image.save(save_path)


    
def draw_coordinates(image_path, coordinates_list, save_path):
    image = Image.open(image_path)
    draw = ImageDraw.Draw(image)
    point_size = 10

    for coord in coordinates_list:
        draw.ellipse((coord[0] - point_size, coord[1] - point_size, coord[0] + point_size, coord[1] + point_size), fill='red')

    image.save(save_path)

def draw_coordinates_and_bounding_boxes(image_path, coordinates_list, bounds_list, save_path):
    image = Image.open(image_path)
    draw = ImageDraw.Draw(image)
    point_size = 15
    assert len(coordinates_list) == len(bounds_list)

    for index in range(len(coordinates_list)):
        coord = coordinates_list[index]
        bounds = bounds_list[index]
        draw.rectangle(bounds, outline="red", width=3)
        draw.ellipse((coord[0] - point_size, coord[1] - point_size, coord[0] + point_size, coord[1] + point_size), fill='red')

    image.save(save_path)

    
def add_tag(coordinates, image_path, output_path, font_size=40, padding_ratio=5):
    image = Image.open(image_path)
    draw = ImageDraw.Draw(image, 'RGBA')
    #font = ImageFont.truetype("Arial.ttf", font_size)
    # Load a font with the specified font size
    font = ImageFont.truetype("arial.ttf", font_size)

    for i in range(len(coordinates)):
        text = str(i + 1)
        text_bbox = draw.textbbox((0, 0), text)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        text_position = [
            (coordinates[i][0] + coordinates[i][2]) / 2 - text_width / 2,
            (coordinates[i][1] + coordinates[i][3]) / 2 - text_height / 2
        ]
        h_padding = text_width / padding_ratio
        v_padding = text_height / padding_ratio
        background_position = [text_position[0] - h_padding, text_position[1] - v_padding,
                               text_position[0] + text_width + h_padding, text_position[1] + text_height + v_padding]
        text_position[1] -= text_height / 4

        draw.rectangle(background_position, fill=(0, 0, 0, 255))
        draw.text(text_position, text, fill=(255, 255, 255, 255), font=font)
    image.save(output_path)

def draw_tag_wtype(image_path, perception_dict, output_path, font_size=20, padding=10):
    image = Image.open(image_path)
    draw = ImageDraw.Draw(image)

    # Load a font
    font_size = font_size  # Adjust font size as needed
    font = ImageFont.truetype("/home/app_agent/RAGGeneration_New/code/SimHei.ttf", font_size)  # Ensure the font file is available

    mapping = {
        "clickable_info": (255, 0, 0),
        "slideable_info": (0, 255, 0),
        "editable_info": (0, 0, 255),
    }
    index = 0
    for action_type, item_list in perception_dict.items():
        background_color = mapping[action_type]

        for item in item_list:
            #draw.rectangle(item["bbox"], outline=color, width=3)
            x_min, y_min, x_max, y_max = item["bbox"]

            # Calculate the middle point
            middle_x = (x_min + x_max) // 2
            middle_y = (y_min + y_max) // 2

            # Label with ascending number starting from zero
            label = str(index)


            # Calculate text size using textbbox
            bbox = draw.textbbox((0, 0), label, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            # Draw background rectangle for text
            padding = padding  # Adjust padding as needed
            # Calculate text position with offset
            text_offset_x = middle_x - text_width//2 - padding
            text_offset_y = middle_y - text_height//2 - padding

            #background_color = (255, 0, 0)  # Example background color
            draw.rectangle(
                [text_offset_x, text_offset_y, text_offset_x + text_width + padding * 2, text_offset_y + text_height + padding * 2],
                fill=background_color
            )

            # Put the label on the image
            draw.text((text_offset_x + padding, text_offset_y + padding), label,
                      fill=(255, 250, 250), font=font)
            index+=1
        # Save or display the image
        image.save(output_path)

def draw_tag_2(coordinates, image_path, output_path, font_size=20, padding=10):
    image = Image.open(image_path)
    draw = ImageDraw.Draw(image)

    # Load a font
    font_size = font_size  # Adjust font size as needed
    font = ImageFont.truetype("arial.ttf", font_size)  # Ensure the font file is available

    for i, (x_min, y_min, x_max, y_max) in enumerate(coordinates):
        # Calculate the middle point
        middle_x = (x_min + x_max) // 2
        middle_y = (y_min + y_max) // 2

        # Label with ascending number starting from zero
        label = str(i)


        # Calculate text size using textbbox
        bbox = draw.textbbox((0, 0), label, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Draw background rectangle for text
        padding = padding  # Adjust padding as needed
        # Calculate text position with offset
        text_offset_x = middle_x - text_width//2 - padding
        text_offset_y = middle_y - text_height//2 - padding

        background_color = (255, 0, 0)  # Example background color
        draw.rectangle(
            [text_offset_x, text_offset_y, text_offset_x + text_width + padding * 2, text_offset_y + text_height + padding * 2],
            fill=background_color
        )

        # Put the label on the image
        draw.text((text_offset_x + padding, text_offset_y + padding), label,
                  fill=(255, 250, 250), font=font)

    # Save or display the image
    image.save(output_path)


# import pyshine as ps
# import cv2
# def draw_bbox_multi(img_path, output_path, elem_list, record_mode=False, dark_mode=False):
#     imgcv = cv2.imread(img_path)
#     count = 1
#     for elem in elem_list:
#         #try:
#             # top_left = elem.bbox[0]
#             # bottom_right = elem.bbox[1]
#         print(elem)
#         bbox = elem["bbox"]
#         left, top = bbox[0], bbox[1]
#         right, bottom = bbox[2], bbox[3]
#         print(left, top, right, bottom)
#         label = str(count)
#         if record_mode:
#             if elem["action_type"] == "CLICK":
#                 color = (250, 0, 0)
#             elif elem["action_type"] == "SWIPE":
#                 color = (0, 0, 250)
#             else:
#                 color = (0, 250, 0)
#             imgcv = ps.putBText(imgcv, label, text_offset_x=(left + right) // 2 + 10, text_offset_y=(top + bottom) // 2 + 10,
#                                 vspace=10, hspace=10, font_scale=1, thickness=2, background_RGB=color,
#                                 text_RGB=(255, 250, 250), alpha=0.5)
#         else:
#             text_color = (10, 10, 10) if dark_mode else (255, 250, 250)
#             bg_color = (255, 250, 250) if dark_mode else (10, 10, 10)
#             imgcv = ps.putBText(imgcv, label, text_offset_x=(left + right) // 2 + 10, text_offset_y=(top + bottom) // 2 + 10,
#                                 vspace=10, hspace=10, font_scale=1, thickness=2, background_RGB=bg_color,
#                                 text_RGB=text_color, alpha=0.5)
#     # except Exception as e:
#     #     print(f"ERROR: An exception occurs while labeling the image\n{e}")
#         count += 1
#         print(count)
#     cv2.imwrite(output_path, imgcv)
#     return imgcv

def add_swipe_visualization(image_path, output_path, start_pos, end_pos, line_color="red", line_width=10):
    """
    在图片上添加表示滑动操作的线条。

    参数:
    - image_path: 输入图片的路径。
    - output_path: 输出图片的路径。
    - start_pos: 线条开始的位置（x, y）。
    - end_pos: 线条结束的位置（x, y）。
    - line_color: 线条的颜色。
    - line_width: 线条的宽度。
    """
    # 打开图片
    image = Image.open(image_path)
    draw = ImageDraw.Draw(image)

    # 在图片上绘制线条
    draw.line([start_pos, end_pos], fill=line_color, width=line_width)

    # 计算箭头的方向和大小
    arrow_length = 30  # 箭头长度
    arrow_angle = math.pi / 6  # 箭头夹角（30度）

    # 线条方向角度
    dx = end_pos[0] - start_pos[0]
    dy = end_pos[1] - start_pos[1]
    angle = math.atan2(dy, dx)

    # 计算箭头的两个点
    arrow_point1 = (
        end_pos[0] - arrow_length * math.cos(angle + arrow_angle),
        end_pos[1] - arrow_length * math.sin(angle + arrow_angle)
    )
    arrow_point2 = (
        end_pos[0] - arrow_length * math.cos(angle - arrow_angle),
        end_pos[1] - arrow_length * math.sin(angle - arrow_angle)
    )

    # 绘制箭头
    draw.polygon([end_pos, arrow_point1, arrow_point2], fill=line_color)

    # 保存修改后的图片
    image.save(output_path)
    #print(f"Visualization added and saved to {output_path}")

    
def plot_image_flow(images, actions, filename,bounding_boxes_list=[]):
    plt.rcParams['font.sans-serif'] = ['SimHei']  
    num_images = len(images)
    num_actions = len(actions)

    # Create a plot
    fig, axes = plt.subplots(1, num_images + num_actions, figsize=((num_images + num_actions) * 4, 6))  # Adjust figure size as needed

    # Loop through images and display them
    for i, image_path in enumerate(images):
        # Open image
        img = Image.open(image_path)
        if len(bounding_boxes_list) > 0 :
            if i < num_actions:
                draw = ImageDraw.Draw(img)
                for box in bounding_boxes_list[i]:
                    draw.rectangle(box, outline="red", width=8)

        # Display image
        axes[i * 2].imshow(img)
        axes[i * 2].axis('off')  # Hide axes

    # Loop through texts and display them between images
    for i, action in enumerate(actions):
        # Display text in between the corresponding images
        # print(action)
        text = action["actionId"]+"\n"+action["actionDesp"]
        axes[i * 2 + 1].text(0.5, 0.5, text, ha='center', va='center', fontsize=12, wrap=True)
        axes[i * 2 + 1].axis('off')  # Hide axes

    # Adjust layout
    # plt.tight_layout()
    plt.savefig(filename)
    plt.close(fig)

def plot_image_flow_2(images, actions, filename,bounding_boxes_list=[]):
    plt.rcParams['font.sans-serif'] = ['SimHei']
    num_images = len(images)
    num_actions = len(actions)

    # Create a plot
    fig, axes = plt.subplots(1, num_images + num_actions, figsize=((num_images + num_actions) * 4, 6))  # Adjust figure size as needed

    # Loop through images and display them
    for i, image_path in enumerate(images):
        # Open image
        img = Image.open(image_path)
        if len(bounding_boxes_list) > 0 :
            if i < num_actions:
                draw = ImageDraw.Draw(img)
                for box in bounding_boxes_list[i]:
                    draw.rectangle(box, outline="red", width=8)

        # Display image
        axes[i * 2].imshow(img)
        axes[i * 2].axis('off')  # Hide axes

    # Loop through texts and display them between images
    for i, action in enumerate(actions):
        # Display text in between the corresponding images
        # print(action)
        text = action
        axes[i * 2 + 1].text(0.5, 0.5, text, ha='center', va='center', fontsize=12, wrap=True)
        axes[i * 2 + 1].axis('off')  # Hide axes

    # Adjust layout
    # plt.tight_layout()
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])  # Adjust layout to fit the title
    plt.savefig(filename, bbox_inches='tight', pad_inches=0.1)
    plt.close(fig)


# def plot_trace_graph(image_paths, texts, filename):
#
#     G = Network(directed=True)
#     for idx, image_path in enumerate(image_paths):
#         G.add_node(idx + 1, size=15, title=filename, shape="image", image=image_path, physics=False)
#
#     for idx, action in enumerate(texts):
#         G.add_edge(idx+1, idx+2, weight=10, title=action, label=action, physics=False, color='red')
#
#     G.save_graph(filename)