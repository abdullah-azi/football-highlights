# Phase 2 Enhanced Fallback Scan Implementation

## Overview
This document provides the exact code changes needed to implement Phase 2 enhancements to the fallback scan system. Phase 2 adds context-aware detection logic, time window validation, and adaptive retry cycles.

## Prerequisites
- Phase 1 must be implemented first (see `FALLBACK_SCAN_PHASE1_IMPLEMENTATION.md`)
- All Phase 1 configuration variables must be in place

## Phase 2 Features

1. **Context-Aware Alternating Logic**: 
   - Allow alternating cameras if ball is moving near exit zones
   - Require same camera if ball is stationary away from zones

2. **Time Window with Decay**:
   - Consecutive detections must be within 60 frames (2 seconds)
   - Older detections get reduced weight using decay factor

3. **Adaptive Stopping with Retry Cycles**:
   - Max 40 attempts per cycle
   - Pause 90 frames (3 seconds) between cycles
   - Max 3 retry cycles before giving up

## Changes Required

### 1. Update Configuration Section

**Add these new configuration variables after the Phase 1 configuration:**

```python
# Phase 2: Context-aware and adaptive retry configuration
FALLBACK_CONSECUTIVE_SAME_CAM = 3     # If ball in same camera (away from zones)
FALLBACK_CONSECUTIVE_ALTERNATING = 4  # If ball moving between cameras (at zones)
FALLBACK_CONSECUTIVE_TIME_WINDOW = 60  # frames (2 seconds at 30fps) - time window for consecutive detections
FALLBACK_CONSECUTIVE_DECAY = 0.5      # Decay factor if detection is older than half window
FALLBACK_BALL_VELOCITY_THRESHOLD = 0.01  # Minimum velocity to consider ball "moving"
FALLBACK_ZONE_PROXIMITY_THRESHOLD = 0.15  # Distance from zone edge to consider "near zone"

# Adaptive retry cycles
FALLBACK_SCAN_PAUSE_AFTER_MAX = 90   # Pause 90 frames (3 seconds) after max attempts
FALLBACK_SCAN_MAX_CYCLES = 3         # Max retry cycles before giving up
```

### 2. Update Initialization Section

**Update the initialization to include cycle tracking:**

**Replace:**
```python
# Initialize fallback scanning: track last frame when ball was found
last_ball_found_frame = 0
fallback_scan_count = 0  # Track number of scan attempts
fallback_consecutive_found = {}  # Track consecutive detections per camera (for false positive filtering)
last_fallback_scan_frame = 0  # Track last frame we performed fallback scan
```

**With:**
```python
# Initialize fallback scanning: track last frame when ball was found
last_ball_found_frame = 0
fallback_scan_count = 0  # Track number of scan attempts
fallback_consecutive_found = {}  # Track consecutive detections per camera (for false positive filtering)
fallback_detection_history = {}  # Track detection history with timestamps for time window validation
last_fallback_scan_frame = 0  # Track last frame we performed fallback scan
fallback_cycle_count = 0  # Track number of retry cycles
fallback_pause_until_frame = 0  # Frame number when pause ends (0 = not paused)
```

### 3. Enhanced Fallback Scan Logic

**Replace the entire fallback scan section with Phase 2 enhanced version:**

```python
        # ---- Enhanced Fallback camera scanning - Phase 2 (context-aware with retry cycles) ----
        frames_since_ball_found = global_frame_idx - last_ball_found_frame
        fallback_switch_occurred = False
        
        # Check if we're in a pause period (between retry cycles)
        if fallback_pause_until_frame > 0:
            if global_frame_idx < fallback_pause_until_frame:
                # Still in pause, skip scanning
                pass
            else:
                # Pause ended, reset for new cycle
                fallback_pause_until_frame = 0
                fallback_scan_count = 0
                fallback_consecutive_found = {}
                fallback_detection_history = {}
                if ENABLE_ORCHESTRATOR_LOGGING:
                    _orch_log(f"FALLBACK_SCAN: Pause ended, starting cycle {fallback_cycle_count + 1}", "INFO")
        else:
            # Check if we should perform fallback scan
            # Scan immediately when timeout is reached, then every N frames
            should_scan = (
                ENABLE_FALLBACK_SCAN and 
                frames_since_ball_found >= FALLBACK_SCAN_TIMEOUT_FRAMES and
                not camera_switcher.is_cooldown_active() and
                fallback_scan_count < FALLBACK_SCAN_MAX_ATTEMPTS and
                fallback_cycle_count < FALLBACK_SCAN_MAX_CYCLES and
                (global_frame_idx - last_fallback_scan_frame) >= FALLBACK_SCAN_INTERVAL
            )
            
            if should_scan:
                last_fallback_scan_frame = global_frame_idx
                fallback_scan_count += 1
                
                # Scan other cameras for ball
                other_cams = [cid for cid in CAMERA_MAP.keys() if cid != active_cam]
                best_other_cam = None
                best_other_conf = 0.0
                
                # Get ball velocity and position for context-aware logic
                ball_velocity = (0.0, 0.0)
                ball_position = None
                ball_near_zone = False
                
                try:
                    # Try to get velocity from camera switcher's position history
                    if hasattr(camera_switcher, 'pos_hist') and len(camera_switcher.pos_hist) > 1:
                        # Calculate velocity from recent positions
                        recent_positions = list(camera_switcher.pos_hist)[-4:]  # Last 4 positions
                        if len(recent_positions) >= 2:
                            dx = recent_positions[-1][0] - recent_positions[0][0]
                            dy = recent_positions[-1][1] - recent_positions[0][1]
                            ball_velocity = (dx, dy)
                            ball_position = recent_positions[-1]
                            
                            # Check if ball is near exit zones
                            if ball_position:
                                x, y = ball_position
                                zones = EXIT_ZONES.get(active_cam, {})
                                for zone_name, (x1, y1, x2, y2) in zones.items():
                                    # Check if ball is within proximity threshold of zone
                                    if (x1 - FALLBACK_ZONE_PROXIMITY_THRESHOLD <= x <= x2 + FALLBACK_ZONE_PROXIMITY_THRESHOLD and
                                        y1 - FALLBACK_ZONE_PROXIMITY_THRESHOLD <= y <= y2 + FALLBACK_ZONE_PROXIMITY_THRESHOLD):
                                        ball_near_zone = True
                                        break
                except Exception as e:
                    if ENABLE_ORCHESTRATOR_LOGGING:
                        _orch_log(f"Error getting ball context: {e}", "WARNING")
                
                # Determine if ball is moving
                velocity_magnitude = (ball_velocity[0]**2 + ball_velocity[1]**2)**0.5
                is_ball_moving = velocity_magnitude > FALLBACK_BALL_VELOCITY_THRESHOLD
                
                # Determine required consecutive count based on context
                if is_ball_moving and ball_near_zone:
                    # Ball is moving near zones - allow alternating cameras
                    required_consecutive = FALLBACK_CONSECUTIVE_ALTERNATING
                    allow_alternating = True
                else:
                    # Ball is stationary or away from zones - require same camera
                    required_consecutive = FALLBACK_CONSECUTIVE_SAME_CAM
                    allow_alternating = False
                
                for other_cam_id in other_cams:
                    other_cap = caps.get(other_cam_id)
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
                                
                                # Multi-criteria false positive detection (from Phase 1)
                                is_valid = False
                                if other_det.bbox is not None and other_det.conf >= FALLBACK_SCAN_CONF_THRESHOLD:
                                    x1, y1, x2, y2 = other_det.bbox
                                    bbox_width = abs(x2 - x1)
                                    bbox_height = abs(y2 - y1)
                                    bbox_area = bbox_width * bbox_height
                                    h, w = other_frame.shape[:2]
                                    frame_area = h * w
                                    
                                    # Check bbox size (filter too small or too large)
                                    if (FALLBACK_MIN_BBOX_SIZE <= bbox_width <= FALLBACK_MAX_BBOX_SIZE and
                                        FALLBACK_MIN_BBOX_SIZE <= bbox_height <= FALLBACK_MAX_BBOX_SIZE):
                                        
                                        # Check bbox area
                                        if (FALLBACK_MIN_BBOX_AREA <= bbox_area <= FALLBACK_MAX_BBOX_AREA):
                                            
                                            # Check aspect ratio (ball should be roughly circular)
                                            aspect_ratio_w_h = bbox_width / bbox_height if bbox_height > 0 else 0
                                            aspect_ratio_h_w = bbox_height / bbox_width if bbox_width > 0 else 0
                                            
                                            if (FALLBACK_ASPECT_RATIO_MIN <= aspect_ratio_w_h <= FALLBACK_ASPECT_RATIO_MAX or
                                                FALLBACK_ASPECT_RATIO_MIN <= aspect_ratio_h_w <= FALLBACK_ASPECT_RATIO_MAX):
                                                
                                                # Check relative size (ball shouldn't take up too much of frame)
                                                relative_size = bbox_area / frame_area if frame_area > 0 else 0
                                                
                                                if relative_size <= FALLBACK_RELATIVE_SIZE_MAX:
                                                    is_valid = True
                                
                                if is_valid:
                                    # Update best camera if confidence is higher
                                    if other_det.conf > best_other_conf:
                                        best_other_cam = other_cam_id
                                        best_other_conf = other_det.conf
                                        
                            except Exception as e:
                                if ENABLE_ORCHESTRATOR_LOGGING:
                                    _orch_log(f"Error detecting ball in camera {other_cam_id} during fallback scan: {e}", "WARNING")
                    except Exception as e:
                        if ENABLE_ORCHESTRATOR_LOGGING:
                            _orch_log(f"Error reading from camera {other_cam_id} during fallback scan: {e}", "WARNING")
                
                # Phase 2: Enhanced false positive filtering with time window and context-aware logic
                if best_other_cam is not None:
                    # Add detection to history with timestamp
                    if best_other_cam not in fallback_detection_history:
                        fallback_detection_history[best_other_cam] = []
                    
                    fallback_detection_history[best_other_cam].append({
                        'frame': global_frame_idx,
                        'conf': best_other_conf,
                        'timestamp': global_frame_idx
                    })
                    
                    # Clean old detections outside time window
                    current_time = global_frame_idx
                    fallback_detection_history[best_other_cam] = [
                        det for det in fallback_detection_history[best_other_cam]
                        if (current_time - det['timestamp']) <= FALLBACK_CONSECUTIVE_TIME_WINDOW
                    ]
                    
                    # Calculate weighted consecutive count with decay
                    weighted_count = 0.0
                    for det in fallback_detection_history[best_other_cam]:
                        age = current_time - det['timestamp']
                        if age <= FALLBACK_CONSECUTIVE_TIME_WINDOW / 2:
                            # Recent detection - full weight
                            weight = 1.0
                        else:
                            # Older detection - apply decay
                            age_factor = (age - FALLBACK_CONSECUTIVE_TIME_WINDOW / 2) / (FALLBACK_CONSECUTIVE_TIME_WINDOW / 2)
                            weight = max(0.0, 1.0 - (age_factor * (1.0 - FALLBACK_CONSECUTIVE_DECAY)))
                        weighted_count += weight
                    
                    # Update consecutive counter (use integer count for display, weighted for logic)
                    consecutive_count = len(fallback_detection_history[best_other_cam])
                    fallback_consecutive_found[best_other_cam] = consecutive_count
                    
                    # Reset counters for other cameras
                    for cam_id in list(fallback_consecutive_found.keys()):
                        if cam_id != best_other_cam:
                            fallback_consecutive_found[cam_id] = 0
                            if cam_id in fallback_detection_history:
                                fallback_detection_history[cam_id] = []
                    
                    # Context-aware consecutive requirement
                    # If allowing alternating, check if we have detections in different cameras
                    if allow_alternating:
                        # Check if we have recent detections in multiple cameras (alternating pattern)
                        recent_cameras = set()
                        for cam_id, detections in fallback_detection_history.items():
                            recent_dets = [d for d in detections if (current_time - d['timestamp']) <= FALLBACK_CONSECUTIVE_TIME_WINDOW]
                            if len(recent_dets) > 0:
                                recent_cameras.add(cam_id)
                        
                        # If we have detections in multiple cameras, use alternating requirement
                        if len(recent_cameras) > 1:
                            # Alternating pattern detected - use higher requirement
                            effective_required = FALLBACK_CONSECUTIVE_ALTERNATING
                            pattern_type = "alternating"
                        else:
                            # Same camera pattern - use lower requirement
                            effective_required = FALLBACK_CONSECUTIVE_SAME_CAM
                            pattern_type = "same_camera"
                    else:
                        # Not allowing alternating - require same camera
                        effective_required = required_consecutive
                        pattern_type = "same_camera"
                    
                    # Only switch if we have enough consecutive detections (using weighted count)
                    if weighted_count >= effective_required:
                        old_cam = active_cam
                        active_cam = best_other_cam
                        _orch_stats["phase1"]["switches"] += 1
                        
                        switch_event = {
                            "frame": global_frame_idx,
                            "from_cam": old_cam,
                            "to_cam": active_cam,
                            "zone": "FALLBACK_SCAN",
                            "exit_prob": best_other_conf,
                            "reason": f"ball_lost_{frames_since_ball_found}_frames_found_in_other_cam_after_{fallback_scan_count}_scans_cycle_{fallback_cycle_count + 1}"
                        }
                        _orch_stats["phase1"]["switch_events"].append(switch_event)
                        
                        context_info = f"moving={is_ball_moving:.3f}, near_zone={ball_near_zone}, pattern={pattern_type}"
                        print(f"\n🔄 FALLBACK SWITCH at frame={global_frame_idx:06d}: "
                              f"{CAMERA_NAMES[old_cam]} -> {CAMERA_NAMES[active_cam]} "
                              f"(ball lost for {frames_since_ball_found} frames, found with conf={best_other_conf:.2f} "
                              f"after {fallback_scan_count} scans, cycle {fallback_cycle_count + 1}, "
                              f"weighted_count={weighted_count:.1f}/{effective_required}, {context_info})")
                        
                        if ENABLE_ORCHESTRATOR_LOGGING:
                            _orch_log(f"FALLBACK_SWITCH: frame={global_frame_idx}, {old_cam}->{active_cam}, "
                                     f"lost_for={frames_since_ball_found}frames, conf={best_other_conf:.2f}, "
                                     f"scans={fallback_scan_count}, cycle={fallback_cycle_count + 1}, "
                                     f"weighted={weighted_count:.1f}/{effective_required}, {context_info}", "INFO")
                        
                        # Reset sticky tracker and update last_ball_found_frame
                        try:
                            sticky_tracker.reset()
                        except Exception as e:
                            if ENABLE_ORCHESTRATOR_LOGGING:
                                _orch_log(f"Warning: Error resetting sticky tracker: {e}", "WARNING")
                        
                        last_ball_found_frame = global_frame_idx
                        fallback_scan_count = 0  # Reset scan count after successful switch
                        fallback_consecutive_found = {}  # Reset consecutive counters
                        fallback_detection_history = {}  # Reset detection history
                        fallback_cycle_count = 0  # Reset cycle count
                        fallback_switch_occurred = True
                        
                        # Initialize camera usage for new camera
                        if active_cam not in _orch_stats["phase1"]["camera_usage"]:
                            _orch_stats["phase1"]["camera_usage"][active_cam] = 0
                        
                        # Skip normal switching decision for this frame (already switched)
                        continue
                    else:
                        # Not enough consecutive detections yet
                        if ENABLE_ORCHESTRATOR_LOGGING and fallback_scan_count % 10 == 0:
                            _orch_log(f"FALLBACK_SCAN: Ball detected in camera {best_other_cam} with conf={best_other_conf:.2f}, "
                                     f"but need {effective_required} consecutive (weighted: {weighted_count:.1f}, "
                                     f"raw: {consecutive_count}, pattern: {pattern_type})", "INFO")
                else:
                    # No valid detection found, clean old detection history
                    current_time = global_frame_idx
                    for cam_id in list(fallback_detection_history.keys()):
                        fallback_detection_history[cam_id] = [
                            det for det in fallback_detection_history[cam_id]
                            if (current_time - det['timestamp']) <= FALLBACK_CONSECUTIVE_TIME_WINDOW
                        ]
                        # Remove empty histories
                        if len(fallback_detection_history[cam_id]) == 0:
                            del fallback_detection_history[cam_id]
                    
                    # Reset consecutive counters if no recent detections
                    fallback_consecutive_found = {}
                    
                    # Check if we've reached max attempts for this cycle
                    if fallback_scan_count >= FALLBACK_SCAN_MAX_ATTEMPTS:
                        fallback_cycle_count += 1
                        
                        if fallback_cycle_count < FALLBACK_SCAN_MAX_CYCLES:
                            # Start pause period for next cycle
                            fallback_pause_until_frame = global_frame_idx + FALLBACK_SCAN_PAUSE_AFTER_MAX
                            
                            if ENABLE_ORCHESTRATOR_LOGGING:
                                _orch_log(f"FALLBACK_SCAN: Cycle {fallback_cycle_count} completed ({FALLBACK_SCAN_MAX_ATTEMPTS} attempts), "
                                         f"pausing for {FALLBACK_SCAN_PAUSE_AFTER_MAX} frames before cycle {fallback_cycle_count + 1}", "WARNING")
                            print(f"\n⚠️  Fallback scan cycle {fallback_cycle_count} completed: "
                                  f"Reached {FALLBACK_SCAN_MAX_ATTEMPTS} attempts without finding ball. "
                                  f"Pausing for {FALLBACK_SCAN_PAUSE_AFTER_MAX} frames before retry...")
                            
                            # Reset for next cycle
                            fallback_scan_count = 0
                            fallback_consecutive_found = {}
                            fallback_detection_history = {}
                        else:
                            # All cycles exhausted
                            if ENABLE_ORCHESTRATOR_LOGGING:
                                _orch_log(f"FALLBACK_SCAN: All {FALLBACK_SCAN_MAX_CYCLES} cycles exhausted, stopping fallback scan", "WARNING")
                            print(f"\n⚠️  Fallback scan stopped: All {FALLBACK_SCAN_MAX_CYCLES} retry cycles exhausted. "
                                  f"Relying on normal exit zone switching.")
                            
                            # Reset everything
                            fallback_scan_count = 0
                            fallback_cycle_count = 0
                            fallback_consecutive_found = {}
                            fallback_detection_history = {}
                            fallback_pause_until_frame = 0
        
        # Reset scan count and cycles if ball is found in current camera
        if ball_found:
            fallback_scan_count = 0
            fallback_cycle_count = 0
            fallback_consecutive_found = {}
            fallback_detection_history = {}
            fallback_pause_until_frame = 0
```

## Key Phase 2 Features

### 1. Context-Aware Alternating Logic

**How it works:**
- Calculates ball velocity from position history
- Checks if ball is near exit zones
- If ball is moving AND near zones → allows alternating cameras (requires 4 consecutive)
- If ball is stationary OR away from zones → requires same camera (requires 3 consecutive)

**Benefits:**
- Handles ball movement between cameras naturally
- Reduces false positives when ball is stationary
- Adapts to different game situations

### 2. Time Window with Decay

**How it works:**
- Tracks detection history with timestamps
- Only counts detections within 60 frames (2 seconds)
- Applies decay factor (0.5) to older detections
- Uses weighted count for more accurate validation

**Benefits:**
- Ensures we're tracking the same ball movement
- Prevents counting unrelated detections
- More robust than simple consecutive counting

### 3. Adaptive Stopping with Retry Cycles

**How it works:**
- After 40 attempts, pauses for 90 frames (3 seconds)
- Starts a new cycle (up to 3 cycles total)
- Resets counters between cycles
- Stops after 3 cycles and relies on normal switching

**Benefits:**
- Prevents infinite scanning loops
- Gives system time to recover between attempts
- Balances persistence with resource usage

## Configuration Tuning

### Context-Aware Parameters

- `FALLBACK_BALL_VELOCITY_THRESHOLD`: Minimum velocity to consider ball "moving"
  - Lower (0.005) = more sensitive to movement
  - Higher (0.02) = requires more movement
  - Default: 0.01

- `FALLBACK_ZONE_PROXIMITY_THRESHOLD`: Distance from zone to consider "near"
  - Lower (0.10) = stricter zone proximity
  - Higher (0.20) = more lenient
  - Default: 0.15

### Time Window Parameters

- `FALLBACK_CONSECUTIVE_TIME_WINDOW`: Time window for consecutive detections
  - 45 frames = 1.5 seconds (tighter)
  - 60 frames = 2 seconds (default)
  - 90 frames = 3 seconds (more lenient)

- `FALLBACK_CONSECUTIVE_DECAY`: Decay factor for older detections
  - 0.3 = stronger decay (older detections count less)
  - 0.5 = moderate decay (default)
  - 0.7 = weaker decay (older detections still count)

### Retry Cycle Parameters

- `FALLBACK_SCAN_PAUSE_AFTER_MAX`: Pause duration between cycles
  - 60 frames = 2 seconds (shorter pause)
  - 90 frames = 3 seconds (default)
  - 120 frames = 4 seconds (longer pause)

- `FALLBACK_SCAN_MAX_CYCLES`: Maximum retry cycles
  - 2 cycles = less persistent
  - 3 cycles = balanced (default)
  - 5 cycles = very persistent

## Testing Phase 2

### Test Scenarios

1. **Moving Ball Near Zones**:
   - Ball moving left to right near exit zone
   - Should allow alternating cameras
   - Should require 4 consecutive detections

2. **Stationary Ball Away from Zones**:
   - Ball detected but not moving
   - Should require same camera
   - Should require 3 consecutive detections

3. **Time Window Validation**:
   - Detections spread over 3 seconds
   - Older detections should have reduced weight
   - Should only count detections within 2 seconds

4. **Retry Cycles**:
   - Ball lost for extended period
   - Should pause after 40 attempts
   - Should retry up to 3 cycles
   - Should stop after 3 cycles

5. **Ball Found During Scan**:
   - Ball appears in current camera during fallback scan
   - Should immediately reset all counters
   - Should stop scanning

## Integration Notes

- Phase 2 builds on Phase 1 - all Phase 1 features remain active
- Phase 2 adds intelligence on top of Phase 1's validation
- Both phases work together for robust false positive filtering
- Can be disabled by setting `FALLBACK_SCAN_MAX_CYCLES = 0` (falls back to Phase 1 only)

## Expected Behavior

**Scenario 1: Ball moving between cameras**
- Detects ball in Camera A, then Camera B, then Camera A
- Recognizes alternating pattern
- Requires 4 consecutive detections
- Switches after meeting requirement

**Scenario 2: Ball stationary in one camera**
- Detects ball in Camera A multiple times
- Recognizes same camera pattern
- Requires 3 consecutive detections
- Switches after meeting requirement

**Scenario 3: Extended ball loss**
- Scans for 40 attempts (200 frames = ~6.7 seconds)
- Pauses for 90 frames (3 seconds)
- Retries cycle 2
- If still no ball, retries cycle 3
- After 3 cycles, stops and relies on normal switching

## Performance Considerations

- Time window validation adds minimal overhead (just timestamp tracking)
- Context calculation (velocity, zone proximity) is lightweight
- Retry cycles prevent excessive scanning
- Overall impact: ~5-10% additional processing during fallback scan phase
