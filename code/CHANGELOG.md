# Changelog - Performance Optimizations & Duration Control

This document tracks all changes made for performance optimization and duration control. Use this to understand what was changed and how to revert if needed.

---

## Table of Contents

1. [Performance Optimizations](#performance-optimizations)
   - [Phase 0 Scan Frames Reduction](#1-phase-0-scan-frames-reduction)
   - [Camera Synchronization Optimization](#2-camera-synchronization-optimization)
   - [Fallback Scanning Removal](#3-fallback-scanning-removal)
2. [Duration Control Changes](#duration-control-changes)
   - [Frame-Based Duration Control](#4-frame-based-duration-control)

---

## Performance Optimizations

### 1. Phase 0 Scan Frames Reduction

**Date:** Performance optimization session  
**Location:** Lines ~7973 and ~9841  
**Purpose:** Reduce startup time by scanning fewer frames

**Change:**
- **Before:** `PHASE0_SCAN_FRAMES = 900` (30 seconds per camera)
- **After:** `PHASE0_SCAN_FRAMES = 300` (10 seconds per camera)

**Impact:**
- **Time saved:** ~31 seconds (66% reduction in Phase 0)
- **Before:** 900 frames × 2 cameras × 26ms = ~47 seconds
- **After:** 300 frames × 2 cameras × 26ms = ~16 seconds

**Code Location:**
```python
# Line ~7973 (orchestrator section)
PHASE0_SCAN_FRAMES = 300          # frames to scan per camera (~10 seconds at 30fps, reduced from 900 for performance)

# Line ~9841 (highlight generation section)
PHASE0_SCAN_FRAMES = 300          # frames to scan per camera (~10 seconds at 30fps, reduced from 900 for performance)
```

**To Revert:**
Change both instances back to `900`.

---

### 2. Camera Synchronization Optimization

**Date:** Performance optimization session  
**Location:** Lines ~10312-10328  
**Purpose:** Reduce synchronization overhead by syncing less frequently

**Change:**
- **Before:** Synced all cameras on every frame
- **After:** Syncs every 30 frames (~1 second @ 30fps)

**Impact:**
- Reduces position checks and seeks
- **Time saved:** ~0.1-0.2ms per frame × 459 frames = ~50-100ms
- More significant for longer videos

**Code Location:**
```python
# Lines ~10312-10328
# PERFORMANCE OPTIMIZATION: Sync cameras less frequently (every 30 frames = ~1 second @ 30fps)
# This reduces overhead while maintaining synchronization
SYNC_INTERVAL = 30  # Sync every N frames instead of every frame
if global_frame_idx % SYNC_INTERVAL == 0:
    try:
        active_frame_pos = _get_frame_pos(cap)
        # Sync all other cameras to the same frame position
        for cam_id, other_cap in caps_out.items():
            if cam_id != active_cam and other_cap is not None:
                other_pos = _get_frame_pos(other_cap)
                # Only sync if there's a significant difference (avoid unnecessary seeks)
                if abs(other_pos - active_frame_pos) > 1:
                    _hard_sync_cap(other_cap, active_frame_pos)
    except Exception as e:
        # Don't fail on sync errors, but log them
        if ENABLE_HIGHLIGHT_LOGGING and global_frame_idx % 300 == 0:
            _highlight_log(f"Warning: Could not sync cameras after frame read: {e}", "WARNING")
```

**Previous Code (Before Change):**
```python
# CRITICAL: Maintain synchronization - sync all cameras to active camera's position
# This prevents drift and ensures smooth switching
try:
    active_frame_pos = _get_frame_pos(cap)
    # Sync all other cameras to the same frame position
    for cam_id, other_cap in caps_out.items():
        if cam_id != active_cam and other_cap is not None:
            other_pos = _get_frame_pos(other_cap)
            # Only sync if there's a significant difference (avoid unnecessary seeks)
            if abs(other_pos - active_frame_pos) > 1:
                _hard_sync_cap(other_cap, active_frame_pos)
except Exception as e:
    # Don't fail on sync errors, but log them
    if ENABLE_HIGHLIGHT_LOGGING and global_frame_idx % 300 == 0:
        _highlight_log(f"Warning: Could not sync cameras after frame read: {e}", "WARNING")
```

**To Revert:**
Remove the `SYNC_INTERVAL` check and restore the original code that syncs every frame.

---

### 3. Fallback Scanning Removal

**Date:** Performance optimization session  
**Location:** Lines ~10347-10350 (replacement), Lines ~9845-9847 (config removal)  
**Purpose:** Remove expensive fallback scanning code for highlight generation

**Change:**
- **Before:** Full fallback scanning block (~180 lines) that scanned other cameras when ball was lost
- **After:** Removed entirely, replaced with simple comment

**Impact:**
- **Time saved:** ~0.1-0.5ms per frame (50-200ms total for 459 frames)
- Eliminates zone proximity check loop (runs every frame)
- Removes expensive multi-camera detection when ball is lost

**Code Location:**
```python
# Lines ~10347-10350 (replacement)
# PERFORMANCE OPTIMIZATION: Fallback scanning removed for highlight generation
# Fallback scanning is expensive (detects ball on all cameras) and less critical for highlights
# Main switching logic handles normal camera transitions efficiently

# Lines ~9845-9847 (config section)
# PERFORMANCE OPTIMIZATION: Fallback scanning removed for highlight generation
# Fallback scanning is expensive (detects ball on all cameras) and less critical for highlights
# Main switching logic handles normal camera transitions efficiently
```

**Removed Code:**
- Ball found tracking (lines ~10346-10351)
- Zone proximity check loop (lines ~10358-10371)
- Entire fallback scanning block (lines ~10353-10532)
- Configuration variable `ENABLE_FALLBACK_FOR_HIGHLIGHT` (line ~9846)

**To Revert:**
See `FALLBACK_CODE_REMOVED.md` for complete restoration instructions.

**Related Files:**
- `FALLBACK_CODE_REMOVED.md` - Detailed documentation of removed fallback code

---

## Duration Control Changes

### 4. Frame-Based Duration Control

**Date:** Duration control improvement  
**Location:** Multiple locations (see details below)  
**Purpose:** Ensure output video is exactly `MAX_DUR` seconds regardless of processing speed

**Change:**
- **Before:** Stopped based on processing time (`elapsed >= MAX_DUR`)
- **After:** Stops based on frames written (`written_frames >= target_frames`)

**Impact:**
- Output video is now exactly `MAX_DUR` seconds long
- Processing time no longer affects output duration
- More accurate progress reporting

**Code Locations:**

#### 4.1. Target Frames Calculation (Lines ~10262-10277)

**Added Code:**
```python
# ------------------------------
# CALCULATE TARGET FRAMES FOR EXACT DURATION
# ------------------------------
# Use the output FPS to calculate exact number of frames needed for MAX_DUR seconds
# This ensures the output video is exactly MAX_DUR seconds regardless of processing time
output_fps = fps_map_out.get(initial_cam, OUTPUT_FPS_FALLBACK)
target_frames = int(MAX_DUR * output_fps)  # Exact number of frames for desired duration

print(f"\n🎬 Writing highlight video...")
print(f"   Target duration: {MAX_DUR} seconds")
print(f"   Output FPS: {output_fps:.2f}")
print(f"   Target frames: {target_frames}")
if ENABLE_HIGHLIGHT_LOGGING:
    _highlight_log("Starting highlight video generation", "INFO")
    _highlight_log(f"Starting camera: {initial_cam} ({CAMERA_NAMES.get(initial_cam, 'Unknown')})", "INFO")
    _highlight_log(f"Target: {target_frames} frames ({MAX_DUR}s @ {output_fps:.2f} fps)", "INFO")
```

#### 4.2. Loop Stop Condition (Lines ~10283-10290)

**Changed From:**
```python
try:
    while True:
        elapsed = time.time() - start_time
        if elapsed >= MAX_DUR:
            print(f"\n📊 Reached MAX_DUR limit ({MAX_DUR}s). Stopping.")
            if ENABLE_HIGHLIGHT_LOGGING:
                _highlight_log(f"Reached MAX_DUR limit: {MAX_DUR}s", "INFO")
            break
```

**Changed To:**
```python
try:
    while True:
        # Stop when we've written the exact number of frames for the target duration
        # This ensures output video is exactly MAX_DUR seconds regardless of processing speed
        if written_frames >= target_frames:
            print(f"\n📊 Reached target frame count ({target_frames} frames = {MAX_DUR}s). Stopping.")
            if ENABLE_HIGHLIGHT_LOGGING:
                _highlight_log(f"Reached target frame count: {target_frames} frames ({MAX_DUR}s)", "INFO")
            break
```

#### 4.3. Overlay Display Update (Lines ~10492-10499)

**Changed From:**
```python
overlay_texts = [
    f"Frame: {global_frame_idx} | Camera: {CAMERA_NAMES[active_cam]}",
    f"Time: {elapsed:5.1f}s / {MAX_DUR:.0f}s | Skip: {SKIP_SECONDS/60:.1f}m"
]
```

**Changed To:**
```python
# Calculate video time based on frames written (not processing time)
# Use current camera's FPS for accurate time calculation
current_cam_fps = fps_map_out.get(active_cam, OUTPUT_FPS_FALLBACK)
video_time_sec = written_frames / current_cam_fps if current_cam_fps > 0 else 0
processing_time_elapsed = time.time() - start_time

overlay_texts = [
    f"Frame: {global_frame_idx} | Camera: {CAMERA_NAMES[active_cam]}",
    f"Video: {video_time_sec:5.1f}s / {MAX_DUR:.0f}s | Processing: {processing_time_elapsed:5.1f}s"
]
```

#### 4.4. Progress Logging Update (Lines ~10520-10540)

**Changed From:**
```python
# ---- Progress logging ----
current_time = time.time()
if current_time - last_progress_log >= PROGRESS_LOG_EVERY_N_SEC:
    progress_pct = (elapsed / MAX_DUR * 100) if MAX_DUR > 0 else 0
    progress_info = (
        f"⏱️  {elapsed:6.1f}s / {MAX_DUR:.0f}s ({progress_pct:5.1f}%) | "
        f"frames={global_frame_idx} | written={written_frames} | "
        f"cam={active_cam} ({CAMERA_NAMES[active_cam]}) | "
        f"switches={_highlight_stats['processing']['switches']}"
    )
    print(progress_info)

    if ENABLE_HIGHLIGHT_LOGGING:
        _highlight_log(f"Progress: {elapsed:.1f}s/{MAX_DUR:.0f}s, {global_frame_idx} frames, "
                     f"{written_frames} written, {_highlight_stats['processing']['switches']} switches", "INFO")
```

**Changed To:**
```python
# ---- Progress logging ----
# Use video time (frames/FPS) instead of processing time for accurate progress
current_time = time.time()
if current_time - last_progress_log >= PROGRESS_LOG_EVERY_N_SEC:
    # Calculate video time based on frames written and FPS (use current camera's FPS)
    current_cam_fps = fps_map_out.get(active_cam, OUTPUT_FPS_FALLBACK)
    video_time_sec = written_frames / current_cam_fps if current_cam_fps > 0 else 0
    progress_pct = (written_frames / target_frames * 100) if target_frames > 0 else 0
    processing_time_elapsed = current_time - start_time
    
    progress_info = (
        f"⏱️  Video: {video_time_sec:6.1f}s / {MAX_DUR:.0f}s ({progress_pct:5.1f}%) | "
        f"Processing: {processing_time_elapsed:6.1f}s | "
        f"frames={global_frame_idx} | written={written_frames}/{target_frames} | "
        f"cam={active_cam} ({CAMERA_NAMES[active_cam]}) | "
        f"switches={_highlight_stats['processing']['switches']}"
    )
    print(progress_info)

    if ENABLE_HIGHLIGHT_LOGGING:
        _highlight_log(f"Progress: {video_time_sec:.1f}s/{MAX_DUR:.0f}s video, {processing_time_elapsed:.1f}s processing, "
                     f"{global_frame_idx} frames, {written_frames}/{target_frames} written, "
                     f"{_highlight_stats['processing']['switches']} switches", "INFO")
```

#### 4.5. Final Summary Update (Lines ~10617-10625)

**Changed From:**
```python
print(f"\n📈 Processing Summary:")
print(f"   Frames written: {written_frames}")
print(f"   Processing time: {processing_time:.1f} seconds ({processing_time/60:.1f} minutes)")
if processing_time > 0:
    output_fps = written_frames / processing_time
    print(f"   Output speed: {output_fps:.1f} fps")
print(f"   Camera switches: {_highlight_stats['processing']['switches']}")
```

**Changed To:**
```python
print(f"\n📈 Processing Summary:")
print(f"   Frames written: {written_frames} / {target_frames} (target)")
# Use the output FPS that was actually used (from initial camera or writer initialization)
final_output_fps = fps_map_out.get(initial_cam, OUTPUT_FPS_FALLBACK)
if 'writer' in locals() and writer is not None:
    # Try to get FPS from writer if available
    try:
        writer_fps = writer.get(cv2.CAP_PROP_FPS) if hasattr(writer, 'get') else None
        if writer_fps and writer_fps > 0:
            final_output_fps = writer_fps
    except:
        pass
video_duration = written_frames / final_output_fps if final_output_fps > 0 else 0
print(f"   Video duration: {video_duration:.2f} seconds (target: {MAX_DUR}s)")
print(f"   Processing time: {processing_time:.1f} seconds ({processing_time/60:.1f} minutes)")
if processing_time > 0:
    processing_fps = written_frames / processing_time
    print(f"   Processing speed: {processing_fps:.1f} fps")
print(f"   Camera switches: {_highlight_stats['processing']['switches']}")
```

**To Revert:**
1. Remove target frames calculation (lines ~10262-10277)
2. Restore original loop stop condition (use `elapsed >= MAX_DUR`)
3. Restore original overlay display (use `elapsed` instead of `video_time_sec`)
4. Restore original progress logging (use `elapsed` instead of `video_time_sec`)
5. Restore original final summary (remove video duration calculation)

---

## Summary of All Changes

| Change | Location | Impact | Revert Difficulty |
|--------|----------|--------|-------------------|
| Phase 0 reduction | Lines ~7973, ~9841 | ~31s saved | Easy (change value) |
| Sync optimization | Lines ~10312-10328 | ~50-100ms saved | Medium (restore code) |
| Fallback removal | Lines ~10347-10350, ~9845-9847 | ~50-200ms saved | Hard (see FALLBACK_CODE_REMOVED.md) |
| Duration control | Multiple locations | Exact duration output | Medium (restore 5 sections) |

---

## Testing After Changes

After making any changes, verify:
1. **Phase 0:** Should complete in ~16 seconds (down from ~47 seconds)
2. **Synchronization:** Cameras should still stay in sync (check every 30 frames)
3. **Fallback:** Main switching should still work (fallback was only for recovery)
4. **Duration:** Output video should be exactly `MAX_DUR` seconds long

---

## Related Documentation

- `FALLBACK_CODE_REMOVED.md` - Detailed documentation of removed fallback code
- `PERFORMANCE_OPTIMIZATIONS_APPLIED.md` - Summary of performance improvements

---

**Last Updated:** Performance optimization and duration control session
