# Football Highlights - Multi-Camera Video Switching System

Intelligent multi-camera football video switching system that automatically tracks the ball across synchronized camera feeds and generates highlight videos with optimal camera angles. Features YOLO-based ball detection, motion-consistent tracking, exit-zone switching logic, and fallback scanning for seamless camera transitions.

## 🎯 Features

### Core Capabilities
- **Multi-Camera Support**: Seamlessly switch between 2-3 synchronized camera feeds (Left, Right, Middle)
- **Intelligent Ball Tracking**: YOLO-based object detection with motion consistency and pitch-aware filtering
- **Automatic Camera Switching**: Exit-zone detection and trajectory-based switching logic
- **Sticky Tracking**: Maintains ball position during brief detection losses
- **Fallback Scanning**: Scans non-active cameras when ball is lost on the active camera
- **Highlight Generation**: Automatically generates highlight videos with optimal camera angles
- **Video Synchronization**: Handles synchronized multi-camera video streams

### Advanced Features
- **Motion Consistency**: Prevents ball "teleportation" by tracking motion patterns
- **Pitch-Aware Filtering**: Reduces false positives from crowd, scoreboard, and off-field areas
- **FPS-Scaled Thresholds**: Consistent behavior across different frame rates (25fps, 30fps, 60fps)
- **Exit Zone Detection**: Configurable exit zones for each camera (TOP, BOTTOM, LEFT, RIGHT)
- **Switch Cooldown**: Prevents rapid camera switching and flickering
- **Pre-Switch Validation**: Verifies camera readiness before switching
- **Comprehensive Logging**: Detailed debug logs and statistics for analysis

## 📋 Requirements

### System Requirements
- **Python**: 3.7 or higher
- **GPU**: NVIDIA GPU recommended (CUDA support) for faster processing
- **RAM**: 8GB minimum (16GB recommended)
- **Storage**: Sufficient space for input videos and output highlights

### Dependencies
- **PyTorch**: Deep learning framework (with CUDA support if GPU available)
- **OpenCV**: Video processing and computer vision
- **Ultralytics YOLO**: Object detection model
- **NumPy**: Numerical computations
- **Pillow**: Image processing

See `code/Scripts/requirements.txt` for additional dependencies.

## 🚀 Installation

### 1. Clone the Repository
```bash
git clone git@github-personal:abdullah-azi/football-highlights.git
cd football-highlights
```

### 2. Install Python Dependencies
```bash
pip install torch torchvision torchaudio
pip install opencv-python ultralytics numpy pillow
```

### 3. GPU Setup (Optional but Recommended)
If you have an NVIDIA GPU, install PyTorch with CUDA support:
```bash
# For CUDA 11.8
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# For CUDA 12.1
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### 4. Verify Installation
Run the system check in the main script to verify all dependencies are installed correctly.

## 📖 Usage

### Basic Usage

1. **Prepare Your Videos**
   - Place synchronized video files in the `videos/` directory
   - Ensure videos are synchronized (same start time and duration)
   - Supported formats: `.mp4`, `.mov`, `.avi`, `.mkv`

2. **Configure Camera Setup**
   - Edit camera configuration in `football_camera_switching.py`:
     ```python
     CAMERA_MAP = {
         0: "path/to/right_camera.mp4",
         1: "path/to/left_camera.mp4",
         2: "path/to/middle_camera.mp4"  # Optional
     }
     ```

3. **Run the Script**
   ```bash
   python code/football_camera_switching.py
   ```

4. **Output**
   - Highlight videos will be saved in the `output/` directory
   - Debug logs and statistics in `code/debug/` directory

### Configuration Options

#### Camera Switching Parameters
- `BALL_MISS_SEC_TO_SWITCH`: Seconds of consecutive misses before switching (default: 0.10s)
- `SWITCH_COOLDOWN_SEC`: Cooldown period after switching (default: 0.60s)
- `ZONE_ARM_SEC`: Consecutive seconds in exit zone to arm switch (default: 0.20s)
- `MIN_HOLD_SEC`: Minimum hold duration after switch (default: 0.0s)

#### Ball Detection Parameters
- `CONFIDENCE_THRESHOLD`: Minimum confidence for ball detection (default: 0.25)
- `MOTION_CONSISTENCY_MAX_JUMP_PX`: Maximum allowed jump distance (default: 150px)
- `PITCH_AWARE_ENABLED`: Enable pitch-aware filtering (default: True)

#### Camera Roles
```python
CAMERA_ROLES = {
    0: "RIGHT",   # Right camera
    1: "LEFT",    # Left camera
    2: "MIDDLE"   # Middle camera (optional)
}
```

## 📁 Project Structure

```
football-highlights/
├── code/
│   ├── football_camera_switching.py    # Main script
│   ├── football_camera_switching.ipynb # Jupyter notebook version
│   ├── Scripts/
│   │   ├── extract_metadata.py        # Video metadata extraction
│   │   ├── mov_to_mp4.py              # Video format conversion
│   │   ├── trim_video.py               # Video trimming utility
│   │   └── requirements.txt           # Additional dependencies
│   ├── debug/                          # Debug logs and statistics
│   └── *.md                            # Documentation files
├── videos/                             # Input video files
├── output/                             # Generated highlight videos
├── tests/                              # Test files
├── .gitignore                          # Git ignore rules
└── README.md                           # This file
```

## 🔧 Key Components

### 1. Ball Detection
- Uses YOLO model for real-time ball detection
- Motion consistency filtering to prevent false positives
- Pitch-aware filtering to exclude off-field detections

### 2. Camera Switching Logic
- State machine with FOUND/HELD/LOST states
- Exit zone detection for each camera
- Trajectory-based switching decisions
- Cooldown and hold mechanisms

### 3. Multi-Camera Orchestrator
- Synchronizes multiple camera streams
- Manages timeline alignment
- Performs fallback scanning
- Applies switch decisions

### 4. Highlight Generation
- Selects optimal camera angles
- Generates synchronized highlight videos
- Includes debug overlays (optional)

## 📚 Documentation

The project includes extensive documentation in the `code/` directory:

- `CAMERA_SETUP_ANALYSIS.md`: Camera configuration guide
- `MIDDLE_CAMERA_INTEGRATION.md`: Adding a third camera
- `camera_switching_improvements.md`: Switching logic details
- `ball_tracking_improvements.md`: Ball detection improvements
- `ORCHESTRATOR_IMPROVEMENTS.md`: Orchestrator architecture
- `improvements_implemented_summary.md`: List of implemented features

## 🐛 Troubleshooting

### Common Issues

1. **Ball not detected**
   - Check confidence threshold settings
   - Verify video quality and lighting
   - Enable debug mode to see detection overlays

2. **Camera switching too frequently**
   - Increase `SWITCH_COOLDOWN_SEC`
   - Adjust exit zone thresholds
   - Check for false positive detections

3. **Videos not synchronized**
   - Use the video synchronization tools in `Scripts/`
   - Ensure all videos have the same start time and duration

4. **GPU not detected**
   - Verify CUDA installation: `nvidia-smi`
   - Install PyTorch with CUDA support
   - Check GPU compatibility

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is open source and available for educational and research purposes.

## 🙏 Acknowledgments

- YOLO model by Ultralytics
- PyTorch team for the deep learning framework
- OpenCV community for computer vision tools

## 📧 Contact

For questions or issues, please open an issue on GitHub.

---

**Note**: This project was originally developed in Google Colab and has been adapted for local execution. Make sure to configure paths and dependencies according to your environment.
