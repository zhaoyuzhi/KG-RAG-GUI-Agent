from utils.basic_utils import save_json, load_json
from utils.get_path_from_kg import *
from collections import defaultdict

def get_subgraph(dist_data, start_node, max_depth):
    queue = [(start_node, 0)]  # (node, current_depth)
    visited = set()
    visited_edge_id = set()
    graph = defaultdict(list)
    subgraph = defaultdict(list)
    edges = dist_data['edges']
    nodes = dist_data['nodes']
    for edge in edges:
        graph[edge['from']].append(edge['to']) # {'8A9B7F48079F9FBA5F4EC2590E1194DD': [xxx, xxx]} 

    while queue:
        cur_node, depth = queue.pop(0)

        if cur_node not in visited and depth <= max_depth:
            visited.add(cur_node)

            if cur_node not in graph:
                continue

            neighbor_nodes = graph[cur_node]
            for neighbor in neighbor_nodes:
                if neighbor not in visited and depth + 1 <= max_depth:
                    queue.append((neighbor, depth + 1))
                    subgraph[cur_node].append(neighbor)
                    visited_edge_id.add('#'.join([cur_node, neighbor]))

    new_edges = [edge for edge in edges if edge['id'] in visited_edge_id]
    new_nodes = {k: v for k, v in nodes.items() if k in visited}
    dist_data['edges'] = new_edges
    dist_data['nodes'] = new_nodes
    return dist_data

if __name__ == "__main__":
    dist_data_path = "data\com.hexin.plat.android\dist\static\com.hexin.plat.android_bp.json"
    dist_data = load_json(dist_data_path)

    # start_node = '8A9B7F48079F9FBA5F4EC2590E1194DD'
    # start_node = '758F8A4A62C45BEE1B2C229FF1D9155F'
    start_node = '2AA6431B0E7BAA5DCA84910532A9AC5C'
    new_json = get_subgraph(dist_data, start_node, max_depth=3)
    
    # save_json(new_json, filename="data\com.hexin.plat.android\dist\static\\com.hexin.plat.android.json")
