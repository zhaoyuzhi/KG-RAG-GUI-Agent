import os
import time
import subprocess
from PIL import Image
from screen_discription import process_image
from description_to_vector import get_candidates

def get_screenshot(adb_path):
    command = adb_path + " shell rm /sdcard/screenshot.png"
    subprocess.run(command, capture_output=True, text=True, shell=True)
    # command = adb_path + " shell rm /sdcard/layout.xml"
    # subprocess.run(command, capture_output=True, text=True, shell=True)
    time.sleep(0.5)

    command = adb_path + " shell screencap -p /sdcard/screenshot.png"
    subprocess.run(command, capture_output=True, text=True, shell=True)
    # command = adb_path + " shell uiautomator dump -p /sdcard/layout.xml"
    # subprocess.run(command, capture_output=True, text=True, shell=True)
    time.sleep(0.5)

    command = adb_path + " pull /sdcard/screenshot.png ../screenshot"
    subprocess.run(command, capture_output=True, text=True, shell=True)
    # command = adb_path + " pull /sdcard/layout.xml ./screenshot"
    # subprocess.run(command, capture_output=True, text=True, shell=True)

    image_path = "../screenshot/screenshot.png"
    save_path = "../screenshot/screenshot.jpg"
    image = Image.open(image_path)
    image.convert("RGB").save(save_path, "JPEG")
    os.remove(image_path)


# adb_path = "/Users/jinpeng/Library/Android/sdk/platform-tools/adb"
adb_path = r"C:\Users\AppData\Local\Android\Sdk\platform-tools\adb.exe"

get_screenshot(adb_path)
query_path = "../screenshot/screenshot.jpg"
# all_embedding_path = r'/Users/jinpeng/Desktop/text/descriptions_embeddings.csv'
all_embedding_path = \
    r'E:\Datasets\AppTestAgent\0624HuaweiMusic\all_nodes\descriptions_embeddings.csv'

description = process_image(query_path)
print(description)
matches = get_candidates(description, all_embedding_path)

print(matches[:3])
