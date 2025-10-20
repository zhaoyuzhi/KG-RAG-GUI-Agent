import subprocess
import time


def get_size(hdc_path):
    command = hdc_path + " shell hidumper -s 10 -a screen"
    result = subprocess.run(command, capture_output=True, text=True, shell=True)
    resolution_line = result.stdout.strip().split('\n')[-1]
    width = None
    height = None
    # for item in resolution_line.split(","):
    #     if "phywidth" in item:
    #         width = int(item.split("phywidth=")[-1])
    #     if "phyheight" in item:
    #         height = int(item.split("phyheight=")[-1])
    # print(f"width:{width}, height:{height}")
    # return width, height
    for item in result.stdout.strip().split('\n'):
        if "physical screen resolution" not in item:
            continue
        for sub_item in item.split(","):
            if "physical screen resolution" not in sub_item:
                continue
            print(sub_item)
            resolution = sub_item.split(":")[-1].strip()
            width, height = resolution.split("x")[0], resolution.split("x")[1]
            return width, height
    return width, height


def get_layout(hdc_path, save_path):
    command = hdc_path + f" shell uitest dumpLayout"
    result = subprocess.run(command, capture_output=True, text=True, shell=True)
    local_json_path = result.stdout.split(':')[-1].strip("\n")
    command = hdc_path + f" file recv {local_json_path} {save_path}"
    subprocess.run(command, capture_output=True, text=True, shell=True)
    time.sleep(0.5)
    command = hdc_path + f" shell rm {local_json_path}"
    subprocess.run(command, capture_output=True, text=True, shell=True)
    #time.sleep(0.5)


def get_screenshot(hdc_path, save_path):

    time.sleep(0.5)
    command = hdc_path + " shell rm /data/local/tmp/screen.jpeg"
    subprocess.run(command, capture_output=True, text=True, shell=True)
    time.sleep(0.5)


    command = hdc_path + " shell snapshot_display -f /data/local/tmp/screen.jpeg"
    subprocess.run(command, capture_output=True, text=True, shell=True)
    time.sleep(0.5)

    command = hdc_path + " file recv /data/local/tmp/screen.jpeg %s"%save_path
    subprocess.run(command, capture_output=True, text=True, shell=True)


def tap(hdc_path, x, y):
    command = hdc_path + f" shell uinput -T -c {x} {y}"
    subprocess.run(command, capture_output=True, text=True, shell=True)


def type(hdc_path, text):
    command = hdc_path + f" shell uitest uiInput inputText 100 100 {text}"
    subprocess.run(command, capture_output=True, text=True, shell=True)


def slide(hdc_path, x1, y1, x2, y2):
    command = hdc_path + f" shell uinput -T -m {x1} {y1} {x2} {y2} 500"
    subprocess.run(command, capture_output=True, text=True, shell=True)


def back(hdc_path):
    command = hdc_path + f" shell uinput -K -d 2 -u 2 "
    subprocess.run(command, capture_output=True, text=True, shell=True)


def home(hdc_path):
    command = hdc_path + f" shell uinput -K -d 1 -u 1 "
    subprocess.run(command, capture_output=True, text=True, shell=True)


def open_app(hdc_path, package_name, ability_name="EntryAbility"):
    command = hdc_path + f" shell aa start -a {ability_name} -b {package_name}"
    subprocess.run(command, capture_output=True, text=True, shell=True)


def kill_app(hdc_path, package_name):
    command = hdc_path + f" hdc shell aa force-stop {package_name}"
    subprocess.run(command, capture_output=True, text=True, shell=True)


def check_lock_screen_state(hdc_path):
    command = hdc_path + " hdc shell \"hidumper -s PowerManagerService -a '-s'\""
    result = subprocess.run(command, capture_output=True, text=True, shell=True)
    for item in result.stdout.split("\n"):
        if "Current State" not in item:
            continue
        print(item)
        if "SLEEP" in item:
            return False
        if "AWAKE" in item:
            return True
    return "ERROR"


def unlock_screen(hdc_path):
    command = hdc_path + f" shell power-shell wakeup"
    subprocess.run(command, capture_output=True, text=True, shell=True)


if __name__ == "__main__":
    # pass
    hdc_path = r"C:\Users\Desktop\hdc\hdc\bin\hdc.exe"
    package_name = "com.sankuai.hmeituan"
    save_path = r"C:\Users\PycharmProjects\AppAgent_online\screenshot"
    layout_save_path = r"C:\Users\PycharmProjects\AppAgent_online\layout"
    # get_screenshot(hdc_path, save_path)
    # get_layout(hdc_path, layout_save_path)
    get_size(hdc_path)
