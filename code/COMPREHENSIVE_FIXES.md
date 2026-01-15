# Comprehensive Fixes for Camera Switching Issues

## Issues Identified

1. ❌ Exit zones only defined for camera 3 (not cameras 0 and 1)
2. ❌ No visual representation of zones (because zones don't exist for active cameras)
3. ❌ Default fallback should be camera 1 (RIGHT_CAM), not camera 0
4. ❌ Phase 0 only scans 6 seconds (180 frames) instead of 30 seconds
5. ❌ No camera switches detected despite balls moving left/right

## Fixes Applied Automatically

✅ **Phase 0 scan duration**: Changed from 180 frames (~6 seconds) to 900 frames (~30 seconds)
✅ **Orchestrator fallback**: Changed to prefer camera 1 (RIGHT_CAM) as default fallback
✅ **Exit zone visualization**: Code is already in place in Cell 9 - will work once zones are defined

## Manual Fixes Required in Cell 6

The edit tool had trouble with Cell 6. Please manually apply these fixes:

### FIX 1: Replace EXIT_ZONES Dictionary

**Find this code in Cell 6:**
```python
EXIT_ZONES: Dict[int, Dict[str, Tuple[float, float, float, float]]] = {
    # cam_id: { zone_name: (x_min, y_min, x_max, y_max) }
    3: {
        "LEFT":       (0.00, 0.00, 0.15, 1.00),
        "LEFT_BOTTOM":(0.00, 0.70, 0.22, 1.00),
        "BOTTOM":     (0.00, 0.85, 1.00, 1.00),
        "RIGHT":      (0.85, 0.00, 1.00, 1.00),
        "RIGHT_TOP":  (0.78, 0.00, 1.00, 0.25),
    },
    # If you have other cameras, define their zones too.
    # 0: {"RIGHT": (...), "TOP": (...)}
    # 1: {"LEFT": (...)}
}
```

**Replace with:**
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

### FIX 2: Replace NEXT_CAMERA_BY_ZONE Dictionary

**Find this code in Cell 6:**
```python
NEXT_CAMERA_BY_ZONE: Dict[int, Dict[str, int]] = {
    3: {
        "LEFT": 1,
        "LEFT_BOTTOM": 1,
        "BOTTOM": 1,
        "RIGHT": 2,
        "RIGHT_TOP": 2,
    }
}
```

**Replace with:**
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

### FIX 3: Replace START_CAMERA Configuration

**Find this code in Cell 6:**
```python
# Set your starting camera here (e.g., the right-side view you tested)
START_CAMERA = 3  # Can be changed
camera_switcher.reset_switch_state(active_cam=START_CAMERA)
```

**Replace with:**
```python
# Set your starting camera here - default to camera 1 (RIGHT_CAM) as fallback
START_CAMERA = 1  # Changed to camera 1 (RIGHT_CAM) as default fallback
if START_CAMERA not in EXIT_ZONES:
    # Fallback to first available camera with zones, or camera 1 if available
    if 1 in EXIT_ZONES:
        START_CAMERA = 1
    elif 0 in EXIT_ZONES:
        START_CAMERA = 0
    else:
        START_CAMERA = list(EXIT_ZONES.keys())[0] if EXIT_ZONES else 1
camera_switcher.reset_switch_state(active_cam=START_CAMERA)
```

## Expected Results After Fixes

1. ✅ **Exit zones will be visible** in output videos (colored rectangles with labels)
2. ✅ **Phase 0 will scan 30 seconds** of each camera for ball detection
3. ✅ **Camera 1 (RIGHT_CAM) will be default fallback** if no ball detected
4. ✅ **Camera switches will occur** when ball enters exit zones:
   - Camera 0: ball in RIGHT zone → switch to Camera 1
   - Camera 1: ball in LEFT zone → switch to Camera 0
5. ✅ **Debug stats will show**:
   - `zones_visited`: Will contain zone names (LEFT, RIGHT, etc.)
   - `zone_changes`: Will be > 0
   - `switches`: Will be > 0
   - `camera_usage`: Will show both cameras being used

## Verification Steps

After applying fixes:

1. Re-run Cell 6 (Camera Switching Logic)
2. Check console output - should show:
   - "Camera 0: 5 zones (RIGHT, RIGHT_TOP, ...)"
   - "Camera 1: 5 zones (LEFT, LEFT_TOP, ...)"
   - "Start camera: 1"
3. Re-run Cell 8 (Orchestrator) - Phase 0 should scan for 30 seconds
4. Re-run Cell 9 (Final Highlight Output) - zones should be visible in video
5. Check debug stats - should show switches > 0

## Quick Reference

- **Cell 6**: Camera Switching Logic (fix EXIT_ZONES, NEXT_CAMERA_BY_ZONE, START_CAMERA)
- **Cell 8**: Multi-Camera Orchestrator (already fixed: Phase 0 duration, fallback camera)
- **Cell 9**: Final Highlight Output (visualization already in place)
