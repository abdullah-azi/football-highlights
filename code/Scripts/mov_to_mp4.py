#!/usr/bin/env python3
"""
MOV to MP4 Converter for Windows

Intelligently converts .MOV files to .MP4 using FFmpeg:
- Fast remux (no re-encoding) when codecs are compatible
- Safe re-encoding fallback when needed
- Skips data/metadata streams, only copies video + audio

Requirements:
    - FFmpeg and ffprobe installed and available in PATH
"""

import json
import subprocess
import sys
import argparse
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List


def find_ffmpeg_tool(tool_name: str, custom_path: Optional[str] = None) -> str:
    """
    Find FFmpeg tool (ffmpeg or ffprobe) executable path.
    
    Args:
        tool_name: Name of the tool ('ffmpeg' or 'ffprobe')
        custom_path: Optional custom path to the tool
        
    Returns:
        Path to the executable
        
    Raises:
        FileNotFoundError: If tool cannot be found
    """
    if custom_path:
        custom_path_obj = Path(custom_path)
        if custom_path_obj.exists() and custom_path_obj.is_file():
            return str(custom_path_obj.resolve())
        raise FileNotFoundError(f"{tool_name} not found at specified path: {custom_path}")
    
    # Try to find in PATH
    tool_exe = shutil.which(tool_name)
    if tool_exe:
        return tool_exe
    
    # Search common Windows installation locations
    if sys.platform == 'win32':
        common_paths = [
            Path(f'C:/ffmpeg/bin/{tool_name}.exe'),
            Path(f'C:/Program Files/ffmpeg/bin/{tool_name}.exe'),
            Path(f'C:/Program Files (x86)/ffmpeg/bin/{tool_name}.exe'),
            Path.home() / f'ffmpeg/bin/{tool_name}.exe',
            Path(f'C:/tools/ffmpeg/bin/{tool_name}.exe'),
        ]
        
        for path in common_paths:
            if path.exists() and path.is_file():
                return str(path.resolve())
    
    raise FileNotFoundError(
        f"{tool_name} not found. Please ensure FFmpeg is installed and available in PATH.\n"
        f"Download FFmpeg from: https://ffmpeg.org/download.html"
    )


def probe_video(video_path: str, ffprobe_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Probe video file using ffprobe to extract metadata.
    
    Args:
        video_path: Path to the video file
        ffprobe_path: Optional custom path to ffprobe
        
    Returns:
        Dictionary containing ffprobe output
        
    Raises:
        FileNotFoundError: If ffprobe not found
        RuntimeError: If ffprobe execution fails
    """
    ffprobe_exe = find_ffmpeg_tool('ffprobe', ffprobe_path)
    video_path = str(Path(video_path).resolve())
    
    cmd = [
        ffprobe_exe,
        '-v', 'quiet',
        '-print_format', 'json',
        '-show_format',
        '-show_streams',
        video_path
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        return json.loads(result.stdout)
    except FileNotFoundError:
        raise
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"ffprobe execution failed: {e.stderr}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse ffprobe JSON output: {e}")


def analyze_streams(probe_data: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Analyze video streams to find video, audio, and other streams.
    
    Args:
        probe_data: Output from ffprobe
        
    Returns:
        Tuple of (video_stream, audio_stream, other_streams)
    """
    video_stream = None
    audio_stream = None
    other_streams = []
    
    if 'streams' not in probe_data:
        return None, None, []
    
    for stream in probe_data['streams']:
        codec_type = stream.get('codec_type', 'unknown')
        codec_name = stream.get('codec_name', 'unknown')
        
        if codec_type == 'video' and video_stream is None:
            video_stream = {
                'index': stream.get('index'),
                'codec_name': codec_name,
                'codec_long_name': stream.get('codec_long_name'),
                'width': stream.get('width'),
                'height': stream.get('height'),
                'pix_fmt': stream.get('pix_fmt'),
            }
        elif codec_type == 'audio' and audio_stream is None:
            audio_stream = {
                'index': stream.get('index'),
                'codec_name': codec_name,
                'codec_long_name': stream.get('codec_long_name'),
                'sample_rate': stream.get('sample_rate'),
                'channels': stream.get('channels'),
            }
        else:
            # Data, subtitle, or other stream types
            other_streams.append({
                'index': stream.get('index'),
                'codec_type': codec_type,
                'codec_name': codec_name,
            })
    
    return video_stream, audio_stream, other_streams


def determine_strategy(video_stream: Optional[Dict[str, Any]], 
                       audio_stream: Optional[Dict[str, Any]]) -> Tuple[str, str]:
    """
    Determine conversion strategy based on codecs.
    
    Args:
        video_stream: Video stream metadata
        audio_stream: Audio stream metadata
        
    Returns:
        Tuple of (strategy, reason)
        Strategy: 'remux' or 'reencode'
    """
    if not video_stream:
        return 'reencode', 'No video stream found'
    
    if not audio_stream:
        return 'reencode', 'No audio stream found'
    
    video_codec = video_stream.get('codec_name', '').lower()
    audio_codec = audio_stream.get('codec_name', '').lower()
    
    # Check if codecs are compatible for remux
    compatible_video_codecs = ['h264', 'hevc', 'h265']
    compatible_audio_codecs = ['aac', 'mp3']
    
    video_compatible = video_codec in compatible_video_codecs
    audio_compatible = audio_codec in compatible_audio_codecs
    
    if video_compatible and audio_compatible:
        return 'remux', f'Codecs compatible: {video_codec.upper()} + {audio_codec.upper()}'
    else:
        reason_parts = []
        if not video_compatible:
            reason_parts.append(f'Video codec {video_codec} not compatible')
        if not audio_compatible:
            reason_parts.append(f'Audio codec {audio_codec} not compatible')
        return 'reencode', ', '.join(reason_parts)


def remux_to_mp4(input_path: str, output_path: str, 
                  video_index: int, audio_index: int,
                  ffmpeg_path: Optional[str] = None) -> bool:
    """
    Fast remux (copy streams without re-encoding).
    
    Args:
        input_path: Path to input .MOV file
        output_path: Path to output .MP4 file
        video_index: Index of video stream
        audio_index: Index of audio stream
        ffmpeg_path: Optional custom path to ffmpeg
        
    Returns:
        True if successful, False otherwise
    """
    ffmpeg_exe = find_ffmpeg_tool('ffmpeg', ffmpeg_path)
    input_path = str(Path(input_path).resolve())
    output_path = str(Path(output_path).resolve())
    
    cmd = [
        ffmpeg_exe,
        '-i', input_path,
        '-map', f'0:v:{video_index}',
        '-map', f'0:a:{audio_index}',
        '-c', 'copy',  # Copy streams without re-encoding
        '-movflags', '+faststart',  # Optimize for web streaming
        '-y',  # Overwrite output file if exists
        output_path
    ]
    
    print(f"  Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"  Error: {e.stderr}", file=sys.stderr)
        return False


def reencode_to_mp4(input_path: str, output_path: str,
                    video_index: int, audio_index: int,
                    ffmpeg_path: Optional[str] = None) -> bool:
    """
    Re-encode video to MP4 with safe settings.
    
    Args:
        input_path: Path to input .MOV file
        output_path: Path to output .MP4 file
        video_index: Index of video stream
        audio_index: Index of audio stream
        ffmpeg_path: Optional custom path to ffmpeg
        
    Returns:
        True if successful, False otherwise
    """
    ffmpeg_exe = find_ffmpeg_tool('ffmpeg', ffmpeg_path)
    input_path = str(Path(input_path).resolve())
    output_path = str(Path(output_path).resolve())
    
    cmd = [
        ffmpeg_exe,
        '-i', input_path,
        '-map', f'0:v:{video_index}',
        '-map', f'0:a:{audio_index}',
        # Video encoding settings
        '-c:v', 'libx264',
        '-crf', '18',  # High quality (lower = better quality, 18 is visually lossless)
        '-pix_fmt', 'yuv420p',  # Ensure compatibility
        '-preset', 'medium',  # Encoding speed vs compression
        # Audio encoding settings
        '-c:a', 'aac',
        '-b:a', '192k',  # Audio bitrate
        # MP4 optimization
        '-movflags', '+faststart',  # Optimize for web streaming
        '-y',  # Overwrite output file if exists
        output_path
    ]
    
    print(f"  Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"  Error: {e.stderr}", file=sys.stderr)
        return False


def convert_mov_to_mp4(input_path: str, output_path: Optional[str] = None,
                       ffmpeg_path: Optional[str] = None,
                       ffprobe_path: Optional[str] = None) -> bool:
    """
    Convert .MOV file to .MP4 intelligently.
    
    Args:
        input_path: Path to input .MOV file
        output_path: Optional path to output .MP4 file (auto-generated if not provided)
        ffmpeg_path: Optional custom path to ffmpeg
        ffprobe_path: Optional custom path to ffprobe
        
    Returns:
        True if conversion successful, False otherwise
        
    Raises:
        FileNotFoundError: If input file or tools not found
        ValueError: If video file is invalid
    """
    # Validate input file
    input_path_obj = Path(input_path)
    if not input_path_obj.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    if not input_path_obj.is_file():
        raise ValueError(f"Path is not a file: {input_path}")
    
    # Generate output path if not provided
    if output_path is None:
        output_path = str(input_path_obj.with_suffix('.mp4'))
    else:
        output_path = str(Path(output_path).resolve())
    
    print(f"Input file: {input_path}")
    print(f"Output file: {output_path}")
    print()
    
    # Step 1: Probe video to get metadata
    print("Step 1: Analyzing video metadata...")
    try:
        probe_data = probe_video(input_path, ffprobe_path)
    except Exception as e:
        print(f"  Error probing video: {e}", file=sys.stderr)
        return False
    
    # Step 2: Analyze streams
    print("Step 2: Analyzing streams...")
    video_stream, audio_stream, other_streams = analyze_streams(probe_data)
    
    if video_stream:
        print(f"  Video stream #{video_stream['index']}: {video_stream['codec_name'].upper()}")
        print(f"    Resolution: {video_stream.get('width')}x{video_stream.get('height')}")
        print(f"    Pixel format: {video_stream.get('pix_fmt', 'unknown')}")
    else:
        print("  Warning: No video stream found", file=sys.stderr)
    
    if audio_stream:
        print(f"  Audio stream #{audio_stream['index']}: {audio_stream['codec_name'].upper()}")
        print(f"    Sample rate: {audio_stream.get('sample_rate', 'unknown')} Hz")
        print(f"    Channels: {audio_stream.get('channels', 'unknown')}")
    else:
        print("  Warning: No audio stream found", file=sys.stderr)
    
    if other_streams:
        print(f"  Other streams: {len(other_streams)} (will be skipped)")
        for stream in other_streams:
            print(f"    Stream #{stream['index']}: {stream['codec_type']} ({stream['codec_name']})")
    
    print()
    
    # Step 3: Determine strategy
    print("Step 3: Determining conversion strategy...")
    strategy, reason = determine_strategy(video_stream, audio_stream)
    print(f"  Strategy: {strategy.upper()}")
    print(f"  Reason: {reason}")
    print()
    
    if not video_stream or not audio_stream:
        print("  Error: Cannot convert without video and audio streams", file=sys.stderr)
        return False
    
    # Step 4: Perform conversion
    print(f"Step 4: Converting to MP4 ({strategy})...")
    
    # Get stream indices (relative to stream type, not absolute)
    video_index = 0  # First video stream
    audio_index = 0  # First audio stream
    
    if strategy == 'remux':
        success = remux_to_mp4(input_path, output_path, video_index, audio_index, ffmpeg_path)
    else:
        success = reencode_to_mp4(input_path, output_path, video_index, audio_index, ffmpeg_path)
    
    if success:
        output_path_obj = Path(output_path)
        if output_path_obj.exists():
            size_mb = output_path_obj.stat().st_size / (1024 * 1024)
            print(f"  ✓ Conversion successful!")
            print(f"  Output file size: {size_mb:.2f} MB")
            return True
        else:
            print("  Error: Output file was not created", file=sys.stderr)
            return False
    else:
        print("  ✗ Conversion failed", file=sys.stderr)
        return False


def main():
    """CLI entry point for the MOV to MP4 converter."""
    parser = argparse.ArgumentParser(
        description='Convert .MOV files to .MP4 intelligently using FFmpeg',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python mov_to_mp4.py video.mov
    # Converts to video.mp4 in same directory
  
  python mov_to_mp4.py video.mov --out output.mp4
    # Converts to specified output file
  
  python mov_to_mp4.py video.mov --ffmpeg-path "C:\\ffmpeg\\bin\\ffmpeg.exe"
    # Uses custom ffmpeg path
        """
    )
    
    parser.add_argument(
        'input',
        type=str,
        help='Path to the input .MOV file'
    )
    
    parser.add_argument(
        '--out', '-o',
        type=str,
        default=None,
        help='Output .MP4 file path (default: same as input with .mp4 extension)'
    )
    
    parser.add_argument(
        '--ffmpeg-path',
        type=str,
        default=None,
        help='Custom path to ffmpeg executable (if not in PATH)'
    )
    
    parser.add_argument(
        '--ffprobe-path',
        type=str,
        default=None,
        help='Custom path to ffprobe executable (if not in PATH)'
    )
    
    args = parser.parse_args()
    
    try:
        success = convert_mov_to_mp4(
            args.input,
            output_path=args.out,
            ffmpeg_path=args.ffmpeg_path,
            ffprobe_path=args.ffprobe_path
        )
        
        if success:
            print("\n✓ Conversion completed successfully!")
            sys.exit(0)
        else:
            print("\n✗ Conversion failed", file=sys.stderr)
            sys.exit(1)
            
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
