import base64
import json
import os
import tqdm
import requests
from utils.basic_utils import save_jsonl
ocr_url = "http://10.90.78.139:8093/pps_ocr/recognize"  # paddle自研

def get_ocr_recognize(img_path):
    with open(img_path, "rb") as f:
        img_base64 = base64.b64encode(f.read())

    payload = json.dumps({
        "key": [
            "image"
        ],
        "lang": [
            "zh",
            "zh"
        ],
        "value": [img_base64.decode('utf-8')]
    })
    headers = {
        'Content-Type': 'application/json'
    }

    res = requests.request("POST", ocr_url, headers=headers, data=payload)

    response_code = res.status_code

    # print('响应码', response_code)
    if response_code == 200:
        response = res.json()
    else:
        response = res.text
        # print(response)
    # print('响应', response)
    response_time = res.elapsed.total_seconds()
    #print('响应时间', response_time)
    return response

if __name__ == '__main__':

    keyword = "隐私政策"
    package = "com.feeyo.variflight"

    root = os.path.join("graph_data",package)
    #root = os.path.join(package,"dist","static")
    screen_path = os.path.join(root,"screenshot")
    matched_list = []
    for img_path in tqdm.tqdm(os.listdir(screen_path)):
        #flag = False
        pic_path = os.path.join(screen_path, img_path)
        #print(pic_path)
        result = get_ocr_recognize(pic_path)
        words_result = eval(result.get("value")[0])
        #print(type(words_result))
        for _meta in words_result:
            # print(type(_meta))
            # print(len(_meta))
            assert len(_meta) == 1
            predict = _meta[0]
            #confidence = item["confidence"]
            text = predict["text"]
            if keyword in text:
                flag = True
                matched_list.append({"img_path":img_path,"match":predict})
                break

    save_jsonl(matched_list, os.path.join(root,"ocr_demo.jsonl"))
