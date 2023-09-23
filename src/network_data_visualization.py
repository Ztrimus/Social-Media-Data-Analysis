'''
File: network_data_visualization.py
Project: src
File Created: 22nd Sep 2023 8:50 pm, Friday
Author: Saurabh Zinjad (GitHub: Ztrimus)
Email: zinjadsaurabh1997@gmail.com

Copyright (c) 2023 Saurabh Zinjad
'''

import json
import config
import networkx as nx
import matplotlib.pyplot as plt

# Open the JSON file in read mode
json_file_path = config.JSON_DATA_PATH
with open(json_file_path, "r") as json_file:
    data = json.load(json_file)

relational_data = []
for user in data:
    if len(user['followers']) or len(user['followings']):
        relational_data.append(user)

print(f"connected nodes: {len(relational_data)}")

# Initialize a directed graph for the Friendship Network
G = nx.DiGraph()

# Add nodes (users) to the graph
for user in data:
    username = user['username']
    G.add_node(username)

# Add directed edges based on follower and followee relationships
for user in data:
    username = user['username']
    followings = user['followings']  # Assuming 'followings' contains user IDs being followed
    for following_user_id in followings:
        following_user = next((x for x in data if x['id'] == following_user_id), None)
        if following_user:
            following_username = following_user['username']
            G.add_edge(username, following_username)

# Visualize the Friendship Network (optional)
pos = nx.spring_layout(G)
plt.figure(figsize=(12, 12))
nx.draw(G, pos, node_size=10, node_color='skyblue', with_labels=True, font_size=8, font_color='black', font_weight='bold', arrowsize=5)
plt.title("Friendship Network")
plt.show()