import networkx as nx

# 创建一个有向图或无向图
G = nx.Graph()  # 对于无向图
# G = nx.DiGraph()  # 对于有向图

# 添加节点和边
G.add_edge('A', 'B', weight=1)
G.add_edge('B', 'C', weight=2)
G.add_edge('A', 'C', weight=2)
G.add_edge('C', 'D', weight=1)
G.add_edge('B', 'D', weight=3)

# 使用最短路径算法，指定源节点和目标节点
shortest_path = nx.shortest_path(G, source='A', target='D', weight='weight')

# 获取路径的长度
path_length = nx.shortest_path_length(G, source='A', target='D', weight='weight')

print(f"从A到D的最短路径是：{shortest_path}")
print(f"最短路径的长度是：{path_length}")
