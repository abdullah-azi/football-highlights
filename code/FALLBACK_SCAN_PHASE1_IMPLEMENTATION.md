# Phase 1 Enhanced Fallback Scan Implementation

## Overview
This document provides the exact code changes needed to implement Phase 1 of the enhanced fallback scan system.

## Changes Required

### 1. Update Configuration Section (around line 6847)

**Replace:**
```python
# Fallback camera scanning configuration
ENABLE_FALLBACK_SCAN = True          # Enable fallback scanning when ball is lost
FALLBACK_SCAN_TIMEOUT_FRAMES = 105   # 3.5 seconds at 30fps (adjust: 90-120 frames)
FALLBACK_SCAN_MIN_CONF = 0.20        # Minimum confidence to consider ball "found" in other camera
```

**With:**
```python
# Fallback camera scanning configuration - Phase 1 Enhanced
ENABLE_FALLBACK_SCAN = True          # Enable fallback scanning when ball is lost
FALLBACK_SCAN_TIMEOUT_FRAMES = 90    # 3 seconds at 30fps (adjust: 90-120 frames for 3-4 seconds)
FALLBACK_SCAN_MIN_CONF = 0.20        # Minimum confidence for normal ball tracking (current camera)
FALLBACK_SCAN_CONF_THRESHOLD = 0.25  # Higher threshold during fallback scan phase (reduces false positives)
FALLBACK_SCAN_INTERVAL = 5           # Scan every N frames once timeout is reached (reduces overhead)
FALLBACK_SCAN_REQUIRE_CONSECUTIVE = 3  # Require N consecutive detections in same camera to avoid false positives
FALLBACK_SCAN_MAX_ATTEMPTS = 40      # Maximum scan attempts before pausing (prevents infinite loops)

# Multi-criteria bbox validation for false positive detection
FALLBACK_MIN_BBOX_SIZE = 8           # Minimum dimension (pixels)
FALLBACK_MAX_BBOX_SIZE = 150         # Maximum dimension (pixels)
FALLBACK_MIN_BBOX_AREA = 64          # Minimum area (8x8 = 64 pixels²)
FALLBACK_MAX_BBOX_AREA = 22500       # Maximum area (150x150 = 22500 pixels²)
FALLBACK_ASPECT_RATIO_MIN = 0.5      # Minimum aspect ratio (width/height or height/width)
FALLBACK_ASPECT_RATIO_MAX = 2.0      # Maximum aspect ratio (ball should be roughly circular)
FALLBACK_RELATIVE_SIZE_MAX = 0.15    # Max bbox area relative to frame area (15% of frame)
```

### 2. Update Initialization Section (around line 6891)

**Replace:**
```python
# Initialize fallback scanning: track last frame when ball was found
last_ball_found_frame = 0
```

**With:**
```python
# Initialize fallback scanning: track last frame when ball was found
last_ball_found_frame = 0
fallback_scan_count = 0  # Track number of scan attempts
fallback_consecutive_found = {}  # Track consecutive detections per camera (for false positive filtering)
last_fallback_scan_frame = 0  # Track last frame we performed fallback scan
```

### 3. Replace Entire Fallback Scan Section (around line 6953)

**Replace the entire section from:**
```python
        # ---- Fallback camera scanning (when ball lost for too long) ----
        frames_since_ball_found = global_frame_idx - last_ball_found_frame
        fallback_switch_occurred = False
        
        if (ENABLE_FALLBACK_SCAN and 
            frames_since_ball_found >= FALLBACK_SCAN_TIMEOUT_FRAMES and
            not camera_switcher.is_cooldown_active()):  # Don't scan during cooldown
```

**To the end of the fallback scan section (before `# ---- Camera switching decision`)**

**With the new enhanced Phase 1 implementation (see next section)**

## Complete Enhanced Fallback Scan Code

Replace the entire fallback scan section with:

```python
        # ---- Enhanced Fallback camera scanning - Phase 1 (continuous until ball found) ----
        frames_since_ball_found = global_frame_idx - last_ball_found_frame
        fallback_switch_occurred = False
        
        # Check if we should perform fallback scan
        # Scan immediately when timeout is reached, then every N frames
        should_scan = (
            ENABLE_FALLBACK_SCAN and 
            frames_since_ball_found >= FALLBACK_SCAN_TIMEOUT_FRAMES and
            not camera_switcher.is_cooldown_active() and
            fallback_scan_count < FALLBACK_SCAN_MAX_ATTEMPTS and
            (global_frame_idx - last_fallback_scan_frame) >= FALLBACK_SCAN_INTERVAL
        )
        
        if should_scan:
            last_fallback_scan_frame = global_frame_idx
            fallback_scan_count += 1
            
            # Scan other cameras for ball
            other_cams = [cid for cid in CAMERA_MAP.keys() if cid != active_cam]
            best_other_cam = None
            best_other_conf = 0.0
            
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
                            
                            # Multi-criteria false positive detection
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
            
            # False positive filtering: require consecutive detections in same camera
            if best_other_cam is not None:
                # Update consecutive detection counter
                if best_other_cam not in fallback_consecutive_found:
                    fallback_consecutive_found[best_other_cam] = 0
                fallback_consecutive_found[best_other_cam] += 1
                
                # Reset counters for other cameras
                for cam_id in list(fallback_consecutive_found.keys()):
                    if cam_id != best_other_cam:
                        fallback_consecutive_found[cam_id] = 0
                
                # Only switch if we have enough consecutive detections
                if fallback_consecutive_found[best_other_cam] >= FALLBACK_SCAN_REQUIRE_CONSECUTIVE:
                    old_cam = active_cam
                    active_cam = best_other_cam
                    _orch_stats["phase1"]["switches"] += 1
                    
                    switch_event = {
                        "frame": global_frame_idx,
                        "from_cam": old_cam,
                        "to_cam": active_cam,
                        "zone": "FALLBACK_SCAN",
                        "exit_prob": best_other_conf,
                        "reason": f"ball_lost_{frames_since_ball_found}_frames_found_in_other_cam_after_{fallback_scan_count}_scans"
                    }
                    _orch_stats["phase1"]["switch_events"].append(switch_event)
                    
                    print(f"\n🔄 FALLBACK SWITCH at frame={global_frame_idx:06d}: "
                          f"{CAMERA_NAMES[old_cam]} -> {CAMERA_NAMES[active_cam]} "
                          f"(ball lost for {frames_since_ball_found} frames, found with conf={best_other_conf:.2f} "
                          f"after {fallback_scan_count} scans, {FALLBACK_SCAN_REQUIRE_CONSECUTIVE} consecutive confirmations)")
                    
                    if ENABLE_ORCHESTRATOR_LOGGING:
                        _orch_log(f"FALLBACK_SWITCH: frame={global_frame_idx}, {old_cam}->{active_cam}, "
                                 f"lost_for={frames_since_ball_found}frames, conf={best_other_conf:.2f}, "
                                 f"scans={fallback_scan_count}, consecutive={FALLBACK_SCAN_REQUIRE_CONSECUTIVE}", "INFO")
                    
                    # Reset sticky tracker and update last_ball_found_frame
                    try:
                        sticky_tracker.reset()
                    except Exception as e:
                        if ENABLE_ORCHESTRATOR_LOGGING:
                            _orch_log(f"Warning: Error resetting sticky tracker: {e}", "WARNING")
                    
                    last_ball_found_frame = global_frame_idx
                    fallback_scan_count = 0  # Reset scan count after successful switch
                    fallback_consecutive_found = {}  # Reset consecutive counters
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
                                 f"but need {FALLBACK_SCAN_REQUIRE_CONSECUTIVE} consecutive (current: {fallback_consecutive_found[best_other_cam]})", "INFO")
            else:
                # No valid detection found, reset consecutive counters
                fallback_consecutive_found = {}
                
                # Log if we're hitting max attempts
                if fallback_scan_count >= FALLBACK_SCAN_MAX_ATTEMPTS:
                    if ENABLE_ORCHESTRATOR_LOGGING:
                        _orch_log(f"FALLBACK_SCAN: Reached max attempts ({FALLBACK_SCAN_MAX_ATTEMPTS}), pausing scan", "WARNING")
                    print(f"\n⚠️  Fallback scan paused: Reached max attempts ({FALLBACK_SCAN_MAX_ATTEMPTS}) without finding ball")
        
        # Reset scan count if ball is found in current camera
        if ball_found:
            fallback_scan_count = 0
            fallback_consecutive_found = {}
```

## Key Features

1. **Immediate + Interval Scanning**: Scans immediately at timeout, then every 5 frames
2. **Multi-Criteria Bbox Validation**: Size, area, aspect ratio, and relative size checks
3. **Consecutive Detection Requirement**: Requires 3 consecutive detections in same camera
4. **Dynamic Confidence Threshold**: Uses 0.25 during fallback scan (vs 0.20 for normal tracking)
5. **Max Attempts Protection**: Stops after 40 attempts to prevent infinite loops
6. **Auto-Reset**: Resets counters when ball is found in current camera

## Testing

After implementation, test:
1. Ball lost in one camera, appears in another
2. False positive detection (person's head) - should be filtered
3. Continuous scanning until ball found
4. Max attempts limit
