# Camera Setup Analysis: Opposite Sides, Facing Each Other

## Your Setup

**Physical Configuration:**
- **Right Camera**: Physically placed on **LEFT side**, **faces RIGHT** (toward right side of field)
- **Left Camera**: Physically placed on **RIGHT side**, **faces LEFT** (toward left side of field)

This is a **cross-field setup** where cameras are on opposite sidelines facing each other.

---

## How Exit Zones Work

Exit zones are defined **relative to the camera's frame**, not physical position:

### Right Camera (on left side, facing right):
- **LEFT zone** (0.00-0.08) = **Left edge of frame** = Ball going **away from field** (out of bounds)
- **RIGHT zone** (0.95-1.00) = **Right edge of frame** = Ball going **toward center/right side of field**

### Left Camera (on right side, facing left):
- **RIGHT zone** (0.95-1.00) = **Right edge of frame** = Ball going **away from field** (out of bounds)
- **LEFT zone** (0.00-0.08) = **Left edge of frame** = Ball going **toward center/left side of field**

---

## Current Switching Logic

### Right Camera (facing right):
```python
# When ball exits RIGHT zone (toward center):
next_camera_by_zone[right_cam_id]["RIGHT"] = middle_cam_id  # or left_cam_id in 2-cam mode
# ✅ CORRECT: Ball moving toward center → switch to middle/left camera

# When ball exits LEFT zone (away from field):
next_camera_by_zone[right_cam_id]["LEFT"] = middle_cam_id  # or left_cam_id in 2-cam mode
# ✅ CORRECT: Ball going out of bounds → switch to another camera
```

### Left Camera (facing left):
```python
# When ball exits LEFT zone (toward center):
next_camera_by_zone[left_cam_id]["LEFT"] = middle_cam_id  # or right_cam_id in 2-cam mode
# ✅ CORRECT: Ball moving toward center → switch to middle/right camera

# When ball exits RIGHT zone (away from field):
next_camera_by_zone[left_cam_id]["RIGHT"] = middle_cam_id  # or right_cam_id in 2-cam mode
# ✅ CORRECT: Ball going out of bounds → switch to another camera
```

---

## Expected Behavior

### ✅ **This Setup Should Work Correctly!**

The system uses:
1. **Exit zones** = Frame edges (LEFT/RIGHT relative to camera frame)
2. **Camera names** = Direction camera faces (RIGHT = faces right, LEFT = faces left)
3. **Switching logic** = Maps zones to cameras based on names

Since your camera names match the **direction they face** (not where they're placed), the logic should work correctly.

---

## Example Scenarios

### Scenario 1: Ball Moving from Left Side to Center

**On Right Camera (facing right, on left side):**
- Ball exits **RIGHT zone** (right edge of frame) → Moving toward center
- System switches to **middle camera** or **left camera**
- ✅ **CORRECT**: Ball is moving toward center, switch to appropriate camera

### Scenario 2: Ball Moving from Right Side to Center

**On Left Camera (facing left, on right side):**
- Ball exits **LEFT zone** (left edge of frame) → Moving toward center
- System switches to **middle camera** or **right camera**
- ✅ **CORRECT**: Ball is moving toward center, switch to appropriate camera

### Scenario 3: Ball Going Out of Bounds (Left Side)

**On Right Camera (facing right, on left side):**
- Ball exits **LEFT zone** (left edge of frame) → Going out of bounds
- System switches to **middle camera** or **left camera**
- ✅ **CORRECT**: Try to catch ball on another camera

---

## Potential Issues to Watch For

### 1. **Zone Thresholds May Need Adjustment**

If zones are too narrow or wide, you might get:
- **Too sensitive**: Switches too early when ball is still in frame
- **Not sensitive enough**: Misses switches when ball actually exits

**Solution**: Adjust zone thresholds in `build_exit_zones_dynamic()`:
```python
# Right Camera
"RIGHT": (0.95, 0.00, 1.00, 1.00),  # Current: 5% of frame width
# Make wider (more sensitive):
"RIGHT": (0.90, 0.00, 1.00, 1.00),  # 10% of frame width

# Left Camera  
"LEFT": (0.00, 0.00, 0.08, 1.00),   # Current: 8% of frame width
# Make wider (more sensitive):
"LEFT": (0.00, 0.00, 0.10, 1.00),   # 10% of frame width
```

### 2. **Middle Camera TOP/BOTTOM Logic**

The middle camera uses position-based switching for TOP/BOTTOM zones:
- If ball X < 0.5 (left half) → Switch to Left camera
- If ball X >= 0.5 (right half) → Switch to Right camera

**This assumes:**
- Left camera covers left side of field
- Right camera covers right side of field

**With your setup**, this should still work because:
- Right camera (facing right) covers right side of field ✅
- Left camera (facing left) covers left side of field ✅

### 3. **Velocity-Based Switching for Middle Camera**

When ball exits middle camera TOP zone:
- If moving right (vx > 0) → Switch to Left camera
- If moving left (vx < 0) → Switch to Right camera

**This should work correctly** because:
- Moving right → toward right side → Left camera (on right side) can see it ✅
- Moving left → toward left side → Right camera (on left side) can see it ✅

---

## Summary

### ✅ **Your Setup Should Work Correctly**

**Why:**
1. Exit zones are frame-relative (LEFT/RIGHT edges), not position-relative
2. Camera names match direction they face (RIGHT faces right, LEFT faces left)
3. Switching logic maps zones to cameras correctly

**What to Monitor:**
- Zone sensitivity (may need threshold adjustments)
- Switch timing (may need zone size tweaks)
- Middle camera switching (TOP/BOTTOM position logic)

**If Issues Occur:**
- Adjust zone thresholds (make wider/narrower)
- Check zone definitions match your camera field of view
- Verify camera names match facing direction (which you have ✅)

---

## Quick Verification

To verify everything is working:

1. **Check camera roles:**
   ```python
   from football_camera_switching import get_camera_roles
   print(get_camera_roles())
   # Should show: {0: "RIGHT", 1: "LEFT"} (or similar)
   ```

2. **Check exit zones:**
   ```python
   print(EXIT_ZONES)
   # Right camera should have RIGHT zone (0.95-1.00)
   # Left camera should have LEFT zone (0.00-0.08)
   ```

3. **Check switching mappings:**
   ```python
   print(NEXT_CAMERA_BY_ZONE)
   # Right camera RIGHT zone → should map to middle/left
   # Left camera LEFT zone → should map to middle/right
   ```

4. **Test with ball movement:**
   - Ball moving right to center on right camera → should switch
   - Ball moving left to center on left camera → should switch
   - Ball going out of bounds → should switch appropriately

---

**Conclusion:** Your setup should work correctly as-is! The system is designed to work with cameras facing each other from opposite sides.
