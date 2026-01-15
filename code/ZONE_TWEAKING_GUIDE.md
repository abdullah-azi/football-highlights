# Exit Zone Tweaking Guide

## Understanding Zone Coordinates

Exit zones are defined using **normalized coordinates** (0.0 to 1.0), where:
- `0.0` = left edge (X) or top edge (Y) of the frame
- `1.0` = right edge (X) or bottom edge (Y) of the frame
- Works for any frame size (1920x1080, 1280x720, etc.)

### Zone Format
```python
"ZONE_NAME": (x1, y1, x2, y2)
```
- `x1, y1` = top-left corner of the zone rectangle
- `x2, y2` = bottom-right corner of the zone rectangle

## Where to Edit Zones

**Location:** Cell 6 (Camera Switching Logic) - `build_exit_zones_dynamic()` function

### Right Camera Zones (around line 6408)
```python
exit_zones[right_cam_id] = {
    "LEFT":        (0.00, 0.00, 0.08, 1.00),      # Left edge
    "LEFT_TOP":    (0.00, 0.00, 0.10, 0.25),      # Left-top corner
    "LEFT_BOTTOM": (0.00, 0.75, 0.10, 1.00),      # Left-bottom corner
    "BOTTOM":      (0.00, 0.92, 1.00, 1.00),      # Bottom edge
    "TOP":         (0.00, 0.00, 1.00, 0.08),      # Top edge
    "RIGHT":       (0.92, 0.00, 1.00, 1.00),      # Right edge
}
```

### Left Camera Zones (around line 6438)
```python
exit_zones[left_cam_id] = {
    "RIGHT":       (0.92, 0.00, 1.00, 1.00),      # Right edge
    "RIGHT_TOP":   (0.90, 0.00, 1.00, 0.25),     # Right-top corner
    "RIGHT_BOTTOM":(0.90, 0.75, 1.00, 1.00),     # Right-bottom corner
    "BOTTOM":      (0.00, 0.92, 1.00, 1.00),     # Bottom edge
    "TOP":         (0.00, 0.00, 1.00, 0.08),     # Top edge
    "LEFT":        (0.00, 0.00, 0.08, 1.00),     # Left edge
}
```

### Middle Camera Zones (around line 6470)
Uses configurable thresholds:
```python
MIDDLE_CAM_LEFT_THRESHOLD = 0.06
MIDDLE_CAM_RIGHT_THRESHOLD = 0.94
MIDDLE_CAM_TOP_THRESHOLD = 0.10
MIDDLE_CAM_BOTTOM_THRESHOLD = 0.90
```

---

## Common Adjustments

### 1. Make Zones Bigger (More Sensitive)

**Example: Make LEFT zone wider (trigger earlier)**
```python
# Before (8% of frame width)
"LEFT": (0.00, 0.00, 0.08, 1.00)

# After (12% of frame width - triggers earlier)
"LEFT": (0.00, 0.00, 0.12, 1.00)
```

**Example: Make TOP zone taller**
```python
# Before (8% of frame height)
"TOP": (0.00, 0.00, 1.00, 0.08)

# After (12% of frame height)
"TOP": (0.00, 0.00, 1.00, 0.12)
```

### 2. Make Zones Smaller (Less Sensitive)

**Example: Make LEFT zone narrower (trigger later)**
```python
# Before (8% of frame width)
"LEFT": (0.00, 0.00, 0.08, 1.00)

# After (5% of frame width - triggers later)
"LEFT": (0.00, 0.00, 0.05, 1.00)
```

**Example: Make BOTTOM zone shorter**
```python
# Before (8% from bottom)
"BOTTOM": (0.00, 0.92, 1.00, 1.00)

# After (5% from bottom)
"BOTTOM": (0.00, 0.95, 1.00, 1.00)
```

### 3. Adjust Corner Zones

**Example: Make LEFT_TOP corner bigger**
```python
# Before
"LEFT_TOP": (0.00, 0.00, 0.10, 0.25)

# After - wider and taller
"LEFT_TOP": (0.00, 0.00, 0.15, 0.30)
```

**Example: Make RIGHT_BOTTOM corner smaller**
```python
# Before
"RIGHT_BOTTOM": (0.90, 0.75, 1.00, 1.00)

# After - narrower and shorter
"RIGHT_BOTTOM": (0.92, 0.80, 1.00, 1.00)
```

### 4. Change Zone Shapes

**Example: Make LEFT zone only cover middle portion (not full height)**
```python
# Before - full height
"LEFT": (0.00, 0.00, 0.08, 1.00)

# After - only middle 60% of frame
"LEFT": (0.00, 0.20, 0.08, 0.80)
```

**Example: Make TOP zone only cover center (not full width)**
```python
# Before - full width
"TOP": (0.00, 0.00, 1.00, 0.08)

# After - only center 50% of frame
"TOP": (0.25, 0.00, 0.75, 0.08)
```

---

## Visual Reference

### Frame Coordinate System
```
(0.0, 0.0) ──────────────────────── (1.0, 0.0)
    │                                    │
    │                                    │
    │         FRAME (1920x1080)          │
    │                                    │
    │                                    │
(0.0, 1.0) ──────────────────────── (1.0, 1.0)
```

### Example: LEFT Zone
```python
"LEFT": (0.00, 0.00, 0.08, 1.00)
```
- Starts at: `x=0.00` (left edge), `y=0.00` (top)
- Ends at: `x=0.08` (8% from left), `y=1.00` (bottom)
- **Width:** 8% of frame
- **Height:** 100% of frame (full height)

### Example: TOP Zone
```python
"TOP": (0.00, 0.00, 1.00, 0.08)
```
- Starts at: `x=0.00` (left), `y=0.00` (top)
- Ends at: `x=1.00` (right), `y=0.08` (8% from top)
- **Width:** 100% of frame (full width)
- **Height:** 8% of frame

### Example: LEFT_TOP Corner
```python
"LEFT_TOP": (0.00, 0.00, 0.10, 0.25)
```
- Starts at: `x=0.00`, `y=0.00` (top-left corner)
- Ends at: `x=0.10` (10% from left), `y=0.25` (25% from top)
- **Width:** 10% of frame
- **Height:** 25% of frame

---

## Practical Examples

### Scenario 1: Ball switches too early (before leaving frame)
**Problem:** Camera switches when ball is still well inside the frame

**Solution:** Make zones smaller
```python
# Reduce LEFT zone from 8% to 5%
"LEFT": (0.00, 0.00, 0.05, 1.00)  # Was 0.08

# Reduce TOP zone from 8% to 5%
"TOP": (0.00, 0.00, 1.00, 0.05)  # Was 0.08
```

### Scenario 2: Ball switches too late (after leaving frame)
**Problem:** Camera switches after ball has already left the frame

**Solution:** Make zones bigger
```python
# Increase LEFT zone from 8% to 12%
"LEFT": (0.00, 0.00, 0.12, 1.00)  # Was 0.08

# Increase BOTTOM zone from 8% to 12%
"BOTTOM": (0.00, 0.88, 1.00, 1.00)  # Was 0.92
```

### Scenario 3: Corner zones not triggering
**Problem:** Ball exits through corners but corner zones don't trigger

**Solution:** Make corner zones bigger
```python
# Make LEFT_TOP bigger
"LEFT_TOP": (0.00, 0.00, 0.15, 0.30)  # Was (0.00, 0.00, 0.10, 0.25)

# Make RIGHT_BOTTOM bigger
"RIGHT_BOTTOM": (0.85, 0.70, 1.00, 1.00)  # Was (0.90, 0.75, 1.00, 1.00)
```

### Scenario 4: Zones triggering on stationary balls
**Problem:** Ball stays in zone but camera switches (already handled by new logic, but you can also adjust zones)

**Solution:** Make zones smaller OR adjust the edge threshold in `should_switch_camera`
```python
# In should_switch_camera function, around line 7080:
EDGE_THRESHOLD = 0.03  # Increase to 0.05 for stricter edge detection
```

---

## Middle Camera Adjustments

Middle camera uses configurable thresholds. Edit these values:

```python
MIDDLE_CAM_LEFT_THRESHOLD = 0.06      # Increase to make LEFT zone bigger
MIDDLE_CAM_RIGHT_THRESHOLD = 0.94     # Decrease to make RIGHT zone bigger
MIDDLE_CAM_TOP_THRESHOLD = 0.10       # Increase to make TOP zone bigger
MIDDLE_CAM_BOTTOM_THRESHOLD = 0.90    # Decrease to make BOTTOM zone bigger
MIDDLE_CAM_CORNER_TOP = 0.28          # Adjust corner boundaries
MIDDLE_CAM_CORNER_BOTTOM = 0.72       # Adjust corner boundaries
```

**Example: Make middle camera LEFT zone bigger**
```python
MIDDLE_CAM_LEFT_THRESHOLD = 0.10  # Was 0.06 (now triggers earlier)
```

**Example: Make middle camera TOP zone smaller**
```python
MIDDLE_CAM_TOP_THRESHOLD = 0.08  # Was 0.10 (now triggers later)
```

---

## Quick Reference Table

| Zone Type | Current Size | Make Bigger | Make Smaller |
|-----------|-------------|-------------|--------------|
| **LEFT** | 8% width | Increase `x2` (e.g., 0.08 → 0.12) | Decrease `x2` (e.g., 0.08 → 0.05) |
| **RIGHT** | 8% width | Decrease `x1` (e.g., 0.92 → 0.88) | Increase `x1` (e.g., 0.92 → 0.95) |
| **TOP** | 8% height | Increase `y2` (e.g., 0.08 → 0.12) | Decrease `y2` (e.g., 0.08 → 0.05) |
| **BOTTOM** | 8% height | Decrease `y1` (e.g., 0.92 → 0.88) | Increase `y1` (e.g., 0.92 → 0.95) |
| **LEFT_TOP** | 10%×25% | Increase both `x2` and `y2` | Decrease both `x2` and `y2` |
| **RIGHT_BOTTOM** | 10%×25% | Decrease `x1`, decrease `y1` | Increase `x1`, increase `y1` |

---

## Testing Your Changes

1. **Run Cell 6** to rebuild exit zones
2. **Run Cell 9** (orchestrator) to test switching
3. **Watch the logs** for zone detection:
   - Look for `[ZONE]` messages showing zone changes
   - Check if switches happen at the right time
4. **Adjust iteratively:**
   - Start with small changes (0.02-0.03)
   - Test and observe
   - Fine-tune based on results

---

## Tips

1. **Start conservative:** Make zones smaller first, then gradually increase if needed
2. **Test with real footage:** Use actual game footage to see when switches should happen
3. **Consider camera angles:** Different camera positions may need different zone sizes
4. **Balance sensitivity:** Too big = switches too early, too small = switches too late
5. **Use corner zones:** They help catch diagonal ball movements
6. **Check edge threshold:** The `EDGE_THRESHOLD = 0.03` in `should_switch_camera` also affects when switches trigger in 2-camera mode

---

## Example: Complete Zone Set for More Sensitive Switching

```python
exit_zones[right_cam_id] = {
    "LEFT":        (0.00, 0.00, 0.12, 1.00),      # Bigger: 8% → 12%
    "LEFT_TOP":    (0.00, 0.00, 0.15, 0.30),     # Bigger: 10%×25% → 15%×30%
    "LEFT_BOTTOM": (0.00, 0.70, 0.15, 1.00),     # Bigger: 10% → 15%
    "BOTTOM":      (0.00, 0.88, 1.00, 1.00),     # Bigger: 92% → 88%
    "TOP":         (0.00, 0.00, 1.00, 0.12),     # Bigger: 8% → 12%
    "RIGHT":       (0.88, 0.00, 1.00, 1.00),     # Bigger: 92% → 88%
}
```

## Example: Complete Zone Set for Less Sensitive Switching

```python
exit_zones[right_cam_id] = {
    "LEFT":        (0.00, 0.00, 0.05, 1.00),      # Smaller: 8% → 5%
    "LEFT_TOP":    (0.00, 0.00, 0.08, 0.20),      # Smaller: 10%×25% → 8%×20%
    "LEFT_BOTTOM": (0.00, 0.80, 0.08, 1.00),      # Smaller: 10% → 8%
    "BOTTOM":      (0.00, 0.95, 1.00, 1.00),      # Smaller: 92% → 95%
    "TOP":         (0.00, 0.00, 1.00, 0.05),      # Smaller: 8% → 5%
    "RIGHT":       (0.95, 0.00, 1.00, 1.00),      # Smaller: 92% → 95%
}
```
