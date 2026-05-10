
import networkx as nx
import json
import chess

file_path = 'chess_graph_small.json'

with open(file_path, 'r') as file:
    data = json.load(file)


print(len(data))

G = nx.DiGraph()

for node_hash, node_data in data.items():
    G.add_node(node_hash, 
               outcomes=node_data.get('outcomes'), 
               visits=node_data.get('total_visits'),
               fen=node_data.get('fen')) 
    
    for next_hash, edge_meta in node_data['edges'].items():
        G.add_edge(node_hash, next_hash, 
                   weight=edge_meta['prob'], 
                   count=edge_meta['count'])

print(f"Graph constructed: {G.number_of_nodes()} total nodes.")






