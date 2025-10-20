from PIL import Image, ImageDraw, ImageFont
from termcolor import colored
import logging
import colorlog
import matplotlib.pyplot as plt

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
    print()

def draw_bounding_boxes(image_path, bounds_list, save_path):
    image = Image.open(image_path)
    draw = ImageDraw.Draw(image)
    
    for bounds in bounds_list:
        draw.rectangle(bounds, outline="red", width=3)
    
    image.save(save_path)

    
def draw_coordinates(image_path, coordinates_list, save_path):
    image = Image.open(image_path)
    draw = ImageDraw.Draw(image)
    point_size = 10

    for coord in coordinates_list:
        draw.ellipse((coord[0] - point_size, coord[1] - point_size, coord[0] + point_size, coord[1] + point_size), fill='red')

    image.save(save_path)

    
def add_tag(coordinates, image_path, output_path, font_size=40, padding_ratio=8):
    image = Image.open(image_path)
    draw = ImageDraw.Draw(image, 'RGBA')
    font = ImageFont.truetype("Arial.ttf", font_size)

    for i in range(len(coordinates)):
        text = str(i + 1)
        text_bbox = draw.textbbox((0, 0), text, font=font)
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

    
def plot_image_flow(images, actions, filename,bounding_boxes_list=[]):
    #plt.rcParams['font.sans-serif'] = ['SimHei']
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