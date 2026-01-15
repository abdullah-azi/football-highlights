#!/usr/bin/env python3
"""
Video Trimming Utility for Large .MOV Files

Trims .MOV video files (iPhone videos, HEVC/H.264) using FFmpeg.
Designed for large files (5-10 GB) with fast, lossless trimming by default.

Requirements:
    - FFmpeg installed and available in PATH
    - Python 3.6+
"""

import subprocess
import sys
import shutil
import argparse
from pathlib import Path
from typing import Optional, Union


def find_ffmpeg(ffmpeg_path: Optional[str] = None) -> str:
    """
    Find FFmpeg executable path.
    
    Args:
        ffmpeg_path: Custom path to FFmpeg (optional)
        
    Returns:
        Path to FFmpeg executable
        
    Raises:
        FileNotFoundError: If FFmpeg cannot be found
    """
    # If custom path provided, use it
    if ffmpeg_path:
        custom_path = Path(ffmpeg_path)
        if custom_path.exists() and custom_path.is_file():
            return str(custom_path.resolve())
        raise FileNotFoundError(f"FFmpeg not found at specified path: {ffmpeg_path}")
    
    # First, try to find FFmpeg in PATH using shutil.which
    ffmpeg_exe = shutil.which('ffmpeg')
    if ffmpeg_exe:
        return ffmpeg_exe
    
    # If not in PATH, search common Windows installation locations
    if sys.platform == 'win32':
        common_paths = [
            Path('C:/ffmpeg/bin/ffmpeg.exe'),
            Path('C:/Program Files/ffmpeg/bin/ffmpeg.exe'),
            Path('C:/Program Files (x86)/ffmpeg/bin/ffmpeg.exe'),
            Path.home() / 'ffmpeg/bin/ffmpeg.exe',
            Path('C:/tools/ffmpeg/bin/ffmpeg.exe'),
        ]
        
        for path in common_paths:
            if path.exists() and path.is_file():
                return str(path.resolve())
    
    # If still not found, raise error with helpful message
    raise FileNotFoundError(
        "FFmpeg not found. Please ensure FFmpeg is installed and available in PATH.\n"
        "You can also specify the path using --ffmpeg-path option.\n"
        "Download FFmpeg from: https://ffmpeg.org/download.html\n"
        "For Windows: https://www.gyan.dev/ffmpeg/builds/"
    )


def parse_time(time_input: Union[str, float, int]) -> float:
    """
    Parse time input in seconds or HH:MM:SS format to seconds (float).
    
    Args:
        time_input: Time as seconds (number or string) or HH:MM:SS format
        
    Returns:
        Time in seconds as float
        
    Raises:
        ValueError: If time format is invalid
    """
    # If it's already a number, return it
    if isinstance(time_input, (int, float)):
        if time_input < 0:
            raise ValueError("Time cannot be negative")
        return float(time_input)
    
    # Convert to string and strip whitespace
    time_str = str(time_input).strip()
    
    # Try parsing as HH:MM:SS or MM:SS format
    if ':' in time_str:
        parts = time_str.split(':')
        if len(parts) == 2:
            # MM:SS format
            minutes, seconds = parts
            try:
                total_seconds = int(minutes) * 60 + float(seconds)
                if total_seconds < 0:
                    raise ValueError("Time cannot be negative")
                return total_seconds
            except ValueError:
                raise ValueError(f"Invalid time format: {time_str}. Expected MM:SS or HH:MM:SS")
        elif len(parts) == 3:
            # HH:MM:SS format
            hours, minutes, seconds = parts
            try:
                total_seconds = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
                if total_seconds < 0:
                    raise ValueError("Time cannot be negative")
                return total_seconds
            except ValueError:
                raise ValueError(f"Invalid time format: {time_str}. Expected HH:MM:SS")
        else:
            raise ValueError(f"Invalid time format: {time_str}. Expected MM:SS or HH:MM:SS")
    else:
        # Try parsing as seconds (float)
        try:
            seconds = float(time_str)
            if seconds < 0:
                raise ValueError("Time cannot be negative")
            return seconds
        except ValueError:
            raise ValueError(f"Invalid time format: {time_str}. Expected seconds (number) or HH:MM:SS")


def format_time(seconds: float) -> str:
    """
    Format seconds to HH:MM:SS.mmm format for FFmpeg.
    
    Args:
        seconds: Time in seconds
        
    Returns:
        Formatted time string (HH:MM:SS.mmm)
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"


def find_ffprobe(ffmpeg_path: Optional[str] = None) -> str:
    """
    Find FFprobe executable path.
    
    Args:
        ffmpeg_path: Custom path to FFmpeg (optional); used to locate ffprobe next to it
        
    Returns:
        Path to FFprobe executable
        
    Raises:
        FileNotFoundError: If FFprobe cannot be found
    """
    if ffmpeg_path:
        ffmpeg_custom = Path(ffmpeg_path)
        ffprobe_candidate = ffmpeg_custom.with_name('ffprobe.exe' if sys.platform == 'win32' else 'ffprobe')
        if ffprobe_candidate.exists() and ffprobe_candidate.is_file():
            return str(ffprobe_candidate.resolve())
    
    ffprobe_exe = shutil.which('ffprobe')
    if ffprobe_exe:
        return ffprobe_exe
    
    if sys.platform == 'win32':
        common_paths = [
            Path('C:/ffmpeg/bin/ffprobe.exe'),
            Path('C:/Program Files/ffmpeg/bin/ffprobe.exe'),
            Path('C:/Program Files (x86)/ffmpeg/bin/ffprobe.exe'),
            Path.home() / 'ffmpeg/bin/ffprobe.exe',
            Path('C:/tools/ffmpeg/bin/ffprobe.exe'),
        ]
        
        for path in common_paths:
            if path.exists() and path.is_file():
                return str(path.resolve())
    
    raise FileNotFoundError(
        "FFprobe not found. Please ensure FFmpeg is installed and available in PATH.\n"
        "You can also specify the path to FFmpeg using --ffmpeg-path so FFprobe can be located.\n"
        "Download FFmpeg from: https://ffmpeg.org/download.html\n"
        "For Windows: https://www.gyan.dev/ffmpeg/builds/"
    )


def get_video_duration_seconds(input_file: str, ffmpeg_path: Optional[str] = None) -> float:
    """Get full duration of a video file using FFprobe."""
    ffprobe_exe = find_ffprobe(ffmpeg_path)
    input_path = Path(input_file).resolve()
    
    cmd = [
        ffprobe_exe,
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=nk=1:nw=1',
        str(input_path),
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if e.stderr else e.stdout if e.stdout else "Unknown error"
        raise RuntimeError(
            f"FFprobe execution failed:\n"
            f"Command: {' '.join(cmd)}\n"
            f"Error: {error_msg}"
        )
    
    output = result.stdout.strip()
    try:
        return float(output)
    except ValueError as e:
        raise RuntimeError(f"Unable to parse video duration from FFprobe output: {output}") from e


def trim_video(
    input_file: str,
    output_file: str,
    start_time: Union[str, float, int],
    duration: Optional[Union[str, float, int]] = None,
    end_time: Optional[Union[str, float, int]] = None,
    to_end: bool = False,
    frame_accurate: bool = False,
    ffmpeg_path: Optional[str] = None,
    overwrite: bool = False
) -> bool:
    """
    Trim a video file using FFmpeg.
    
    Args:
        input_file: Path to input video file
        output_file: Path to output video file
        start_time: Start time (seconds or HH:MM:SS format)
        duration: Duration of trimmed segment (seconds or HH:MM:SS). Mutually exclusive with end_time and to_end
        end_time: End time of trimmed segment (seconds or HH:MM:SS). Mutually exclusive with duration and to_end
        to_end: If True, trim from start time to end of video
        frame_accurate: If True, re-encode for frame-accurate trimming. If False, use stream copy (fast, lossless)
        ffmpeg_path: Optional custom path to FFmpeg executable
        overwrite: If True, overwrite output file if it exists
        
    Returns:
        True if trimming succeeded, False otherwise
        
    Raises:
        FileNotFoundError: If input file or FFmpeg not found
        ValueError: If time parameters are invalid or multiple trim options are provided
        RuntimeError: If FFmpeg execution fails
    """
    # Validate input file exists
    input_path = Path(input_file)
    if not input_path.exists():
        raise FileNotFoundError(f"Input video file not found: {input_file}")
    if not input_path.is_file():
        raise ValueError(f"Input path is not a file: {input_file}")
    
    # Validate output directory exists or can be created
    output_path = Path(output_file)
    output_dir = output_path.parent
    if not output_dir.exists():
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise RuntimeError(f"Cannot create output directory: {e}")
    
    # Check if output file exists
    if output_path.exists() and not overwrite:
        raise FileExistsError(
            f"Output file already exists: {output_file}\n"
            "Use overwrite=True or --overwrite flag to overwrite it."
        )
    
    # Validate duration/end_time/to_end mutual exclusivity
    if to_end and (duration is not None or end_time is not None):
        raise ValueError("Cannot use to_end with duration or end_time. Use only one option.")
    if duration is not None and end_time is not None:
        raise ValueError("Cannot specify both duration and end_time. Use one or the other.")
    if duration is None and end_time is None and not to_end:
        raise ValueError("Must specify either duration, end_time, or to_end.")
    
    # Parse time inputs
    start_seconds = parse_time(start_time)
    
    if to_end:
        total_duration = get_video_duration_seconds(input_file, ffmpeg_path=ffmpeg_path)
        duration_seconds = total_duration - start_seconds
        if duration_seconds <= 0:
            raise ValueError("Start time must be less than full video duration")
    elif duration is not None:
        duration_seconds = parse_time(duration)
        if duration_seconds <= 0:
            raise ValueError("Duration must be greater than 0")
    else:
        # Calculate duration from end_time
        end_seconds = parse_time(end_time)
        if end_seconds <= start_seconds:
            raise ValueError("End time must be greater than start time")
        duration_seconds = end_seconds - start_seconds
    
    # Find FFmpeg executable
    ffmpeg_exe = find_ffmpeg(ffmpeg_path)
    
    # Build FFmpeg command
    # Use absolute paths for Windows compatibility
    input_file_abs = str(input_path.resolve())
    output_file_abs = str(output_path.resolve())
    
    start_time_formatted = format_time(start_seconds)
    duration_formatted = format_time(duration_seconds)
    
    cmd = [
        ffmpeg_exe,
        '-i', input_file_abs,
        '-ss', start_time_formatted,
        '-t', duration_formatted,
    ]
    
    # Add codec options based on frame_accurate mode
    if frame_accurate:
        # Re-encode for frame-accurate trimming
        # Use high quality settings suitable for iPhone videos
        cmd.extend([
            '-c:v', 'libx264',  # H.264 encoder (widely compatible)
            '-preset', 'medium',  # Encoding speed/quality balance
            '-crf', '18',  # High quality (lower = better quality, 18 is visually lossless)
            '-c:a', 'aac',  # AAC audio codec
            '-b:a', '192k',  # Audio bitrate
        ])
    else:
        # Stream copy - fast, lossless, but may not be frame-accurate
        cmd.extend([
            '-c', 'copy',  # Copy all streams without re-encoding
        ])
    
    # Overwrite output file if it exists
    if overwrite:
        cmd.append('-y')
    else:
        cmd.append('-n')  # Do not overwrite (safety check)
    
    # Add output file
    cmd.append(output_file_abs)
    
    # Run FFmpeg
    try:
        # Use CREATE_NO_WINDOW on Windows to avoid console window popup
        creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            creationflags=creation_flags
        )
        
        return True
        
    except FileNotFoundError:
        raise FileNotFoundError(
            "FFmpeg not found. Please ensure FFmpeg is installed and available in PATH."
        )
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if e.stderr else e.stdout if e.stdout else "Unknown error"
        raise RuntimeError(
            f"FFmpeg execution failed:\n"
            f"Command: {' '.join(cmd)}\n"
            f"Error: {error_msg}"
        )


def main():
    """CLI entry point for the video trimming utility."""
    parser = argparse.ArgumentParser(
        description='Trim .MOV video files using FFmpeg (fast, lossless by default)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Trim from 10 seconds, duration 30 seconds (fast, lossless)
  python trim_video.py input.mov output.mov --start 10 --duration 30
  
  # Trim from 00:01:30 to 00:02:00 (using end time)
  python trim_video.py input.mov output.mov --start 00:01:30 --end 00:02:00
  
  # Frame-accurate trimming (re-encodes, slower but precise)
  python trim_video.py input.mov output.mov --start 10 --duration 30 --frame-accurate
  
  # Using seconds for start and duration
  python trim_video.py input.mov output.mov --start 45.5 --duration 15.2
  
  # Trim from start to end of video
  python trim_video.py input.mov output.mov --start 00:01:30 --to-end
  
  # Overwrite existing output file
  python trim_video.py input.mov output.mov --start 0 --duration 60 --overwrite
        """
    )
    
    parser.add_argument(
        'input',
        type=str,
        help='Path to input .MOV video file'
    )
    
    parser.add_argument(
        'output',
        type=str,
        help='Path to output trimmed video file'
    )
    
    parser.add_argument(
        '--start', '-s',
        type=str,
        required=True,
        help='Start time (seconds or HH:MM:SS format, e.g., "10" or "00:01:30")'
    )
    
    duration_group = parser.add_mutually_exclusive_group(required=True)
    duration_group.add_argument(
        '--duration', '-d',
        type=str,
        help='Duration of trimmed segment (seconds or HH:MM:SS format)'
    )
    duration_group.add_argument(
        '--end', '-e',
        type=str,
        help='End time of trimmed segment (seconds or HH:MM:SS format)'
    )
    duration_group.add_argument(
        '--to-end',
        action='store_true',
        help='Trim from start time to end of video'
    )
    
    parser.add_argument(
        '--frame-accurate',
        action='store_true',
        help='Enable frame-accurate trimming (re-encodes video, slower but precise)'
    )
    
    parser.add_argument(
        '--ffmpeg-path',
        type=str,
        default=None,
        help='Custom path to FFmpeg executable (if not in PATH)'
    )
    
    parser.add_argument(
        '--overwrite',
        action='store_true',
        help='Overwrite output file if it exists'
    )
    
    args = parser.parse_args()
    
    try:
        success = trim_video(
            input_file=args.input,
            output_file=args.output,
            start_time=args.start,
            duration=args.duration,
            end_time=args.end,
            to_end=args.to_end,
            frame_accurate=args.frame_accurate,
            ffmpeg_path=args.ffmpeg_path,
            overwrite=args.overwrite
        )
        
        if success:
            output_path = Path(args.output)
            if output_path.exists():
                file_size = output_path.stat().st_size
                size_mb = file_size / (1024 * 1024)
                print(f"Video trimmed successfully: {args.output}", file=sys.stderr)
                print(f"  Output size: {size_mb:.2f} MB", file=sys.stderr)
            else:
                print(f"Video trimming completed: {args.output}", file=sys.stderr)
        
        sys.exit(0)
        
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except FileExistsError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
