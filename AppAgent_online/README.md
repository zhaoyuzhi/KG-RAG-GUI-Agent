# AppAgent_online

## Environment requirement
see requirements.txt

### ADB or HDC requirement
make sure you install the "adb" for android phone and "hdc" for the harmony phone.
Change adb_path to your installed directory.

### VUT requirement
to get WidgetList from layout
1. Additional [jar data](https://onebox.huawei.com/p/b4bed40c9fba4c75ee0952e702f411c8) 
2. Additional [JDK_DATA](https://onebox.huawei.com/p/c213bf4adf738c319a190f8c806384ad)
3. Modify the "os.environ['JAVA_HOME']" and "jdk_path" to your directory 

## Benchmark
Use the ["oracle_test_app_second_stage"](https://onebox.huawei.com/p/0d73844501683ef7ee84544b41322641) data by 徐东来 x30051251.
It contains the main-branch graph of several apps.

The full pair of intent/sequence is within "data/intent_sequence_pair_1125.jsonl".

Currently I only test on two apps (i.e., ctrip and netease) with the harmony phone.
The evaluation results is shown in [accuracy](https://onebox.huawei.com/v/d77af89d3dd9fb09d7af5413a72d2076?type=1&sheet=11.25&time=1726814432177).

## Architecture
You can refer to [Figure1](./assets/architecture.png).

Key modules are borrow from the [MobileAgent-v2](https://arxiv.org/abs/2406.01014).

### Modification
1. the visual perception module is changed to the [VUT](https://arxiv.org/abs/2112.05692) model. You can refer to [Figure2](./assets/vut.png). The interface of the VUT model is maintained by  李孟启 l30037787. 

2. polish the prompts of decision/reflection agent.

export HYDRA_FULL_ERROR=1

## Run

1. running when connecting the android phone via adb
```
python run_andriod_new.py --multirun exp_configs=ctrip00_andriod
```

2. running when connecting the harmony phone via hdc
```
python run_harmony.py --multirun exp_configs=ctrip00
```

3. running everywhere using remote machine (based on the interface by 赵士杰 z30024019)
```
python run_harmony_phone2.py --multirun exp_configs=ctrip00
```

Note that we need a config file to initialize the variables.
The config sample looks like
``` 
app_name: alipay # not neccessarily need to be accurate
id: alipay00 # corresponding to the dataset benchmark id
intent: 支付宝首页通过扫一扫转账  # important! Make sure it is accurate! 
package_name: com.alipay.mobile.client  # important! Make sure it is accurate! The package_name for harmony and andriod phone is different! 
```

## Output
We provide a output sample in "logs" directory. It has the running logging content in "run_original_polish_1.log".
The format of the output directory looks like the below:
```
log/app_intent
└───layout/
│    └───output_layout_0.json  
│    └───output_layout_1.json
│    └───...
└───/img_plus_bbox
│    └───output_img_plus_bbox_0.png
│    └───output_img_plus_bbox_1.png
│    └───...
└───/img_plus_som
│    └───output_img_plus_som_0.png
│    └───output_img_plus_som_1.png
│    └───...
└───perception/
│    └───output_perception_0.jsonl
│    └───output_perception_1.jsonl
│    └───...
└───screenshot/
│    └───output_image_0.png
│    └───output_image_action_0.png
│    └───output_image_1.png
│    └───output_image_action_1.png
│    └───output_image_2.png
│    └───...
└───run_original_polish_1.log
```

## RAG (How to incorporate internal knowledge)
Currently, there is a "add_info" variable. If the "add_info" is not empty, the prompts for decision agent will add this knowledge.
