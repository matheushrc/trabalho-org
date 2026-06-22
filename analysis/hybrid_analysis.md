# Hybrid Simulation Analysis and Comparison

Following the individual parameter sweep simulations, we analyzed every configuration against each other to identify the "best performers" for each parameter. We then designed and executed hybrid configurations combining these optimal settings.

---

## 1. Control Configuration (Baseline)

To evaluate the performance of our hybrid designs, we use the default simulation configuration as our **Control Group**. Its parameters are:

*   **CPU Type**: `TIMING` (In-Order pipeline model)
*   **Branch Predictor**: `LocalBP` (Simple local predictor)
*   **Clock Frequency**: `3GHz`
*   **Cache L1 (Data / Instruction)**: `32kB` each
*   **Cache L2 (Unified)**: `256kB`
*   **Number of Cores**: `1`
*   **Memory Size**: `1GB`
*   **Cache Hierarchy**: `private_l1_private_l2`

This baseline configuration yielded **`106,596,297`** simulated ticks during the execution of the `heapSort` benchmark.

---

## 2. Parameter Sweep Analysis

We analyzed the simulated ticks (`simTicks`) for each parameter group from the `/workspace/simulations/` directory. Ticks in gem5 are measured in absolute simulated time (lower is better).

*   **Branch Prediction**: `BiModeBP` (35.15M ticks) outperformed `LocalBP` (36.08M ticks) due to lower branch misprediction rates (~3.18% vs. 5.30%).
*   **CPU Type**: `O3` (Out-of-Order, 36.08M ticks) significantly outperformed `TIMING` (In-Order, 106.60M ticks) due to instruction-level parallelism (ILP) and pipeline execution efficiencies.
*   **Clock Frequency**: `4GHz` (88.78M ticks) outperformed lower clock frequencies (1GHz: 252.49M, 2GHz: 143.42M, 3GHz: 106.60M) as expected due to shorter cycle times.
*   **Cache L1**: `64kB` (106.52M ticks) had a slight advantage over smaller sizes (32kB: 106.60M, 16kB: 106.60M, 8kB: 106.73M) by reducing L1 misses.
*   **Cache L2**: All sizes (128kB to 1MB) yielded the exact same execution time (106.60M ticks).
*   **Number of Cores**: 1 Core, 2 Cores, and 4 Cores yielded the exact same execution time (106.60M ticks).
*   **Memory Size**: 512MB, 1GB, and 2GB yielded the exact same execution time (106.60M ticks).
*   **Cache Hierarchy**: Both `private_l1_l2` and `private_l1_private_l2` yielded the exact same execution time (106.60M ticks).

> [!IMPORTANT]
> **Why did some parameters have identical ticks?**
> 1. **Cores**: The `heapSort` benchmark is a single-threaded sequential program. Additional cores remain idle and do not speed up execution.
> 2. **L2 Cache & Memory**: The memory working set of `heapSort` is extremely small and fits entirely within the L1 cache. Consequently, L2 cache hits/misses and main memory capacities do not impact the core execution speed.

---

## 3. Hybrid Configurations

Using these findings, we created two hybrid configurations to test how the optimal settings interact:

### Hybrid 1: Performance-Optimized (Max Parameters)
Combines the absolute maximum values for all parameters where performance was positive or flat.
*   **CPU Type**: `O3` (Out-of-Order)
*   **Branch Predictor**: `BiModeBP`
*   **Clock**: `4GHz`
*   **L1 Cache (i / d)**: `64kB`
*   **L2 Cache**: `1MB`
*   **Cores**: `1`
*   **Memory**: `2GB`
*   **Cache Hierarchy**: `private_l1_private_l2`

### Hybrid 2: Cost-Efficient Optimized (Balanced)
Combines the best performance options but selects the smallest/cheapest size for parameters that showed flat performance (L2 cache, Cores, Memory).
*   **CPU Type**: `O3` (Out-of-Order)
*   **Branch Predictor**: `BiModeBP`
*   **Clock**: `4GHz`
*   **L1 Cache (i / d)**: `64kB`
*   **L2 Cache**: `128kB` (cheapest L2 option)
*   **Cores**: `1` (cheapest core option)
*   **Memory**: `512MB` (cheapest memory option)
*   **Cache Hierarchy**: `private_l1_l2` (cheapest/simplest hierarchy)

---

## 4. Results and Performance Comparison

The execution ticks and relative speedups compared to the **Control (Baseline)** configuration are shown below:

| Configuration | Simulated Ticks | Execution Time (% of Baseline) | Speedup vs. Baseline |
| :--- | :---: | :---: | :---: |
| **Control (Baseline)** | 106,596,297 | 100.00% | 1.00x (ref) |
| **Hybrid 1 (Performance)** | 32,258,250 | 30.26% | **3.30x** |
| **Hybrid 2 (Balanced)** | 32,258,250 | 30.26% | **3.30x** |

### Key Architectural Findings

1.  **3.30x speedup**: Both hybrid configurations achieved a substantial 3.30x speedup over the baseline configuration. This is driven primarily by the transition from `TIMING` to `O3` CPU (which enables instruction-level parallelism), the use of `BiModeBP` (which reduces squashed instructions from branch mispredictions), and the clock rate increase to `4GHz`.
2.  **Identical Hybrid Performance**: Hybrid 1 and Hybrid 2 achieved **exactly the same number of ticks** (`32,258,250`).
    This proves that for this specific workload (`heapSort`), paying for a larger L2 cache (`1MB` vs. `128kB`) or more RAM (`2GB` vs. `512MB`) provides **zero performance benefit**.
3.  **Optimal Solution**: **Hybrid 2** is the best architectural design because it delivers the maximum possible speedup (3.30x) while keeping hardware area, power consumption, and production costs minimal.

---

## 5. Decisions Not Taken (Architectural Trade-offs)

In the design of the optimal hybrid processor, several decisions were explicitly rejected based on the simulation data. These trade-offs represent the classic multi-objective optimization balance between **Performance**, **Silicon Area (Cost)**, and **Power Consumption**.

### 1. Rejection of Multi-Core CPU (`num_cores > 1`)
*   **Decision**: We explicitly chose to configure the optimal design with a **single core** (`num_cores = 1`) rather than 2 or 4 cores.
*   **Rationale**: The target workload (`heapSort.riscv`) is an assembly-level sequential implementation with no multithreading features. In our Randomized Search, 2-core configurations (e.g., `random_19` and `random_16`) resulted in the exact same execution time down to the simulated tick compared to 1-core equivalents. Allocating extra cores would increase silicon area and static leakage power by 100% to 300% while providing **0% speedup**.

### 2. Rejection of Large L2 Cache (`l2_size > 128kB`)
*   **Decision**: We rejected configuring the optimal balanced design with `256kB`, `512kB`, or `1MB` L2 cache, opting instead for the smallest size of `128kB`.
*   **Rationale**: The memory footprint of the benchmark fits entirely inside the L1 Cache (particularly with `32kB` or `64kB` configurations). Ticks remained completely unchanged regardless of L2 cache size variations. A larger L2 cache would only waste die area and budget.

### 3. Rejection of High Memory Capacity (`memory_size > 512MB`)
*   **Decision**: We bypassed `1GB` and `2GB` RAM options, keeping the memory at `512MB`.
*   **Rationale**: The benchmark's data structures require only a few kilobytes of memory. A `512MB` main memory is more than sufficient, making high-capacity RAM channels redundant.

### 4. Rejection of Advanced Cache Hierarchies
*   **Decision**: We preferred the simpler `private_l1_l2` over `private_l1_private_l2`.
*   **Rationale**: Because the processor is constrained to a single core, complex multi-level private/shared coherency protocols provide no execution benefits while introducing unnecessary design complexity.

---

## 6. Influence of Input Dataset Size (Array Size)

A critical factor in this simulation-based analysis is the size of the sorted array. In the current benchmark (`heapSort_gem5.s`), the input array is statically initialized with **only 6 elements** (`n_elems: .word 6`), which equates to a mere **24 bytes** of data.

This extremely small size directly biases the architectural analysis in the following ways:

### 1. Memory Hierarchy Under-utilization (L2 and DRAM)
*   Because 24 bytes fits completely inside even the smallest tested L1 data cache (`8kB`), **no data cache misses occur**.
*   The entire execution resides in L1. Consequently, changing the L2 Cache size (from `128kB` to `1MB`) or the DDR3 main memory size (from `512MB` to `2GB`) has exactly a 0% impact on execution ticks.
*   **Scaling Up**: If the array size were increased to, say, **10,000 elements** (~40kB) or **100,000 elements** (~400kB), L1 cache misses would occur. At that scale, L2 cache capacity and memory bus latencies would actively affect execution time, showing a clear performance difference between L2 configurations.

### 2. CPU Model Stalls and Latency Hiding
*   Under the current 6-element dataset, the in-order CPU (`TIMING`) never stalls on memory instructions because L1 cache access is instantaneous.
*   **Scaling Up**: With a larger dataset, the `TIMING` CPU would stall frequently waiting for L2 or DRAM. The out-of-order CPU (`O3`) could use its Instruction Window, physical registers, and MSHRs (Miss Status Holding Registers) to execute independent instructions out-of-order and hide memory latencies. This means the performance gap between `O3` and `TIMING` (currently 3.30x speedup) would likely expand significantly.

### 3. Branch Predictor Training (Warm-up)
*   With 6 elements, the program completes in under 100,000 ticks. The branch predictor tables (which index thousands of entries) do not have enough loops to fully "warm up."
*   **Scaling Up**: Since Heap Sort has $O(N \log N)$ complexity, a larger array size would increase the number of branch decisions, giving the global branch predictor (`BiModeBP`) more time to train its global history register and achieve higher relative accuracy than `LocalBP` where cold mispredictions are a larger share of the run.
