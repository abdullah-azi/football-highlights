# Orchestrator Improvements Summary

## Overview
This document summarizes the improvements applied to the **main orchestrator cell** (Cell 9) based on the **temp orchestrator cell** (Cell 12).

## Key Improvements Applied

### 1. ✅ Timeline Synchronization Helpers
**Location**: After Phase 1 config (around line 8318)

Added helper functions for timeline synchronization:
- `_get_frame_pos(cap)`: Gets current frame position from video capture
- `_hard_sync_cap(cap, target_frame)`: Hard-syncs camera to target frame position (fixes time-jumps)

**Why**: Prevents time-jumps when switching cameras by ensuring all cameras are synchronized to the same timeline position.

### 2. ✅ Reference Camera Tracking
**Location**: Before main loop (around line 8338)

- Initialize `REF_CAM_ID` to active camera (or first camera as fallback)
- Initialize `ACTIVE_CAM_TIMELINE = []` for timeline tracking
- Update `REF_CAM_ID = active_cam` in main loop

**Why**: Uses actual video frame positions as the true timeline, not loop counter, ensuring accurate synchronization.

### 3. ✅ Timeline Tracking After Frame Read
**Location**: After `cap.read()` in main loop (around line 8429)

- Get `ref_frame_pos` from reference camera AFTER reading frame
- Append `(ref_frame_pos, active_cam)` to `ACTIVE_CAM_TIMELINE`

**Why**: Ensures timeline uses actual video position, not loop iteration count. This prevents desynchronization when cameras have different frame rates or seek positions.

### 4. ✅ Hard-Sync Before Camera Switches
**Location**: 
- Fallback switch (around line 8710)
- Normal switch decision (around line 8855)

Before switching to a new camera:
```python
ref_frame_pos = _get_frame_pos(caps.get(REF_CAM_ID))
_hard_sync_cap(caps[decision.to_cam], ref_frame_pos)
```

**Why**: Prevents time-jumps by ensuring target camera is at the same timeline position as reference camera before switching.

### 5. ✅ Better Error Handling - Failover on End of Video
**Location**: After `cap.read()` fails (around line 8425)

Instead of stopping when active camera reaches end:
- Try switching to other cameras
- Sync other cameras to reference position
- Continue processing if another camera has frames available

**Why**: Prevents premature stopping when one camera ends but others still have content.

### 6. ✅ Round-Robin Fallback Scanning
**Location**: Fallback scan section (around line 8520)

Added `FALLBACK_SCAN_ONE_CAM_PER_TICK` option:
- If enabled: Scan one camera per tick (round-robin) instead of all cameras
- Reduces CPU load during fallback scanning
- Uses `fallback_rr_idx` to cycle through cameras

**Why**: Reduces CPU load when scanning multiple cameras during fallback phase.

### 7. ✅ Hard-Sync in Fallback Scan
**Location**: Fallback scan loop (around line 8580)

When scanning other cameras:
- Use `ref_frame_pos` from reference camera
- Sync each camera to `ref_frame_pos` before reading
- Ensures all cameras are at same timeline position

**Why**: Prevents timeline drift when scanning multiple cameras during fallback.

### 8. ✅ Timeline Stats in Output
**Location**: Stats saving section (around line 9045)

Added timeline information to saved stats:
```python
stats["timeline_sample_head"] = ACTIVE_CAM_TIMELINE[:50]
stats["timeline_len"] = len(ACTIVE_CAM_TIMELINE)
```

**Why**: Provides timeline data for debugging and analysis.

## Fixed Issues

### 1. Indentation Errors
- Fixed `while running:` indentation (was incorrectly indented)
- Fixed `if not ok:` indentation (was incorrectly indented)
- Fixed `continue` statement indentation

### 2. Reference Camera Initialization
- Fixed `ref_cap` initialization to handle cases where `REF_CAM_ID` camera doesn't exist
- Added fallback to `active_cam` or `cap` when needed

### 3. Timeline Position Calculation
- Moved timeline tracking to AFTER frame read (as temp cell does)
- Ensures accurate frame position tracking

## Improvements from Temp Cell NOT Applied (Intentionally)

### 1. Simplified Detection Parsing
**Temp cell has**: `_parse_det()` function to normalize detection output
**Main cell**: Uses existing `BallDet` class directly
**Reason**: Main cell already has proper detection structure, no need to change

### 2. Different Phase 0 Configuration
**Temp cell**: `PHASE0_SCAN_FRAMES = 60`, `PHASE0_CONF_THRESHOLD = 0.30`
**Main cell**: `PHASE0_SCAN_FRAMES = 900`, `PHASE0_CONF_THRESHOLD = 0.12`
**Reason**: Main cell's configuration is more thorough (30 seconds vs 2 seconds)

### 3. Different Fallback Configuration
**Temp cell**: Simpler fallback logic with `FALLBACK_SCAN_EVERY_N_FRAMES = 10`
**Main cell**: More sophisticated Phase 2 fallback with consecutive detection validation
**Reason**: Main cell's fallback is more advanced and reduces false positives better

## Testing Recommendations

After applying these improvements, test:

1. **Timeline Synchronization**: 
   - Verify cameras stay synchronized after switches
   - Check that `ref_frame_pos` matches actual video positions
   - Verify no time-jumps occur during switches

2. **Failover Handling**:
   - Test behavior when one camera reaches end of video
   - Verify system switches to other cameras instead of stopping

3. **Round-Robin Scanning**:
   - Enable `FALLBACK_SCAN_ONE_CAM_PER_TICK = True`
   - Verify CPU usage decreases during fallback scanning
   - Verify ball detection still works correctly

4. **Timeline Tracking**:
   - Check `ACTIVE_CAM_TIMELINE` in saved stats
   - Verify timeline positions are sequential and accurate

## Configuration Options Added

```python
# Round-robin fallback scanning (from temp cell improvement)
FALLBACK_SCAN_ONE_CAM_PER_TICK = False  # Set True to scan one camera per tick (reduces CPU load)
```

## Summary

The main orchestrator cell now includes all critical improvements from the temp cell:
- ✅ Hard-sync target camera at switch moment
- ✅ Use CAP_PROP_POS_FRAMES as true timeline index
- ✅ Safer fallback scanning (round-robin option)
- ✅ Better failover handling
- ✅ Timeline tracking and stats

The main cell retains its advanced features (Phase 2 fallback, hybrid switching, etc.) while gaining the synchronization and error handling improvements from the temp cell.
