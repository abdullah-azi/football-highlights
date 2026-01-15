#!/usr/bin/env python3
"""
Apply all critical fixes to football_camera_switching.ipynb notebook.
"""

import json
import sys
from pathlib import Path

NOTEBOOK_PATH = Path(__file__).parent / "football_camera_switching.ipynb"
BACKUP_PATH = NOTEBOOK_PATH.with_suffix(".ipynb.backup")

def apply_fixes():
    """Apply all fixes to the notebook."""
    
    # Load notebook
    print(f"Loading notebook: {NOTEBOOK_PATH}")
    with open(NOTEBOOK_PATH, 'r', encoding='utf-8') as f:
        notebook = json.load(f)
    
    # Create backup
    print(f"Creating backup: {BACKUP_PATH}")
    with open(BACKUP_PATH, 'w', encoding='utf-8') as f:
        json.dump(notebook, f, indent=1, ensure_ascii=False)
    
    fixes_applied = 0
    
    # Fix 1: Add _last_active_set_frame initialization in __init__
    for cell in notebook['cells']:
        if cell['cell_type'] == 'code':
            source = ''.join(cell['source'])
            if 'self._last_switch_frame: Optional[int] = None' in source and 'self._last_active_set_frame' not in source:
                # Find the line and add after it
                lines = cell['source']
                for i, line in enumerate(lines):
                    if 'self._last_switch_frame: Optional[int] = None' in line:
                        # Insert after this line
                        indent = len(line) - len(line.lstrip())
                        new_line = ' ' * indent + 'self._last_active_set_frame: int = 0  # CRITICAL: Initialize to prevent AttributeError\n'
                        lines.insert(i + 1, new_line)
                        fixes_applied += 1
                        print("[OK] Added _last_active_set_frame initialization in __init__")
                        break
    
    # Fix 2: Add _last_active_set_frame reset in reset_switch_state
    for cell in notebook['cells']:
        if cell['cell_type'] == 'code':
            source = ''.join(cell['source'])
            if 'self._last_switch_frame = None' in source and 'def reset_switch_state' in source:
                lines = cell['source']
                for i, line in enumerate(lines):
                    if 'self._last_switch_frame = None' in line and 'self._last_active_set_frame' not in ''.join(lines[i:i+3]):
                        indent = len(line) - len(line.lstrip())
                        new_line = ' ' * indent + 'self._last_active_set_frame = 0  # CRITICAL: Reset to prevent AttributeError\n'
                        lines.insert(i + 1, new_line)
                        fixes_applied += 1
                        print("[OK] Added _last_active_set_frame reset in reset_switch_state")
                        break
    
    # Fix 3: Change ENABLE_MOTION_CONSISTENCY to False
    for cell in notebook['cells']:
        if cell['cell_type'] == 'code':
            source = ''.join(cell['source'])
            if 'ENABLE_MOTION_CONSISTENCY = True' in source:
                cell['source'] = [line.replace(
                    'ENABLE_MOTION_CONSISTENCY = True  # Set to False to disable motion-consistency filtering',
                    'ENABLE_MOTION_CONSISTENCY = False  # Set to True to enable motion-consistency filtering (may be too aggressive)'
                ) if 'ENABLE_MOTION_CONSISTENCY = True  # Set to False to disable motion-consistency filtering' in line else line
                for line in cell['source']]
                if any('ENABLE_MOTION_CONSISTENCY = False' in line for line in cell['source']):
                    fixes_applied += 1
                    print("[OK] Changed ENABLE_MOTION_CONSISTENCY to False")
                    # Also update the comment
                    cell['source'] = [line.replace(
                        '# Configuration flags (can be disabled if causing issues)',
                        '# Configuration flags (can be disabled if causing issues)\n    # DISABLED BY DEFAULT: Motion consistency can filter out valid detections if ball jumps or camera switches'
                    ) if '# Configuration flags (can be disabled if causing issues)' in line and 'DISABLED BY DEFAULT' not in ''.join(cell['source']) else line
                    for line in cell['source']]
    
    # Fix 4: Change BALL_CONF_THRESH from 0.60 to 0.15
    for cell in notebook['cells']:
        if cell['cell_type'] == 'code':
            source = ''.join(cell['source'])
            if 'BALL_CONF_THRESH = 0.60' in source:
                cell['source'] = [line.replace(
                    'BALL_CONF_THRESH = 0.60  # Increased to 0.6 to reduce false positives and use only highest confidence ball',
                    'BALL_CONF_THRESH = 0.15  # Lowered from 0.60 to 0.15 for better detection (0.60 was too high and missed balls)'
                ) if 'BALL_CONF_THRESH = 0.60' in line else line
                for line in cell['source']]
                if any('BALL_CONF_THRESH = 0.15' in line for line in cell['source']):
                    fixes_applied += 1
                    print("[OK] Changed BALL_CONF_THRESH from 0.60 to 0.15")
    
    # Fix 5: Add camera_switcher.update_active_camera() in fallback scan
    for cell in notebook['cells']:
        if cell['cell_type'] == 'code':
            source = ''.join(cell['source'])
            if 'if best_other_cam is not None:' in source and 'camera_switcher.update_active_camera' not in source:
                lines = cell['source']
                for i, line in enumerate(lines):
                    if 'active_cam = best_other_cam' in line:
                        # Insert after this line
                        indent = len(line) - len(line.lstrip())
                        new_lines = [
                            ' ' * indent + '\n',
                            ' ' * indent + '                # CRITICAL FIX: Update camera_switcher\'s internal state to match\n',
                            ' ' * indent + '                # Otherwise, the switcher will reset active_cam on the next frame\n',
                            ' ' * indent + '                try:\n',
                            ' ' * indent + '                    camera_switcher.update_active_camera(best_other_cam, global_frame_idx)\n',
                            ' ' * indent + '                except Exception as e:\n',
                            ' ' * indent + '                    if ENABLE_HIGHLIGHT_LOGGING:\n',
                            ' ' * indent + '                        _highlight_log(f"Warning: Error updating camera_switcher state: {e}", "WARNING")\n',
                            ' ' * indent + '                \n'
                        ]
                        # Insert after active_cam = best_other_cam
                        for j, new_line in enumerate(new_lines):
                            lines.insert(i + 1 + j, new_line)
                        # Also update _orch_stats to _highlight_stats
                        for j in range(i + len(new_lines) + 1, len(lines)):
                            if '_orch_stats["phase1"]["switches"]' in lines[j]:
                                lines[j] = lines[j].replace('_orch_stats["phase1"]["switches"]', '_orch_stats["phase1"]["switches"]\n                _highlight_stats["processing"]["switches"]')
                                break
                        fixes_applied += 1
                        print("[OK] Added camera_switcher.update_active_camera() in fallback scan")
                        break
    
    # Fix 6: Add active_cam = new_cam in normal switch
    for cell in notebook['cells']:
        if cell['cell_type'] == 'code':
            source = ''.join(cell['source'])
            if 'if decision.action == "SWITCH":' in source and 'active_cam = new_cam' not in source:
                lines = cell['source']
                for i, line in enumerate(lines):
                    if 'new_cam = decision.to_cam' in line:
                        # Insert after this line
                        indent = len(line) - len(line.lstrip())
                        new_lines = [
                            ' ' * indent + '            \n',
                            ' ' * indent + '            # CRITICAL: Update active_cam to match switcher\'s decision\n',
                            ' ' * indent + '            # The switcher already updated its internal state in update_active_camera()\n',
                            ' ' * indent + '            active_cam = new_cam\n'
                        ]
                        for j, new_line in enumerate(new_lines):
                            lines.insert(i + 1 + j, new_line)
                        fixes_applied += 1
                        print("[OK] Added active_cam = new_cam in normal switch")
                        break
    
    # Save notebook
    print(f"\nSaving notebook with {fixes_applied} fixes applied...")
    with open(NOTEBOOK_PATH, 'w', encoding='utf-8') as f:
        json.dump(notebook, f, indent=1, ensure_ascii=False)
    
    print(f"\n[SUCCESS] Applied {fixes_applied} fixes to notebook")
    print(f"Backup saved to: {BACKUP_PATH}")

if __name__ == '__main__':
    try:
        apply_fixes()
    except Exception as e:
        print(f"[ERROR] Failed to apply fixes: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
