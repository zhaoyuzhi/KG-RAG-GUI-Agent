# KG-RAG

<br>Official PyTorch Implementation of the EMNLP 2025 Main Paper<br>

[Project](https://github.com/zhaoyuzhi/QRNet) | [arXiv](https://arxiv.org/abs/2509.00366)

## UTGs

### 1. Downloading

Please download the UTGs from:

Link: https://pan.baidu.com/s/1Q_HTMJLx-H4KivOopLJbzw?pwd=7paa

Code: 7paa

### 2. Details

- Chinese APPs:

We provide UTGs for 30 Chinese APPs, on Andriod and HarmonyOS, respectively. Please see `APP_names.txt` for details.

| English Name | Amap | Baidu Browser | Baihe | CapCut | Ctrip | Daily Alarm Clock | Dianping | Dongchedi | Douyin | Douyu |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 中文名 | 高德地图 | 百度 | 百合网 | 剪印 | 携程 | 闹钟助手 | 大众点评 | 懂车帝 | 抖音 | 斗鱼 |

| English Name | Himalaya FM | Hupu | Jinri Toutiao | Keep | Meituan Takeaway | Moji Weather | NetEase Cloud Music | NetEase Mail | Pupu Supermarket | QQmusic |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 中文名 | 喜马拉雅 | 虎扑 | 今日头条 | Keep | 美团外卖 | 墨迹天气 | 网易云音乐 | 网易邮箱 | 朴朴超市 | QQ音乐 |

| English Name | Taobao | Tomato Novel | VIP | Weibo | WeSing | Xingtu | Youdao Dictionary | Youku | Zhihu | Zhixing Train Tickets |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 中文名 | 淘宝 | 番茄小说 | 唯品会 | 微博 | 全民K歌 | 醒图 | 有道云词典 | 优酷 | 知乎 | 智行火车票 |

- English APPs:

We provide UTGs for 12 English APPs only on Andriod platform.

| English Name | APP Launcher | Calendar | Camera | Clock | Contacts | Dialer | File Manager | Gallery | Music Player | Notes | SMS Messenger | Voice Recorder |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 中文名 | 应用启动器 | 日历 | 相机 | 时钟 | 联系人 | 拨号器 | 文件管理器 | 图库 | 音乐播放器 | 备忘录 | 短信 | 录音机 |

## Pre-installation

Please install all required packages:
```bash
pip install -r requirements.txt
```

## Runing

### 1. UTG Extraction

Please download pre-extracted UTGs (see **UTGs Downloading**)

### 2. Offline Intent Generation

See README.md for more inforamtion
```bash
cd ./Intent_Generation/single_screen_service
python intention_generation_prompt_engineering.py
```
Note: Please modify the data path in this file

### 3. Intent-guided LLM Search

See README.md for more inforamtion
```bash
cd ./AppAgent_offline/
python main_all_intention.py
```
Note: Please modify the data path and package name in this file

### 4. KG-RAG Knowledge Database (RAG Generation)

Step 1: Collect the available paths from the Stage 2.
```bash
cd RAG_Generation
python collect_completed_intention.py 
```
You can modify the **prompt** to get general Information

Step 2: Generate the text and image embedding in advance for later searches
```bash
python get_image_text_embedding_from_graph.py
```

### 5. Using KG-RAG in online devices

Follow the README.md guideline.
```bash
cd AppAgent_online
python run_harmony_phone2.py --multirun exp_configs=ctrip00
```
