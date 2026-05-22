import pandas as pd
import numpy as np
import random
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score


# 1. Feature Extraction Function
def extract_path_features(graph, path):
    """Converts a path into a ML vector."""
    edge_probs = []
    node_evs = []
    out_degrees = []

    for i in range(len(path) - 1):
        u, v = path[i], path[i+1]
        edge_probs.append(graph[u][v].get('weight', 0.0))
        node_evs.append(graph.nodes[v].get('expected_value', 0.0))
        out_degrees.append(graph.out_degree(v))

    return {
        'path_length': len(path),
        'avg_edge_prob': np.mean(edge_probs) if edge_probs else 0,
        'min_edge_prob': np.min(edge_probs) if edge_probs else 0, # Bottlenecks or bridges
        'avg_expected_value': np.mean(node_evs) if node_evs else 0,
        'terminal_node_ev': node_evs[-1] if node_evs else 0,
        'avg_out_degree': np.mean(out_degrees) if out_degrees else 0
    }


def generate_training_data(G, walks_per_start=20, walk_length=5, top_start_nodes=50):
    # 2. Generate a Training Dataset via Random Walks
    training_data = []

    # 1000 random walks starting from highly visited nodes
    walk_starts = [n for n, d in sorted(G.out_degree(), key=lambda x: x[1], reverse=True)[:top_start_nodes]]

    for start_node in walk_starts:
        for _ in range(walks_per_start): # 20 walks per start node
            current_node = start_node
            path = [current_node]
            path_score = 0.0

            for _ in range(walk_length):
                successors = list(G.successors(current_node))
                if not successors:
                    break

                next_node = random.choice(successors)

                # score (Our Target Variable 'y')
                step_prob = G[current_node][next_node].get('weight', 0.0)
                step_ev = G.nodes[next_node].get('expected_value', 0.0)
                path_score += (step_prob * step_ev)

                path.append(next_node)
                current_node = next_node

            if len(path) > 2: # Only keep meaningful paths
                features = extract_path_features(G, path)
                features['target_score'] = path_score
                training_data.append(features)

    return pd.DataFrame(training_data)


def train_random_forest_regressor(G, top_paths=None, test_size=0.2, random_state=42):
    df = generate_training_data(G)

    # 3. Train the Regression Model
    print(f"Training Random Forest on {len(df)} paths...")
    X = df.drop(columns=['target_score'])
    y = df['target_score']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=random_state)

    model = RandomForestRegressor(n_estimators=100, random_state=random_state)
    model.fit(X_train, y_train)

    # Evaluate the model
    y_pred = model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))

    print("\nModel Performance:")
    print(f"R-squared Score: {r2:.4f} (How well topology predicts outcome)")
    print(f"Root Mean Squared Error: {rmse:.4f}")

    # Feature Importance
    importances = model.feature_importances_
    feature_names = X.columns
    print("\nMost Critical Structural Features for Winning:")
    for name, importance in sorted(zip(feature_names, importances), key=lambda x: x[1], reverse=True):
        print(f"- {name}: {importance:.3f}")

    if top_paths is not None:
        # Top 5 Algorithm Paths!
        print("\nTesting ML Model against our Top 5 DFS Paths:")
        for i, (path, actual_score) in enumerate(top_paths):
            path_features = pd.DataFrame([extract_path_features(G, path)])
            predicted_score = model.predict(path_features)[0]
            print(f"Rank {i+1} Path | Math Score: {actual_score:.4f} | ML Predicted Score: {predicted_score:.4f}")

    return model, df, X_test, y_test, y_pred, r2, rmse
