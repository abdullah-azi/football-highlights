# Hybrid Switching and Skip Synchronization Fix

## Summary

This document describes the fixes needed for:
1. **Complete hybrid switching implementation** - Handle missing ball case
2. **Fix video skipping to maintain synchronization** - Use reference camera for all cameras

## Current Problem with Skipping

The current skipping implementation calculates skip frames per camera based on their individual FPS:
```python
skip_frames = int(SKIP_SECONDS * fps)  # Different for each camera if FPS differs
cap.set(cv2.CAP_PROP_POS_FRAMES, skip_frames_map[cam_id])  # Each camera seeks to different frame
```

**Issue**: If cameras have slightly different FPS (e.g., 29.99 vs 30.00), they'll calculate different frame numbers for the same time, causing desynchronization even though videos are already synchronized.

## Solution

Since videos are already synchronized (from the sync step), we should:
1. Use a reference camera's frame position
2. Use that same frame number for all cameras (since they're synced, same frame = same time)
3. Or use time-based seeking (CAP_PROP_POS_MSEC) which is more accurate

## Changes Required

### 1. Complete Hybrid Switching (Cell 6 - should_switch_camera method)

**Location**: Around line 7488-7509

**Replace section #4 with**:
```python
        # 4) Fallback: If ball is missing and was in zone, check if it disappeared from zone
        # This handles cases where ball detection fails but ball was exiting
        if det.bbox is None and self._ball_was_in_zone and self._zone_when_in_zone != "NONE":
            # Ball is missing but was in exit zone - might have exited
            prev_vx, prev_vy = self._velocity_when_in_zone
            was_moving_toward_exit = _toward_zone(prev_vx, prev_vy, self._zone_when_in_zone)
            
            if was_moving_toward_exit and self.miss_count >= BALL_MISS_FRAMES_TO_SWITCH:
                # Ball was moving toward exit and now missing - likely exited
                if USE_EXIT_PROBABILITY and exit_prob < EXIT_PROB_THRESHOLD:
                    return (False, f"exit_prob<{EXIT_PROB_THRESHOLD:.2f}")
                return (True, f"ball_missing_after_exit_{self._zone_when_in_zone}")

        # 5) For 3-camera mode: If ball is found in exit zone, allow switching (don't require misses)
        # This is a fallback for when hybrid switching doesn't trigger
        if det.bbox is not None and det.conf >= MIN_CONF_FOR_FOUND:
            # Ball is found in exit zone - check other requirements
            if USE_TRAJECTORY and not _toward_zone(vx, vy, zone):
                return (False, "trajectory_not_toward_zone")
            if USE_EXIT_PROBABILITY and exit_prob < EXIT_PROB_THRESHOLD:
                return (False, f"exit_prob<{EXIT_PROB_THRESHOLD:.2f}")
            return (True, "ball_in_exit_zone")

        # 6) optional: require trajectory toward zone
        if USE_TRAJECTORY and not _toward_zone(vx, vy, zone):
            return (False, "trajectory_not_toward_zone")

        # 7) probability threshold
        if USE_EXIT_PROBABILITY and exit_prob < EXIT_PROB_THRESHOLD:
            return (False, f"exit_prob<{EXIT_PROB_THRESHOLD:.2f}")

        # 8) If ball is missing, require sustained miss
        if self.miss_count < BALL_MISS_FRAMES_TO_SWITCH:
           return (False, f"miss<{BALL_MISS_FRAMES_TO_SWITCH}")

        return (True, "exit_confirmed")
```

**Change**: Renumber comments #4 → #5, #5 → #6, #6 → #7, #7 → #8, and add new #4 section.

### 2. Fix Skip Synchronization (Cell 11 - Highlight Output)

**Location**: Around line 11006-11024

**Replace the entire skipping section with**:
```python
# ------------------------------
# SEEK / SKIP FIRST N SECONDS (SYNCHRONIZED)
# ------------------------------
# Since videos are already synchronized, use reference camera's frame position
# to maintain synchronization across all cameras
print(f"\n⏩ Seeking to skip point ({SKIP_SECONDS}s) - maintaining synchronization...")

# Use first camera as reference (or find camera with most common FPS)
reference_cam_id = min(caps_out.keys())
reference_fps = fps_map_out[reference_cam_id]
reference_skip_frames = skip_frames_map[reference_cam_id]

print(f"   📌 Using Camera {reference_cam_id} ({CAMERA_NAMES.get(reference_cam_id, 'Unknown')}) as reference")
print(f"      Reference FPS: {reference_fps:.2f}, Skip frames: {reference_skip_frames}")

# Try time-based seeking first (more accurate for sync), fallback to frame-based
use_time_based_seek = True
for cam_id, cap in caps_out.items():
    try:
        # Try time-based seeking (milliseconds) - more accurate for synchronization
        if use_time_based_seek:
            skip_time_ms = int(SKIP_SECONDS * 1000)
            cap.set(cv2.CAP_PROP_POS_MSEC, skip_time_ms)
            actual_time_ms = cap.get(cv2.CAP_PROP_POS_MSEC)
            actual_pos = cap.get(cv2.CAP_PROP_POS_FRAMES)
            expected_time_ms = skip_time_ms
            
            # Check if time-based seeking worked (within 50ms tolerance)
            if abs(actual_time_ms - expected_time_ms) > 50:
                # Time-based seeking failed, fall back to frame-based
                use_time_based_seek = False
                print(f"   ⚠️  Time-based seek inaccurate, switching to frame-based for all cameras")
                # Re-seek using frame-based
                cap.set(cv2.CAP_PROP_POS_FRAMES, reference_skip_frames)
                actual_pos = cap.get(cv2.CAP_PROP_POS_FRAMES)
        else:
            # Frame-based seeking (use reference camera's frame number for all cameras)
            # Since videos are synchronized, same frame number = same time point
            cap.set(cv2.CAP_PROP_POS_FRAMES, reference_skip_frames)
            actual_pos = cap.get(cv2.CAP_PROP_POS_FRAMES)
        
        # Verify seek accuracy
        expected_pos = reference_skip_frames
        if abs(actual_pos - expected_pos) > 1:
            print(f"   ⚠️  Camera {cam_id} ({CAMERA_NAMES.get(cam_id, 'Unknown')}): "
                  f"Requested frame {expected_pos}, got {actual_pos} (diff: {abs(actual_pos - expected_pos)} frames)")
            if ENABLE_HIGHLIGHT_LOGGING:
                _highlight_log(f"Seek warning camera {cam_id}: requested={expected_pos}, "
                             f"actual={actual_pos}", "WARNING")
    except Exception as e:
        error_msg = f"Error seeking camera {cam_id}: {e}"
        print(f"   ⚠️  {error_msg}")
        if ENABLE_HIGHLIGHT_LOGGING:
            _highlight_log(error_msg, "ERROR")

seek_method = "time-based" if use_time_based_seek else "frame-based (synchronized)"
print(f"   ✅ Skipped first {SKIP_SECONDS} seconds (~{SKIP_SECONDS/60:.1f} min) for all cameras using {seek_method} seeking")
```

**Also update the verification section** (around line 11026-11053) to use reference frame:
```python
# Verify all cameras are synchronized after skipping
print(f"\n🔍 Verifying camera synchronization after skip...")
sync_verified = True
for cam_id, cap in caps_out.items():
    actual_pos = cap.get(cv2.CAP_PROP_POS_FRAMES)
    expected_pos = reference_skip_frames  # Use reference frame for all cameras
    fps = fps_map_out[cam_id]
    actual_time = actual_pos / fps if fps > 0 else 0
    expected_time = expected_pos / fps if fps > 0 else 0
    
    # Allow 1 frame tolerance for seek accuracy
    if abs(actual_pos - expected_pos) > 1:
        sync_verified = False
        print(f"   ⚠️  Camera {cam_id} ({CAMERA_NAMES.get(cam_id, 'Unknown')}): "
              f"Position mismatch - Expected: {expected_pos} frames ({expected_time:.2f}s), "
              f"Got: {actual_pos} frames ({actual_time:.2f}s)")
    else:
        print(f"   ✅ Camera {cam_id} ({CAMERA_NAMES.get(cam_id, 'Unknown')}): "
              f"Synchronized at {actual_pos} frames ({actual_time:.2f}s)")

if sync_verified:
    print(f"   ✅ All {len(caps_out)} camera(s) are synchronized after skipping")
    if ENABLE_HIGHLIGHT_LOGGING:
        _highlight_log(f"All {len(caps_out)} cameras synchronized after skip", "INFO")
else:
    print(f"   ⚠️  Warning: Some cameras may not be perfectly synchronized")
    if ENABLE_HIGHLIGHT_LOGGING:
        _highlight_log("Warning: Camera synchronization may be imperfect", "WARNING")
```

## How It Works

### Hybrid Switching
1. **Track zone state**: When ball enters exit zone, remember which zone and velocity
2. **Detect disappearance**: When ball disappears from that zone, check if it was moving toward exit
3. **Switch decision**: If yes, switch immediately (ball has exited)
4. **Fallback**: If ball is missing but was in zone, check after sustained miss

### Synchronized Skipping
1. **Reference camera**: Use first camera (or most common FPS) as reference
2. **Time-based seeking**: Try CAP_PROP_POS_MSEC first (more accurate)
3. **Frame-based fallback**: If time-based fails, use reference camera's frame number for all cameras
4. **Verification**: Check all cameras are at same frame position (within 1 frame tolerance)

## Benefits

1. **Hybrid switching**: Reduces false switches while maintaining smooth transitions
2. **Synchronized skipping**: Maintains video synchronization after skipping
3. **Middle camera included**: All cameras (including middle) are handled the same way
4. **Better accuracy**: Time-based seeking is more accurate than frame-based

## Testing

After implementing:
1. Run highlight generation with SKIP_SECONDS > 0
2. Check console output for synchronization verification
3. Verify all cameras show same frame number after skipping
4. Test hybrid switching with ball disappearing from zones
