# Highlight Output - Missing Items Review

**Date:** 2026-01-10  
**File:** `football_camera_switching.py`

## Review Summary

After reviewing the highlight output section (lines ~9400-10361) against the `highlight_output_improvements.md` recommendations, here are the findings:

---

## ✅ What's Already Implemented

1. **Hard-align cameras after skip** - ✅ IMPLEMENTED
   - Lines 9640-9677: Camera synchronization verification after skip
   - Uses reference frame for alignment
   - Auto-resync if mismatch detected

2. **Camera dominance warnings** - ✅ IMPLEMENTED
   - Lines 10303-10316: Warnings when camera > 90% usage
   - Includes diagnostic suggestions

3. **Frame-accurate skip logic** - ✅ IMPLEMENTED
   - Lines 9596-9637: Frame-based skipping with reference camera
   - Fallback to time-based if needed
   - Verification and resync logic

4. **Lazy VideoWriter initialization** - ✅ IMPLEMENTED
   - Lines 10195-10206: Writer initialized after first valid frame

5. **FPS fallback protection** - ✅ IMPLEMENTED
   - Line 9552: `fps = fps if fps and fps > 0 else OUTPUT_FPS_FALLBACK`
   - Line 10198: Uses fallback FPS for writer

6. **Logging and statistics** - ✅ IMPLEMENTED
   - Comprehensive logging throughout
   - Statistics tracking and saving

7. **Treat orchestrator as single source of truth** - ✅ IMPLEMENTED
   - Uses `camera_switcher.active_cam` directly
   - No decision logic in highlight cell

---

## ❌ What's Missing

### 1. **Frame Indices and Camera IDs Logging During Writing** - PARTIALLY MISSING
**Status:** ⚠️ PARTIAL  
**Priority:** MEDIUM

**Current State:**
- Frame index is logged in progress updates (line 10230)
- Camera ID is logged in progress updates (line 10224)
- Switch events include frame indices (line 10101)

**Missing:**
- Detailed per-frame logging of `(frame_idx, camera_id)` during writing is not explicitly logged to file
- Could add detailed frame-by-frame logging option for debugging

**Recommendation:**
Add optional detailed frame logging:
```python
if ENABLE_HIGHLIGHT_LOGGING and (global_frame_idx % 30 == 0):  # Every 30 frames
    _highlight_log(f"Frame {global_frame_idx}: camera={active_cam}, written={written_frames}", "DEBUG")
```

---

### 2. **Explicit Frame Read Failure Handling** - PARTIALLY MISSING
**Status:** ⚠️ BASIC HANDLING EXISTS  
**Priority:** MEDIUM

**Current State:**
- Basic error handling exists (lines 9881-9891)
- Error counter and break on too many errors
- Exception handling for read failures

**Missing:**
- No explicit retry logic for transient failures
- No distinction between end-of-video vs read failure
- No explicit decision on retry/skip/terminate policy

**Current Code:**
```python
try:
    ok, frame = cap.read()
except Exception as e:
    errors += 1
    # ... logging ...
    if errors > 10:
        break
    continue
```

**Recommendation:**
Add explicit retry logic and better failure classification:
```python
# Track read failures per camera
read_failures_per_camera = {}
max_retries = 3

try:
    ok, frame = cap.read()
    if not ok:
        # Distinguish end-of-video from read failure
        read_failures_per_camera[active_cam] = read_failures_per_camera.get(active_cam, 0) + 1
        if read_failures_per_camera[active_cam] < max_retries:
            # Retry
            continue
        else:
            # End of video or persistent failure
            break
except Exception as e:
    # Explicit retry for transient failures
    ...
```

---

### 3. **Output FPS Policy Documentation** - MISSING
**Status:** ❌ NOT DOCUMENTED  
**Priority:** LOW

**Current State:**
- Output FPS is computed from active camera (line 10198)
- Fallback FPS is used if camera FPS unavailable
- No explicit documentation of the policy

**Missing:**
- No comment explaining the FPS policy
- No documentation of whether FPS normalization is intentional

**Recommendation:**
Add documentation comment:
```python
# Output FPS Policy:
# - Uses active camera's FPS if available
# - Falls back to OUTPUT_FPS_FALLBACK if camera FPS is 0 or unavailable
# - This may cause slight speed differences if input FPS varies
# - For consistent output speed, consider normalizing all inputs to same FPS
out_fps = fps_map_out.get(active_cam, OUTPUT_FPS_FALLBACK)
```

---

### 4. **Audio Handling Documentation** - MISSING
**Status:** ❌ NOT DOCUMENTED  
**Priority:** LOW

**Current State:**
- OpenCV VideoWriter is used (line 10200)
- No audio handling
- No documentation about audio loss

**Missing:**
- No comment explaining that audio is dropped
- No mention of post-process audio mux option

**Recommendation:**
Add clear documentation:
```python
# ==============================
# NOTE: Audio Handling
# ==============================
# OpenCV VideoWriter does NOT preserve audio from source videos.
# The output highlight video will be SILENT.
#
# To add audio:
# 1. Use FFmpeg post-processing to mux audio from source videos
# 2. Example: ffmpeg -i highlight.mp4 -i source_audio.wav -c copy output_with_audio.mp4
# ==============================
```

---

## Summary

### Missing Items (Priority Order)

1. **Explicit Frame Read Failure Handling** (MEDIUM)
   - Add retry logic
   - Distinguish end-of-video from failures
   - Better failure classification

2. **Frame Indices and Camera IDs Logging During Writing** (MEDIUM)
   - Add optional detailed per-frame logging
   - Useful for debugging timeline issues

3. **Output FPS Policy Documentation** (LOW)
   - Document the FPS selection policy
   - Explain potential speed differences

4. **Audio Handling Documentation** (LOW)
   - Document that audio is dropped
   - Mention post-process options

---

## Implementation Recommendations

### Quick Wins (Easy to Add)

1. **Add FPS Policy Comment** - Just add a comment block
2. **Add Audio Documentation** - Just add a comment block explaining audio loss

### Medium Effort

3. **Enhanced Frame Read Failure Handling** - Add retry logic and better classification
4. **Detailed Frame Logging** - Add optional debug logging for frame indices

---

## Notes

- Most critical improvements are already implemented
- Missing items are mostly documentation and polish
- Frame read failure handling could be improved but current implementation is functional
- Audio handling is a known limitation that should be documented

---

**End of Review**
