import json
import sys
import os

# Mapping of index to branch type name in gem5 branch predictor vectors
BRANCH_TYPE_MAP = {
    '0': 'NoBranch',
    '1': 'Return',
    '2': 'CallDirect',
    '3': 'CallIndirect',
    '4': 'DirectCond',
    '5': 'DirectUncond',
    '6': 'IndirectCond',
    '7': 'IndirectUncond'
}

TARGET_PROVIDER_MAP = {
    '0': 'None/Fallthrough',
    '1': 'BTB',
    '2': 'RAS',
    '3': 'IndirectPredictor'
}

def load_bp_stats(stats_path):
    if not os.path.exists(stats_path):
        print(f"Error: File not found: {stats_path}")
        return None
    try:
        with open(stats_path, 'r') as f:
            data = json.load(f)
        if isinstance(data, list):
            first_elem = data[0]
        else:
            first_elem = data
        
        bp = first_elem['board']['processor']['cores']['value'][0]['core']['branchPred']
        return bp
    except KeyError as e:
        print(f"Error: Could not find branch predictor stats path in {stats_path}. Key not found: {e}")
        return None
    except Exception as e:
        print(f"Error reading {stats_path}: {e}")
        return None

def format_vector(vector_stat, mapping):
    """Formats gem5 vector statistics using a key map."""
    if not isinstance(vector_stat, dict):
        return {}
    
    # Check if it is a Vector2d
    if vector_stat.get('type') == 'Vector2d':
        inner_val = vector_stat.get('value', {}).get('0', {}).get('value', {})
        result = {}
        for k, v in inner_val.items():
            name = mapping.get(k, f"Index_{k}")
            if isinstance(v, dict) and 'value' in v:
                result[name] = v['value']
            else:
                result[name] = v
        return result
        
    # Check if it is a Vector (1D)
    if vector_stat.get('type') == 'Vector' or 'value' in vector_stat:
        val = vector_stat.get('value', {})
        if isinstance(val, dict):
            result = {}
            for k, v in val.items():
                name = mapping.get(k, f"Index_{k}")
                if isinstance(v, dict) and 'value' in v:
                    result[name] = v['value']
                else:
                    result[name] = v
            return result
            
    return {}

def format_scalar_dict(d):
    """Formats a dict of scalar stats (e.g. btb sub-stats)."""
    if not isinstance(d, dict):
        return {}
    result = {}
    for k, v in d.items():
        if isinstance(v, dict) and 'value' in v:
            result[k] = v['value']
        else:
            result[k] = v
    return result

def get_stats_summary(bp):
    """Extracts all relevant BP stats into a structured dictionary."""
    summary = {}
    
    # 1. Global counts
    lookups = format_vector(bp.get('lookups', {}), BRANCH_TYPE_MAP)
    committed = format_vector(bp.get('committed', {}), BRANCH_TYPE_MAP)
    mispredicted = format_vector(bp.get('mispredicted', {}), BRANCH_TYPE_MAP)
    
    summary['total_lookups'] = sum(lookups.values())
    summary['lookups_by_type'] = lookups
    
    summary['total_committed'] = sum(committed.values())
    summary['committed_by_type'] = committed
    
    summary['total_mispredicted'] = sum(mispredicted.values())
    summary['mispredicted_by_type'] = mispredicted
    summary['mispred_rate'] = (summary['total_mispredicted'] / summary['total_committed'] * 100) if summary['total_committed'] > 0 else 0
    
    # 2. Breakdown
    pred_err = format_vector(bp.get('mispredictDueToPredictor', {}), BRANCH_TYPE_MAP)
    btb_err = format_vector(bp.get('mispredictDueToBTBMiss', {}), BRANCH_TYPE_MAP)
    summary['mispred_due_to_pred'] = sum(pred_err.values())
    summary['mispred_due_to_btb'] = sum(btb_err.values())
    
    # 3. Providers
    providers = format_vector(bp.get('targetProvider', {}), TARGET_PROVIDER_MAP)
    summary['providers'] = providers
    
    # 4. BTB
    summary['btb_lookups'] = bp.get('BTBLookups', {}).get('value', 0)
    summary['btb_hits'] = bp.get('BTBHits', {}).get('value', 0)
    summary['btb_hit_rate'] = (summary['btb_hits'] / summary['btb_lookups'] * 100) if summary['btb_lookups'] > 0 else 0
    summary['btb_updates'] = bp.get('BTBUpdates', {}).get('value', 0)
    summary['btb_mispredicted'] = bp.get('BTBMispredicted', {}).get('value', 0)
    
    # BTB Breakdown
    btb_obj = bp.get('btb', {})
    summary['btb_lookups_by_type'] = format_scalar_dict(btb_obj.get('lookups', {}))
    summary['btb_misses_by_type'] = format_scalar_dict(btb_obj.get('misses', {}))
    summary['btb_updates_by_type'] = format_scalar_dict(btb_obj.get('updates', {}))
    summary['btb_mispredict_by_type'] = format_scalar_dict(btb_obj.get('mispredict', {}))

    # 5. RAS
    ras = bp.get('ras', {})
    summary['ras_pushes'] = ras.get('pushes', {}).get('value', 0)
    summary['ras_pops'] = ras.get('pops', {}).get('value', 0)
    summary['ras_used'] = ras.get('used', {}).get('value', 0)
    summary['ras_correct'] = ras.get('correct', {}).get('value', 0)
    summary['ras_incorrect'] = ras.get('incorrect', {}).get('value', 0)
    summary['ras_accuracy'] = (summary['ras_correct'] / summary['ras_used'] * 100) if summary['ras_used'] > 0 else 0
    
    # 6. Indirect
    ind = bp.get('indirectBranchPred', {})
    summary['ind_lookups'] = ind.get('lookups', {}).get('value', 0)
    summary['ind_hits'] = ind.get('hits', {}).get('value', 0)
    summary['ind_misses'] = ind.get('misses', {}).get('value', 0)
    summary['ind_mispredicted'] = ind.get('indirectMispredicted', {}).get('value', 0)
    summary['ind_hit_rate'] = (summary['ind_hits'] / summary['ind_lookups'] * 100) if summary['ind_lookups'] > 0 else 0
    
    # 7. Conditional
    summary['cond_predicted'] = bp.get('condPredicted', {}).get('value', 0)
    summary['cond_predicted_taken'] = bp.get('condPredictedTaken', {}).get('value', 0)
    summary['cond_incorrect'] = bp.get('condIncorrect', {}).get('value', 0)
    summary['cond_accuracy'] = ((summary['cond_predicted'] - summary['cond_incorrect']) / summary['cond_predicted'] * 100) if summary['cond_predicted'] > 0 else 0

    return summary

def print_bp_report(s, name="Simulation"):
    print("=" * 60)
    print(f" BRANCH PREDICTOR STATS REPORT: {name}")
    print("=" * 60)
    
    # 1. Global Metrics
    print("\n--- Global Statistics ---")
    print(f"Total Lookups: {s['total_lookups']:.1f} (Number of times branch predictor was queried)")
    for btype, val in s['lookups_by_type'].items():
        if val > 0:
            print(f"  - {btype}: {val:.1f} ({val/s['total_lookups']*100:.2f}%)")
            
    print(f"Total Committed Branches: {s['total_committed']:.1f} (Branches that reached the commit stage and executed)")
    for btype, val in s['committed_by_type'].items():
        if val > 0:
            print(f"  - {btype}: {val:.1f} ({val/s['total_committed']*100:.2f}%)")

    print(f"Total Mispredicted Committed Branches: {s['total_mispredicted']:.1f} ({s['mispred_rate']:.2f}% misprediction rate)")
    for btype, val in s['mispredicted_by_type'].items():
        comm_val = s['committed_by_type'].get(btype, 0)
        rate = (val / comm_val * 100) if comm_val > 0 else 0
        if val > 0 or comm_val > 0:
            print(f"  - {btype}: {val:.1f} mispredicted / {comm_val:.1f} committed ({rate:.2f}% type mispred rate)")

    # 2. Breakdown of Mispredictions
    print("\n--- Misprediction Breakdown ---")
    print(f"Mispredictions due to Predictor (Direction Error): {s['mispred_due_to_pred']:.1f} ({s['mispred_due_to_pred']/s['total_mispredicted']*100:.2f}% of mispredictions)" if s['total_mispredicted'] > 0 else "No mispredictions")
    print(f"Mispredictions due to BTB Miss (Target Error): {s['mispred_due_to_btb']:.1f} ({s['mispred_due_to_btb']/s['total_mispredicted']*100:.2f}% of mispredictions)" if s['total_mispredicted'] > 0 else "")
    
    # 3. Target Providers
    print("\n--- Target Providers (Where did targets come from?) ---")
    for prov, val in s['providers'].items():
        print(f"  - {prov}: {val:.1f} ({val/s['total_lookups']*100:.2f}% of lookups)")

    # 4. BTB Statistics
    print("\n--- BTB (Branch Target Buffer) ---")
    print(f"BTB Lookups: {s['btb_lookups']:.1f}")
    print(f"BTB Hits: {s['btb_hits']:.1f} ({s['btb_hit_rate']:.2f}% hit rate)")
    print(f"BTB Updates: {s['btb_updates']:.1f}")
    print(f"BTB Mispredicted (Target wrong): {s['btb_mispredicted']:.1f}")

    # 5. RAS (Return Address Stack)
    print("\n--- RAS (Return Address Stack) ---")
    print(f"RAS Pushes: {s['ras_pushes']:.1f}")
    print(f"RAS Pops: {s['ras_pops']:.1f}")
    print(f"RAS Used as Target Provider: {s['ras_used']:.1f}")
    print(f"RAS Predictions Correct: {s['ras_correct']:.1f} ({s['ras_accuracy']:.2f}% accuracy)")
    print(f"RAS Predictions Incorrect: {s['ras_incorrect']:.1f}")

    # 6. Indirect Predictor
    print("\n--- Indirect Predictor ---")
    print(f"Indirect Lookups: {s['ind_lookups']:.1f}")
    print(f"Indirect Hits: {s['ind_hits']:.1f} ({s['ind_hit_rate']:.2f}% hit rate)")
    print(f"Indirect Misses: {s['ind_misses']:.1f}")
    print(f"Indirect Mispredicted: {s['ind_mispredicted']:.1f}")

    # 7. Conditional Predictor
    print("\n--- Conditional Predictor (Direction Prediction) ---")
    print(f"Conditional Predictions: {s['cond_predicted']:.1f}")
    print(f"Conditional Predicted Taken: {s['cond_predicted_taken']:.1f} ({s['cond_predicted_taken']/s['cond_predicted']*100:.2f}%)" if s['cond_predicted'] > 0 else "")
    print(f"Conditional Predictions Incorrect: {s['cond_incorrect']:.1f} ({100 - s['cond_accuracy']:.2f}% error rate)" if s['cond_predicted'] > 0 else "")
    print(f"Conditional Predictions Correct: {s['cond_predicted'] - s['cond_incorrect']:.1f} ({s['cond_accuracy']:.2f}% accuracy)" if s['cond_predicted'] > 0 else "")

def print_comparison_table(s_bi, s_loc):
    print("=" * 90)
    print(f"{'METRIC COMPARISON TABLE':^90}")
    print("=" * 90)
    print(f"{'Metric':<40} | {'BiModeBP':>20} | {'LocalBP':>20} | {'Diff (%)':>10}")
    print("-" * 90)
    
    metrics = [
        ("Total Lookups", s_bi['total_lookups'], s_loc['total_lookups'], False),
        ("Total Committed Branches", s_bi['total_committed'], s_loc['total_committed'], False),
        ("Total Mispredictions", s_bi['total_mispredicted'], s_loc['total_mispredicted'], True),
        ("Overall Misprediction Rate (%)", s_bi['mispred_rate'], s_loc['mispred_rate'], True),
        ("Mispred due to Predictor Direction", s_bi['mispred_due_to_pred'], s_loc['mispred_due_to_pred'], True),
        ("Mispred due to BTB Miss (Target)", s_bi['mispred_due_to_btb'], s_loc['mispred_due_to_btb'], True),
        ("BTB Hit Rate (%)", s_bi['btb_hit_rate'], s_loc['btb_hit_rate'], False),
        ("RAS Accuracy (%)", s_bi['ras_accuracy'], s_loc['ras_accuracy'], False),
        ("Indirect Hit Rate (%)", s_bi['ind_hit_rate'], s_loc['ind_hit_rate'], False),
        ("Conditional Predictor Accuracy (%)", s_bi['cond_accuracy'], s_loc['cond_accuracy'], False),
    ]
    
    for label, val_bi, val_loc, lower_is_better in metrics:
        if val_loc == 0:
            diff_pct = 0.0
        else:
            diff_pct = ((val_bi - val_loc) / val_loc) * 100.0
        
        # Color coding in text or indicator: 
        # For lower_is_better=True: negative diff is good (-), positive is bad (+)
        # For lower_is_better=False: positive diff is good (+), negative is bad (-)
        sign = "+" if diff_pct > 0 else ""
        print(f"{label:<40} | {val_bi:>20.2f} | {val_loc:>20.2f} | {sign}{diff_pct:>8.2f}%")
        
    print("-" * 90)
    print("\n* Conditional Branch Misprediction Rate Breakdown by Branch Type (Mispredicted / Committed):")
    print(f"{'Branch Type':<25} | {'BiModeBP':<28} | {'LocalBP':<28}")
    print("-" * 90)
    for btype in BRANCH_TYPE_MAP.values():
        bi_mis = s_bi['mispredicted_by_type'].get(btype, 0)
        bi_comm = s_bi['committed_by_type'].get(btype, 0)
        bi_rate = (bi_mis / bi_comm * 100) if bi_comm > 0 else 0
        
        loc_mis = s_loc['mispredicted_by_type'].get(btype, 0)
        loc_comm = s_loc['committed_by_type'].get(btype, 0)
        loc_rate = (loc_mis / loc_comm * 100) if loc_comm > 0 else 0
        
        if bi_comm > 0 or loc_comm > 0:
            print(f"{btype:<25} | {bi_mis:>6.0f}/{bi_comm:<6.0f} ({bi_rate:>5.2f}%) | {loc_mis:>6.0f}/{loc_comm:<6.0f} ({loc_rate:>5.2f}%)")

if __name__ == "__main__":
    ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
    bimode_path = os.path.join(ROOT, 'simulations', 'branch_prediction', 'BiModeBP', 'stats.json')
    local_path = os.path.join(ROOT, 'simulations', 'branch_prediction', 'LocalBP', 'stats.json')
    
    if len(sys.argv) > 2:
        path1 = sys.argv[1]
        path2 = sys.argv[2]
        bp1 = load_bp_stats(path1)
        bp2 = load_bp_stats(path2)
        if bp1 and bp2:
            s1 = get_stats_summary(bp1)
            s2 = get_stats_summary(bp2)
            print_comparison_table(s1, s2)
    elif len(sys.argv) > 1:
        path = sys.argv[1]
        bp = load_bp_stats(path)
        if bp:
            s = get_stats_summary(bp)
            print_bp_report(s, os.path.basename(os.path.dirname(path)))
    else:
        # Report both & Compare
        bp_bi = load_bp_stats(bimode_path)
        bp_loc = load_bp_stats(local_path)
        if bp_bi and bp_loc:
            s_bi = get_stats_summary(bp_bi)
            s_loc = get_stats_summary(bp_loc)
            
            print_bp_report(s_bi, "BiModeBP")
            print("\n\n" + "="*90 + "\n\n")
            print_bp_report(s_loc, "LocalBP")
            print("\n\n" + "="*90 + "\n\n")
            print_comparison_table(s_bi, s_loc)
