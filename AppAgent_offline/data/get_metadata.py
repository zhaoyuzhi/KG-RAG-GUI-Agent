import os 
import pandas as pd
from utils import load_json, save_json

def get_widget_bbox_map(nodes):
    """return all widgets with corresponding bounding boxes (left, top, right, bottom)"""
    widget_bbox_map = {}
    for node in nodes.values():
        for widget_id, widget_info in node["exactScenes"][0]["widgetList"].items():
            if widget_id in widget_bbox_map.keys():
                continue
            bounds = widget_info['bounds'].replace('][', ',').replace('[', '').replace(']', '')
            bbox = list(map(int, bounds.split(','))) 
            widget_bbox_map[widget_id] = bbox
                
    return widget_bbox_map

def get_action_edge_map(edges):
    """return all edges with action_id as key"""
    action_edge_map = {}
    for edge in edges:
        for action in edge['events']:
            action_edge_map[action['actionId']] = edge['id']
            
    return action_edge_map


def get_all_edge_dicts(nodes, edges):
    """return all edges with {bbox, action_type, to (node_id), from (node_id)}"""
    all_edge_dicts = {}
    widget_bbox_map = get_widget_bbox_map(nodes)
    action_edge_map = get_action_edge_map(edges)
    for node in nodes.values():
        for scene_action in node["exactScenes"][0]["sceneActionList"]:
            action_id = scene_action['actionId']
            edge_id = action_edge_map[action_id]
            from_node, to_node = edge_id.split('#')
            bboxes = []
            action_types = []
            try:
                for action in scene_action['actionList']:
                    action_type = action['action'].lower()
                    action_type = action_type + ' ' + action['swipeType'].lower().replace('swipe', '') if action_type == "swipe" else action_type
                    widget_id = action['widgetId']
                    bboxes.append(widget_bbox_map[widget_id])
                    action_types.append(action_type)

                all_edge_dicts[action_id] = {
                    'bboxes': bboxes,
                    'action_types':  action_types,
                    'from': from_node,
                    'to': to_node
                }
            except:
                continue

    return all_edge_dicts

if __name__ == "__main__":
    package_names = ['com.qiyi.video.hmy', 'com.sankuai.hmeituan', 'com.jd.hm.mall', 'com.ss.hm.ugc.aweme', 'com.ss.hm.article.news']
    for package_name in package_names:
        path_prefix = f'data\{package_name}'
        json_data = os.path.join(path_prefix, f'{package_name}.json')
        screenshot_dir = os.path.join(path_prefix, 'screenshot')
        dist_data = load_json(json_data)
        nodes = dist_data['nodes']
        edges = dist_data["edges"]

        node_data_list = []
        for sid, node in nodes.items():
            metadata = node["exactScenes"][0]
            img_path = metadata["img"]
            layout_path = metadata["layout"]
            node_data_list.append([sid, img_path, layout_path])
        node_df = pd.DataFrame(node_data_list)

        new_path_prefix = os.path.join('utgs', package_name)
        if not os.path.exists(new_path_prefix):
            os.makedirs(new_path_prefix)
        node_df.to_csv(os.path.join(new_path_prefix, 'metadata.csv'), index=False, header=False)
        all_edge_dicts = get_all_edge_dicts(nodes, edges)
        save_json(all_edge_dicts, os.path.join(new_path_prefix, 'edges.json'))
    