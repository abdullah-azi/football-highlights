# Video Trimming Enhancements - Stricter Checks and Metadata Saving

## Overview
This document provides exact code changes to:
1. Add stricter trimming validation
2. Save metadata BEFORE trimming to debug directory
3. Save metadata AFTER trimming to debug directory
4. Display durations in HR:MIN:SEC format in terminal

## Changes Required

### 1. Add Duration Formatting Helper Function

**Location**: After `format_time_for_ffmpeg` function (around line 2028)

**Add this function:**
```python
    def format_duration_display(seconds: float) -> str:
        """Format seconds to HR:MIN:SEC format for display (e.g., 1:23:45 or 0:05:30)."""
        if seconds is None or seconds < 0:
            return "N/A"
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours}:{minutes:02d}:{secs:02d}"
```

### 2. Enhance trim_video_sync with Stricter Validation

**Location**: Inside `trim_video_sync` function, after input validation (around line 2048)

**Add stricter validation after:**
```python
            # Validate input
            if not input_file.exists():
                raise FileNotFoundError(f"Input video not found: {input_file}")
```

**Add:**
```python
            # Stricter validation: Get video duration and validate trim parameters
            try:
                # Get video metadata to validate trim parameters
                ffprobe_data = run_ffprobe(str(input_file))
                video_duration = None
                if 'format' in ffprobe_data and 'duration' in ffprobe_data['format']:
                    video_duration = float(ffprobe_data['format']['duration'])
                
                if video_duration is not None:
                    # Validate start_trim_seconds
                    if start_trim_seconds < 0:
                        raise ValueError(f"Start trim cannot be negative: {start_trim_seconds}")
                    if start_trim_seconds >= video_duration:
                        raise ValueError(
                            f"Start trim ({start_trim_seconds:.2f}s) must be less than video duration "
                            f"({video_duration:.2f}s)"
                        )
                    
                    # Validate duration_seconds
                    if duration_seconds <= 0:
                        raise ValueError(f"Duration must be positive: {duration_seconds}")
                    if duration_seconds > video_duration:
                        raise ValueError(
                            f"Duration ({duration_seconds:.2f}s) cannot exceed video duration "
                            f"({video_duration:.2f}s)"
                        )
                    
                    # Validate that start_trim + duration doesn't exceed video duration
                    end_time = start_trim_seconds + duration_seconds
                    if end_time > video_duration:
                        raise ValueError(
                            f"Trim range exceeds video: start ({start_trim_seconds:.2f}s) + duration "
                            f"({duration_seconds:.2f}s) = {end_time:.2f}s > video duration "
                            f"({video_duration:.2f}s)"
                        )
                    
                    # Additional strict check: ensure minimum duration
                    if duration_seconds < 1.0:
                        raise ValueError(f"Duration too short: {duration_seconds:.2f}s (minimum: 1.0s)")
            except Exception as e:
                if "FFmpeg" not in str(e) and "ffprobe" not in str(e).lower():
                    # Re-raise validation errors
                    raise
                # If ffprobe fails, log warning but continue (less strict)
                if ENABLE_ORCHESTRATOR_LOGGING:
                    _orch_log(f"Warning: Could not validate trim parameters (ffprobe failed): {e}", "WARNING")
```

### 3. Save Metadata BEFORE Trimming

**Location**: In the trimming loop, before calling `trim_video_sync` (around line 2230)

**Add before:**
```python
        # Perform trimming
        try:
            print(f"      🔄 Trimming...")
            start_time = datetime.now()
```

**Add:**
```python
        # -------- Save Metadata BEFORE Trimming --------
        try:
            print(f"      💾 Saving metadata BEFORE trimming...")
            before_metadata = extract_video_metadata_sync(input_video)
            
            # Save to debug directory
            DEBUG_DIR_SYNC.mkdir(parents=True, exist_ok=True)
            before_metadata_file = DEBUG_DIR_SYNC / f"{input_video.stem}_before_trim_metadata.json"
            
            # Serialize metadata (convert datetime to ISO string)
            before_metadata_serialized = {
                'path': before_metadata.get('path'),
                'name': before_metadata.get('name'),
                'creation_time': before_metadata.get('creation_time'),
                'creation_time_dt': before_metadata.get('creation_time_dt').isoformat() if before_metadata.get('creation_time_dt') else None,
                'duration': before_metadata.get('duration'),
                'fps': before_metadata.get('fps'),
                'file_size_bytes': input_video.stat().st_size if input_video.exists() else None,
                'file_size_mb': (input_video.stat().st_size / (1024 * 1024)) if input_video.exists() else None,
                'trim_parameters': {
                    'start_trim_seconds': start_trim,
                    'end_trim_seconds': end_trim,
                    'final_duration_seconds': final_duration
                },
                'timestamp': datetime.now().isoformat()
            }
            
            with open(before_metadata_file, 'w', encoding='utf-8') as f:
                json.dump(before_metadata_serialized, f, indent=2, ensure_ascii=False)
            
            print(f"         ✅ Saved: {before_metadata_file.name}")
            
        except Exception as e:
            print(f"         ⚠️  Warning: Could not save before-trim metadata: {e}")
        
        # -------- Stricter Pre-Trimming Validation --------
        # Validate trim parameters against actual video
        try:
            # Get video metadata for validation
            video_metadata = next((m for m in VIDEO_METADATA if m['name'] == video_name), None)
            
            if video_metadata and video_metadata.get('duration'):
                original_duration = video_metadata['duration']
                
                # Strict validation checks
                validation_errors = []
                
                # Check 1: Start trim must be non-negative
                if start_trim < 0:
                    validation_errors.append(f"Start trim is negative: {start_trim:.2f}s")
                
                # Check 2: Start trim must be less than video duration
                if start_trim >= original_duration:
                    validation_errors.append(
                        f"Start trim ({start_trim:.2f}s) >= video duration ({original_duration:.2f}s)"
                    )
                
                # Check 3: Final duration must be positive
                if final_duration <= 0:
                    validation_errors.append(f"Final duration is not positive: {final_duration:.2f}s")
                
                # Check 4: Final duration must be <= original duration
                if final_duration > original_duration:
                    validation_errors.append(
                        f"Final duration ({final_duration:.2f}s) > original duration ({original_duration:.2f}s)"
                    )
                
                # Check 5: Start trim + final duration must not exceed original duration
                calculated_end = start_trim + final_duration
                if calculated_end > original_duration:
                    validation_errors.append(
                        f"Trim range exceeds video: {start_trim:.2f}s + {final_duration:.2f}s = "
                        f"{calculated_end:.2f}s > {original_duration:.2f}s"
                    )
                
                # Check 6: Minimum duration requirement
                if final_duration < MIN_SYNC_DURATION_SECONDS:
                    validation_errors.append(
                        f"Final duration ({final_duration:.2f}s) < minimum required "
                        f"({MIN_SYNC_DURATION_SECONDS}s)"
                    )
                
                # Check 7: End trim validation (start + duration + end should equal original)
                expected_total = start_trim + final_duration + end_trim
                total_diff = abs(expected_total - original_duration)
                if total_diff > 0.1:  # Allow 0.1s tolerance for floating point
                    validation_errors.append(
                        f"Trim calculation mismatch: start ({start_trim:.2f}s) + duration "
                        f"({final_duration:.2f}s) + end ({end_trim:.2f}s) = {expected_total:.2f}s, "
                        f"expected {original_duration:.2f}s (diff: {total_diff:.2f}s)"
                    )
                
                if validation_errors:
                    error_msg = "Strict validation failed:\\n" + "\\n".join(f"   - {e}" for e in validation_errors)
                    print(f"      ❌ {error_msg}")
                    raise ValueError(error_msg)
                else:
                    print(f"      ✅ Strict validation passed")
                    
        except ValueError as e:
            # Re-raise validation errors
            raise
        except Exception as e:
            print(f"      ⚠️  Warning: Pre-trimming validation check failed: {e}")
            # Continue anyway (less strict mode)
        
        # Perform trimming
        try:
            print(f"      🔄 Trimming...")
            start_time = datetime.now()
```

### 4. Save Metadata AFTER Trimming

**Location**: After successful trimming, when output file exists (around line 2250)

**Add after:**
```python
                # Get output file size
                if output_path.exists():
                    output_size = output_path.stat().st_size
                    output_size_mb = output_size / (1024 * 1024)
                    print(f"      ✅ Success! ({elapsed:.1f}s)")
                    print(f"         Output: {output_name}")
                    print(f"         Size: {output_size_mb:.2f} MB")
```

**Add:**
```python
                    # -------- Save Metadata AFTER Trimming --------
                    try:
                        print(f"      💾 Saving metadata AFTER trimming...")
                        after_metadata = extract_video_metadata_sync(output_path)
                        
                        # Save to debug directory
                        after_metadata_file = DEBUG_DIR_SYNC / f"{input_video.stem}_after_trim_metadata.json"
                        
                        # Serialize metadata
                        after_metadata_serialized = {
                            'path': after_metadata.get('path'),
                            'name': after_metadata.get('name'),
                            'creation_time': after_metadata.get('creation_time'),
                            'creation_time_dt': after_metadata.get('creation_time_dt').isoformat() if after_metadata.get('creation_time_dt') else None,
                            'duration': after_metadata.get('duration'),
                            'fps': after_metadata.get('fps'),
                            'file_size_bytes': output_size,
                            'file_size_mb': output_size_mb,
                            'trim_parameters': {
                                'start_trim_seconds': start_trim,
                                'end_trim_seconds': end_trim,
                                'final_duration_seconds': final_duration,
                                'expected_duration': final_duration
                            },
                            'processing_info': {
                                'processing_time_seconds': elapsed,
                                'trim_mode': 'lossless' if USE_LOSSLESS_TRIMMING else 're-encode'
                            },
                            'timestamp': datetime.now().isoformat()
                        }
                        
                        with open(after_metadata_file, 'w', encoding='utf-8') as f:
                            json.dump(after_metadata_serialized, f, indent=2, ensure_ascii=False)
                        
                        print(f"         ✅ Saved: {after_metadata_file.name}")
                        
                        # Verify duration matches expected
                        if after_metadata.get('duration'):
                            actual_duration = after_metadata['duration']
                            duration_diff = abs(actual_duration - final_duration)
                            if duration_diff > 0.5:  # More than 0.5s difference
                                print(f"         ⚠️  Duration mismatch: expected {format_duration_display(final_duration)}, "
                                      f"got {format_duration_display(actual_duration)} (diff: {duration_diff:.2f}s)")
                            else:
                                print(f"         ✅ Duration verified: {format_duration_display(actual_duration)}")
                        
                    except Exception as e:
                        print(f"         ⚠️  Warning: Could not save after-trim metadata: {e}")
```

### 5. Update All Duration Displays to HR:MIN:SEC Format

**Find and replace all duration display statements:**

**Replace:**
```python
print(f"      Final duration: {final_duration:.2f}s")
```

**With:**
```python
print(f"      Final duration: {format_duration_display(final_duration)} ({final_duration:.2f}s)")
```

**Replace:**
```python
print(f"      Start trim: {start_trim:.2f}s")
print(f"      End trim: {end_trim:.2f}s")
```

**With:**
```python
print(f"      Start trim: {format_duration_display(start_trim)} ({start_trim:.2f}s)")
print(f"      End trim: {format_duration_display(end_trim)} ({end_trim:.2f}s)")
```

**Also update in metadata extraction section:**
- Find: `duration_str = f"{metadata['duration']:.1f}s"`
- Replace with: `duration_str = f"{format_duration_display(metadata['duration'])} ({metadata['duration']:.1f}s)"`

**Update in synchronization strategy display:**
- Find: `print(f"   Common duration: {common_duration:.2f} seconds")`
- Replace with: `print(f"   Common duration: {format_duration_display(common_duration)} ({common_duration:.2f} seconds)")`

**Update in verification section:**
- Find: `print(f"      ✅ Duration matches: {actual_duration:.2f}s")`
- Replace with: `print(f"      ✅ Duration matches: {format_duration_display(actual_duration)} ({actual_duration:.2f}s)")`

## Summary of Changes

1. ✅ Added `format_duration_display()` helper function
2. ✅ Enhanced `trim_video_sync()` with stricter validation
3. ✅ Save metadata BEFORE trimming to debug directory
4. ✅ Save metadata AFTER trimming to debug directory
5. ✅ Updated all duration displays to HR:MIN:SEC format

## File Locations

- Before-trim metadata: `debug/{video_name}_before_trim_metadata.json`
- After-trim metadata: `debug/{video_name}_after_trim_metadata.json`

## Validation Checks Added

1. Start trim must be non-negative
2. Start trim must be < video duration
3. Final duration must be positive
4. Final duration must be <= original duration
5. Start trim + final duration must not exceed video duration
6. Final duration must meet minimum requirement
7. Trim calculation consistency check
