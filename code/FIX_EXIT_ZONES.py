"""
Manual Fix Script for Exit Zones Configuration
===============================================

This script shows the exact code changes needed in Cell 6 of the notebook.
Copy and paste these changes directly into Cell 6.

FIX 1: Replace EXIT_ZONES dictionary
"""

EXIT_ZONES_FIX = """
EXIT_ZONES: Dict[int, Dict[str, Tuple[float, float, float, float]]] = {
    # Camera 0 (LEFT_CAM): ball exiting right side means switch to camera 1
    0: {
        "RIGHT":       (0.85, 0.00, 1.00, 1.00),      # Right edge
        "RIGHT_TOP":   (0.78, 0.00, 1.00, 0.30),      # Right-top corner
        "RIGHT_BOTTOM":(0.80, 0.70, 1.00, 1.00),      # Right-bottom corner
        "BOTTOM":      (0.00, 0.85, 1.00, 1.00),      # Bottom edge
        "TOP":         (0.00, 0.00, 1.00, 0.15),      # Top edge
    },
    # Camera 1 (RIGHT_CAM): ball exiting left side means switch to camera 0
    1: {
        "LEFT":        (0.00, 0.00, 0.15, 1.00),      # Left edge
        "LEFT_TOP":    (0.00, 0.00, 0.22, 0.30),      # Left-top corner
        "LEFT_BOTTOM": (0.00, 0.70, 0.22, 1.00),      # Left-bottom corner
        "BOTTOM":      (0.00, 0.85, 1.00, 1.00),      # Bottom edge
        "TOP":         (0.00, 0.00, 1.00, 0.15),      # Top edge
    },
}
"""

NEXT_CAMERA_BY_ZONE_FIX = """
NEXT_CAMERA_BY_ZONE: Dict[int, Dict[str, int]] = {
    # Camera 0: ball exiting right/bottom/top -> switch to camera 1
    0: {
        "RIGHT": 1,
        "RIGHT_TOP": 1,
        "RIGHT_BOTTOM": 1,
        "BOTTOM": 1,
        "TOP": 1,
    },
    # Camera 1: ball exiting left/bottom/top -> switch to camera 0
    1: {
        "LEFT": 0,
        "LEFT_TOP": 0,
        "LEFT_BOTTOM": 0,
        "BOTTOM": 0,
        "TOP": 0,
    }
}
"""

START_CAMERA_FIX = """
# Set your starting camera here - default to camera 1 (RIGHT_CAM) as fallback
START_CAMERA = 1  # Changed to camera 1 (RIGHT_CAM) as default fallback
if START_CAMERA not in EXIT_ZONES:
    # Fallback to first available camera with zones, or camera 1 if available
    if 1 in EXIT_ZONES:
        START_CAMERA = 1
    elif 0 in EXIT_ZONES:
        START_CAMERA = 0
    else:
        START_CAMERA = list(EXIT_ZONES.keys())[0] if EXIT_ZONES else 1
camera_switcher.reset_switch_state(active_cam=START_CAMERA)
"""

if __name__ == "__main__":
    print("=" * 70)
    print("EXIT ZONES CONFIGURATION FIXES")
    print("=" * 70)
    print("\n1. EXIT_ZONES Dictionary:")
    print(EXIT_ZONES_FIX)
    print("\n2. NEXT_CAMERA_BY_ZONE Dictionary:")
    print(NEXT_CAMERA_BY_ZONE_FIX)
    print("\n3. START_CAMERA Configuration:")
    print(START_CAMERA_FIX)
    print("\n" + "=" * 70)
    print("Copy these fixes into Cell 6 of your notebook")
    print("=" * 70)
