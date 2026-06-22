# Analysis of gem5 Branch Predictor Statistics (stats.json)

In gem5 simulations, the branch predictor statistics are exported within a hierarchy inside the `stats.json` file. For a single-core out-of-order CPU configuration, these statistics are located at:
`board.processor.cores.value[0].core.branchPred`

---

## 1. Key Metrics and What They Represent

### Global Lookup and Commit Stats

- **`lookups`** (_Vector2d_): The number of times the branch predictor was queried at the Fetch stage. It represents the total number of branches (including wrong-path branches) fetched.
- **`committed`** (_Vector2d_): The number of branches that actually executed and reached the commit stage (i.e., correct-path branches).
- **`mispredicted`** (_Vector2d_): The number of committed branches that were predicted incorrectly (either direction or target was wrong).

> [!NOTE]
> Why does `LocalBP` have more **`lookups`** than `BiModeBP`?
> When the predictor makes a misprediction, the CPU fetches instructions along the incorrect path. These incorrect paths can contain more branches, which are queried (looked up) but eventually squashed. A worse predictor (`LocalBP`) causes more wrong-path execution, increasing the total number of lookups even though the number of committed branches is identical.

### Misprediction Breakdown

- **`mispredictDueToPredictor`** (_Vector2d_): Committed branches that were mispredicted due to **direction prediction error** (e.g., predicted Taken when it was Not Taken, or vice versa).
- **`mispredictDueToBTBMiss`** (_Vector2d_): Committed branches that were mispredicted because they **missed in the BTB** (Branch Target Buffer). If a branch misses in the BTB, its target is unknown at fetch time, causing a target misprediction even if the direction is predicted correctly.

### Target Providers

- **`targetProvider`** (_Vector2d_): Records which hardware component provided the target address for each lookup. The sum of all provider counts equals the total lookups:
  - `0`: **None / Fallthrough** (No target predicted; fallthrough to PC + instruction size).
  - `1`: **BTB** (Branch Target Buffer).
  - `2`: **RAS** (Return Address Stack).
  - `3`: **Indirect Predictor**.
- **`targetWrong`** (_Vector2d_): Number of branches where the target was incorrect or unavailable at prediction time.

### Component-Specific Stats

#### BTB (Branch Target Buffer)

- **`BTBLookups`**: Total lookups in the BTB.
- **`BTBHits`**: BTB hits (PC was found in the BTB).
- **`BTBUpdates`**: Number of times the BTB contents were updated.
- **`BTBMispredicted`**: The BTB hit but provided the incorrect target (common for indirect branches).
- **`btb.lookups` / `btb.misses` / `btb.updates` / `btb.mispredict`** (_Scalar dicts_): Sub-component metrics broken down by branch type.

#### RAS (Return Address Stack)

Used specifically for predicting return instruction targets (e.g., `ret` / `jr ra`).

- **`ras.pushes`**: Number of call instructions that pushed a return PC onto the RAS.
- **`ras.pops`**: Number of return instructions that popped a target PC from the RAS.
- **`ras.used`**: Number of times the RAS provided the target address.
- **`ras.correct`**: Number of times the RAS target was correct.
- **`ras.incorrect`**: Number of times the RAS target was wrong.

#### Indirect Predictor

Used for predicting targets of indirect branches (e.g., `jr a0`).

- **`indirectLookups`**: Lookups in the indirect predictor.
- **`indirectHits`**: Tag hits in the indirect predictor.
- **`indirectMisses`**: Misses in the indirect predictor.
- **`indirectMispredicted`**: Mispredicted indirect branches.

#### Conditional Predictor (Direction Predictor)

Used for predicting the taken/not-taken direction of conditional branches.

- **`condPredicted`**: Total conditional branch predictions.
- **`condPredictedTaken`**: Conditional branches predicted as Taken.
- **`condIncorrect`**: Conditional branches with incorrect direction prediction.

---

## 2. Vector Index Mappings

For the vector statistics (`lookups`, `committed`, `mispredicted`, etc.), the indices `0` through `7` correspond to the following branch types in gem5:

|  Index  | Branch Type Name |                           Description                           |
| :-----: | :--------------: | :-------------------------------------------------------------: |
| **`0`** |    `NoBranch`    |                     Non-branch instructions                     |
| **`1`** |     `Return`     |           Return instructions (e.g., `ret` / `jr ra`)           |
| **`2`** |   `CallDirect`   |               Direct function calls (e.g., `jal`)               |
| **`3`** |  `CallIndirect`  |             Indirect function calls (e.g., `jalr`)              |
| **`4`** |   `DirectCond`   |        Direct conditional branches (e.g., `beq`, `bne`)         |
| **`5`** |  `DirectUncond`  | Direct unconditional branches (e.g., `j`, `jal` without return) |
| **`6`** |  `IndirectCond`  |           Indirect conditional branches (rarely used)           |
| **`7`** | `IndirectUncond` |        Indirect unconditional branches (e.g., `jr reg`)         |

---

## 3. Comparison: BiModeBP vs. LocalBP

The following table summarizes the performance metrics from the benchmark run on `BiModeBP` (global predictor) and `LocalBP` (local predictor):

|             Metric             | BiModeBP  |  LocalBP  | Difference  |                                           Analysis                                            |
| :----------------------------: | :-------: | :-------: | :---------: | :-------------------------------------------------------------------------------------------: |
|       **Total Lookups**        | 39,218.00 | 46,370.00 | **-15.42%** |           BiModeBP reduces wrong-path execution, fetching 15.4% fewer instructions.           |
|  **Total Committed Branches**  | 30,971.00 | 30,971.00 |  **0.00%**  |                 Baseline matches because the program executes to completion.                  |
|    **Total Mispredictions**    |  984.00   | 1,643.00  | **-40.11%** |                       **BiModeBP reduces total mispredictions by 40%**.                       |
| **Overall Misprediction Rate** |   3.18%   |   5.30%   | **-40.11%** |                         BiModeBP has a much lower misprediction rate.                         |
|  **Mispred due to Direction**  |  542.00   | 1,189.00  | **-54.42%** | **BiModeBP halves direction mispredictions**, proving its global history is highly effective. |
|  **Mispred due to BTB Miss**   |  442.00   |  454.00   | **-2.64%**  |                      BTB target misses are very similar (same BTB size).                      |
|        **BTB Hit Rate**        |  40.99%   |  44.45%   | **-7.77%**  |          LocalBP has a slightly higher BTB hit rate due to fetching different paths.          |
|        **RAS Accuracy**        |  100.00%  |  100.00%  |  **0.00%**  |                           Both predict returns with 100% accuracy.                            |
|     **Indirect Hit Rate**      |  87.97%   |  94.76%   | **-7.17%**  |                LocalBP hit rate is slightly higher but on a larger lookup set.                |
|    **Conditional Accuracy**    |  96.39%   |  95.05%   | **+1.40%**  |                 BiModeBP achieves **96.39% direction accuracy** (vs 95.05%).                  |

### Conditional Branch Misprediction Rates by Branch Type

|     Branch Type      | BiModeBP (Mispred / Comm) |  LocalBP (Mispred / Comm)  |                               Analysis                                |
| :------------------: | :-----------------------: | :------------------------: | :-------------------------------------------------------------------: |
|     **`Return`**     |     0 / 2,194 (0.00%)     |     0 / 2,194 (0.00%)      |                       Correctly handled by RAS.                       |
|   **`CallDirect`**   |    112 / 2,147 (5.22%)    |    121 / 2,147 (5.64%)     |      Low misprediction, mostly due to initial target resolution.      |
|  **`CallIndirect`**  |     27 / 52 (51.92%)      |      27 / 52 (51.92%)      |    High misprediction rate due to low volume (difficult to train).    |
|   **`DirectCond`**   | **772 / 21,909 (3.52%)**  | **1,421 / 21,909 (6.49%)** | **BiModeBP almost halves the conditional branch misprediction rate!** |
|  **`DirectUncond`**  |    59 / 2,927 (2.02%)     |     60 / 2,927 (2.05%)     |                   Very low, mostly cold BTB misses.                   |
| **`IndirectUncond`** |    14 / 1,742 (0.80%)     |     14 / 1,742 (0.80%)     |                 Well predicted by indirect predictor.                 |
