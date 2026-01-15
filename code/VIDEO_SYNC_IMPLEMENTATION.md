# Video Synchronization Implementation Guide

## Is This Possible?

**Yes, this is absolutely possible and is a common requirement for multi-camera systems.** The implementation leverages your existing scripts (`extract_metadata.py` and `trim_video.py`) and integrates seamlessly into your camera switching pipeline.

## Overview

The synchronization process will:
1. Extract metadata from all videos in the `Videos` directory
2. Compare timestamps and durations to determine sync offsets
3. Intelligently trim videos to align them temporally
4. Save synchronized videos to the `input` directory
5. Use synchronized videos for camera switching

## Step-by-Step Implementation Guide

### Step 1: Add New Cell After Drive Mount

**Location**: Insert a new cell after Cell 2 (Google Drive Mount) and before Cell 3 (Project Configuration)

**Purpose**: This cell will handle the entire video synchronization workflow

### Step 2: Define Video Synchronization Configuration

**What to Configure:**
- Path to `Videos` directory in Drive (e.g., `/content/drive/MyDrive/football/final/Videos`)
- Path to `input` directory (already exists in your config)
- Optional: Maximum allowed time difference between videos (e.g., 5 minutes)
- Optional: Minimum video duration after trimming (e.g., 30 seconds)

### Step 3: Discover Videos in Videos Directory

**Process:**
1. Scan the `Videos` directory for video files
2. Filter for supported formats (.MOV, .MP4, etc.)
3. Validate that at least 2 videos are found (required for multi-camera)
4. Store list of video paths for processing

**Error Handling:**
- If no videos found, raise clear error message
- If only 1 video found, warn that synchronization may not be needed
- If videos directory doesn't exist, create it or provide helpful error

### Step 4: Extract Metadata from All Videos

**Process:**
1. Loop through each discovered video file
2. Use your existing `extract_metadata.py` functionality (or import its functions)
3. Extract key metadata:
   - **Creation timestamp** (`creation_time` from metadata)
   - **Duration** (in seconds)
   - **File path** and name
   - **Frame rate** (for accurate frame calculations)

**Data Structure:**
- Store metadata in a list of dictionaries
- Each dictionary contains: `path`, `name`, `creation_time`, `duration`, `fps`, `metadata_file_path`

**Error Handling:**
- If metadata extraction fails for a video, log error and skip it
- Continue processing other videos even if one fails
- Provide summary of successful vs failed extractions

### Step 5: Parse and Normalize Timestamps

**Process:**
1. Parse `creation_time` strings from metadata (format: ISO 8601, e.g., "2026-01-05T20:04:20+0000")
2. Convert all timestamps to a common timezone (UTC recommended)
3. Handle different timestamp formats gracefully
4. Calculate absolute time differences between videos

**Key Considerations:**
- Some videos may have timestamps, others may not
- Handle missing timestamp data (fallback to file modification time)
- Account for timezone differences if cameras are in different locations

### Step 6: Determine Synchronization Strategy

**Analysis:**
1. Find the **earliest start time** among all videos (this becomes the reference)
2. Calculate **time offsets** for each video relative to the earliest
3. Determine the **common duration** (overlap period where all videos have content)
4. Identify if videos need trimming at the start, end, or both

**Synchronization Logic:**
- **Scenario A**: Videos start at different times but have overlapping duration
  - Solution: Trim early-starting videos from the beginning to match latest start
  - Solution: Trim late-starting videos from the beginning (no action needed, just note offset)
  
- **Scenario B**: Videos have different durations but same start time
  - Solution: Trim longer videos from the end to match shortest duration
  
- **Scenario C**: Videos have both different start times and durations
  - Solution: Trim from start to align, then trim from end to match shortest common duration

**Decision Making:**
- Calculate the **common time window** where all videos overlap
- This becomes the synchronized duration
- Store trim parameters: `start_trim_seconds` and `end_trim_seconds` for each video

### Step 7: Validate Synchronization Feasibility

**Checks:**
1. Ensure common overlap duration is sufficient (e.g., > 30 seconds)
2. Verify that time differences are reasonable (not hours apart)
3. Check that all videos have valid metadata
4. Confirm frame rates are compatible (or handle frame rate differences)

**Error Handling:**
- If videos don't overlap sufficiently, warn user
- If time difference is too large, suggest manual review
- If frame rates differ significantly, note this for user awareness

### Step 8: Generate Trimmed/Synchronized Videos

**Process:**
1. For each video, calculate trim parameters:
   - `start_time`: Time offset from video start (seconds)
   - `duration`: Duration to keep (seconds) OR `end_time`: Time to stop at
   
2. Use your existing `trim_video.py` functionality:
   - Call trim function with calculated parameters
   - Use fast, lossless trimming (stream copy) for speed
   - Save output to `input` directory with descriptive names

**Naming Convention:**
- Original: `IMG_0687.MOV`
- Synced: `IMG_0687_synced.MOV` or `IMG_0687_synced.mp4`
- Alternative: `camera_0_synced.mp4`, `camera_1_synced.mp4` (if you want sequential naming)

**Processing:**
- Process videos sequentially or in parallel (sequential is safer)
- Show progress for each video (e.g., "Trimming video 1/3...")
- Handle errors gracefully (continue with other videos if one fails)

### Step 9: Verify Synchronized Videos

**Validation:**
1. Check that all output files were created successfully
2. Verify file sizes are reasonable (not zero bytes)
3. Optionally: Extract metadata from synced videos to confirm alignment
4. Compare durations to ensure they match (within small tolerance)

**Error Handling:**
- If a synced video is missing, log error and continue
- If file size is suspiciously small, warn user
- Provide summary of successful vs failed synchronizations

### Step 10: Update Camera Mapping

**Process:**
1. After synchronization, update the camera mapping in your notebook
2. Map camera IDs to the new synced video files in `input` directory
3. Ensure the mapping matches the order you want (e.g., camera 0 = left, camera 1 = right)

**Integration:**
- The existing `CAMERA_MAP` in Cell 9 (orchestrator) should point to synced videos
- Update `INPUT_VIDEOS` discovery to use synced files
- Ensure video discovery (Cell 4) finds the synced videos

### Step 11: Cleanup and Summary

**Output:**
1. Print summary of synchronization:
   - Number of videos processed
   - Common start time (reference)
   - Common duration (synchronized length)
   - Time offsets for each video
   - Output file paths
   
2. Save synchronization metadata (optional):
   - JSON file with sync parameters
   - Can be used for reference or debugging
   - Store in `debug` directory

**Error Reporting:**
- List any videos that failed to sync
- Provide reasons for failures
- Suggest next steps if issues occurred

## Implementation Considerations

### Performance Optimization

1. **Parallel Processing**: Consider processing multiple videos in parallel if system resources allow
2. **Caching**: Cache metadata extraction results to avoid re-extraction
3. **Skip if Already Synced**: Check if synced videos already exist and skip if timestamps match

### Edge Cases to Handle

1. **Missing Timestamps**: Some videos may not have creation_time in metadata
   - Fallback: Use file modification time
   - Alternative: Manual time offset configuration

2. **Very Large Time Differences**: Videos recorded hours apart
   - Warn user about large differences
   - Allow manual override or skip synchronization

3. **Different Frame Rates**: Videos with different FPS
   - Note the difference in logs
   - Consider frame rate conversion (optional, adds complexity)

4. **Insufficient Overlap**: Videos don't overlap enough
   - Calculate overlap duration
   - Warn if below threshold
   - Allow user to proceed anyway

5. **Corrupted Metadata**: Some videos may have invalid metadata
   - Skip problematic videos
   - Continue with videos that have valid metadata
   - Report which videos were skipped

### Integration Points

1. **After Cell 2**: Insert sync cell here (after Drive mount, before config)
2. **Cell 3**: Update to reference synced videos in input directory
3. **Cell 4**: Video discovery should find synced videos
4. **Cell 9**: Camera mapping should use synced video paths

### User Experience

1. **Progress Indicators**: Show progress for each step (metadata extraction, trimming)
2. **Clear Messages**: Explain what's happening at each stage
3. **Error Messages**: Provide actionable error messages
4. **Summary Report**: Clear summary of what was synchronized and how

## Workflow Summary

```
1. Mount Drive (Cell 2)
   ↓
2. NEW: Video Synchronization Cell
   ├─ Discover videos in Videos/ directory
   ├─ Extract metadata from all videos
   ├─ Parse timestamps and calculate offsets
   ├─ Determine sync strategy
   ├─ Trim videos to align them
   └─ Save synced videos to input/ directory
   ↓
3. Project Configuration (Cell 3)
   ↓
4. Video Discovery (Cell 4) - finds synced videos
   ↓
5. Rest of pipeline (Cells 5-10)
```

## Benefits of This Approach

1. **Automated**: No manual video alignment needed
2. **Intelligent**: Uses actual recording timestamps for accuracy
3. **Flexible**: Handles videos with different start times and durations
4. **Integrated**: Uses your existing scripts (extract_metadata.py, trim_video.py)
5. **Robust**: Handles edge cases and provides clear error messages
6. **Efficient**: Fast lossless trimming preserves video quality

## Potential Challenges and Solutions

### Challenge 1: Timestamp Accuracy
**Issue**: Camera timestamps may not be perfectly synchronized
**Solution**: Use creation_time as primary, but allow small tolerance (e.g., ±1 second)

### Challenge 2: Large File Sizes
**Issue**: Trimming large videos can be slow
**Solution**: Use fast stream copy (lossless) instead of re-encoding

### Challenge 3: Multiple Video Formats
**Issue**: Different cameras may record in different formats
**Solution**: Your trim_video.py already handles this with format detection

### Challenge 4: Metadata Extraction Time
**Issue**: Extracting metadata from many large videos can be slow
**Solution**: 
- Cache metadata results
- Show progress indicators
- Consider parallel extraction if possible

## Next Steps

1. **Create the synchronization cell** with the steps outlined above
2. **Test with sample videos** to verify synchronization accuracy
3. **Add error handling** for edge cases
4. **Integrate with existing pipeline** by updating camera mappings
5. **Add logging** to track synchronization process
6. **Test end-to-end** to ensure synced videos work with camera switching

## Validation Checklist

After implementation, verify:
- [ ] Videos are discovered from Videos/ directory
- [ ] Metadata is extracted successfully
- [ ] Timestamps are parsed correctly
- [ ] Sync offsets are calculated accurately
- [ ] Videos are trimmed correctly
- [ ] Synced videos are saved to input/ directory
- [ ] Synced videos have matching durations
- [ ] Camera switching works with synced videos
- [ ] Error handling works for edge cases
- [ ] Logging provides useful information

## Conclusion

This implementation is not only possible but recommended for a robust multi-camera system. The approach leverages your existing tools and integrates cleanly into your pipeline. The key is careful timestamp parsing, intelligent offset calculation, and robust error handling.

The synchronization will ensure that when your camera switching system switches between cameras, the frames are temporally aligned, making the final output video smooth and coherent.
