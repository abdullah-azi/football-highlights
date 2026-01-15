#!/usr/bin/env python3
"""
Script to add fallback camera scanning feature to the orchestrator cell.
This modifies the notebook JSON directly to add the fallback scanning logic.
"""

import json
import sys
from pathlib import Path

NOTEBOOK_PATH = Path("football_camera_switching.ipynb")

def add_fallback_scan(notebook_path):
    """Add fallback scanning implementation to Cell 8 (orchestrator)."""
    
    # Read notebook
    with open(notebook_path, 'r', encoding='utf-8') as f:
        notebook = json.load(f)
    
    # Find the orchestrator cell (Cell 8 - should be around index 7)
    orchestrator_cell_idx = None
    for idx, cell in enumerate(notebook['cells']):
        if cell['cell_type'] == 'code':
            source = ''.join(cell['source'])
            if 'MULTI-CAMERA ORCHESTRATOR' in source and 'PHASE 1' in source:
                orchestrator_cell_idx = idx
                break
    
    if orchestrator_cell_idx is None:
        print("[ERROR] Could not find orchestrator cell!")
        return False
    
    print(f"[OK] Found orchestrator cell at index {orchestrator_cell_idx}")
    
    # Get the cell source
    cell = notebook['cells'][orchestrator_cell_idx]
    source_lines = cell['source']
    
    # Find where to add initialization (before "try:\n    while running:")
    init_insert_idx = None
    for i, line in enumerate(source_lines):
        if '_orch_stats["phase1"]["camera_usage"][active_cam] = 0' in line:
            # Insert after this line
            init_insert_idx = i + 1
            break
    
    if init_insert_idx is None:
        print("[ERROR] Could not find initialization location!")
        return False
    
    # Add initialization
    if 'last_ball_found_frame = 0' not in ''.join(source_lines):
        source_lines.insert(init_insert_idx, '\n')
        source_lines.insert(init_insert_idx + 1, '# Initialize fallback scanning: track last frame when ball was found\n')
        source_lines.insert(init_insert_idx + 2, 'last_ball_found_frame = 0\n')
        print("[OK] Added initialization")
    
    # Find where to add fallback logic (after ball tracking, before camera switching decision)
    fallback_insert_idx = None
    for i, line in enumerate(source_lines):
        if '})()' in line and i + 1 < len(source_lines):
            # Check if next line is camera switching decision
            if i + 2 < len(source_lines) and '# ---- Camera switching decision ----' in source_lines[i + 2]:
                fallback_insert_idx = i + 2
                break
    
    if fallback_insert_idx is None:
        print("[ERROR] Could not find fallback logic insertion point!")
        return False
    
    # Check if already added
    if 'FALLBACK SWITCH' in ''.join(source_lines):
        print("[WARNING] Fallback scanning already appears to be implemented!")
        return True
    
    # Add fallback scanning code
    fallback_code = [
        '\n',
        '        # Track last frame when ball was found (for fallback scanning)\n',
        '        ball_found = (det.bbox is not None and det.conf >= FALLBACK_SCAN_MIN_CONF)\n',
        '        if ball_found:\n',
        '            last_ball_found_frame = global_frame_idx\n',
        '        elif \'last_ball_found_frame\' not in locals():\n',
        '            last_ball_found_frame = global_frame_idx  # Initialize on first frame\n',
        '\n',
        '        # ---- Fallback camera scanning (when ball lost for too long) ----\n',
        '        frames_since_ball_found = global_frame_idx - last_ball_found_frame\n',
        '        fallback_switch_occurred = False\n',
        '        \n',
        '        if (ENABLE_FALLBACK_SCAN and \n',
        '            frames_since_ball_found >= FALLBACK_SCAN_TIMEOUT_FRAMES and\n',
        '            not camera_switcher.is_cooldown_active()):  # Don\'t scan during cooldown\n',
        '            \n',
        '            # Scan other cameras for ball\n',
        '            other_cams = [cid for cid in CAMERA_MAP.keys() if cid != active_cam]\n',
        '            best_other_cam = None\n',
        '            best_other_conf = 0.0\n',
        '            \n',
        '            for other_cam_id in other_cams:\n',
        '                other_cap = caps.get(other_cam_id)\n',
        '                if other_cap is None:\n',
        '                    continue\n',
        '                \n',
        '                # Get current frame position of active camera\n',
        '                try:\n',
        '                    active_frame_pos = int(cap.get(cv2.CAP_PROP_POS_FRAMES))\n',
        '                    # Seek other camera to same relative position\n',
        '                    other_cap.set(cv2.CAP_PROP_POS_FRAMES, active_frame_pos)\n',
        '                    ok, other_frame = other_cap.read()\n',
        '                    \n',
        '                    if ok and other_frame is not None:\n',
        '                        # Detect ball in other camera\n',
        '                        try:\n',
        '                            other_det = detect_ball(other_frame)\n',
        '                            if (other_det.bbox is not None and \n',
        '                                other_det.conf >= FALLBACK_SCAN_MIN_CONF and\n',
        '                                other_det.conf > best_other_conf):\n',
        '                                best_other_cam = other_cam_id\n',
        '                                best_other_conf = other_det.conf\n',
        '                        except Exception as e:\n',
        '                            if ENABLE_ORCHESTRATOR_LOGGING:\n',
        '                                _orch_log(f"Error detecting ball in camera {other_cam_id} during fallback scan: {e}", "WARNING")\n',
        '                except Exception as e:\n',
        '                    if ENABLE_ORCHESTRATOR_LOGGING:\n',
        '                        _orch_log(f"Error reading from camera {other_cam_id} during fallback scan: {e}", "WARNING")\n',
        '            \n',
        '            # Switch to other camera if ball found there\n',
        '            if best_other_cam is not None:\n',
        '                old_cam = active_cam\n',
        '                active_cam = best_other_cam\n',
        '                _orch_stats["phase1"]["switches"] += 1\n',
        '                \n',
        '                switch_event = {\n',
        '                    "frame": global_frame_idx,\n',
        '                    "from_cam": old_cam,\n',
        '                    "to_cam": active_cam,\n',
        '                    "zone": "FALLBACK_SCAN",\n',
        '                    "exit_prob": best_other_conf,\n',
        '                    "reason": f"ball_lost_{frames_since_ball_found}_frames_found_in_other_cam"\n',
        '                }\n',
        '                _orch_stats["phase1"]["switch_events"].append(switch_event)\n',
        '                \n',
        '                print(f"\\n🔄 FALLBACK SWITCH at frame={global_frame_idx:06d}: "\n',
        '                      f"{CAMERA_NAMES[old_cam]} -> {CAMERA_NAMES[active_cam]} "\n',
        '                      f"(ball lost for {frames_since_ball_found} frames, found with conf={best_other_conf:.2f})")\n',
        '                \n',
        '                if ENABLE_ORCHESTRATOR_LOGGING:\n',
        '                    _orch_log(f"FALLBACK_SWITCH: frame={global_frame_idx}, {old_cam}->{active_cam}, "\n',
        '                             f"lost_for={frames_since_ball_found}frames, conf={best_other_conf:.2f}", "INFO")\n',
        '                \n',
        '                # Reset sticky tracker and update last_ball_found_frame\n',
        '                try:\n',
        '                    sticky_tracker.reset()\n',
        '                except Exception as e:\n',
        '                    if ENABLE_ORCHESTRATOR_LOGGING:\n',
        '                        _orch_log(f"Warning: Error resetting sticky tracker: {e}", "WARNING")\n',
        '                \n',
        '                last_ball_found_frame = global_frame_idx\n',
        '                fallback_switch_occurred = True\n',
        '                \n',
        '                # Initialize camera usage for new camera\n',
        '                if active_cam not in _orch_stats["phase1"]["camera_usage"]:\n',
        '                    _orch_stats["phase1"]["camera_usage"][active_cam] = 0\n',
        '                \n',
        '                # Skip normal switching decision for this frame (already switched)\n',
        '                continue\n',
        '\n',
        '        # ---- Camera switching decision (only if no fallback switch occurred) ----\n',
    ]
    
    # Insert the code
    for i, line in enumerate(fallback_code):
        source_lines.insert(fallback_insert_idx + i, line)
    
    print("[OK] Added fallback scanning logic")
    
    # Update the comment if needed
    for i, line in enumerate(source_lines):
        if '# ---- Camera switching decision ----' in line and '(only if no fallback switch occurred)' not in line:
            source_lines[i] = '# ---- Camera switching decision (only if no fallback switch occurred) ----\n'
            print("[OK] Updated camera switching decision comment")
            break
    
    # Write back
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(notebook, f, indent=1, ensure_ascii=False)
    
    print(f"[OK] Successfully updated {notebook_path}")
    return True

if __name__ == '__main__':
    notebook_path = Path(__file__).parent / NOTEBOOK_PATH
    if not notebook_path.exists():
        print(f"[ERROR] Notebook not found: {notebook_path}")
        sys.exit(1)
    
    success = add_fallback_scan(notebook_path)
    sys.exit(0 if success else 1)
