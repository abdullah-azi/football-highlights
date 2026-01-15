# Exclusion Zone Format and Adjustment Guide

## Understanding the Zone Format

### Basic Format

```python
EXCLUSION_ZONES = {
    CAMERA_ID: [
        (x1, y1, x2, y2),  # Zone rectangle in normalized coordinates
    ],
}
```

### Coordinate System

**Normalized Coordinates:**
- Range: `0.0` to `1.0`
- `0.0` = left/top edge of frame
- `1.0` = right/bottom edge of frame
- `0.5` = center of frame

**Zone Rectangle:**
- `(x1, y1, x2, y2)` defines a rectangle
- `(x1, y1)` = **top-left corner**
- `(x2, y2)` = **bottom-right corner**
- `x1 < x2` and `y1 < y2` (always)

### Visual Example

For a 1920x1080 frame:

```
Frame Layout (Normalized):
┌─────────────────────────────────────┐
│ (0.0, 0.0)                    (1.0, 0.0) │
│                                         │
│                                         │
│                                         │
│                                         │
│                                         │
│ (0.0, 1.0)                    (1.0, 1.0) │
└─────────────────────────────────────┘

Example Zone: (0.05, 0.78, 0.15, 0.88)
┌─────────────────────────────────────┐
│                                     │
│                                     │
│                                     │
│                                     │
│  ┌─────┐                            │
│  │     │  ← Exclusion Zone          │
│  └─────┘                            │
│                                     │
└─────────────────────────────────────┘
```

### Converting Pixel → Normalized

**Formula:**
```python
x_norm = pixel_x / frame_width
y_norm = pixel_y / frame_height
```

**Example (1920x1080 frame):**
- Pixel `(200, 900)` → Normalized `(0.104, 0.833)`
- Pixel `(960, 540)` → Normalized `(0.500, 0.500)` (center)

---

## Creating an Exclusion Zone

### Step-by-Step Process

#### Step 1: Find False Positive Location

Use debug mode (see main guide) or check logs to find pixel coordinates.

**Example:** False positive detected at pixel `(200, 900)` in 1920x1080 frame.

#### Step 2: Convert to Normalized

```python
x_norm = 200 / 1920 = 0.104
y_norm = 900 / 1080 = 0.833
```

#### Step 3: Create Zone Around Detection

**Option A: Using Helper Function (Recommended)**

```python
from your_notebook import suggest_exclusion_zone

# Detection at pixel (200, 900) in 1920x1080 frame
zone = suggest_exclusion_zone(200, 900, 1920, 1080, margin=0.08)
# Returns: (0.024, 0.753, 0.184, 0.913)
```

**Option B: Manual Calculation**

```python
# Detection center
cx_norm = 0.104
cy_norm = 0.833

# Add margin (e.g., 0.08 = 8% of frame)
margin = 0.08

x1 = max(0.0, cx_norm - margin)  # 0.024
y1 = max(0.0, cy_norm - margin)  # 0.753
x2 = min(1.0, cx_norm + margin)  # 0.184
y2 = min(1.0, cy_norm + margin)  # 0.913

zone = (x1, y1, x2, y2)  # (0.024, 0.753, 0.184, 0.913)
```

#### Step 4: Add to EXCLUSION_ZONES

```python
EXCLUSION_ZONES = {
    1: [  # Left camera
        (0.024, 0.753, 0.184, 0.913),  # Zone around false positive
    ],
}
```

---

## Adjusting Zone Size

### Understanding Margins

**Margin** = distance from detection center to zone edge (normalized)

| Margin | Frame Coverage | Use Case |
|--------|---------------|----------|
| `0.05` | ~5% of frame | Small, precise false positives |
| `0.08` | ~8% of frame | **Default** - balanced |
| `0.10` | ~10% of frame | Medium-sized false positives |
| `0.15` | ~15% of frame | Large false positives or uncertain location |

### Common Scenarios

#### Scenario 1: Zone Too Small (False Positive Still Detected)

**Symptoms:**
- False positive still appears in detection
- Logs show detections near but outside zone

**Solution:**
```python
# Increase margin
zone = suggest_exclusion_zone(cx, cy, w, h, margin=0.12)  # Was 0.08
```

**Or manually expand:**
```python
# Original: (0.024, 0.753, 0.184, 0.913)
# Expanded: (0.020, 0.750, 0.190, 0.920)  # Slightly larger
EXCLUSION_ZONES = {
    1: [
        (0.020, 0.750, 0.190, 0.920),  # Expanded zone
    ],
}
```

#### Scenario 2: Zone Too Large (Real Ball Filtered)

**Symptoms:**
- Real ball detections are filtered
- Ball disappears when near false positive area

**Solution:**
```python
# Decrease margin
zone = suggest_exclusion_zone(cx, cy, w, h, margin=0.05)  # Was 0.08
```

**Or manually shrink:**
```python
# Original: (0.024, 0.753, 0.184, 0.913)
# Shrunk: (0.030, 0.760, 0.178, 0.906)  # Slightly smaller
EXCLUSION_ZONES = {
    1: [
        (0.030, 0.760, 0.178, 0.906),  # Shrunk zone
    ],
}
```

#### Scenario 3: Multiple False Positives in Same Camera

**Solution:** Add multiple zones

```python
EXCLUSION_ZONES = {
    1: [  # Left camera
        (0.024, 0.753, 0.184, 0.913),  # Bottom-left false positive
        (0.000, 0.000, 0.100, 0.200),  # Top-left false positive
        (0.850, 0.800, 1.000, 1.000),  # Bottom-right false positive
    ],
}
```

---

## Zone Size Reference

### Pixel Sizes (1920x1080 frame)

| Normalized Size | Pixel Size | Frame Coverage | Typical Use |
|----------------|------------|----------------|-------------|
| `0.05 x 0.05` | 96x54 px | 0.25% | Very small objects |
| `0.08 x 0.08` | 154x86 px | 0.64% | Small objects (default) |
| `0.10 x 0.10` | 192x108 px | 1.00% | Medium objects |
| `0.15 x 0.15` | 288x162 px | 2.25% | Large objects |
| `0.20 x 0.20` | 384x216 px | 4.00% | Very large objects |

### Common Zone Patterns

#### Bottom-Left Corner (Ground Object)
```python
(0.00, 0.80, 0.15, 1.00)  # Covers bottom-left 15% x 20%
```

#### Bottom-Right Corner
```python
(0.85, 0.80, 1.00, 1.00)  # Covers bottom-right 15% x 20%
```

#### Top-Left Corner
```python
(0.00, 0.00, 0.15, 0.20)  # Covers top-left 15% x 20%
```

#### Center Area (Avoid - too risky)
```python
# NOT RECOMMENDED - filters too much of the field
(0.40, 0.40, 0.60, 0.60)  # Center 20% x 20%
```

#### Edge Strip (Horizontal)
```python
(0.00, 0.90, 1.00, 1.00)  # Bottom 10% across entire width
```

#### Edge Strip (Vertical)
```python
(0.00, 0.00, 0.10, 1.00)  # Left 10% across entire height
```

---

## Testing and Validation

### Step 1: Visualize Zone

Use the helper function to see zone details:

```python
from your_notebook import visualize_exclusion_zone

zone = (0.024, 0.753, 0.184, 0.913)
visualize_exclusion_zone(1, zone, frame_width=1920, frame_height=1080)
```

**Output:**
```
📐 Exclusion Zone Visualization - Camera 1:
   Normalized: (0.024, 0.753) to (0.184, 0.913)
   Pixel coords: (46, 813) to (353, 986)
   Size: 307x173 pixels (0.5% of frame)
   Center: (200, 900)
```

### Step 2: Test Zone

1. Add zone to `EXCLUSION_ZONES`
2. Run Cell 8 to initialize
3. Run Cell 9 (orchestrator)
4. Check logs for: `"Exclusion zone filter: cam=X, pos=(cx,cy), holding last"`
5. Verify false positive is filtered

### Step 3: Adjust if Needed

**If false positive still detected:**
- Increase zone size (larger margin)
- Check if coordinates are correct

**If real ball filtered:**
- Decrease zone size (smaller margin)
- Verify zone doesn't overlap with ball path

---

## Quick Reference

### Creating a Zone

```python
# Method 1: Using helper (recommended)
zone = suggest_exclusion_zone(cx_px, cy_px, width, height, margin=0.08)

# Method 2: Manual
x_norm = cx_px / width
y_norm = cy_px / height
zone = (
    max(0.0, x_norm - 0.08),  # x1
    max(0.0, y_norm - 0.08),  # y1
    min(1.0, x_norm + 0.08),  # x2
    min(1.0, y_norm + 0.08),  # y2
)
```

### Adjusting Zone Size

```python
# Smaller zone (more precise)
zone = suggest_exclusion_zone(cx, cy, w, h, margin=0.05)

# Larger zone (more coverage)
zone = suggest_exclusion_zone(cx, cy, w, h, margin=0.12)
```

### Visualizing Zone

```python
visualize_exclusion_zone(camera_id, zone, frame_width, frame_height)
```

---

## Examples

### Example 1: Ground Object Near Left Camera

**Detection:** Pixel `(150, 950)` in 1920x1080 frame

**Step 1: Convert**
```python
x_norm = 150 / 1920 = 0.078
y_norm = 950 / 1080 = 0.880
```

**Step 2: Create Zone**
```python
zone = suggest_exclusion_zone(150, 950, 1920, 1080, margin=0.10)
# Returns: (0.000, 0.780, 0.178, 1.000)
```

**Step 3: Add to Config**
```python
EXCLUSION_ZONES = {
    1: [  # Left camera
        (0.000, 0.780, 0.178, 1.000),  # Bottom-left area
    ],
}
```

### Example 2: Small Static Marker

**Detection:** Pixel `(960, 100)` in 1920x1080 frame (top center)

**Zone:**
```python
zone = suggest_exclusion_zone(960, 100, 1920, 1080, margin=0.05)
# Returns: (0.450, 0.043, 0.550, 0.143)
```

**Config:**
```python
EXCLUSION_ZONES = {
    0: [  # Right camera (or whichever camera)
        (0.450, 0.043, 0.550, 0.143),  # Top center marker
    ],
}
```

### Example 3: Multiple False Positives

**Left Camera has 2 false positives:**
1. Bottom-left: `(100, 900)`
2. Top-left: `(50, 50)`

**Config:**
```python
EXCLUSION_ZONES = {
    1: [  # Left camera
        suggest_exclusion_zone(100, 900, 1920, 1080, margin=0.08),  # Bottom-left
        suggest_exclusion_zone(50, 50, 1920, 1080, margin=0.05),   # Top-left
    ],
}
```

---

## Tips

1. **Start with default margin (0.08)** - works for most cases
2. **Test incrementally** - adjust margin by 0.02-0.03 at a time
3. **Use visualization** - `visualize_exclusion_zone()` shows exact coverage
4. **Check logs** - verify zone is being applied (`"Exclusion zone filter"`)
5. **Avoid center zones** - don't filter center of frame (where ball plays)
6. **Edge zones are safer** - corners and edges are less likely to filter real balls

---

## Troubleshooting

### Zone Not Working

**Check:**
- Camera ID matches `CAMERA_NAMES` in Cell 9
- Coordinates are normalized (0.0-1.0)
- `ENABLE_EXCLUSION_ZONES = True`
- Zone actually covers false positive location

**Debug:**
```python
# Visualize zone to verify
visualize_exclusion_zone(camera_id, zone, frame_width, frame_height)

# Check if detection is in zone
from your_notebook import _is_in_exclusion_zone
is_in_zone = _is_in_exclusion_zone(camera_id, x_norm, y_norm, width, height)
```

### Zone Too Aggressive

**Symptoms:** Real ball filtered

**Solution:**
- Reduce margin (0.08 → 0.05)
- Shrink zone manually
- Check if zone overlaps with ball path

### Zone Not Aggressive Enough

**Symptoms:** False positive still detected

**Solution:**
- Increase margin (0.08 → 0.12)
- Expand zone manually
- Verify zone covers false positive location
