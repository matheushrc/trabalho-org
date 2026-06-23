import subprocess
import os
import json
import time

def run_command(cmd):
    print(f"Running command: {' '.join(cmd)}")
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    # Wait for the process to finish
    stdout, stderr = process.communicate()
    
    if process.returncode != 0:
        print(f"Command failed with return code {process.returncode}")
        print(f"Stderr:\n{stderr}")
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

def main():
    # Define paths
    root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
    simulations_dir = os.path.join(root, 'simulations')
    hybrids_dir = os.path.join(simulations_dir, 'hybrids')
    os.makedirs(hybrids_dir, exist_ok=True)
    
    # Hybrid 1: Performance-Optimized
    # Combining O3 CPU, BiModeBP, 4GHz clock, 64kB L1 cache, 1MB L2 cache, 2GB Memory, 1 Core.
    perf_out = os.path.join(hybrids_dir, 'performance')
    perf_cmd = [
        "docker", "exec", "gem5", 
        "/gem5/build/RISCV/gem5.opt", 
        f"--outdir=/workspace/simulations/hybrids/performance", 
        f"--stats-file=json:///workspace/simulations/hybrids/performance/stats.json", 
        "/workspace/src/models/inorder.py", 
        "--binary", "/workspace/src/heapSort_100k.riscv",
        "--cpu-type", "O3",
        "--branch-predictor", "BiModeBP",
        "--clk-freq", "4GHz",
        "--l1d-size", "64kB",
        "--l1i-size", "64kB",
        "--l2-size", "1MB",
        "--num-cores", "1",
        "--memory-size", "2GB",
        "--cache-hierarchy", "private_l1_private_l2"
    ]
    
    # Hybrid 2: Cost-Efficient Optimized
    # Combining O3 CPU, BiModeBP, 4GHz clock, 64kB L1 cache, 128kB L2 cache, 512MB Memory, 1 Core, private_l1_l2 hierarchy.
    bal_out = os.path.join(hybrids_dir, 'balanced')
    bal_cmd = [
        "docker", "exec", "gem5", 
        "/gem5/build/RISCV/gem5.opt", 
        f"--outdir=/workspace/simulations/hybrids/balanced", 
        f"--stats-file=json:///workspace/simulations/hybrids/balanced/stats.json", 
        "/workspace/src/models/inorder.py", 
        "--binary", "/workspace/src/heapSort_100k.riscv",
        "--cpu-type", "O3",
        "--branch-predictor", "BiModeBP",
        "--clk-freq", "4GHz",
        "--l1d-size", "64kB",
        "--l1i-size", "64kB",
        "--l2-size", "128kB",
        "--num-cores", "1",
        "--memory-size", "512MB",
        "--cache-hierarchy", "private_l1_l2"
    ]
    
    print("Starting Hybrid 1 (Performance-Optimized) simulation...")
    start_time = time.time()
    success1, _ = run_command(perf_cmd)
    end_time1 = time.time()
    if success1:
        print(f"Hybrid 1 completed in {end_time1 - start_time:.2f} seconds.")
    else:
        print("Hybrid 1 failed.")
        
    print("\nStarting Hybrid 2 (Cost-Efficient Optimized) simulation...")
    start_time = time.time()
    success2, _ = run_command(bal_cmd)
    end_time2 = time.time()
    if success2:
        print(f"Hybrid 2 completed in {end_time2 - start_time:.2f} seconds.")
    else:
        print("Hybrid 2 failed.")

    # Load results and compare
    baseline_ticks = 106596297 # LocalBP, TIMING, 3GHz, 32kB L1, 256kB L2, 1core, 1GB, private_l1_private_l2
    perf_ticks = load_sim_ticks(os.path.join(perf_out, 'stats.json'))
    bal_ticks = load_sim_ticks(os.path.join(bal_out, 'stats.json'))
    
    print("\n" + "="*60)
    print(" HYBRID SIMULATIONS SUMMARY REPORT")
    print("="*60)
    print(f"Baseline (TIMING CPU, LocalBP, 3GHz, 32kB L1, 256kB L2)  : {baseline_ticks:,.0f} ticks (100.0%)")
    
    if perf_ticks:
        perf_pct = (perf_ticks / baseline_ticks) * 100.0
        perf_speedup = baseline_ticks / perf_ticks
        print(f"Hybrid 1 (Performance: O3, BiModeBP, 4GHz, 64kB L1, 1MB L2) : {perf_ticks:,.0f} ticks ({perf_pct:.2f}%) - Speedup: {perf_speedup:.2f}x")
    else:
        print("Hybrid 1 (Performance) : N/A")
        
    if bal_ticks:
        bal_pct = (bal_ticks / baseline_ticks) * 100.0
        bal_speedup = baseline_ticks / bal_ticks
        print(f"Hybrid 2 (Balanced: O3, BiModeBP, 4GHz, 64kB L1, 128kB L2)  : {bal_ticks:,.0f} ticks ({bal_pct:.2f}%) - Speedup: {bal_speedup:.2f}x")
    else:
        print("Hybrid 2 (Balanced)    : N/A")
    print("="*60)

if __name__ == "__main__":
    main()
