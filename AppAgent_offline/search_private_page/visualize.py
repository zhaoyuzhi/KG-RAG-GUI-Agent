import os.path
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw
from utils.basic_utils import load_jsonl
import math

def draw_bounding_boxes_on_images(data_list, max_width=1000,suffix=""):
    """
    Creates a large image by combining a list of images with red bounding boxes from a list of dictionaries.

    Parameters:
    - data_list: List of dictionaries, where each dictionary contains:
        - "img_path": String representing the file path to an image.
        - "match": A dictionary containing:
            - "box": List of four coordinate pairs defining the bounding box.
    """
    # Open images and draw bounding boxes
    images_with_boxes = []
    for data in data_list:
        image_path = data['img_path']
        box = data['match']['box']

        # Open the image
        image = Image.open(os.path.join(screen_path,image_path))

        # Draw the bounding box
        draw = ImageDraw.Draw(image)
        # Extract coordinates: [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]
        x1, y1 = box[0]
        x2, y2 = box[2]  # Bottom-right coordinates
        draw.rectangle([x1, y1, x2, y2], outline="red", width=2)

        # # Resize image if necessary
        # if image.width > max_width:
        #     resize_factor = max_width / image.width
        #     new_size = (max_width, int(image.height * resize_factor))
        #     image = image.resize(new_size, Image.LANCZOS)

        images_with_boxes.append(image)

    # Calculate the layout of the grid
    num_images = len(images_with_boxes)
    cols = min(num_images, 7)  # Use up to 3 columns for better layout
    rows = math.ceil(num_images / cols)

    # Create subplots
    fig, axes = plt.subplots(rows, cols, figsize=(1.5*num_images, 1.0*num_images))
    axes = axes.flatten() if rows > 1 or cols > 1 else [axes]  # Ensure axes is iterable

    # Display each image in its own subplot
    for i, img in enumerate(images_with_boxes):
        axes[i].imshow(img)
        axes[i].axis('off')  # Hide axes for clarity

    # Hide any remaining empty subplots
    for i in range(num_images, len(axes)):
        axes[i].axis('off')

    plt.tight_layout()

    plt.savefig("visualize_%s.png"%suffix, bbox_inches='tight', pad_inches=0.1)
    plt.show()
    # # Calculate the layout of the grid
    # num_images = len(images_with_boxes)
    # cols = min(num_images, 10)  # Use up to 3 columns for better layout
    # rows = math.ceil(num_images / cols)
    #
    # # Determine the max width and height for each grid cell
    # max_img_width = max(img.width for img in images_with_boxes)
    # max_img_height = max(img.height for img in images_with_boxes)
    #
    # # Create a new blank image for the collage
    # collage_width = cols * max_img_width
    # collage_height = rows * max_img_height
    # collage = Image.new('RGB', (collage_width, collage_height), (255, 255, 255))
    #
    # # Paste each image into the collage
    # for index, img in enumerate(images_with_boxes):
    #     row = index // cols
    #     col = index % cols
    #     x_offset = col * max_img_width
    #     y_offset = row * max_img_height
    #     collage.paste(img, (x_offset, y_offset))
    #
    # return collage

if __name__ == '__main__':

    package = "com.feeyo.variflight"#"com.ss.android.article.news"#"com.hexin.plat.android" #com.hexin.plat.android
    root = os.path.join("graph_data",package)#os.path.join(package, "dist", "static")
    screen_path = os.path.join(root, "screenshot")
    #root = "com.gotokeep.keep/dist/static/screenshot"
    data_list = load_jsonl(os.path.join(root, "ocr_demo.jsonl"))
    number = len(data_list)
    # Draw bounding boxes and display images in a grid layout
    #for _ in range(0,number,10):
    draw_bounding_boxes_on_images(data_list,suffix="variflight_full")
    # Example usage:
    # data_list = [
    #     {
    #         "img_path": "group-o-0b6902b670b644ec830928dca1b8bf9b.jpeg",
    #         "match": {
    #             "text": "隐私政策>",
    #             "confidence": 0.9848054051399231,
    #             "box": [[709.0, 1841.0], [897.0, 1841.0], [897.0, 1884.0], [709.0, 1884.0]]
    #         }
    #     },
    #     # Add more dictionaries as needed
    # ]

    # Create the collage
    # collage = create_collage_with_bounding_boxes(data_list)
    #
    # # Display the collage
    # #plt.figure(figsize=(15, 10))
    # plt.imshow(collage)
    # plt.axis('off')  # Hide axis
    # plt.tight_layout()
    # plt.savefig("test_3.png", bbox_inches='tight', pad_inches=0.1)
    # plt.show()
# Example usage:
# image_paths = ['path/to/image1.jpg', 'path/to/image2.jpg']  # Replace with actual paths
# bounding_boxes = [(50, 30, 100, 150), (60, 40, 120, 160)]  # Replace with actual bounding boxes (x, y, width, height)

# # Create the collage
# collage = create_collage_with_bounding_boxes(data)
#
# # Display the collage
# plt.imshow(collage)
# plt.axis('off')  # Hide axis
# plt.show()