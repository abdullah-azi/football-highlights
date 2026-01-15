# Middle Camera Integration Guide

## Overview

This guide explains how to integrate a third camera (middle camera) into the existing two-camera switching system without breaking current functionality. The system currently uses:
- **Camera 0**: Right camera (IMG_0687_synced.mp4)
- **Camera 1**: Left camera (IMG_2768_synced.mp4)
- **Camera 2**: Middle camera (IMG_5043_synced.mp4) - **NEW**

## Current System Architecture

### Existing Camera Configuration
- Two-camera setup with LEFT and RIGHT cameras
- Exit zones defined for each camera (TOP, BOTTOM, LEFT, RIGHT)
- Switching logic based on ball position and exit probability
- Camera cooldown period to prevent rapid switching

### Current Switching Logic
- Switches occur when ball exits the active camera's field of view
- Exit zones determine which camera to switch to
- Sticky tracking maintains ball position during brief detection losses

## Integration Strategy

### Phase 1: Camera Mapping Update

**Step 1: Update Camera Map**
- Add Camera 2 to the `CAMERA_MAP` dictionary
- Assign the middle camera video file (IMG_5043_synced.mp4)
- Update `CAMERA_NAMES` to include "MIDDLE_CAM" or "CENTER_CAM"

**Step 2: Verify Video Synchronization**
- Ensure all three videos are synchronized (same start time and duration)
- Verify frame rates are compatible
- Check that video durations match exactly

**Step 3: Update Input Videos List**
- Add the middle camera video to `INPUT_VIDEOS` list
- Maintain consistent ordering (0: Right, 1: Left, 2: Middle)

### Phase 2: Exit Zones Configuration

**Understanding Exit Zones for Three Cameras**

The middle camera changes the exit zone logic:

**For Right Camera (Camera 0):**
- **TOP exit**: Ball moving up → Switch to Middle Camera (Camera 2)
- **BOTTOM exit**: Ball moving down → Switch to Middle Camera (Camera 2)
- **LEFT exit**: Ball moving left → Switch to Left Camera (Camera 1)
- **RIGHT exit**: Ball moving right → Out of view (switch to Middle or Left based on context)

**For Left Camera (Camera 1):**
- **TOP exit**: Ball moving up → Switch to Middle Camera (Camera 2)
- **BOTTOM exit**: Ball moving down → Switch to Middle Camera (Camera 2)
- **LEFT exit**: Ball moving left → Out of view (switch to Middle or Right based on context)
- **RIGHT exit**: Ball moving right → Switch to Right Camera (Camera 0)

**For Middle Camera (Camera 2) - NEW:**
- **TOP exit**: Ball moving up → Out of view (switch to Left or Right based on ball position)
- **BOTTOM exit**: Ball moving down → Out of view (switch to Left or Right based on ball position)
- **LEFT exit**: Ball moving left → Switch to Left Camera (Camera 1)
- **RIGHT exit**: Ball moving right → Switch to Right Camera (Camera 0)

**Implementation Approach:**
- Update `EXIT_ZONES` configuration for each camera
- Add `NEXT_CAMERA_BY_ZONE` mappings for the middle camera
- Consider ball position (X coordinate) when deciding between Left/Right from Middle camera

### Phase 3: Switching Logic Updates

**Priority-Based Switching**

When the ball exits the middle camera's TOP or BOTTOM zones, use ball position to determine next camera:

**Decision Logic:**
- If ball X position < 0.5 (left half of frame) → Switch to Left Camera
- If ball X position >= 0.5 (right half of frame) → Switch to Right Camera
- This ensures smooth transitions based on ball trajectory

**Cooldown Management**
- Maintain existing cooldown period (15 frames)
- Apply cooldown consistently across all three cameras
- Prevent rapid switching between all cameras

**Fallback Strategy**
- If middle camera loses ball, check which side cameras can see it
- Prefer switching to camera with better ball visibility
- Maintain current "sticky tracking" behavior during transitions

### Phase 4: Testing and Validation

**Backward Compatibility Testing**

**Test 1: Two-Camera Mode**
- Temporarily disable middle camera
- Verify existing two-camera switching still works
- Ensure no regressions in current functionality

**Test 2: Three-Camera Mode**
- Enable all three cameras
- Test switching from Right → Middle → Left
- Test switching from Left → Middle → Right
- Verify smooth transitions

**Test 3: Edge Cases**
- Ball exits top/bottom of middle camera
- Ball moves quickly between all three cameras
- Ball detection loss during multi-camera transitions
- Cooldown period enforcement across all cameras

**Test 4: Performance**
- Monitor frame processing time with three cameras
- Check memory usage with additional video streams
- Verify no significant performance degradation

### Phase 5: Configuration Updates

**Exit Zones Configuration**

Update the exit zones for each camera to include middle camera transitions:

**Right Camera (Camera 0):**
- TOP zone → Next camera: Middle (Camera 2)
- BOTTOM zone → Next camera: Middle (Camera 2)
- LEFT zone → Next camera: Left (Camera 1)
- RIGHT zone → Next camera: Middle or Left (based on context)

**Left Camera (Camera 1):**
- TOP zone → Next camera: Middle (Camera 2)
- BOTTOM zone → Next camera: Middle (Camera 2)
- LEFT zone → Next camera: Middle or Right (based on context)
- RIGHT zone → Next camera: Right (Camera 0)

**Middle Camera (Camera 2):**
- TOP zone → Next camera: Left or Right (based on X position)
- BOTTOM zone → Next camera: Left or Right (based on X position)
- LEFT zone → Next camera: Left (Camera 1)
- RIGHT zone → Next camera: Right (Camera 0)

**Zone Thresholds**

Consider adjusting zone thresholds for the middle camera:
- Middle camera may have different field of view coverage
- May need different exit zone boundaries
- Test and calibrate based on actual camera positions

### Phase 6: Gradual Rollout

**Step 1: Add Camera Without Active Switching**
- Add middle camera to map but don't enable switching to it
- Monitor system behavior
- Verify no errors or crashes

**Step 2: Enable One-Way Switching**
- Allow switching TO middle camera from side cameras
- Don't allow switching FROM middle camera yet
- Test transitions: Right → Middle, Left → Middle

**Step 3: Enable Full Three-Way Switching**
- Enable all switching directions
- Test complete camera switching cycle
- Monitor for any issues

**Step 4: Fine-Tuning**
- Adjust exit zone boundaries if needed
- Tune switching sensitivity
- Optimize cooldown periods

## Key Considerations

### Maintaining Backward Compatibility

**Configuration Flags**
- Add a flag to enable/disable middle camera
- Allow fallback to two-camera mode if issues arise
- Keep existing two-camera logic intact

**Code Structure**
- Keep existing switching logic modular
- Add middle camera logic as extensions, not replacements
- Use conditional checks to support both modes

### Performance Impact

**Resource Usage**
- Three video streams require more memory
- Frame processing time may increase
- Consider optimizing video loading (lazy loading for inactive cameras)

**Optimization Strategies**
- Only decode frames from active camera when possible
- Cache recent frames from side cameras for quick switching
- Use efficient video access patterns

### Edge Cases to Handle

**Ball Position Ambiguity**
- When ball exits middle camera top/bottom, use X position to decide
- Consider ball velocity/direction for better predictions
- Fallback to closest camera if position unclear

**Rapid Multi-Camera Switching**
- Enforce cooldown periods strictly
- Prevent switching loops (Right → Middle → Right quickly)
- Add state tracking to detect switching patterns

**Camera Availability**
- Handle cases where middle camera video is unavailable
- Gracefully fall back to two-camera mode
- Log warnings but don't crash

## Validation Checklist

Before deploying three-camera system:

- [ ] All three videos synchronized and verified
- [ ] Camera mapping updated correctly
- [ ] Exit zones configured for all three cameras
- [ ] Switching logic handles all transition paths
- [ ] Cooldown periods work correctly
- [ ] Two-camera mode still works (backward compatibility)
- [ ] Performance acceptable with three cameras
- [ ] Edge cases handled gracefully
- [ ] Logging and debugging enabled
- [ ] Test videos processed successfully

## Rollback Plan

If issues arise:

1. **Immediate Rollback**: Disable middle camera flag
2. **Partial Rollback**: Disable switching FROM middle camera only
3. **Full Rollback**: Revert to previous two-camera configuration
4. **Investigation**: Review logs and identify root cause
5. **Fix and Retry**: Address issues and re-enable gradually

## Expected Benefits

**Improved Coverage**
- Better coverage of field with three camera angles
- Reduced blind spots between side cameras
- Smoother transitions during ball movement

**Enhanced Viewing Experience**
- More dynamic camera angles
- Better tracking of ball across field
- More professional-looking output

**Future Extensibility**
- Framework supports additional cameras if needed
- Modular design allows easy expansion
- Configuration-driven approach simplifies changes

## Next Steps

1. Review this guide and understand the integration approach
2. Update camera mapping configuration
3. Configure exit zones for middle camera
4. Test in isolated environment first
5. Gradually enable features
6. Monitor and fine-tune based on results
7. Document any customizations or adjustments made

## Notes

- Keep existing two-camera logic intact for backward compatibility
- Test thoroughly before full deployment
- Monitor performance and adjust as needed
- Document any deviations from this guide
- Consider camera positioning and field of view when configuring zones
