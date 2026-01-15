# No Switching Diagnosis

## Problem Summary

**Stats Analysis:**
- **0 switches** occurred in 1146 frames
- **190 trajectory blocks** - Main blocker!
- Ball was in **LEFT** zone (486 times) and **LEFT_BOTTOM** zone (75 times)
- Starting camera: **Camera 0 (RIGHT_CAM)**
- Only Camera 0 was used (100% of frames)

---

## Root Cause: Trajectory Check Blocking Switches

### The Issue

**Ball is in LEFT/LEFT_BOTTOM zones on Right Camera:**
- LEFT zone = left edge of Right Camera frame = ball going **out of bounds**
- System tries to switch to Left Camera (correct mapping)
- But **trajectory check blocks the switch**!

**Why Trajectory Check Fails:**
- For LEFT zone, `_toward_zone()` requires `vx < -0.001` (ball moving left, negative X)
- If ball is:
  - **Stationary** (vx ≈ 0)
  - **Moving slowly** (|vx| < 0.001)
  - **Moving in different direction** (vx > 0 or vy dominant)
- Then trajectory check fails → switch blocked

**Result:** 190 potential switches blocked by trajectory check!

---

## Why This Happens

### Current Configuration
```python
USE_TRAJECTORY = True  # Requires velocity to point toward zone
EXIT_PROB_THRESHOLD = 0.50  # Also requires exit probability >= 0.50
```

### The Logic Flow
1. Ball enters LEFT zone on Right Camera ✅
2. System checks: Should we switch? ✅
3. Checks trajectory: Is ball moving toward LEFT? ❌ **FAILS**
4. Switch blocked → stays on Right Camera ❌

### Why Trajectory Check Fails for LEFT Zone

**LEFT zone on Right Camera:**
- Ball is at **left edge** of frame (x < 0.08)
- Ball is **already in the zone**
- But trajectory check requires `vx < -0.001` (moving further left)
- If ball is:
  - Stationary in zone → vx ≈ 0 → check fails
  - Moving slowly → |vx| < 0.001 → check fails
  - Bouncing/oscillating → velocity inconsistent → check fails

---

## Solutions

### Solution 1: Disable Trajectory Check (Quick Fix)

**For zones where ball is already present, trajectory check may be too strict:**

```python
USE_TRAJECTORY = False  # Disable trajectory requirement
```

**Pros:** Immediate fix, allows switches when ball is in zones
**Cons:** May allow some false switches

### Solution 2: Relax Trajectory Check for Zones

**Modify `should_switch_camera()` to be less strict when ball is already in zone:**

```python
# If ball is already in exit zone, don't require strict trajectory
if zone != "NONE" and det.bbox is not None:
    # Ball is in zone and detected - allow switch even if trajectory is weak
    if USE_TRAJECTORY:
        # Only block if velocity strongly points AWAY from zone
        if zone.startswith("LEFT") and vx > 0.002:  # Moving right, away from LEFT zone
            return (False, "trajectory_away_from_zone")
        elif zone.startswith("RIGHT") and vx < -0.002:  # Moving left, away from RIGHT zone
            return (False, "trajectory_away_from_zone")
    # Otherwise allow switch
    return (True, "ball_in_exit_zone")
```

### Solution 3: Lower Trajectory Threshold

**Make trajectory check less strict:**

```python
# In _toward_zone() function, lower the threshold
if zone_name.startswith("LEFT"):
    return vx < -0.0005  # Lowered from -0.001
if zone_name.startswith("RIGHT"):
    return vx > 0.0005   # Lowered from 0.001
```

### Solution 4: Use Hybrid Approach (Recommended)

**Allow switching when ball is in zone, even if trajectory is weak:**

```python
# In should_switch_camera():
# If ball is in zone and detected, allow switch with relaxed trajectory
if zone != "NONE" and det.bbox is not None and det.conf >= MIN_CONF_FOR_FOUND:
    # Ball is clearly in exit zone
    if USE_TRAJECTORY:
        # Only block if velocity STRONGLY points away (not just weak/zero)
        velocity_away = False
        if zone.startswith("LEFT") and vx > 0.002:  # Moving right, away from LEFT
            velocity_away = True
        elif zone.startswith("RIGHT") and vx < -0.002:  # Moving left, away from RIGHT
            velocity_away = True
        
        if not velocity_away:
            # Velocity is neutral or toward zone - allow switch
            if USE_EXIT_PROBABILITY and exit_prob < EXIT_PROB_THRESHOLD:
                return (False, f"exit_prob<{EXIT_PROB_THRESHOLD:.2f}")
            return (True, "ball_in_exit_zone")
    else:
        # No trajectory check - allow switch
        if USE_EXIT_PROBABILITY and exit_prob < EXIT_PROB_THRESHOLD:
            return (False, f"exit_prob<{EXIT_PROB_THRESHOLD:.2f}")
        return (True, "ball_in_exit_zone")
```

---

## Additional Issues

### Issue 2: Ball in LEFT Zone (Out of Bounds)

**Question:** Should we switch when ball is in LEFT zone on Right Camera?

**LEFT zone on Right Camera = left edge = going out of bounds**

**Options:**
1. **Switch anyway** - Try to catch ball on Left Camera (current behavior)
2. **Don't switch** - Ball is leaving field, no point switching

**Current behavior:** Tries to switch (correct), but blocked by trajectory check.

### Issue 3: Low Detection Rate

**Detection rate: 32.7%** (375 detections out of 1146 frames)
- This means ball is lost 67.3% of the time
- When ball is lost, switching logic can't work
- May need to improve detection or adjust thresholds

---

## Recommended Fix

### Immediate Action: Relax Trajectory Check

**Option A: Disable for testing**
```python
USE_TRAJECTORY = False  # Quick test to see if switches work
```

**Option B: Make it less strict (better)**
Modify the switching logic to allow switches when:
1. Ball is in exit zone AND
2. Ball is detected (not lost) AND  
3. Velocity doesn't STRONGLY point away from zone

This way:
- ✅ Allows switches when ball is stationary in zone
- ✅ Allows switches when ball is moving slowly
- ✅ Still blocks switches when ball is clearly moving away from zone

---

## Testing After Fix

After applying fix, check:
1. **Switches occur** (should see switch_events in stats)
2. **Trajectory blocks decrease** (should be much lower)
3. **Camera usage changes** (should see Camera 1 used, not just Camera 0)
4. **Switching happens at appropriate times** (when ball moves between cameras)

---

## Summary

**Main Problem:** Trajectory check is too strict - blocks 190 potential switches
**Root Cause:** Requires `vx < -0.001` for LEFT zone, but ball may be stationary/slow
**Solution:** Relax trajectory check when ball is already in exit zone
**Quick Fix:** Set `USE_TRAJECTORY = False` to test
**Better Fix:** Modify logic to allow switches when ball is in zone, even with weak/zero velocity
