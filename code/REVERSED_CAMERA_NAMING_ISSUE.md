# Reversed Camera Naming Issue

## Problem Scenario

If your **"Right" camera is physically on the LEFT side** and your **"Left" camera is physically on the RIGHT side**, the switching logic will behave incorrectly.

---

## How the System Currently Works

### 1. **Camera Role Detection**
The system determines camera roles by looking for keywords in camera names:
- Camera with "RIGHT" in name → Role: `RIGHT`
- Camera with "LEFT" in name → Role: `LEFT`
- Camera with "MIDDLE" or "CENTER" in name → Role: `MIDDLE`

**Code Location:** `get_camera_roles()` function (line ~6357)

### 2. **Exit Zone Definition**
Exit zones are defined based on the **physical position** of the camera:
- **LEFT zone**: Left edge of the frame (where ball exits to the left)
- **RIGHT zone**: Right edge of the frame (where ball exits to the right)
- **TOP zone**: Top edge of the frame
- **BOTTOM zone**: Bottom edge of the frame

**Code Location:** `build_exit_zones_dynamic()` function (line ~6416)

### 3. **Switching Logic**
When ball exits a zone, the system switches to the camera with the **matching name**:
- Ball exits **LEFT zone** → Switch to camera named **"LEFT"**
- Ball exits **RIGHT zone** → Switch to camera named **"RIGHT"**

**Code Location:** `select_next_camera()` function (line ~7079)

---

## What Happens with Reversed Naming

### Example Scenario

**Physical Setup:**
- Camera physically on **LEFT side** → Named **"RIGHT_CAM"** ❌ (WRONG!)
- Camera physically on **RIGHT side** → Named **"LEFT_CAM"** ❌ (WRONG!)

**What the System Does:**

1. **Camera physically on LEFT (named "RIGHT_CAM"):**
   - Ball exits **RIGHT zone** (toward center) → System switches to **"RIGHT_CAM"** 
   - **Result:** ❌ Switches to itself! (or wrong camera)
   - Ball exits **LEFT zone** (away from field) → System switches to **"LEFT_CAM"**
   - **Result:** ❌ Switches to wrong camera (should stay or go to middle)

2. **Camera physically on RIGHT (named "LEFT_CAM"):**
   - Ball exits **LEFT zone** (toward center) → System switches to **"LEFT_CAM"**
   - **Result:** ❌ Switches to itself! (or wrong camera)
   - Ball exits **RIGHT zone** (away from field) → System switches to **"RIGHT_CAM"**
   - **Result:** ❌ Switches to wrong camera (should stay or go to middle)

---

## Expected Behavior (Incorrect)

### Scenario 1: Ball Moving from Left Side to Center

**Correct Behavior:**
- Ball on left camera (physically left) exits RIGHT zone → Switch to middle/right camera

**What Actually Happens (with reversed naming):**
- Ball on "RIGHT_CAM" (physically left) exits RIGHT zone → System tries to switch to "RIGHT_CAM" (itself!)
- **Result:** No switch or incorrect behavior

### Scenario 2: Ball Moving from Right Side to Center

**Correct Behavior:**
- Ball on right camera (physically right) exits LEFT zone → Switch to middle/left camera

**What Actually Happens (with reversed naming):**
- Ball on "LEFT_CAM" (physically right) exits LEFT zone → System tries to switch to "LEFT_CAM" (itself!)
- **Result:** No switch or incorrect behavior

---

## Root Cause

The issue is a **mismatch between:**
1. **Exit zones** (defined by physical camera position)
2. **Camera names** (used for switching decisions)

The system assumes:
- Camera named "RIGHT" is **physically on the right**
- Camera named "LEFT" is **physically on the left**

If this assumption is violated, switching logic breaks.

---

## Solutions

### Solution 1: Fix Camera Names (Recommended)
**Rename cameras to match their physical positions:**
```python
# If camera physically on LEFT is named "RIGHT_CAM", rename it:
CAMERA_NAMES[0] = "LEFT_CAM"  # If it's physically on the left

# If camera physically on RIGHT is named "LEFT_CAM", rename it:
CAMERA_NAMES[1] = "RIGHT_CAM"  # If it's physically on the right
```

### Solution 2: Use Explicit Camera Roles
**Set explicit roles that match physical positions:**
```python
# Define roles based on PHYSICAL position, not names
CAMERA_ROLES = {
    0: "LEFT",   # Camera 0 is physically on the left
    1: "RIGHT",  # Camera 1 is physically on the right
    2: "MIDDLE"  # Camera 2 is in the middle
}
```

The system will use `CAMERA_ROLES` if defined, overriding name-based inference.

### Solution 3: Fix Exit Zone Mappings
**Manually adjust `NEXT_CAMERA_BY_ZONE` mappings:**
```python
# Manually override the mappings if names don't match positions
NEXT_CAMERA_BY_ZONE = {
    0: {  # Camera 0 (physically left, but named "RIGHT")
        "RIGHT": 2,  # Exit right → go to middle (not to itself!)
        "LEFT": None,  # Exit left → out of view
        "TOP": 2,
        "BOTTOM": 2
    },
    1: {  # Camera 1 (physically right, but named "LEFT")
        "LEFT": 2,  # Exit left → go to middle (not to itself!)
        "RIGHT": None,  # Exit right → out of view
        "TOP": 2,
        "BOTTOM": 2
    }
}
```

---

## Detection

### How to Check if You Have This Problem

1. **Check camera names:**
   ```python
   print(CAMERA_NAMES)
   # or
   print(SYNCED_CAMERA_NAMES)
   ```

2. **Check camera roles:**
   ```python
   from football_camera_switching import get_camera_roles
   print(get_camera_roles())
   ```

3. **Observe switching behavior:**
   - If ball exits toward center but switches to wrong camera
   - If ball exits away from field but switches to center camera
   - If switches seem backwards or incorrect

4. **Check exit zone mappings:**
   ```python
   print(NEXT_CAMERA_BY_ZONE)
   ```

---

## Summary

**If camera names don't match physical positions:**
- ❌ Switching will be **backwards/incorrect**
- ❌ Ball exiting toward center may switch to wrong camera
- ❌ Ball exiting away from field may switch incorrectly
- ❌ System may try to switch camera to itself

**Fix by:**
- ✅ Renaming cameras to match physical positions, OR
- ✅ Setting explicit `CAMERA_ROLES` based on physical positions, OR
- ✅ Manually overriding `NEXT_CAMERA_BY_ZONE` mappings

---

**Key Takeaway:** Camera names should reflect **physical positions**, not arbitrary labels. The system uses names to determine switching logic, so mismatched names cause incorrect behavior.
