import networkx as nx
import json
import chess

file_path = 'chess_graph_2015_05_6k.json'

with open(file_path, 'r') as file:
    raw_data = json.load(file)

print("leng")
print(len(raw_data))

# 2. Sort the data by 'total_visits' descending
# This ensures the starting position (most visits) is at index 0
sorted_items = sorted(
    raw_data.items(), 
    key=lambda item: item[1].get('total_visits', 0), 
    reverse=True
)

# Convert back to an ordered dictionary
ordered_data = dict(sorted_items)

# 3. Construct the Directed Graph
G = nx.DiGraph()

# Add nodes first to preserve the 'topological' visit-based order
for node_hash, node_info in ordered_data.items():
    G.add_node(node_hash, 
               fen=node_info.get('fen'),
               visits=node_info.get('total_visits'),
               outcomes=node_info.get('outcomes'))

# Now add the edges
for node_hash, node_info in ordered_data.items():
    edges = node_info.get('edges', {})
    for next_hash, edge_data in edges.items():
        # We only add edges if the destination exists in our node list
        if G.has_node(next_hash):
            G.add_edge(node_hash, next_hash, 
                       weight=edge_data['prob'], 
                       count=edge_data['count'])

# 4. Verify the "First" Node
first_node_hash = list(ordered_data.keys())[0]
first_node_data = G.nodes[first_node_hash]

print(f"Total Nodes: {G.number_of_nodes()}")
print(f"First Node Hash: {first_node_hash}")
print(f"First Node Visits: {first_node_data['visits']}")
print(f"First Node FEN: {first_node_data['fen']}")

# Display the board of the first node
if first_node_data['fen']:
    print("\n--- Visual Confirmation of First Node ---")
    print(chess.Board(first_node_data['fen']))

