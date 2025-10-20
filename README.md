# KG-RAG

<br>Official PyTorch Implementation of the EMNLP 2025 Main Paper<br>

[Project](https://github.com/zhaoyuzhi/QRNet) | [arXiv](https://arxiv.org/abs/2509.00366)

## UTGs Downloading

Please download the UTGs from:

Please see `APP_names.txt` for details.

## Pre-installation

Please install all required packages:
```bash
pip install -r requirements.txt
```

## Runing

### 1. UTG Extraction

Please download pre-extracted UTGs:

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
