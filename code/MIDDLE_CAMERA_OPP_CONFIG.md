# Middle Camera Opposite Side Configuration

## Overview

Added support for middle camera placement on the **opposite side** of the field from the left/right cameras. When enabled, the switching logic is **inverted** to correctly handle ball movement.

---

## Configuration

### Enable Middle-Op Mode

**Location:** Line ~6364

```python
ENABLE_MIDDLE_OPP = False  # Set to True when middle camera is on opposite side
```

**Usage:**
- Set to `False` when middle camera is on the **same side** as left/right cameras (default)
- Set to `True` when middle camera is on the **opposite side** of the field

---

## How It Works

### Normal Mode (Same Side) - `ENABLE_MIDDLE_OPP = False`

**Switching Logic:**
- Ball goes **LEFT** in frame → switch to **LEFT camera**
- Ball goes **RIGHT** in frame → switch to **RIGHT camera**

**Zone Mappings:**
```python
LEFT zones → LEFT camera
RIGHT zones → RIGHT camera
TOP/BOTTOM → RIGHT camera (preferred)
EQUAL → RIGHT camera (preferred)
```

### Middle-Op Mode (Opposite Side) - `ENABLE_MIDDLE_OPP = True`

**Switching Logic (INVERTED):**
- Ball goes **RIGHT** in frame → switch to **LEFT camera** (inverted)
- Ball goes **LEFT** in frame → switch to **RIGHT camera** (inverted)

**Zone Mappings:**
```python
RIGHT zones → LEFT camera (inverted)
LEFT zones → RIGHT camera (inverted)
TOP/BOTTOM → LEFT camera (preferred, inverted)
EQUAL → LEFT camera (preferred, inverted)
```

---

## Zone Definitions

Both modes use the **same zone definitions** - only the switching logic differs.

### Middle Camera Zones (All Modes)

**Well-defined zones:**
1. **LEFT** - Left edge (0.00 - 0.04)
2. **LEFT_TOP** - Left-top corner
3. **LEFT_BOTTOM** - Left-bottom corner
4. **RIGHT** - Right edge (0.96 - 1.00)
5. **RIGHT_TOP** - Right-top corner
6. **RIGHT_BOTTOM** - Right-bottom corner
7. **TOP** - Top edge (0.00 - 0.05)
8. **BOTTOM** - Bottom edge (0.95 - 1.00)
9. **EQUAL** - Center zone (0.45 - 0.55, 0.40 - 0.60) - **NEW**

**Zone Coordinates:**
```python
"LEFT":        (0.00, 0.00, 0.04, 1.00)
"LEFT_TOP":    (0.00, 0.00, 0.06, 0.25)
"LEFT_BOTTOM": (0.00, 0.75, 0.06, 1.00)
"RIGHT":       (0.96, 0.00, 1.00, 1.00)
"RIGHT_TOP":   (0.94, 0.00, 1.00, 0.25)
"RIGHT_BOTTOM":(0.94, 0.75, 1.00, 1.00)
"BOTTOM":      (0.00, 0.95, 1.00, 1.00)
"TOP":         (0.00, 0.00, 1.00, 0.05)
"EQUAL":       (0.45, 0.40, 0.55, 0.60)  # Center zone
```

---

## Code Locations

### 1. Configuration Flag
**Location:** Lines ~6357-6364
```python
# ==============================
# MIDDLE CAMERA OPPOSITE SIDE CONFIGURATION
# ==============================
ENABLE_MIDDLE_OPP = False  # Set to True when middle camera is on opposite side
```

### 2. Zone Building Logic
**Location:** Lines ~6518-6640
- Checks `ENABLE_MIDDLE_OPP` flag
- Creates zones (same for both modes)
- Sets up switching mappings (different for each mode)

### 3. Zone Visualization
**Location:** Lines ~10539-10543
- Added EQUAL zone color (cyan) for visualization

### 4. Configuration Display
**Location:** Lines ~6579-6600
- Shows which mode is active (Middle vs Middle-Op)

---

## Example Usage

### Scenario 1: Middle Camera on Same Side
```python
ENABLE_MIDDLE_OPP = False

# Ball goes LEFT in middle camera frame → switches to LEFT camera
# Ball goes RIGHT in middle camera frame → switches to RIGHT camera
```

### Scenario 2: Middle Camera on Opposite Side
```python
ENABLE_MIDDLE_OPP = True

# Ball goes RIGHT in middle camera frame → switches to LEFT camera (inverted)
# Ball goes LEFT in middle camera frame → switches to RIGHT camera (inverted)
```

---

## Why This Is Needed

When the middle camera is on the **opposite side** of the field:
- The camera's **frame orientation** is reversed relative to the field
- Ball movement that appears to go "right" in the frame is actually going "left" on the field
- Without inversion, switches would go to the wrong camera

**Example:**
- Middle camera on opposite side, facing the field
- Ball moves toward the left side of the field
- In the middle camera's frame, this appears as movement toward the **right edge**
- Without inversion: Would switch to RIGHT camera (wrong!)
- With inversion: Correctly switches to LEFT camera (correct!)

---

## Testing

After enabling/disabling `ENABLE_MIDDLE_OPP`:

1. **Check configuration display:**
   ```
   ⚙️  Middle Camera Mode: OPPOSITE SIDE (inverted switching enabled)
   ```
   or
   ```
   ⚙️  Middle Camera Mode: SAME SIDE (standard switching)
   ```

2. **Verify zone mappings:**
   - Check that zones are correctly mapped to cameras
   - LEFT zones should map to LEFT camera (normal) or RIGHT camera (inverted)
   - RIGHT zones should map to RIGHT camera (normal) or LEFT camera (inverted)

3. **Test switching:**
   - Ball moving left in frame → should switch to correct camera
   - Ball moving right in frame → should switch to correct camera

---

## Zone Thresholds (Adjustable)

If zones need fine-tuning, adjust these values in `build_exit_zones_dynamic()`:

```python
MIDDLE_CAM_LEFT_THRESHOLD = 0.04      # Left edge threshold
MIDDLE_CAM_RIGHT_THRESHOLD = 0.96    # Right edge threshold
MIDDLE_CAM_TOP_THRESHOLD = 0.05       # Top edge threshold
MIDDLE_CAM_BOTTOM_THRESHOLD = 0.95   # Bottom edge threshold
MIDDLE_CAM_CORNER_TOP = 0.25         # Top corner boundary
MIDDLE_CAM_CORNER_BOTTOM = 0.75      # Bottom corner boundary
MIDDLE_CAM_CENTER_LEFT = 0.45        # Center-left boundary (for EQUAL zone)
MIDDLE_CAM_CENTER_RIGHT = 0.55       # Center-right boundary (for EQUAL zone)
```

---

## Summary

✅ **Added:** `ENABLE_MIDDLE_OPP` configuration flag  
✅ **Added:** EQUAL zone for center/balanced switching  
✅ **Added:** Inverted switching logic for opposite-side placement  
✅ **Added:** Zone visualization support for EQUAL zone  
✅ **Added:** Configuration display showing active mode  

**Both middle and Middle-Op modes have well-defined zones:**
- LEFT, LEFT_TOP, LEFT_BOTTOM
- RIGHT, RIGHT_TOP, RIGHT_BOTTOM
- TOP, BOTTOM
- EQUAL (center zone)

---

**Last Updated:** Middle camera opposite side configuration added
