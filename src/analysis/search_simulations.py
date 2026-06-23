import subprocess
import os
import json
import random
import time
from itertools import product
from multiprocessing import Pool, cpu_count

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

# Full parameter space
PARAM_GRID = {
    'cpu_type': ['TIMING', 'O3'],
    'branch_predictor': ['LocalBP', 'BiModeBP'],
    'clk_freq': ['1GHz', '2GHz', '3GHz', '4GHz'],
    'l1_size': ['8kB', '16kB', '32kB', '64kB'], # we will set both l1d and l1i to this value
    'l2_size': ['128kB', '256kB', '512kB', '1MB'],
    'num_cores': [1, 2],
    'memory_size': ['512MB', '1GB', '2GB'],
    'cache_hierarchy': ['private_l1_l2', 'private_l1_private_l2']
}

# Sub-grid for Reduced Grid Search (16 configs)
REDUCED_GRID = {
    'cpu_type': ['TIMING', 'O3'],
    'branch_predictor': ['LocalBP', 'BiModeBP'],
    'clk_freq': ['2GHz', '4GHz'],
    'l1_size': ['16kB', '64kB']
}

def run_simulation(config, outdir):
    """Runs a single gem5 simulation with the specified configuration."""
    os.makedirs(outdir, exist_ok=True)
    
    # Map l1_size to l1d and l1i
    l1_size = config['l1_size']
    
    cmd = [
        "docker", "exec", "gem5",
        "/gem5/build/RISCV/gem5.opt",
        f"--outdir=/workspace/simulations/search/{outdir.split('/')[-1]}",
        f"--stats-file=json:///workspace/simulations/search/{outdir.split('/')[-1]}/stats.json",
        "/workspace/src/models/inorder.py",
        "--binary", "/workspace/src/heapSort_100k.riscv",
        "--cpu-type", config['cpu_type'],
        "--branch-predictor", config['branch_predictor'],
        "--clk-freq", config['clk_freq'],
        "--l1d-size", l1_size,
        "--l1i-size", l1_size,
        "--l2-size", config.get('l2_size', '256kB'),
        "--num-cores", str(config.get('num_cores', 1)),
        "--memory-size", config.get('memory_size', '1GB'),
        "--cache-hierarchy", config.get('cache_hierarchy', 'private_l1_private_l2')
    ]
    
    # Run command
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = process.communicate()
    
    if process.returncode != 0:
        return False, stderr
    return True, stdout

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
        return first_elem.get('simTicks', {}).get('value')
    except Exception as e:
        return None

def worker_task(task_args):
    idx, total, search_type, outdir_name, config, base_dir = task_args
    outdir = os.path.join(base_dir, outdir_name)
    
    print(f"[{search_type.upper()}] Starting [{idx+1}/{total}] ID={outdir_name}: CPU={config['cpu_type']}, BP={config['branch_predictor']}, CLK={config['clk_freq']}, L1={config['l1_size']}")
    start = time.time()
    success, err = run_simulation(config, outdir)
    elapsed = time.time() - start
    
    ticks = load_sim_ticks(os.path.join(outdir, 'stats.json'))
    if success and ticks:
        print(f"[{search_type.upper()}] Finished [{idx+1}/{total}] ID={outdir_name}: Success. Ticks: {ticks:,.0f} (Took {elapsed:.1f}s)")
        return {
            'search_type': search_type,
            'id': outdir_name,
            'ticks': ticks,
            'config': config,
            'elapsed': elapsed,
            'success': True
        }
    else:
        print(f"[{search_type.upper()}] Finished [{idx+1}/{total}] ID={outdir_name}: FAILED! (Took {elapsed:.1f}s) Error: {err}")
        return {
            'search_type': search_type,
            'id': outdir_name,
            'ticks': None,
            'config': config,
            'elapsed': elapsed,
            'success': False,
            'error': err
        }

def main():
    base_dir = os.path.join(ROOT, 'simulations', 'search')
    os.makedirs(base_dir, exist_ok=True)
    
    tasks = []
    
    # ---------------------------------------------------------
    # 1. GridSearchCV (Reduced Sub-Grid: 16 combinations)
    # ---------------------------------------------------------
    grid_keys = list(REDUCED_GRID.keys())
    grid_values = [REDUCED_GRID[k] for k in grid_keys]
    combinations = list(product(*grid_values))
    
    for idx, combo in enumerate(combinations):
        config = dict(zip(grid_keys, combo))
        config['l2_size'] = '256kB'
        config['num_cores'] = 1
        config['memory_size'] = '1GB'
        config['cache_hierarchy'] = 'private_l1_private_l2'
        
        outdir_name = f"grid_{idx}"
        tasks.append((idx, len(combinations), 'grid', outdir_name, config, base_dir))

    # ---------------------------------------------------------
    # 2. RandomizedSearchCV (20 random combinations from full grid)
    # ---------------------------------------------------------
    num_samples = 20
    sampled_configs = []
    attempts = 0
    while len(sampled_configs) < num_samples and attempts < 1000:
        attempts += 1
        config = {
            'cpu_type': random.choice(PARAM_GRID['cpu_type']),
            'branch_predictor': random.choice(PARAM_GRID['branch_predictor']),
            'clk_freq': random.choice(PARAM_GRID['clk_freq']),
            'l1_size': random.choice(PARAM_GRID['l1_size']),
            'l2_size': random.choice(PARAM_GRID['l2_size']),
            'num_cores': random.choice(PARAM_GRID['num_cores']),
            'memory_size': random.choice(PARAM_GRID['memory_size']),
            'cache_hierarchy': random.choice(PARAM_GRID['cache_hierarchy'])
        }
        if config not in sampled_configs:
            sampled_configs.append(config)
            
    for idx, config in enumerate(sampled_configs):
        outdir_name = f"random_{idx}"
        tasks.append((idx, num_samples, 'random', outdir_name, config, base_dir))

    total_sims = len(tasks)
    # Set number of workers based on available cores (leave some headroom)
    cores_avail = cpu_count()
    num_workers = max(1, min(8, cores_avail - 2))
    
    print("=" * 60)
    print(f"  DESIGN SPACE EXPLORATION (Parallel execution)")
    print("=" * 60)
    print(f"  Total simulations scheduled: {total_sims}")
    print(f"  Available CPU cores        : {cores_avail}")
    print(f"  Concurrent worker processes: {num_workers}")
    print("=" * 60)
    print("Starting execution pool...\n")
    
    start_all = time.time()
    
    # Run tasks using multiprocessing Pool
    results = []
    with Pool(processes=num_workers) as pool:
        worker_results = pool.map(worker_task, tasks)
        
    for res in worker_results:
        if res['success'] and res['ticks'] is not None:
            results.append(res)
            
    elapsed_all = time.time() - start_all
    
    # Write summary analysis
    results.sort(key=lambda x: x['ticks'])
    
    # Save raw results to JSON
    raw_results_path = os.path.join(ROOT, 'analysis', 'search_raw_results.json')
    with open(raw_results_path, 'w') as f:
        out_data = [{
            'search_type': r['search_type'],
            'id': r['id'],
            'ticks': r['ticks'],
            'config': r['config']
        } for r in results]
        json.dump(out_data, f, indent=2)
        
    print("\n" + "=" * 60)
    print(f"Completed search in {elapsed_all:.1f}s ({elapsed_all/60:.1f} minutes)!")
    print(f"Saved raw results to {raw_results_path}")
    print("=" * 60)
    print("\nTop 5 Best Performing Configurations:")
    for i, res in enumerate(results[:5]):
        c = res['config']
        print(f"{i+1}. Ticks: {res['ticks']:,.0f} | CPU: {c['cpu_type']} | BP: {c['branch_predictor']} | CLK: {c['clk_freq']} | L1: {c['l1_size']} | L2: {c['l2_size']} ({res['search_type'].upper()} id: {res['id']})")
    print("=" * 60)

if __name__ == "__main__":
    main()
