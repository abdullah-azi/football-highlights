# Exit Zone Configuration Fixes Required

## Critical Issues Found

Based on the debug analysis, the following issues need to be fixed manually in **Cell 6** (Camera Switching Logic):

### 1. Exit Zones Only Defined for Camera 3 (Not Used)

**Current Problem:**
- Exit zones are only defined for camera ID `3`
- Actual cameras in use are `0` (LEFT_CAM) and `1` (RIGHT_CAM)
- This causes 99.1% of frames to be blocked by "no_exit_zone_blocks"

**Fix Required in Cell 6:**

Replace the `EXIT_ZONES` dictionary with:

```python
EXIT_ZONES: Dict[int, Dict[str, Tuple[float, float, float, float]]] = {
    # Camera 0 (LEFT_CAM): ball exiting right side means switch to camera 1
    0: {
        "RIGHT":       (0.85, 0.00, 1.00, 1.00),      # Right edge
        "RIGHT_TOP":   (0.78, 0.00, 1.00, 0.30),      # Right-top corner
        "RIGHT_BOTTOM":(0.80, 0.70, 1.00, 1.00),      # Right-bottom corner
        "BOTTOM":      (0.00, 0.85, 1.00, 1.00),      # Bottom edge
        "TOP":         (0.00, 0.00, 1.00, 0.15),      # Top edge
    },
    # Camera 1 (RIGHT_CAM): ball exiting left side means switch to camera 0
    1: {
        "LEFT":        (0.00, 0.00, 0.15, 1.00),      # Left edge
        "LEFT_TOP":    (0.00, 0.00, 0.22, 0.30),      # Left-top corner
        "LEFT_BOTTOM": (0.00, 0.70, 0.22, 1.00),      # Left-bottom corner
        "BOTTOM":      (0.00, 0.85, 1.00, 1.00),      # Bottom edge
        "TOP":         (0.00, 0.00, 1.00, 0.15),      # Top edge
    },
}
```

### 2. NEXT_CAMERA_BY_ZONE Only Defined for Camera 3

**Fix Required in Cell 6:**

Replace the `NEXT_CAMERA_BY_ZONE` dictionary with:

```python
NEXT_CAMERA_BY_ZONE: Dict[int, Dict[str, int]] = {
    # Camera 0: ball exiting right/bottom/top -> switch to camera 1
    0: {
        "RIGHT": 1,
        "RIGHT_TOP": 1,
        "RIGHT_BOTTOM": 1,
        "BOTTOM": 1,
        "TOP": 1,
    },
    # Camera 1: ball exiting left/bottom/top -> switch to camera 0
    1: {
        "LEFT": 0,
        "LEFT_TOP": 0,
        "LEFT_BOTTOM": 0,
        "BOTTOM": 0,
        "TOP": 0,
    }
}
```

### 3. START_CAMERA Set to 3 (Doesn't Exist)

**Fix Required in Cell 6:**

Find this line:
```python
START_CAMERA = 3  # Can be changed
```

Replace with:
```python
START_CAMERA = 0  # Changed from 3 to 0 to match actual cameras (0=LEFT_CAM, 1=RIGHT_CAM)
if START_CAMERA not in EXIT_ZONES:
    # Fallback to first available camera with zones
    START_CAMERA = list(EXIT_ZONES.keys())[0] if EXIT_ZONES else 0
```

## What Has Been Fixed Automatically

✅ **Exit Zone Visualization Added to Cell 9**
   - Exit zones are now drawn on output videos with semi-transparent overlays
   - Each zone is color-coded and labeled
   - Helps visualize why switching isn't occurring

✅ **Detection Confidence Threshold Lowered**
   - Changed from 0.35 to 0.25 in Cell 2
   - Should improve detection rate from 1.8% to higher values

## Expected Improvements After Fixes

1. **Camera Switching Will Work**: Exit zones for cameras 0 and 1 will allow switching logic to trigger
2. **Better Detection Rate**: Lower confidence threshold should detect more balls
3. **Visual Feedback**: Exit zones visible in output video help debug switching decisions

## Next Steps

1. Manually apply the fixes above to Cell 6
2. Re-run the notebook from Cell 6 onwards
3. Check the new debug logs to verify:
   - Exit zones are being detected (zones_visited should not be empty)
   - Camera switches are occurring (switches > 0)
   - Detection rate has improved
