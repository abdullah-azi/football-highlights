# Fallback Code Removed for Performance

**Date:** Performance optimization for highlight generation  
**Purpose:** Removed fallback scanning code to improve processing speed  
**Impact:** Saves ~0.1-0.5ms per frame (50-200ms total for 459 frames)

---

## Summary of Removals

1. **Ball Found Tracking** (Lines ~10346-10351)
2. **Zone Proximity Check Loop** (Lines ~10358-10371)
3. **Entire Fallback Scanning Block** (Lines ~10353-10532)
4. **Configuration Variable** (Line ~9846)

---

## 1. Ball Found Tracking (Removed)

**Location:** After ball tracking, before fallback scanning  
**Approximate Lines:** ~10346-10351

**Removed Code:**
```python
# Track last frame when ball was found (for fallback scanning)
ball_found = (det.bbox is not None and det.conf >= FALLBACK_SCAN_MIN_CONF)
if ball_found:
    last_ball_found_frame = global_frame_idx
elif 'last_ball_found_frame' not in locals():
    last_ball_found_frame = global_frame_idx  # Initialize on first frame
```

**What it did:** Tracked when the ball was last detected to determine if fallback scanning should trigger.

---

## 2. Zone Proximity Check Loop (Removed)

**Location:** Before fallback scanning condition  
**Approximate Lines:** ~10358-10371

**Removed Code:**
```python
# IMPROVEMENT: Check if ball was near exit zone before fallback scanning
# This prevents false switches when ball is in center field but temporarily occluded
ball_was_near_zone = False
if hasattr(camera_switcher, 'pos_hist') and len(camera_switcher.pos_hist) > 0:
    last_pos = camera_switcher.pos_hist[-1]
    if last_pos:
        x, y = last_pos
        zones = EXIT_ZONES.get(active_cam, {})
        for zone_name, (x1, y1, x2, y2) in zones.items():
            # Check if ball was near any exit zone (with proximity threshold)
            if (x1 - FALLBACK_ZONE_PROXIMITY_THRESHOLD <= x <= x2 + FALLBACK_ZONE_PROXIMITY_THRESHOLD and
                y1 - FALLBACK_ZONE_PROXIMITY_THRESHOLD <= y <= y2 + FALLBACK_ZONE_PROXIMITY_THRESHOLD):
                ball_was_near_zone = True
                break
```

**What it did:** Checked if the ball was near any exit zone before triggering fallback scanning. This prevented false switches when the ball was in the center field but temporarily occluded.

**Performance Impact:** This loop runs on every frame and iterates through all exit zones, adding overhead.

---

## 3. Fallback Scanning Block (Removed)

**Location:** Main highlight generation loop  
**Approximate Lines:** ~10353-10532 (entire block)

**Removed Code Structure:**
```python
# ---- Enhanced Fallback camera scanning (when ball lost for too long) ----
# Priority: When middle camera loses ball, check side cameras first for better visibility
frames_since_ball_found = global_frame_idx - last_ball_found_frame
fallback_switch_occurred = False

# [Zone proximity check - see section 2 above]

# PERFORMANCE OPTIMIZATION: Disable fallback scanning for highlight generation
# Fallback scanning is expensive (detects ball on all cameras) and less critical for highlights
ENABLE_FALLBACK_FOR_HIGHLIGHT = False  # Set to True to enable fallback scanning in highlights

if (ENABLE_FALLBACK_SCAN and ENABLE_FALLBACK_FOR_HIGHLIGHT and
    frames_since_ball_found >= FALLBACK_SCAN_TIMEOUT_FRAMES and
    not camera_switcher.is_cooldown_active() and
    ball_was_near_zone):  # Only scan if ball was near exit zone (prevents center-field false switches)

    # Identify camera types for priority-based scanning
    current_cam_name = CAMERA_NAMES.get(active_cam, "").upper()
    is_middle_cam = 'MIDDLE' in current_cam_name or 'CENTER' in current_cam_name

    # Find side cameras (Left and Right) for priority scanning
    side_cam_ids = []
    other_cam_ids = []

    for cid in CAMERA_MAP.keys():
        if cid == active_cam:
            continue
        cam_name = CAMERA_NAMES.get(cid, "").upper()
        if 'LEFT' in cam_name or 'RIGHT' in cam_name:
            side_cam_ids.append(cid)
        else:
            other_cam_ids.append(cid)

    # Priority order: If coming from middle camera, scan side cameras first
    # Otherwise, scan all cameras equally
    if is_middle_cam and side_cam_ids:
        scan_order = side_cam_ids + other_cam_ids
        if ENABLE_ORCHESTRATOR_LOGGING:
            _orch_log(f"FALLBACK_SCAN: Middle camera lost ball, prioritizing side cameras: {side_cam_ids}", "INFO")
    else:
        scan_order = side_cam_ids + other_cam_ids

    # If no specific order needed, use all other cameras
    if not scan_order:
        scan_order = [cid for cid in CAMERA_MAP.keys() if cid != active_cam]

    best_other_cam = None
    best_other_conf = 0.0
    camera_visibilities = {}  # Track visibility scores for all cameras

    for other_cam_id in scan_order:
        other_cap = caps_out.get(other_cam_id)  # FIX: Use caps_out for highlight generation
        if other_cap is None:
            continue

        # Get current frame position of active camera
        try:
            active_frame_pos = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
            # Seek other camera to same relative position
            other_cap.set(cv2.CAP_PROP_POS_FRAMES, active_frame_pos)
            ok, other_frame = other_cap.read()

            if ok and other_frame is not None:
                # Detect ball in other camera
                try:
                    other_det = detect_ball(other_frame)
                    if other_det.bbox is not None and other_det.conf >= FALLBACK_SCAN_MIN_CONF:
                        # Track visibility for all cameras
                        camera_visibilities[other_cam_id] = other_det.conf

                        # Update best camera based on confidence
                        # If coming from middle camera, prefer side cameras with same confidence
                        is_side_cam = other_cam_id in side_cam_ids
                        current_best_is_side = best_other_cam in side_cam_ids if best_other_cam is not None else False

                        should_update = False
                        if best_other_cam is None:
                            should_update = True
                        elif is_middle_cam:
                            # Priority: Side cameras preferred when coming from middle
                            if is_side_cam and not current_best_is_side:
                                should_update = True  # Prefer side camera
                            elif (is_side_cam == current_best_is_side) and other_det.conf > best_other_conf:
                                should_update = True  # Same type, higher confidence
                            elif not is_side_cam and current_best_is_side:
                                should_update = False  # Don't replace side with non-side
                            elif not is_side_cam and other_det.conf > best_other_conf + 0.1:
                                should_update = True  # Non-side only if significantly better
                        else:
                            # Normal priority: highest confidence wins
                            if other_det.conf > best_other_conf:
                                should_update = True

                        if should_update:
                            best_other_cam = other_cam_id
                            best_other_conf = other_det.conf
                except Exception as e:
                    if ENABLE_ORCHESTRATOR_LOGGING:
                        _orch_log(f"Error detecting ball in camera {other_cam_id} during fallback scan: {e}", "WARNING")
        except Exception as e:
            if ENABLE_ORCHESTRATOR_LOGGING:
                _orch_log(f"Error reading from camera {other_cam_id} during fallback scan: {e}", "WARNING")

    # Switch to camera with best ball visibility
    # Prefers side cameras when coming from middle camera
    if best_other_cam is not None:
        old_cam = active_cam
        active_cam = best_other_cam
        
        # CRITICAL FIX: Update camera_switcher's internal state to match
        # Otherwise, the switcher will reset active_cam on the next frame
        try:
            camera_switcher.update_active_camera(best_other_cam, global_frame_idx)
        except Exception as e:
            if ENABLE_HIGHLIGHT_LOGGING:
                _highlight_log(f"Warning: Error updating camera_switcher state: {e}", "WARNING")
        
        _orch_stats["phase1"]["switches"] += 1
        _highlight_stats["processing"]["switches"] += 1

        switch_event = {
            "frame": global_frame_idx,
            "from_cam": old_cam,
            "to_cam": active_cam,
            "zone": "FALLBACK_SCAN",
            "exit_prob": best_other_conf,
            "reason": f"ball_lost_{frames_since_ball_found}_frames_found_in_other_cam"
        }
        _orch_stats["phase1"]["switch_events"].append(switch_event)
        _highlight_stats["processing"]["switch_events"].append(switch_event)

        # Log visibility scores if multiple cameras detected ball
        visibility_info = f"conf={best_other_conf:.2f}"
        if len(camera_visibilities) > 1:
            vis_scores = ", ".join([f"{CAMERA_NAMES.get(cid, cid)}={conf:.2f}"
                                    for cid, conf in sorted(camera_visibilities.items(), key=lambda x: x[1], reverse=True)])
            visibility_info += f" (all: {vis_scores})"

        print(f"\n🔄 FALLBACK SWITCH at frame={global_frame_idx:06d}: "
              f"{CAMERA_NAMES[old_cam]} -> {CAMERA_NAMES[active_cam]} "
              f"(ball lost for {frames_since_ball_found} frames, {visibility_info})")

        if ENABLE_ORCHESTRATOR_LOGGING:
            _orch_log(f"FALLBACK_SWITCH: frame={global_frame_idx}, {old_cam}->{active_cam}, "
                     f"lost_for={frames_since_ball_found}frames, conf={best_other_conf:.2f}, visibilities={camera_visibilities}", "INFO")
        if ENABLE_HIGHLIGHT_LOGGING:
            _highlight_log(f"FALLBACK_SWITCH: frame={global_frame_idx}, {old_cam}->{active_cam}, "
                         f"lost_for={frames_since_ball_found}frames, conf={best_other_conf:.2f}", "INFO")

        # Reset sticky tracker and update last_ball_found_frame
        # Maintain sticky tracking behavior during transitions
        try:
            sticky_tracker.reset()
        except Exception as e:
            if ENABLE_ORCHESTRATOR_LOGGING:
                _orch_log(f"Warning: Error resetting sticky tracker: {e}", "WARNING")

        last_ball_found_frame = global_frame_idx
        fallback_switch_occurred = True

        # Initialize camera usage for new camera
        if active_cam not in _orch_stats["phase1"]["camera_usage"]:
            _orch_stats["phase1"]["camera_usage"][active_cam] = 0
        if active_cam not in _highlight_stats["processing"]["camera_usage"]:
            _highlight_stats["processing"]["camera_usage"][active_cam] = 0

        # Skip normal switching decision for this frame (already switched)
        continue

# ---- Camera switching decision (only if no fallback switch occurred) ----
```

**What it did:** 
- When the ball was lost for too long (`FALLBACK_SCAN_TIMEOUT_FRAMES`), it would scan all other cameras to find where the ball went
- Detected the ball in each other camera (expensive - YOLO inference per camera)
- Switched to the camera with the best ball visibility
- This was a "recovery" mechanism when the main switching logic lost track of the ball

**Performance Impact:** Very expensive - runs YOLO detection on multiple cameras when triggered.

---

## 4. Configuration Variable (Removed)

**Location:** Highlight generation configuration section  
**Approximate Line:** ~9846

**Removed Code:**
```python
# PERFORMANCE OPTIMIZATION: Disable fallback scanning for highlight generation (saves significant time)
ENABLE_FALLBACK_FOR_HIGHLIGHT = False  # Set to True to enable fallback scanning (slower but more robust)
```

**What it did:** Flag to enable/disable fallback scanning specifically for highlight generation.

---

## Current State After Removal

**Location:** After ball tracking, before camera switching decision  
**Approximate Lines:** ~10347-10351

**Current Code:**
```python
# PERFORMANCE OPTIMIZATION: Fallback scanning removed for highlight generation
# Fallback scanning is expensive (detects ball on all cameras) and less critical for highlights
# Main switching logic handles normal camera transitions efficiently

# ---- Camera switching decision ----
```

---

## How to Restore

If you need to restore the fallback scanning functionality:

1. **Restore Configuration Variable** (Line ~9846):
   ```python
   ENABLE_FALLBACK_FOR_HIGHLIGHT = True  # Enable fallback scanning
   ```

2. **Restore Ball Found Tracking** (After line ~10345):
   ```python
   # Track last frame when ball was found (for fallback scanning)
   ball_found = (det.bbox is not None and det.conf >= FALLBACK_SCAN_MIN_CONF)
   if ball_found:
       last_ball_found_frame = global_frame_idx
   elif 'last_ball_found_frame' not in locals():
       last_ball_found_frame = global_frame_idx  # Initialize on first frame
   ```

3. **Restore Zone Proximity Check** (After ball found tracking):
   ```python
   # IMPROVEMENT: Check if ball was near exit zone before fallback scanning
   # This prevents false switches when ball is in center field but temporarily occluded
   ball_was_near_zone = False
   if hasattr(camera_switcher, 'pos_hist') and len(camera_switcher.pos_hist) > 0:
       last_pos = camera_switcher.pos_hist[-1]
       if last_pos:
           x, y = last_pos
           zones = EXIT_ZONES.get(active_cam, {})
           for zone_name, (x1, y1, x2, y2) in zones.items():
               # Check if ball was near any exit zone (with proximity threshold)
               if (x1 - FALLBACK_ZONE_PROXIMITY_THRESHOLD <= x <= x2 + FALLBACK_ZONE_PROXIMITY_THRESHOLD and
                   y1 - FALLBACK_ZONE_PROXIMITY_THRESHOLD <= y <= y2 + FALLBACK_ZONE_PROXIMITY_THRESHOLD):
                   ball_was_near_zone = True
                   break
   ```

4. **Restore Fallback Scanning Block** (After zone proximity check):
   - Insert the entire fallback scanning block (see section 3 above)
   - Make sure the condition includes `ENABLE_FALLBACK_FOR_HIGHLIGHT`
   - Update the comment before camera switching decision to: `# ---- Camera switching decision (only if no fallback switch occurred) ----`

---

## Dependencies

The fallback code uses these constants/variables (should already exist):
- `FALLBACK_SCAN_MIN_CONF` - Minimum confidence for fallback detection
- `FALLBACK_SCAN_TIMEOUT_FRAMES` - Frames to wait before triggering fallback
- `FALLBACK_ZONE_PROXIMITY_THRESHOLD` - Proximity threshold for zone checking
- `ENABLE_FALLBACK_SCAN` - Global flag for fallback scanning
- `EXIT_ZONES` - Dictionary of exit zones per camera
- `CAMERA_NAMES` - Dictionary of camera names
- `CAMERA_MAP` - Dictionary of camera IDs to video paths
- `caps_out` - Dictionary of video capture objects for highlight generation
- `camera_switcher` - Camera switcher instance
- `sticky_tracker` - Sticky ball tracker instance
- `detect_ball()` - Ball detection function
- `_orch_stats`, `_highlight_stats` - Statistics dictionaries

---

## Notes

- **Main switching logic is unaffected** - Normal camera transitions based on exit zones still work perfectly
- **Fallback was only for recovery** - When the ball was lost for extended periods, fallback would try to find it in other cameras
- **Performance trade-off** - Removing fallback makes processing faster but may miss some recovery opportunities
- **For production use** - Consider keeping fallback enabled if ball loss is common, or optimize it further (e.g., scan only when ball was near exit zone)

---

**Last Updated:** Performance optimization session
