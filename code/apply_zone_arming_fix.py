#!/usr/bin/env python3
"""
Apply zone arming attribute initialization fix to football_camera_switching.ipynb notebook.
"""

import json
import sys
from pathlib import Path

NOTEBOOK_PATH = Path(__file__).parent / "football_camera_switching.ipynb"
BACKUP_PATH = NOTEBOOK_PATH.with_suffix(".ipynb.backup2")

def apply_fixes():
    """Apply zone arming initialization fixes to the notebook."""
    
    # Load notebook
    print(f"Loading notebook: {NOTEBOOK_PATH}")
    with open(NOTEBOOK_PATH, 'r', encoding='utf-8') as f:
        notebook = json.load(f)
    
    # Create backup
    print(f"Creating backup: {BACKUP_PATH}")
    with open(BACKUP_PATH, 'w', encoding='utf-8') as f:
        json.dump(notebook, f, indent=1, ensure_ascii=False)
    
    fixes_applied = 0
    
    # Fix: Add zone arming attributes initialization in __init__
    for cell in notebook['cells']:
        if cell['cell_type'] == 'code':
            source = ''.join(cell['source'])
            if 'self._velocity_when_in_zone: Tuple[float, float] = (0.0, 0.0)' in source and '_armed_zone' not in source:
                lines = cell['source']
                for i, line in enumerate(lines):
                    if 'self._velocity_when_in_zone: Tuple[float, float] = (0.0, 0.0)' in line:
                        # Insert after this line
                        indent = len(line) - len(line.lstrip())
                        new_lines = [
                            ' ' * indent + '\n',
                            ' ' * indent + '        # Zone arming state (for stable zone detection to avoid jitter)\n',
                            ' ' * indent + '        self._armed_zone: str = "NONE"            # Currently armed zone\n',
                            ' ' * indent + '        self._zone_arm_count: int = 0            # Frames ball has been in armed zone\n',
                            ' ' * indent + '        self._zone_armed_frame: int = -10**9    # Frame when zone was armed\n',
                            ' ' * indent + '        self._zone_last_seen_frame: int = -10**9 # Last frame ball was seen in zone\n',
                            ' ' * indent + '        \n',
                            ' ' * indent + '        # Miss tracking for zone-based switching\n',
                            ' ' * indent + '        self._miss_in_zone: int = 0               # Consecutive misses while in zone\n',
                            ' ' * indent + '        self._miss_not_in_zone: int = 0           # Consecutive misses while not in zone\n'
                        ]
                        for j, new_line in enumerate(new_lines):
                            lines.insert(i + 1 + j, new_line)
                        fixes_applied += 1
                        print("[OK] Added zone arming attributes initialization in __init__")
                        break
    
    # Fix: Add zone arming attributes reset in reset_switch_state
    for cell in notebook['cells']:
        if cell['cell_type'] == 'code':
            source = ''.join(cell['source'])
            if 'self._velocity_when_in_zone = (0.0, 0.0)' in source and 'def reset_switch_state' in source and '_armed_zone' not in source:
                lines = cell['source']
                for i, line in enumerate(lines):
                    if 'self._velocity_when_in_zone = (0.0, 0.0)' in line:
                        # Insert after this line
                        indent = len(line) - len(line.lstrip())
                        new_lines = [
                            ' ' * indent + '        \n',
                            ' ' * indent + '        # Reset zone arming state\n',
                            ' ' * indent + '        self._armed_zone = "NONE"\n',
                            ' ' * indent + '        self._zone_arm_count = 0\n',
                            ' ' * indent + '        self._zone_armed_frame = -10**9\n',
                            ' ' * indent + '        self._zone_last_seen_frame = -10**9\n',
                            ' ' * indent + '        \n',
                            ' ' * indent + '        # Reset miss tracking\n',
                            ' ' * indent + '        self._miss_in_zone = 0\n',
                            ' ' * indent + '        self._miss_not_in_zone = 0\n'
                        ]
                        for j, new_line in enumerate(new_lines):
                            lines.insert(i + 1 + j, new_line)
                        fixes_applied += 1
                        print("[OK] Added zone arming attributes reset in reset_switch_state")
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
