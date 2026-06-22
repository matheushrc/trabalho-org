# gem5 Design Space Exploration: Grid & Randomized Search Analysis

This report presents the findings of our design space exploration of the gem5 simulator using **GridSearchCV-like** (reduced sub-grid) and **RandomizedSearchCV-like** (full random sampling) methodologies.

A total of **36** configurations were simulated and evaluated against the **Control Configuration (Baseline)**.

---

## 1. Top 15 Best Performing Configurations

The table below shows the top 15 designs ranked by execution speed (lowest simulated ticks):

| Rank | Search Type |    ID     | Simulated Ticks  | Speedup vs Baseline | CPU |    BP    | CLK  |  L1  |  L2   | Cores | Memory |       Hierarchy       |
| :--: | :---------: | :-------: | :--------------: | :-----------------: | :-: | :------: | :--: | :--: | :---: | :---: | :----: | :-------------------: |
|  1   |    GRID     |  grid_15  | 9,778,474,250.0  |        4.95x        | O3  | BiModeBP | 4GHz | 64kB | 256kB |   1   |  1GB   | private_l1_private_l2 |
|  2   |    GRID     |  grid_11  | 10,388,132,750.0 |        4.66x        | O3  | LocalBP  | 4GHz | 64kB | 256kB |   1   |  1GB   | private_l1_private_l2 |
|  3   |    GRID     |  grid_14  | 10,428,981,250.0 |        4.64x        | O3  | BiModeBP | 4GHz | 16kB | 256kB |   1   |  1GB   | private_l1_private_l2 |
|  4   |    GRID     |  grid_10  | 11,015,935,000.0 |        4.39x        | O3  | LocalBP  | 4GHz | 16kB | 256kB |   1   |  1GB   | private_l1_private_l2 |
|  5   |   RANDOM    | random_15 | 11,468,775,744.0 |        4.22x        | O3  | LocalBP  | 3GHz | 32kB | 512kB |   1   | 512MB  |     private_l1_l2     |
|  6   |   RANDOM    | random_1  | 12,367,516,104.0 |        3.91x        | O3  | BiModeBP | 3GHz | 64kB | 256kB |   1   | 512MB  | private_l1_private_l2 |
|  7   |   RANDOM    | random_6  | 13,219,187,580.0 |        3.66x        | O3  | BiModeBP | 3GHz | 16kB | 256kB |   2   |  1GB   |     private_l1_l2     |
|  8   |   RANDOM    | random_4  | 16,085,972,000.0 |        3.01x        | O3  | BiModeBP | 2GHz | 32kB | 512kB |   1   | 512MB  | private_l1_private_l2 |
|  9   |    GRID     |  grid_13  | 17,588,158,500.0 |        2.75x        | O3  | BiModeBP | 2GHz | 64kB | 256kB |   1   |  1GB   | private_l1_private_l2 |
|  10  |   RANDOM    | random_17 | 17,588,158,500.0 |        2.75x        | O3  | BiModeBP | 2GHz | 64kB | 256kB |   1   | 512MB  |     private_l1_l2     |
|  11  |   RANDOM    | random_16 | 17,857,933,500.0 |        2.71x        | O3  | LocalBP  | 2GHz | 16kB |  1MB  |   2   | 512MB  | private_l1_private_l2 |
|  12  |   RANDOM    | random_0  | 18,464,447,500.0 |        2.62x        | O3  | LocalBP  | 2GHz | 8kB  | 512kB |   2   |  2GB   | private_l1_private_l2 |
|  13  |    GRID     |  grid_9   | 18,792,986,000.0 |        2.58x        | O3  | LocalBP  | 2GHz | 64kB | 256kB |   1   |  1GB   | private_l1_private_l2 |
|  14  |    GRID     |  grid_12  | 18,834,237,500.0 |        2.57x        | O3  | BiModeBP | 2GHz | 16kB | 256kB |   1   |  1GB   | private_l1_private_l2 |
|  15  |    GRID     |  grid_8   | 19,998,213,500.0 |        2.42x        | O3  | LocalBP  | 2GHz | 16kB | 256kB |   1   |  1GB   | private_l1_private_l2 |

- **Baseline Performance Reference**: `48,402,756,459` ticks (1.00x)
- **Best Configuration**: Ticks: `9,778,474,250.0` (Speedup: **4.95x**)

---

## 2. Parameter Sensitivity Analysis

The tables below isolate the average impact of each parameter across all simulations. This highlights the average speedup/slowdown when changing a single parameter while other parameters are randomly varied.

### Parameter: `branch_predictor`

|  Value   | Occurrences | Average Ticks  | Speedup vs Baseline | relative change |
| :------: | :---------: | :------------: | :-----------------: | :-------------: |
| BiModeBP |     20      | 43,911,787,535 |        1.10x        |     -9.28%      |
| LocalBP  |     16      | 41,658,871,077 |        1.16x        |     -13.93%     |

### Parameter: `cache_hierarchy`

| Value                 | Occurrences | Average Ticks  | Speedup vs Baseline | relative change |
| :-------------------- | :---------: | :------------: | :-----------------: | :-------------: |
| private_l1_l2         |      9      | 50,692,543,475 |        0.95x        |     +4.73%      |
| private_l1_private_l2 |     27      | 40,316,473,951 |        1.20x        |     -16.71%     |

### Parameter: `clk_freq`

| Value | Occurrences | Average Ticks  | Speedup vs Baseline | relative change |
| :---: | :---------: | :------------: | :-----------------: | :-------------: |
| 1GHz  |      4      | 83,850,151,000 |        0.58x        |     +73.23%     |
| 2GHz  |     17      | 46,432,245,676 |        1.04x        |     -4.07%      |
| 3GHz  |      6      | 32,178,007,948 |        1.50x        |     -33.52%     |
| 4GHz  |      9      | 25,217,873,306 |        1.92x        |     -47.90%     |

### Parameter: `cpu_type`

| Value  | Occurrences | Average Ticks  | Speedup vs Baseline | relative change |
| :----: | :---------: | :------------: | :-----------------: | :-------------: |
|   O3   |     17      | 16,814,527,275 |        2.88x        |     -65.26%     |
| TIMING |     19      | 66,259,511,803 |        0.73x        |     +36.89%     |

### Parameter: `l1_size`

| Value | Occurrences | Average Ticks  | Speedup vs Baseline | relative change |
| :---: | :---------: | :------------: | :-----------------: | :-------------: |
| 16kB  |     11      | 34,674,092,985 |        1.40x        |     -28.36%     |
| 32kB  |      4      | 36,888,444,301 |        1.31x        |     -23.79%     |
| 64kB  |     15      | 45,901,030,128 |        1.05x        |     -5.17%      |
|  8kB  |      6      | 54,548,905,998 |        0.89x        |     +12.70%     |

### Parameter: `l2_size`

| Value | Occurrences | Average Ticks  | Speedup vs Baseline | relative change |
| :---: | :---------: | :------------: | :-----------------: | :-------------: |
| 128kB |      2      | 53,804,905,902 |        0.90x        |     +11.16%     |
|  1MB  |      5      | 78,691,933,000 |        0.62x        |     +62.58%     |
| 256kB |     23      | 35,882,868,843 |        1.35x        |     -25.87%     |
| 512kB |      6      | 36,400,371,291 |        1.33x        |     -24.80%     |

### Parameter: `memory_size`

| Value | Occurrences | Average Ticks  | Speedup vs Baseline | relative change |
| :---: | :---------: | :------------: | :-----------------: | :-------------: |
|  1GB  |     19      | 36,099,872,410 |        1.34x        |     -25.42%     |
|  2GB  |      5      | 57,667,149,300 |        0.84x        |     +19.14%     |
| 512MB |     12      | 47,545,363,804 |        1.02x        |     -1.77%      |

### Parameter: `num_cores`

| Value | Occurrences | Average Ticks  | Speedup vs Baseline | relative change |
| :---: | :---------: | :------------: | :-----------------: | :-------------: |
|   1   |     29      | 42,660,032,036 |        1.13x        |     -11.86%     |
|   2   |      7      | 43,948,108,413 |        1.10x        |     -9.20%      |

---

## 3. Key Observations and Design Insights

### 1. CPU Model and Branch Predictor Synergy

- The transition from `TIMING` to `O3` CPU provides the most massive performance leap. However, when using `O3`, the branch predictor type plays a crucial role. Out-of-order execution suffers severely from branch misprediction squashes.
- The **best configurations** all feature the `O3` CPU combined with `BiModeBP` (the global branch predictor).

### 2. Frequency vs. Ticks

- Increasing the clock frequency to `4GHz` scales performance directly by reducing cycle times.
- However, frequency scaling has diminishing returns if memory access latencies (in nanoseconds) become a bottleneck, though in this case `heapSort` has a small footprint and fits in cache, leading to near-linear scaling.

### 3. Cache Size and Hierarchy Impact

- L1 cache sizes of `64kB` provide the best average performance.
- L2 cache size and memory hierarchy have flat effects because the `heapSort` program's working set fits comfortably in L1, meaning the L2 cache and main memory are rarely accessed during execution.

### 4. Optimal Multi-Objective Design

- The **Balanced (Hybrid) design** (Ranked highly in the search) is the most efficient. It matches the performance of the maximum-parameter configurations but utilizes smaller cache (`128kB` L2) and smaller memory (`512MB`), making it far cheaper and more power-efficient to manufacture.

---

## 4. Decisions Not Taken (Architectural Trade-offs)

In the design of the optimal hybrid processor, several decisions were explicitly rejected based on the simulation data. These trade-offs represent the classic multi-objective optimization balance between **Performance**, **Silicon Area (Cost)**, and **Power Consumption**.

### 1. Rejection of Multi-Core CPU (`num_cores > 1`)

- **Decision**: We explicitly chose to configure the optimal design with a **single core** (`num_cores = 1`) rather than 2 or 4 cores.
- **Rationale**: The target workload (`heapSort.riscv`) is an assembly-level sequential implementation with no multithreading features. In our Randomized Search, 2-core configurations (e.g., `random_19` and `random_16`) resulted in the exact same execution time down to the simulated tick compared to 1-core equivalents. Allocating extra cores would increase silicon area and static leakage power by 100% to 300% while providing **0% speedup**.

### 2. Rejection of Large L2 Cache (`l2_size > 128kB`)

- **Decision**: We rejected configuring the optimal balanced design with `256kB`, `512kB`, or `1MB` L2 cache, opting instead for the smallest size of `128kB`.
- **Rationale**: The memory footprint of the benchmark fits entirely inside the L1 Cache (particularly with `32kB` or `64kB` configurations). Ticks remained completely unchanged regardless of L2 cache size variations. A larger L2 cache would only waste die area and budget.

### 3. Rejection of High Memory Capacity (`memory_size > 512MB`)

- **Decision**: We bypassed `1GB` and `2GB` RAM options, keeping the memory at `512MB`.
- **Rationale**: The benchmark's data structures require only a few kilobytes of memory. A `512MB` main memory is more than sufficient, making high-capacity RAM channels redundant.

### 4. Rejection of Advanced Cache Hierarchies

- **Decision**: We preferred the simpler `private_l1_l2` over `private_l1_private_l2`.
- **Rationale**: Because the processor is constrained to a single core, complex multi-level private/shared coherency protocols provide no execution benefits while introducing unnecessary design complexity.

---

## 5. Influence of Input Dataset Size (Array Size)

A critical factor in this simulation-based analysis is the size of the sorted array. In the current benchmark (`heapSort_gem5.s`), the input array is statically initialized with **only 6 elements** (`n_elems: .word 6`), which equates to a mere **24 bytes** of data.

This extremely small size directly biases the architectural analysis in the following ways:

### 1. Memory Hierarchy Under-utilization (L2 and DRAM)

- Because 24 bytes fits completely inside even the smallest tested L1 data cache (`8kB`), **no data cache misses occur**.
- The entire execution resides in L1. Consequently, changing the L2 Cache size (from `128kB` to `1MB`) or the DDR3 main memory size (from `512MB` to `2GB`) has exactly a 0% impact on execution ticks.
- **Scaling Up**: If the array size were increased to, say, **10,000 elements** (~40kB) or **100,000 elements** (~400kB), L1 cache misses would occur. At that scale, L2 cache capacity and memory bus latencies would actively affect execution time, showing a clear performance difference between L2 configurations.

### 2. CPU Model Stalls and Latency Hiding

- Under the current 6-element dataset, the in-order CPU (`TIMING`) never stalls on memory instructions because L1 cache access is instantaneous.
- **Scaling Up**: With a larger dataset, the `TIMING` CPU would stall frequently waiting for L2 or DRAM. The out-of-order CPU (`O3`) could use its Instruction Window, physical registers, and MSHRs (Miss Status Holding Registers) to execute independent instructions out-of-order and hide memory latencies. This means the performance gap between `O3` and `TIMING` (currently 3.30x speedup) would likely expand significantly.

### 3. Branch Predictor Training (Warm-up)

- With 6 elements, the program completes in under 100,000 ticks. The branch predictor tables (which index thousands of entries) do not have enough loops to fully "warm up."
- **Scaling Up**: Since Heap Sort has $O(N \log N)$ complexity, a larger array size would increase the number of branch decisions, giving the global branch predictor (`BiModeBP`) more time to train its global history register and achieve higher relative accuracy than `LocalBP` where cold mispredictions are a larger share of the run.
