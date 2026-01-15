# Switching Fixes Applied

## Problem
- **0 switches** in 1146 frames
- **190 trajectory blocks** preventing switches
- Ball in LEFT/LEFT_BOTTOM zones but switches blocked

---

## Fixes Applied

### 1. **Relaxed Trajectory Check** ⭐ MAIN FIX

**Before:** Required velocity to point toward zone (`vx < -0.001` for LEFT zone)
**After:** Only blocks if velocity STRONGLY points away (`vx > 0.002` for LEFT zone)

**Changes:**
- Allows switches when ball is **stationary** in zone
- Allows switches when ball is **moving slowly** in zone
- Only blocks if velocity **strongly points away** from zone (0.002 threshold)

**Code Locations:**
- Line ~7347-7355: Main switching logic for ball in exit zone
- Line ~7357-7369: Fallback switching logic
- Line ~7326-7331: 2-camera mode switching
- Line ~7333-7345: Missing ball after exit zone

### 2. **Lowered Trajectory Threshold in `_toward_zone()`**

**Before:** Required `vx < -0.001` for LEFT zone
**After:** Requires `vx < -0.0005` for LEFT zone (more lenient)

**Impact:** Makes trajectory detection more sensitive to small movements

**Code Location:** Line ~6857-6885

### 3. **Relaxed Speed Requirement**

**Before:** Always checked `MIN_SPEED_FOR_EXIT` if enabled
**After:** Only checks speed if velocity points toward zone

**Impact:** Allows switches even with slow/stationary ball in zone

**Code Location:** Line ~7351-7352

### 4. **Improved Statistics Tracking**

Updated to track new trajectory block reasons:
- `trajectory_strongly_away_from_zone`
- `trajectory_strongly_away_when_in_zone`
- `trajectory_strongly_away_when_missing`

**Code Location:** Line ~6669-6670

---

## Expected Results

### Before Fix:
- ❌ 0 switches (blocked by trajectory check)
- ❌ 190 trajectory blocks
- ❌ Ball in zones but no switching

### After Fix:
- ✅ Switches should occur when ball is in exit zones
- ✅ Trajectory blocks should decrease significantly
- ✅ Switches allowed even with stationary/slow ball
- ✅ Only blocks if ball is clearly moving away from zone

---

## How It Works Now

### Ball in LEFT Zone (Stationary/Slow):
1. Ball detected in LEFT zone ✅
2. Check trajectory: `vx > 0.002`? (strongly away)
   - If NO → Allow switch ✅
   - If YES → Block switch (ball moving away)
3. Check exit probability ✅
4. Switch to appropriate camera ✅

### Ball in LEFT Zone (Moving Away):
1. Ball detected in LEFT zone ✅
2. Check trajectory: `vx > 0.002`? (strongly away)
   - YES → Block switch (ball moving away) ❌
3. No switch (correct behavior)

### Ball in LEFT Zone (Moving Toward):
1. Ball detected in LEFT zone ✅
2. Check trajectory: `vx > 0.002`? (strongly away)
   - NO → Allow switch ✅
3. Check exit probability ✅
4. Switch to appropriate camera ✅

---

## Testing

After applying fixes, you should see:
1. **Switches occurring** in stats
2. **Trajectory blocks reduced** (from 190 to much lower)
3. **Camera usage changes** (Camera 1 should be used, not just Camera 0)
4. **Switch events** in the output

**Monitor these metrics:**
- `switches` count (should be > 0)
- `trajectory_blocks` (should decrease)
- `camera_usage` (should show multiple cameras)
- `switch_events` (should have entries)

---

## Configuration

The fixes maintain your current settings:
- `USE_TRAJECTORY = True` (still enabled, but more lenient)
- `USE_EXIT_PROBABILITY = True` (still enabled)
- `EXIT_PROB_THRESHOLD = 0.50` (unchanged)
- `MIN_SPEED_FOR_EXIT = 0.005` (unchanged, but only checked when appropriate)

---

## Summary

**Main Fix:** Relaxed trajectory check to only block when velocity **strongly points away** (0.002 threshold) instead of requiring it to point toward zone.

**Result:** Switches should now occur when ball is in exit zones, even if:
- Ball is stationary
- Ball is moving slowly
- Ball has weak/zero velocity

**Only blocks** if ball is clearly moving away from the exit zone.

---

**Last Updated:** Fixes applied to `football_camera_switching.py`
