# AppAgent_offline

## Environment requirement
see requirements.txt

## offline_perception
1. get data. The data format looks like
```
data
└───layout/
│    └───{node_id}.json 
└───screenshot/
│    └───{node_id}.jpeg 
└───{package_name}.json
|
└─── metadata.csv
```
2. use perception/get_node_desc.py to get the screen description 
3. use perception/get_edges.py to get edges.json and metadata.csv
4. use perception/get_edge_desc_new.py to get edge description (VUT model)
5. use perception/convert_graph.py to get reformatted_utg_vut.json (graph-based offline preception)

## Run

1. single intent running
```
python main_7.py
```

2. multi intents sequential running
```
python main_7.py --multirun exp_configs=meituan00,meituan01,meituan02...
```
## Output
```
log/id_intent
└───visualization/
│    └───trace_step_0.png    
│    └───trace_step_1.png
│    └───...
└───history.json
└───main_7.log
└───trace_gt.png
└───trace_predict.png
└───trace_predict.json
```

history.json list of dict
 - 'node': Current node id
 -  'trajectory': trajectory,
 -  "thought": decision agent reasoning,
 - "matched_milestone": trajectory matched milestones,
 - "incomplete_milestone": remaining milestones,
 - 'next_node': Next node id

tract_predict.json:
 - 'task_is_completed': 1/0, need tp automatic check and update (default:1)
 -  predicted_milestones: output of intent agent,
 -  nodeIdList: list of node id,
 -  sceneIdList: list of image sequences,
 - 'package: app package name

trace_gt.png : ground-truth visualization 

trace_predict.png : model prediction visualization 

main_7.log : console log file

Additional information:

1. trajectory format: list of tuple
 - start node id
 - ( node id, action desp, action id)
 - ...

## Demo
Case 1
First conduct "python main_7.py" to run the program, and then conduct
```
python demo_visualization_5.py
```
construct the "log/id_intent/temp" directory and save the image list
use imageio to save the GIF demo

Case 2
single intent running
```
python main_9.py
```
build two threads. One for offline agent, another for gui visualization
