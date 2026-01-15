# Fallback Camera Scanning Implementation

## Overview
This document provides the exact code changes needed to implement fallback camera scanning in Cell 8 (Multi-Camera Orchestrator).

## What It Does
When the ball is lost for 3-4 seconds (105 frames at 30fps), the system will:
1. Scan other cameras to see if the ball is visible there
2. If found in another camera, automatically switch to that camera
3. This acts as a fallback when zone-based switching doesn't trigger

## Configuration (Already Added)
The configuration is already in place at the start of Phase 1:
```python
ENABLE_FALLBACK_SCAN = True          # Enable fallback scanning when ball is lost
FALLBACK_SCAN_TIMEOUT_FRAMES = 105   # 3.5 seconds at 30fps (adjust: 90-120 frames)
FALLBACK_SCAN_MIN_CONF = 0.20        # Minimum confidence to consider ball "found" in other camera
```

## Code Changes Required

### 1. Add Initialization (Before the `while running:` loop)

**Location**: After line `_orch_stats["phase1"]["camera_usage"][active_cam] = 0` and before `try:`

**Add this line:**
```python
# Initialize fallback scanning: track last frame when ball was found
last_ball_found_frame = 0
```

### 2. Add Ball Tracking and Fallback Logic (After ball tracking, before camera switching decision)

**Location**: After the ball tracking section (after `})()` and before `# ---- Camera switching decision ----`)

**Add this code:**
```python
        # Track last frame when ball was found (for fallback scanning)
        ball_found = (det.bbox is not None and det.conf >= FALLBACK_SCAN_MIN_CONF)
        if ball_found:
            last_ball_found_frame = global_frame_idx
        elif 'last_ball_found_frame' not in locals():
            last_ball_found_frame = global_frame_idx  # Initialize on first frame

        # ---- Fallback camera scanning (when ball lost for too long) ----
        frames_since_ball_found = global_frame_idx - last_ball_found_frame
        fallback_switch_occurred = False
        
        if (ENABLE_FALLBACK_SCAN and 
            frames_since_ball_found >= FALLBACK_SCAN_TIMEOUT_FRAMES and
            not camera_switcher.is_cooldown_active()):  # Don't scan during cooldown
            
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
                            if (other_det.bbox is not None and 
                                other_det.conf >= FALLBACK_SCAN_MIN_CONF and
                                other_det.conf > best_other_conf):
                                best_other_cam = other_cam_id
                                best_other_conf = other_det.conf
                        except Exception as e:
                            if ENABLE_ORCHESTRATOR_LOGGING:
                                _orch_log(f"Error detecting ball in camera {other_cam_id} during fallback scan: {e}", "WARNING")
                except Exception as e:
                    if ENABLE_ORCHESTRATOR_LOGGING:
                        _orch_log(f"Error reading from camera {other_cam_id} during fallback scan: {e}", "WARNING")
            
            # Switch to other camera if ball found there
            if best_other_cam is not None:
                old_cam = active_cam
                active_cam = best_other_cam
                _orch_stats["phase1"]["switches"] += 1
                
                switch_event = {
                    "frame": global_frame_idx,
                    "from_cam": old_cam,
                    "to_cam": active_cam,
                    "zone": "FALLBACK_SCAN",
                    "exit_prob": best_other_conf,
                    "reason": f"ball_lost_{frames_since_ball_found}_frames_found_in_other_cam"
                }
                _orch_stats["phase1"]["switch_events"].append(switch_event)
                
                print(f"\n🔄 FALLBACK SWITCH at frame={global_frame_idx:06d}: "
                      f"{CAMERA_NAMES[old_cam]} -> {CAMERA_NAMES[active_cam]} "
                      f"(ball lost for {frames_since_ball_found} frames, found with conf={best_other_conf:.2f})")
                
                if ENABLE_ORCHESTRATOR_LOGGING:
                    _orch_log(f"FALLBACK_SWITCH: frame={global_frame_idx}, {old_cam}->{active_cam}, "
                             f"lost_for={frames_since_ball_found}frames, conf={best_other_conf:.2f}", "INFO")
                
                # Reset sticky tracker and update last_ball_found_frame
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
                
                # Skip normal switching decision for this frame (already switched)
                continue

        # ---- Camera switching decision (only if no fallback switch occurred) ----
```

### 3. Update Comment (Optional)
Change the comment from:
```python
        # ---- Camera switching decision ----
```
to:
```python
        # ---- Camera switching decision (only if no fallback switch occurred) ----
```

## How It Works

1. **Ball Tracking**: After each frame's ball detection, we check if the ball was found (bbox exists and confidence >= 0.20)
2. **Timeout Check**: If ball hasn't been found for 105 frames (3.5 seconds), and we're not in cooldown, trigger fallback scan
3. **Camera Scanning**: For each other camera:
   - Seek to the same frame position as the active camera
   - Read the frame
   - Run ball detection on that frame
   - Track the best detection (highest confidence)
4. **Switch Decision**: If ball found in another camera with confidence >= 0.20, switch to that camera
5. **Skip Normal Logic**: If a fallback switch occurred, skip the normal zone-based switching for this frame

## Configuration Tuning

- **FALLBACK_SCAN_TIMEOUT_FRAMES**: Adjust based on your needs:
  - 90 frames = 3 seconds at 30fps (more aggressive)
  - 105 frames = 3.5 seconds at 30fps (default)
  - 120 frames = 4 seconds at 30fps (more conservative)

- **FALLBACK_SCAN_MIN_CONF**: Minimum confidence to consider ball "found":
  - 0.15 = More sensitive (may switch on weaker detections)
  - 0.20 = Default (balanced)
  - 0.25 = More conservative (only switch on strong detections)

## Expected Behavior

When the ball is lost for 3-4 seconds:
- Console will show: `🔄 FALLBACK SWITCH at frame=XXXXXX: LEFT_CAM -> RIGHT_CAM (ball lost for 105 frames, found with conf=0.XX)`
- Log file will record: `FALLBACK_SWITCH: frame=XXXXXX, 0->1, lost_for=105frames, conf=0.XX`
- Switch event will have `"zone": "FALLBACK_SCAN"` and reason will indicate frames lost

## Testing

After implementing:
1. Run Cell 8 (Orchestrator)
2. Watch for "FALLBACK SWITCH" messages in console
3. Check orchestrator log file for fallback switch events
4. Verify switches occur when ball is lost for 3-4 seconds
