# False Positive Filtering Guide

## Overview

Two filtering mechanisms have been added to reduce false positives:

1. **Exclusion Zones**: Filter detections in specific camera regions (e.g., ground objects near camera)
2. **Stationary Object Detection**: Filter detections that stay in the same place (stationary objects)

---

## 1. Exclusion Zones (Location-Based Filtering)

### What It Does
Rejects detections that fall within predefined zones in specific cameras. Useful for filtering:
- Ground objects near the camera
- Static markers or signs
- Any known false positive locations

### How to Configure

**Location:** Cell 8 (Sticky Ball Tracker) - `EXCLUSION_ZONES` dictionary

**Step 1: Find the False Positive Location**

1. Run your pipeline and check the logs for false positive detections
2. Look for messages like: `[detect_ball] center=(cx,cy)`
3. Note the pixel coordinates `(cx, cy)` of the false positive

**Step 2: Convert to Normalized Coordinates**

For a frame size of 1920x1080:
- `x_norm = cx / 1920`
- `y_norm = cy / 1080`

**Example:**
- False positive at pixel `(200, 900)` in 1920x1080 frame
- `x_norm = 200 / 1920 = 0.104`
- `y_norm = 900 / 1080 = 0.833`

**Step 3: Create Exclusion Zone**

Create a rectangle around the false positive:
```python
EXCLUSION_ZONES = {
    1: [  # Left camera (ID 1)
        (0.05, 0.78, 0.15, 0.88),  # (x1, y1, x2, y2) - covers area around false positive
    ],
}
```

**Zone Format:**
- `(x1, y1, x2, y2)` = rectangle from top-left to bottom-right
- Values are normalized (0.0 to 1.0)
- `x1, y1` = top-left corner
- `x2, y2` = bottom-right corner

**Step 4: Adjust Zone Size**

- **Too small**: False positive still detected → increase zone size
- **Too large**: Real ball filtered → decrease zone size
- **Typical margin**: 0.05-0.10 (5-10% of frame)

### Example Configurations

**Left Camera - Bottom-Left Corner (Ground Object)**
```python
EXCLUSION_ZONES = {
    1: [  # Left camera
        (0.00, 0.80, 0.15, 1.00),  # Bottom-left corner
    ],
}
```

**Right Camera - Bottom-Right Corner**
```python
EXCLUSION_ZONES = {
    0: [  # Right camera
        (0.85, 0.80, 1.00, 1.00),  # Bottom-right corner
    ],
}
```

**Multiple Zones Per Camera**
```python
EXCLUSION_ZONES = {
    1: [  # Left camera
        (0.00, 0.80, 0.15, 1.00),  # Bottom-left
        (0.00, 0.00, 0.10, 0.20),  # Top-left (another false positive)
    ],
}
```

### Testing

1. Add your exclusion zone
2. Run Cell 8 to initialize
3. Run Cell 9 (orchestrator) to test
4. Check logs for: `"Exclusion zone filter: cam=X, pos=(cx,cy), holding last"`
5. Verify false positive is filtered

---

## 2. Stationary Object Detection (Temporal Filtering)

### What It Does
Filters detections that stay in approximately the same position for many frames. Useful for filtering:
- Static objects on the ground
- Markers that don't move
- Any object that remains stationary

### Configuration

**Location:** Cell 8 (Sticky Ball Tracker)

```python
ENABLE_STATIONARY_FILTER = True  # Enable/disable stationary filtering
STATIONARY_THRESHOLD_PX = 20     # Maximum pixel movement to consider "stationary"
STATIONARY_FRAMES_REQUIRED = 30  # Frames detection must be stationary to be filtered
```

### How It Works

1. **Tracks recent positions**: Stores last N detection positions
2. **Checks movement**: If all positions are within `STATIONARY_THRESHOLD_PX` pixels of each other
3. **Counts stationary frames**: Tracks how long detection has been stationary
4. **Filters if stationary**: If stationary for `STATIONARY_FRAMES_REQUIRED` frames, rejects it

### Tuning Parameters

**`STATIONARY_THRESHOLD_PX`** (default: 20px)
- **Lower** (e.g., 15px): More strict - filters even small movements
- **Higher** (e.g., 30px): More lenient - allows some movement

**`STATIONARY_FRAMES_REQUIRED`** (default: 30 frames = 1 second at 30fps)
- **Lower** (e.g., 20 frames): Filters faster but might filter slow-moving balls
- **Higher** (e.g., 45 frames): More conservative - only filters truly stationary objects

### Example Adjustments

**For faster filtering (more aggressive):**
```python
STATIONARY_THRESHOLD_PX = 15     # Stricter movement threshold
STATIONARY_FRAMES_REQUIRED = 20  # Filter after 20 frames (~0.67 seconds)
```

**For more conservative filtering:**
```python
STATIONARY_THRESHOLD_PX = 25     # More lenient movement threshold
STATIONARY_FRAMES_REQUIRED = 45  # Filter after 45 frames (~1.5 seconds)
```

---

## 3. Combined Approach

For maximum false positive reduction, use both:

1. **Exclusion zones** for known static locations (ground objects near camera)
2. **Stationary filter** for any object that stays in place

### Example: Left Camera Ground Object

```python
# Exclusion zone for known ground object location
EXCLUSION_ZONES = {
    1: [
        (0.00, 0.80, 0.15, 1.00),  # Bottom-left corner
    ],
}

# Stationary filter for any other static objects
ENABLE_STATIONARY_FILTER = True
STATIONARY_THRESHOLD_PX = 20
STATIONARY_FRAMES_REQUIRED = 30
```

---

## 4. How to Find False Positive Coordinates

### Method 1: Automatic Debug Mode (Easiest) ⭐ RECOMMENDED

**Enable coordinate debug mode:**

1. In Cell 8 (Sticky Ball Tracker), set:
   ```python
   DEBUG_EXCLUSION_COORDS = True  # Enable coordinate printing
   DEBUG_EXCLUSION_COORDS_EVERY_N = 10  # Print every 10 frames
   ```

2. Run Cell 8 to initialize, then run Cell 9 (orchestrator)

3. Watch the console output - you'll see messages like:
   ```
   📍 [EXCLUSION DEBUG] Frame 100 - Camera 1:
      Pixel coords: (200, 900) | Frame size: 1920x1080
      Normalized: (0.104, 0.833)
      Suggested zone (margin=0.08): (0.02, 0.75, 0.18, 0.91)
      Copy this line to EXCLUSION_ZONES:
      1: [(0.02, 0.75, 0.18, 0.91)],
   ```

4. When you see a false positive detection, copy the suggested zone line directly into `EXCLUSION_ZONES`

5. **Disable debug mode** after configuring:
   ```python
   DEBUG_EXCLUSION_COORDS = False  # Disable after finding coordinates
   ```

**Advantages:**
- Automatically converts pixel → normalized coordinates
- Provides ready-to-use exclusion zone code
- Shows both formats for verification
- No manual calculation needed

### Method 2: From Logs

1. Run the orchestrator (Cell 9)
2. Look for detection logs: `[detect_ball] center=(cx,cy)`
3. When false positive is detected, note the `(cx, cy)` coordinates
4. Convert to normalized: `x_norm = cx / frame_width`, `y_norm = cy / frame_height`

### Method 3: From Debug Output

1. Enable debug logging in Cell 4 or Cell 8
2. Check log files in `debug/` directory
3. Search for false positive detections
4. Extract coordinates

### Method 4: Manual Testing

1. Temporarily add print statement in `detect_ball()`:
   ```python
   if det.bbox is not None:
       print(f"Detection at: {det.center}, normalized: ({det.center[0]/w:.3f}, {det.center[1]/h:.3f})")
   ```
2. Run and note coordinates when false positive appears

---

## 5. Troubleshooting

### Exclusion Zone Not Working

**Check:**
- Camera ID is correct (check `CAMERA_NAMES` in Cell 9)
- Coordinates are normalized (0.0-1.0, not pixels)
- Zone covers the false positive location
- `ENABLE_EXCLUSION_ZONES = True`

**Debug:**
- Check logs for: `"Exclusion zone filter: cam=X"`
- If not appearing, zone might not be matching

### Stationary Filter Too Aggressive

**Symptoms:** Real slow-moving balls are filtered

**Solution:**
- Increase `STATIONARY_THRESHOLD_PX` (e.g., 25-30px)
- Increase `STATIONARY_FRAMES_REQUIRED` (e.g., 45 frames)
- Or disable: `ENABLE_STATIONARY_FILTER = False`

### Stationary Filter Not Working

**Check:**
- `ENABLE_STATIONARY_FILTER = True`
- False positive actually stays in same place (check logs)
- `STATIONARY_FRAMES_REQUIRED` might be too high

**Solution:**
- Decrease `STATIONARY_FRAMES_REQUIRED` (e.g., 20 frames)
- Decrease `STATIONARY_THRESHOLD_PX` (e.g., 15px)

---

## 6. Quick Reference

### Enable/Disable Filters

```python
# Cell 8 - Sticky Ball Tracker
ENABLE_EXCLUSION_ZONES = True   # Enable exclusion zones
ENABLE_STATIONARY_FILTER = True  # Enable stationary filtering
DEBUG_EXCLUSION_COORDS = True   # Enable coordinate debug (set False after configuring)
```

### Configure Exclusion Zone

```python
EXCLUSION_ZONES = {
    CAMERA_ID: [
        (x1, y1, x2, y2),  # Normalized coordinates [0.0-1.0]
    ],
}
```

### Configure Stationary Filter

```python
STATIONARY_THRESHOLD_PX = 20      # Pixel movement threshold
STATIONARY_FRAMES_REQUIRED = 30   # Frames to be stationary
```

---

## 7. Example: Complete Setup for Left Camera Ground Object

### Step 1: Find Coordinates (Using Debug Mode)

```python
# In Cell 8 - Sticky Ball Tracker section

# Enable coordinate debug to find false positive location
DEBUG_EXCLUSION_COORDS = True
DEBUG_EXCLUSION_COORDS_EVERY_N = 10  # Print every 10 frames
```

Run Cell 8 and Cell 9, watch console for false positive detections, copy the suggested zone.

### Step 2: Configure Exclusion Zone

```python
# In Cell 8 - Sticky Ball Tracker section

# Enable filters
ENABLE_EXCLUSION_ZONES = True
ENABLE_STATIONARY_FILTER = True

# Configure exclusion zone for left camera (ID 1)
# Coordinates found using DEBUG_EXCLUSION_COORDS
EXCLUSION_ZONES = {
    1: [  # Left camera
        (0.00, 0.80, 0.15, 1.00),  # Bottom-left corner (adjust based on debug output)
    ],
}

# Configure stationary filter
STATIONARY_THRESHOLD_PX = 20      # 20px movement threshold
STATIONARY_FRAMES_REQUIRED = 30  # 30 frames (~1 second at 30fps)

# Disable debug mode after configuring
DEBUG_EXCLUSION_COORDS = False
```

---

## Summary

- **Exclusion Zones**: Best for known static false positive locations
- **Stationary Filter**: Best for any object that doesn't move
- **Combined**: Maximum false positive reduction
- **Tune iteratively**: Start with default values, adjust based on results
