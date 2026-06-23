import os
import json

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
base_dir = os.path.join(ROOT, 'simulations')

groups = {
    'branch_prediction': ['LocalBP', 'BiModeBP'],
    'cpu_type': ['TIMING', 'O3'],
    'clock_freq': ['1GHz', '2GHz', '3GHz', '4GHz'],
    'cache_l1': ['8kB', '16kB', '32kB', '64kB'],
    'cache_l2': ['128kB', '256kB', '512kB', '1MB'],
    'num_cores': ['1core', '2cores', '4cores'],
    'memory': ['512MB', '1GB', '2GB'],
    'cache_hierarchy': ['private_l1_l2', 'private_l1_private_l2']
}

def load_sim_ticks(stats_path):
    if not os.path.exists(stats_path):
        return None
    try:
        with open(stats_path, 'r') as f:
            data = json.load(f)
        if isinstance(data, list):
            first_elem = data[0]
        else:
            first_elem = data
        
        # Extract simTicks
        sim_ticks = first_elem.get('simTicks', {}).get('value')
        return sim_ticks
    except Exception as e:
        return f"Error: {e}"

results = {}

for group_name, configs in groups.items():
    results[group_name] = {}
    for config in configs:
        stats_path = os.path.join(base_dir, group_name, config, 'stats.json')
        ticks = load_sim_ticks(stats_path)
        results[group_name][config] = ticks

# Print results
for group_name, configs in results.items():
    print(f"\nGroup: {group_name}")
    print("-" * 40)
    best_config = None
    min_ticks = float('inf')
    
    for config, ticks in configs.items():
        if ticks is None:
            print(f"  {config:<25}: N/A (File not found)")
        elif isinstance(ticks, str) and ticks.startswith("Error"):
            print(f"  {config:<25}: {ticks}")
        else:
            print(f"  {config:<25}: {ticks:,.0f} ticks")
            if ticks < min_ticks:
                min_ticks = ticks
                best_config = config
    
    if best_config:
        print(f"  => Best Performer: {best_config} ({min_ticks:,.0f} ticks)")
