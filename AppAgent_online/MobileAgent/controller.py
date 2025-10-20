import os
import time
import subprocess
from PIL import Image

def get_size(adb_path):
    command = adb_path + " shell wm size"
    result = subprocess.run(command, capture_output=True, text=True, shell=True)
    resolution_line = result.stdout.strip().split('\n')[-1]
    width, height = map(int, resolution_line.split(' ')[-1].split('x'))
    return width, height

    
def get_xml(adb_path):
    process = subprocess.Popen([adb_path, 'shell', 'uiautomator', 'dump'], stdout=subprocess.PIPE)
    process.communicate()
    subprocess.run([adb_path, 'pull', '/sdcard/window_dump.xml', './xml/window_dump.xml'])


def take_screenshots(adb_path, num_screenshots, output_folder, crop_y_start, crop_y_end, slide_y_start, slide_y_end):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for i in range(num_screenshots):
        command = adb_path + f" shell rm /sdcard/screenshot{i}.png"
        subprocess.run(command, capture_output=True, text=True, shell=True)
        command = adb_path + f" shell screencap -p /sdcard/screenshot{i}.png"
        subprocess.run(command, capture_output=True, text=True, shell=True)
        command = adb_path + f" pull /sdcard/screenshot{i}.png {output_folder}"
        subprocess.run(command, capture_output=True, text=True, shell=True)
        image = Image.open(f"{output_folder}/screenshot{i}.png")
        cropped_image = image.crop((0, crop_y_start, image.width, crop_y_end))
        cropped_image.save(f"{output_folder}/screenshot{i}.png")
        subprocess.run([adb_path, 'shell', 'input', 'swipe', '500', str(slide_y_start), '500', str(slide_y_end)])


def get_layout(adb_path,save_path="./layout/layout.xml"):
    #color_log("Extracting layout...", self.logger)
    #layout_path = "./layout/layout.xml"
    xml_device_path = "/sdcard/window_dump.xml"
    subprocess.run([adb_path, "shell", "uiautomator", "dump", xml_device_path])
    subprocess.run([adb_path, "pull", xml_device_path, save_path])
    subprocess.run([adb_path, "shell", "rm", xml_device_path])

def get_screenshot(adb_path,save_path="./screenshot/screenshot.jpg"):
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

    command = adb_path + " pull /sdcard/screenshot.png ./screenshot"
    subprocess.run(command, capture_output=True, text=True, shell=True)
    # command = adb_path + " pull /sdcard/layout.xml ./screenshot"
    # subprocess.run(command, capture_output=True, text=True, shell=True)

    image_path = "./screenshot/screenshot.png"
    #save_path = "./screenshot/screenshot.jpg"
    image = Image.open(image_path)
    image.convert("RGB").save(save_path, "JPEG")
    os.remove(image_path)


def get_keyboard(adb_path):
    command = adb_path + " shell dumpsys input_method"
    process = subprocess.run(command, capture_output=True, text=True, shell=True, encoding='utf-8')
    output = process.stdout.strip()
    for line in output.split('\n'):
        if "mInputShown" in line:
            if "mInputShown=true" in line:
                
                for line in output.split('\n'):
                    if "hintText" in line:
                        hintText = line.split("hintText=")[-1].split(" label")[0]
                        break
                
                return True, hintText
            elif "mInputShown=false" in line:
                return False, None


def tap(adb_path, x, y):
    command = adb_path + f" shell input tap {x} {y}"
    subprocess.run(command, capture_output=True, text=True, shell=True)


def type(adb_path, text):
    if text == "delete_all":
        # 执行清空操作
        clear_text(adb_path)
        return

    text = text.replace("\\n", "_").replace("\n", "_")
    for char in text:
        if char == ' ':
            command = adb_path + f" shell input text %s"
            subprocess.run(command, capture_output=True, text=True, shell=True)
        elif char == '_':
            command = adb_path + f" shell input keyevent 66"
            subprocess.run(command, capture_output=True, text=True, shell=True)
        elif 'a' <= char <= 'z' or 'A' <= char <= 'Z' or char.isdigit():
            command = adb_path + f" shell input text {char}"
            subprocess.run(command, capture_output=True, text=True, shell=True)
        elif char in '-.,!?@\'°/:;()':
            command = adb_path + f" shell input text \"{char}\""
            subprocess.run(command, capture_output=True, text=True, shell=True)
        else:
            command = adb_path + f" shell am broadcast -a ADB_INPUT_TEXT --es msg \"{char}\""
            subprocess.run(command, capture_output=True, text=True, shell=True)


# def clear_text(adb_path):
#     # 假设当前输入框中最多有100个字符，通过循环删除这些字符来清空
#     for _ in range(20):
#         command = adb_path + " shell input keyevent 67"  # keyevent 67 是删除键
#         subprocess.run(command, capture_output=True, text=True, shell=True)

def clear_text(adb_path):
    command = adb_path + " adb shell input keyevent 123"
    subprocess.run(command, capture_output=True, text=True, shell=True)
    time.sleep(0.5)
    for _ in range(20):
        command = adb_path + " shell input keyevent 67"
        subprocess.run(command, capture_output=True, text=True, shell=True)

def slide(adb_path, x1, y1, x2, y2):
    command = adb_path + f" shell input swipe {x1} {y1} {x2} {y2} 500"
    subprocess.run(command, capture_output=True, text=True, shell=True)


def battery(adb_path):
    command = adb_path + f" shell dumpsys battery"
    out = subprocess.run(command, capture_output=True, text=True, shell=True)
    return 'battery()函数的输出如下：' + '\n' + out.stdout
    
    
def back(adb_path):
    command = adb_path + f" shell input keyevent 4"
    subprocess.run(command, capture_output=True, text=True, shell=True)
    
    
def home(adb_path):
    command = adb_path + f" shell am start -a android.intent.action.MAIN -c android.intent.category.HOME"
    subprocess.run(command, capture_output=True, text=True, shell=True)

def open_app(adb_path, package_name):
    command = adb_path + f" shell monkey -p {package_name} -c android.intent.category.LAUNCHER 1"
    #print(command)
    result = subprocess.run(command, capture_output=True, text=True, shell=True)
    #print(result)

def kill_app(adb_path, package_name):
    command = adb_path + f" shell am force-stop {package_name}"
    result = subprocess.run(command, capture_output=True, text=True, shell=True)

def check_lock_screen_state(adb_path):
    command = adb_path + f" shell dumpsys window | findstr mDreamingLockscreen"
    result = subprocess.run(command, capture_output=True, text=True, shell=True)
    # Check if the screen is locked
    if "mDreamingLockscreen=true" in result.stdout:
        return True
    elif "mDreamingLockscreen=false" in result.stdout:
        return False
    return False
    # else:
    #     exit(1)


def unlock_screen(adb_path):
    command = adb_path + f" shell input keyevent 26"
    subprocess.run(command, capture_output=True, text=True, shell=True)
    command = adb_path + f" shell input keyevent 82"
    subprocess.run(command, capture_output=True, text=True, shell=True)
    