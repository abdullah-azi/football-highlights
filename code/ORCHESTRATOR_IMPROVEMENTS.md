# Orchestrator Improvements Applied

## Summary
Merged key improvements from the temp orchestrator cell into the main orchestrator cell while preserving all existing features.

## Key Improvements Added

### 1. **Hard-Sync on Camera Switch** ✅
**Problem**: When switching cameras, the target camera might be at a different frame position, causing time-jumps.

**Solution**: Added `_hard_sync_cap()` function that syncs the target camera to the reference timeline position before switching.

**Location**: 
- Before fallback switch (around line 8630)
- Before normal switch (around line 9050)

**Code Added**:
```python
def _hard_sync_cap(cap: cv2.VideoCapture, target_frame: int) -> None:
    """Hard-sync camera to target frame position (fixes time-jumps on switch)."""
    try:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(target_frame))
    except Exception as e:
        if ENABLE_ORCHESTRATOR_LOGGING:
            _orch_log(f"Warning: Could not sync camera to frame {target_frame}: {e}", "WARNING")
```

### 2. **Reference Timeline Tracking** ✅
**Problem**: Using only `global_frame_idx` counter doesn't account for actual video frame positions, which can drift.

**Solution**: Use reference camera's actual frame position (`CAP_PROP_POS_FRAMES`) as the true timeline index.

**Location**: Main loop (around line 8570)

**Code Added**:
```python
# ✅ TIMELINE TRACKING: Use reference camera frame position as true timeline
REF_CAM_ID = active_cam
ref_cap = caps.get(REF_CAM_ID, cap)
ref_frame_pos = _get_frame_pos(ref_cap)
```

### 3. **Round-Robin Fallback Scanning** ✅
**Problem**: Scanning all cameras every tick is CPU-intensive.

**Solution**: Added `FALLBACK_SCAN_ONE_CAM_PER_TICK` option to scan one camera per tick using round-robin.

**Location**: Fallback scan configuration (around line 8470)

**Code Added**:
```python
FALLBACK_SCAN_ONE_CAM_PER_TICK = False  # Set True to scan one camera per tick (reduces CPU load)
fallback_rr_idx = 0  # Round-robin index

# In fallback scan loop:
if FALLBACK_SCAN_ONE_CAM_PER_TICK and len(other_cams) > 0:
    cam_to_scan = other_cams[fallback_rr_idx % len(other_cams)]
    fallback_rr_idx += 1
    cams_to_check = [cam_to_scan]
else:
    cams_to_check = other_cams
```

### 4. **Better Error Handling** ✅
**Problem**: When active camera reaches end of video, orchestrator stops completely.

**Solution**: Added failover logic to try switching to another camera instead of stopping.

**Location**: Main loop read error handling (around line 8580)

**Code Added**:
```python
if not ok:
    # Try switching to another camera instead of stopping
    other_cams = [cid for cid in CAMERA_MAP.keys() if cid != active_cam]
    for other_cam_id in other_cams:
        # Sync and try reading from other camera
        _hard_sync_cap(other_cap, ref_frame_pos)
        ok_test, frame_test = other_cap.read()
        if ok_test:
            # Successfully switched
            active_cam = other_cam_id
            break
```

### 5. **Helper Functions** ✅
**Added**:
- `_get_frame_pos(cap)`: Gets current frame position safely
- `_hard_sync_cap(cap, target_frame)`: Syncs camera to target frame

## Preserved Features

All existing features from the main cell are preserved:
- ✅ SYNCED_CAMERA_MAP integration
- ✅ Exit zone rebuilding
- ✅ Phase 0 startup camera selection
- ✅ Phase 2 fallback enhancements (context-aware, time-windowed, retry cycles)
- ✅ Comprehensive statistics tracking
- ✅ Integration with camera_switcher and sticky_tracker
- ✅ All existing configuration options

## Benefits

1. **No Time-Jumps**: Hard-sync ensures cameras stay aligned when switching
2. **Better Performance**: Round-robin option reduces CPU load during fallback scanning
3. **More Robust**: Better error handling prevents premature stopping
4. **Accurate Timeline**: Reference camera frame position provides true timeline tracking

## Configuration

New configuration option:
- `FALLBACK_SCAN_ONE_CAM_PER_TICK = False`: Set to `True` to enable round-robin scanning (reduces CPU load but may be slightly slower to detect ball)

## Testing Recommendations

1. Test camera switching to verify no time-jumps occur
2. Test fallback scanning with `FALLBACK_SCAN_ONE_CAM_PER_TICK = True` to verify reduced CPU usage
3. Test end-of-video scenario to verify failover works
4. Compare timeline accuracy with reference camera tracking
