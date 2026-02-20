import pandas as pd
from flask import Flask, request, jsonify, render_template
import networkx as nx
import time
from datetime import datetime
from flask_cors import CORS
import math  # <--- Ye MISSING tha!
import json  # <--- Isey upar move kar diya

app = Flask(__name__)
# Sabhi origins aur methods allow karne ke liye detail CORS setup
CORS(app, resources={r"/*": {"origins": "*"}})

# REQUIRED_COLUMNS mein 'timestamp' add kiya gaya hai taaki validation fail na ho
REQUIRED_COLUMNS = ['transaction_id', 'sender_id', 'receiver_id', 'amount', 'timestamp']

def validate_csv(df):
    """Check if uploaded CSV has exact required columns"""
    return all(col in df.columns for col in REQUIRED_COLUMNS)

def detect_fraud(df):
    # Timestamp conversion (Must be in CSV)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    G = nx.from_pandas_edgelist(df, 'sender_id', 'receiver_id', create_using=nx.DiGraph())
    
    fraud_rings = []
    suspicious_accounts = {}

    # 1. Cycle Detection (Fraud Rings) - O(V+E) Logic
    all_cycles = list(nx.simple_cycles(G))
    for i, cycle in enumerate(all_cycles):
        if 3 <= len(cycle) <= 5:
            r_id = f"RING_CYCLE_{i+1}"
            fraud_rings.append({
                "ring_id": r_id, 
                "member_accounts": cycle, 
                "pattern_type": "cycle", 
                "risk_score": 95.0
            })
            for acc in cycle:
                suspicious_accounts[acc] = {
                    "account_id": acc, 
                    "suspicion_score": 98.0, 
                    "detected_patterns": ["cycle_detected"], 
                    "ring_id": r_id
                }

    # 2. Smurfing Detection (High frequency in 72h window)
    for node in G.nodes():
        node_txns = df[df['receiver_id'] == node].sort_values('timestamp')
        if len(node_txns) >= 10:
            # 72 hours window logic
            window_duration = (node_txns['timestamp'].iloc[9] - node_txns['timestamp'].iloc[0]).total_seconds()
            
            if window_duration <= 259200: 
                s_id = f"RING_SMURF_{node}"
                members = list(node_txns['sender_id'].unique()) + [node]
                fraud_rings.append({
                    "ring_id": s_id, 
                    "member_accounts": members, 
                    "pattern_type": "fan-in_72h", 
                    "risk_score": 88.0
                })
                
                if node not in suspicious_accounts:
                    suspicious_accounts[node] = {
                        "account_id": node, 
                        "suspicion_score": 90.0, 
                        "detected_patterns": ["high_frequency_smurfing_72h"], 
                        "ring_id": s_id
                    }

    # 3. Layering/Shell Detection
    for node in G.nodes():
        paths = nx.single_source_shortest_path_length(G, node, cutoff=3)
        long_chains = [target for target, length in paths.items() if length >= 3]
        
        if long_chains:
            l_id = f"SHELL_{node}"
            if node not in suspicious_accounts:
                suspicious_accounts[node] = {
                    "account_id": node, 
                    "suspicion_score": 75.0, 
                    "detected_patterns": ["layered_shell_chain"], 
                    "ring_id": l_id
                }

    return list(suspicious_accounts.values()), fraud_rings

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def upload_file():
    start_time = time.time()
    
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    
    try:
        df = pd.read_csv(file)
        
        if not validate_csv(df):
            return jsonify({"error": "Invalid CSV structure. Required: transaction_id, sender_id, receiver_id, amount, timestamp"}), 400
        
        susp_accs, rings = detect_fraud(df)
        
        total_nodes = len(set(df['sender_id']).union(set(df['receiver_id'])))
        
        output = {
            "suspicious_accounts": sorted(susp_accs, key=lambda x: x['suspicion_score'], reverse=True),
            "fraud_rings": rings,
            "summary": {
                "total_accounts_analyzed": int(total_nodes),
                "suspicious_accounts_flagged": len(susp_accs),
                "fraud_rings_detected": len(rings),
                "processing_time_seconds": round(time.time() - start_time, 2)
            }
        }
        
        # Safe JSON Serialization
        response_data = json.loads(json.dumps(output, default=lambda x: None if isinstance(x, float) and math.isnan(x) else str(x)))

        return jsonify(response_data)
        
    except Exception as e:
        print(f"Error processing file: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)