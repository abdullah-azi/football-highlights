#!/usr/bin/env python3
"""
MOV Metadata Extraction Tool for Windows

Extracts comprehensive metadata from .MOV video files using FFmpeg's ffprobe
and optionally ExifTool for GPS/EXIF data.

Requirements:
    - FFmpeg/ffprobe installed and available in PATH
    - Optional: ExifTool and pyexiftool for GPS/EXIF metadata
"""

import json
import subprocess
import sys
import argparse
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import timedelta


def format_duration(seconds: Optional[str]) -> Optional[Dict[str, Any]]:
    """
    Convert duration in seconds to human-readable format.
    
    Args:
        seconds: Duration as string (e.g., "123.45")
        
    Returns:
        Dictionary with seconds, formatted time, and human-readable string
    """
    if not seconds:
        return None
    
    try:
        sec_float = float(seconds)
        td = timedelta(seconds=sec_float)
        
        # Format as HH:MM:SS.mmm
        hours, remainder = divmod(int(sec_float), 3600)
        minutes, secs = divmod(remainder, 60)
        milliseconds = int((sec_float - int(sec_float)) * 1000)
        
        formatted = f"{hours:02d}:{minutes:02d}:{secs:02d}.{milliseconds:03d}"
        
        # Human-readable string
        if hours > 0:
            human = f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            human = f"{minutes}m {secs}s"
        else:
            human = f"{secs}s"
        
        return {
            'seconds': round(sec_float, 3),
            'formatted': formatted,
            'human_readable': human
        }
    except (ValueError, TypeError):
        return None


def format_bitrate(bitrate: Optional[str]) -> Optional[Dict[str, Any]]:
    """
    Convert bitrate to human-readable format with units.
    
    Args:
        bitrate: Bitrate as string in bits per second
        
    Returns:
        Dictionary with bps, kbps, mbps, and human-readable string
    """
    if not bitrate:
        return None
    
    try:
        bps = int(bitrate)
        kbps = bps / 1000
        mbps = bps / 1000000
        
        if mbps >= 1:
            human = f"{mbps:.2f} Mbps"
        elif kbps >= 1:
            human = f"{kbps:.2f} Kbps"
        else:
            human = f"{bps} bps"
        
        return {
            'bps': bps,
            'kbps': round(kbps, 2),
            'mbps': round(mbps, 3),
            'human_readable': human
        }
    except (ValueError, TypeError):
        return None


def format_file_size(size_bytes: int) -> Dict[str, Any]:
    """
    Convert file size to human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Dictionary with bytes, KB, MB, GB, and human-readable string
    """
    kb = size_bytes / 1024
    mb = size_bytes / (1024 * 1024)
    gb = size_bytes / (1024 * 1024 * 1024)
    
    if gb >= 1:
        human = f"{gb:.2f} GB"
    elif mb >= 1:
        human = f"{mb:.2f} MB"
    elif kb >= 1:
        human = f"{kb:.2f} KB"
    else:
        human = f"{size_bytes} bytes"
    
    return {
        'bytes': size_bytes,
        'kb': round(kb, 2),
        'mb': round(mb, 2),
        'gb': round(gb, 3),
        'human_readable': human
    }


def format_resolution(width: Optional[int], height: Optional[int]) -> Optional[Dict[str, Any]]:
    """
    Format video resolution in a comprehensible way.
    
    Args:
        width: Video width in pixels
        height: Video height in pixels
        
    Returns:
        Dictionary with resolution details
    """
    if not width or not height:
        return None
    
    # Common resolution names
    resolution_names = {
        (3840, 2160): "4K UHD",
        (1920, 1080): "1080p Full HD",
        (1280, 720): "720p HD",
        (854, 480): "480p SD",
        (640, 360): "360p",
    }
    
    name = resolution_names.get((width, height), f"{width}x{height}")
    
    return {
        'width': width,
        'height': height,
        'resolution': f"{width}x{height}",
        'name': name,
        'total_pixels': width * height
    }


def find_ffprobe(ffprobe_path: Optional[str] = None) -> str:
    """
    Find ffprobe executable path.
    
    Args:
        ffprobe_path: Custom path to ffprobe (optional)
        
    Returns:
        Path to ffprobe executable
        
    Raises:
        FileNotFoundError: If ffprobe cannot be found
    """
    # If custom path provided, use it
    if ffprobe_path:
        custom_path = Path(ffprobe_path)
        if custom_path.exists() and custom_path.is_file():
            return str(custom_path.resolve())
        raise FileNotFoundError(f"ffprobe not found at specified path: {ffprobe_path}")
    
    # First, try to find ffprobe in PATH using shutil.which
    ffprobe_exe = shutil.which('ffprobe')
    if ffprobe_exe:
        return ffprobe_exe
    
    # If not in PATH, search common Windows installation locations
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
    
    # If still not found, raise error with helpful message
    raise FileNotFoundError(
        "ffprobe not found. Please ensure FFmpeg is installed and available in PATH.\n"
        "You can also specify the path using --ffprobe-path option.\n"
        "Download FFmpeg from: https://ffmpeg.org/download.html"
    )


def run_ffprobe(video_path: str, ffprobe_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Run ffprobe on a video file and return parsed JSON metadata.
    
    Args:
        video_path: Path to the video file
        ffprobe_path: Optional custom path to ffprobe executable
        
    Returns:
        Dictionary containing ffprobe output
        
    Raises:
        FileNotFoundError: If ffprobe is not found
        subprocess.CalledProcessError: If ffprobe execution fails
    """
    # Find ffprobe executable
    ffprobe_exe = find_ffprobe(ffprobe_path)
    
    # Windows-compatible path handling
    video_path = str(Path(video_path).resolve())
    
    # ffprobe command to extract all metadata in JSON format
    cmd = [
        ffprobe_exe,
        '-v', 'quiet',              # Suppress output except errors
        '-print_format', 'json',    # Output as JSON
        '-show_format',             # Show container format info
        '-show_streams',            # Show all streams (video, audio, etc.)
        '-show_chapters',           # Show chapters if any
        '-show_programs',           # Show programs if any
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
        raise FileNotFoundError(
            "ffprobe not found. Please ensure FFmpeg is installed and available in PATH."
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"ffprobe execution failed: {e.stderr}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse ffprobe JSON output: {e}")


def run_exiftool(video_path: str) -> Optional[Dict[str, Any]]:
    """
    Run ExifTool on a video file to extract GPS/EXIF metadata.
    
    Args:
        video_path: Path to the video file
        
    Returns:
        Dictionary containing ExifTool output, or None if ExifTool is unavailable
    """
    video_path = str(Path(video_path).resolve())
    
    try:
        import exiftool
        
        with exiftool.ExifToolHelper() as et:
            metadata = et.get_metadata(video_path)
            if metadata and len(metadata) > 0:
                return metadata[0]  # ExifTool returns a list
    except ImportError:
        # pyexiftool not installed - this is optional
        return None
    except Exception as e:
        # ExifTool not available or error occurred - fail gracefully
        print(f"Warning: ExifTool metadata extraction failed: {e}", file=sys.stderr)
        return None
    
    return None


def extract_video_stream_metadata(stream: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract and structure video stream metadata in a comprehensible format.
    
    Args:
        stream: Video stream dictionary from ffprobe
        
    Returns:
        Structured video metadata dictionary with human-readable values
    """
    width = stream.get('width')
    height = stream.get('height')
    
    metadata = {
        'codec': {
            'name': stream.get('codec_name'),
            'full_name': stream.get('codec_long_name'),
        },
        'resolution': format_resolution(width, height),
        'aspect_ratio': {
            'display': stream.get('display_aspect_ratio'),
            'pixel': stream.get('sample_aspect_ratio'),
        },
        'frame_rate': {},
        'bitrate': format_bitrate(stream.get('bit_rate')),
        'duration': format_duration(stream.get('duration')),
        'total_frames': stream.get('nb_frames'),
    }
    
    # Parse and format frame rate
    avg_frame_rate = stream.get('avg_frame_rate')
    if avg_frame_rate:
        try:
            num, den = map(int, avg_frame_rate.split('/'))
            if den > 0:
                fps = round(num / den, 3)
                metadata['frame_rate'] = {
                    'fps': fps,
                    'raw': avg_frame_rate,
                    'r_frame_rate': stream.get('r_frame_rate'),
                    'human_readable': f"{fps} fps"
                }
        except (ValueError, ZeroDivisionError):
            metadata['frame_rate'] = {
                'raw': avg_frame_rate,
                'r_frame_rate': stream.get('r_frame_rate'),
            }
    
    # Color space and pixel format
    metadata['color'] = {
        'pixel_format': stream.get('pix_fmt'),
        'color_space': stream.get('color_space'),
        'color_range': stream.get('color_range'),
        'color_primaries': stream.get('color_primaries'),
        'transfer_characteristics': stream.get('color_trc'),
    }
    
    # Rotation metadata
    rotation = 0
    if 'tags' in stream:
        tags = stream['tags']
        # Check for rotation in tags
        rotation_str = tags.get('rotate') or tags.get('rotation')
        if rotation_str:
            try:
                rotation = int(rotation_str)
            except (ValueError, TypeError):
                pass
    
    metadata['rotation'] = {
        'degrees': rotation,
        'human_readable': f"{rotation}°" if rotation != 0 else "No rotation"
    }
    
    # Extract all tags from video stream (for advanced users)
    if 'tags' in stream:
        metadata['raw_tags'] = stream['tags']
    
    return metadata


def extract_audio_stream_metadata(stream: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract and structure audio stream metadata in a comprehensible format.
    
    Args:
        stream: Audio stream dictionary from ffprobe
        
    Returns:
        Structured audio metadata dictionary with human-readable values
    """
    sample_rate = stream.get('sample_rate')
    channels = stream.get('channels')
    
    # Format sample rate
    sample_rate_human = None
    if sample_rate:
        try:
            sr_int = int(sample_rate)
            if sr_int >= 1000:
                sample_rate_human = f"{sr_int / 1000:.1f} kHz"
            else:
                sample_rate_human = f"{sr_int} Hz"
        except (ValueError, TypeError):
            pass
    
    # Format channel layout
    channel_layout = stream.get('channel_layout')
    channels_human = None
    if channels:
        channels_human = f"{channels} channel{'s' if channels != 1 else ''}"
        if channel_layout:
            channels_human += f" ({channel_layout})"
    
    metadata = {
        'codec': {
            'name': stream.get('codec_name'),
            'full_name': stream.get('codec_long_name'),
        },
        'sample_rate': {
            'hz': int(sample_rate) if sample_rate else None,
            'human_readable': sample_rate_human,
        },
        'channels': {
            'count': channels,
            'layout': channel_layout,
            'human_readable': channels_human,
        },
        'bitrate': format_bitrate(stream.get('bit_rate')),
        'duration': format_duration(stream.get('duration')),
        'bit_depth': stream.get('bits_per_raw_sample'),
    }
    
    # Extract all tags from audio stream (for advanced users)
    if 'tags' in stream:
        metadata['raw_tags'] = stream['tags']
    
    return metadata


def extract_camera_metadata(ffprobe_data: Dict[str, Any], exiftool_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extract camera/device-specific metadata from ffprobe and ExifTool data.
    
    Args:
        ffprobe_data: Full ffprobe output
        exiftool_data: ExifTool output (optional)
        
    Returns:
        Dictionary containing camera/device metadata in comprehensible format
    """
    camera_metadata = {
        'device': {},
        'software': {},
        'timestamps': {},
        'location': {},
    }
    
    # Extract from ffprobe format tags
    if 'format' in ffprobe_data and 'tags' in ffprobe_data['format']:
        tags = ffprobe_data['format']['tags']
        
        # Device info
        if 'com.apple.quicktime.make' in tags or 'make' in tags:
            camera_metadata['device']['make'] = tags.get('com.apple.quicktime.make') or tags.get('make')
        if 'com.apple.quicktime.model' in tags or 'model' in tags:
            camera_metadata['device']['model'] = tags.get('com.apple.quicktime.model') or tags.get('model')
        
        # Software info
        if 'com.apple.quicktime.software' in tags or 'software' in tags or 'encoder' in tags:
            software = (tags.get('com.apple.quicktime.software') or 
                       tags.get('software') or 
                       tags.get('encoder'))
            if software:
                camera_metadata['software']['name'] = software
        
        # Timestamps
        if 'com.apple.quicktime.creationdate' in tags or 'creation_time' in tags or 'date' in tags:
            creation_time = (tags.get('com.apple.quicktime.creationdate') or 
                          tags.get('creation_time') or 
                          tags.get('date'))
            if creation_time:
                camera_metadata['timestamps']['creation_time'] = creation_time
        
        # Location (ISO6709 format)
        if 'com.apple.quicktime.location.ISO6709' in tags or 'location' in tags:
            location = (tags.get('com.apple.quicktime.location.ISO6709') or 
                       tags.get('location'))
            if location:
                camera_metadata['location']['iso6709'] = location
    
    # Extract from video stream tags (often contains device info)
    if 'streams' in ffprobe_data:
        for stream in ffprobe_data['streams']:
            if stream.get('codec_type') == 'video' and 'tags' in stream:
                stream_tags = stream['tags']
                
                # Encoder/software info
                if stream_tags.get('encoder') and not camera_metadata['software'].get('name'):
                    camera_metadata['software']['encoder'] = stream_tags.get('encoder')
                if stream_tags.get('handler_name'):
                    camera_metadata['software']['handler'] = stream_tags.get('handler_name')
    
    # Extract GPS and additional metadata from ExifTool if available
    if exiftool_data:
        gps_data = {}
        
        # GPS coordinates
        if 'EXIF:GPSLatitude' in exiftool_data and 'EXIF:GPSLongitude' in exiftool_data:
            lat = exiftool_data.get('EXIF:GPSLatitude')
            lon = exiftool_data.get('EXIF:GPSLongitude')
            alt = exiftool_data.get('EXIF:GPSAltitude')
            
            gps_data['coordinates'] = {
                'latitude': lat,
                'longitude': lon,
                'altitude': alt,
            }
            
            # Create human-readable position string
            if lat and lon:
                try:
                    lat_val = float(str(lat).replace(' deg', ''))
                    lon_val = float(str(lon).replace(' deg', ''))
                    gps_data['coordinates']['human_readable'] = f"{lat_val:.6f}, {lon_val:.6f}"
                except (ValueError, AttributeError):
                    gps_data['coordinates']['human_readable'] = f"{lat}, {lon}"
        
        # GPS string format
        if 'EXIF:GPSPosition' in exiftool_data:
            gps_data['position_string'] = exiftool_data.get('EXIF:GPSPosition')
        
        if gps_data:
            camera_metadata['location']['gps'] = gps_data
        
        # Additional device info from ExifTool
        if 'EXIF:Make' in exiftool_data and not camera_metadata['device'].get('make'):
            camera_metadata['device']['make'] = exiftool_data['EXIF:Make']
        if 'EXIF:Model' in exiftool_data and not camera_metadata['device'].get('model'):
            camera_metadata['device']['model'] = exiftool_data['EXIF:Model']
        if 'EXIF:Software' in exiftool_data and not camera_metadata['software'].get('name'):
            camera_metadata['software']['name'] = exiftool_data['EXIF:Software']
        if 'EXIF:DateTimeOriginal' in exiftool_data:
            camera_metadata['timestamps']['datetime_original'] = exiftool_data['EXIF:DateTimeOriginal']
        if 'EXIF:DateTimeDigitized' in exiftool_data:
            camera_metadata['timestamps']['datetime_digitized'] = exiftool_data['EXIF:DateTimeDigitized']
    
    # Clean up empty sections
    camera_metadata = {k: v for k, v in camera_metadata.items() if v}
    
    # Flatten for backward compatibility (keep top-level keys)
    flattened = {}
    if camera_metadata.get('device', {}).get('make'):
        flattened['make'] = camera_metadata['device']['make']
    if camera_metadata.get('device', {}).get('model'):
        flattened['model'] = camera_metadata['device']['model']
    if camera_metadata.get('software', {}).get('name'):
        flattened['software'] = camera_metadata['software']['name']
    if camera_metadata.get('timestamps', {}).get('creation_time'):
        flattened['creation_time'] = camera_metadata['timestamps']['creation_time']
    if camera_metadata.get('location', {}).get('gps'):
        flattened['gps'] = camera_metadata['location']['gps']
    
    # Merge structured and flattened
    return {**camera_metadata, **flattened}


def extract_mov_metadata(video_path: str, include_exiftool: bool = True, ffprobe_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract comprehensive metadata from a .MOV video file.
    
    Args:
        video_path: Path to the .MOV file
        include_exiftool: Whether to attempt ExifTool extraction (default: True)
        ffprobe_path: Optional custom path to ffprobe executable
        
    Returns:
        Dictionary containing structured metadata
        
    Raises:
        FileNotFoundError: If video file or ffprobe not found
        ValueError: If video file is invalid or metadata parsing fails
    """
    # Validate file exists
    video_path_obj = Path(video_path)
    if not video_path_obj.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    if not video_path_obj.is_file():
        raise ValueError(f"Path is not a file: {video_path}")
    
    # Run ffprobe
    ffprobe_data = run_ffprobe(video_path, ffprobe_path)
    
    # Optionally run ExifTool
    exiftool_data = None
    if include_exiftool:
        exiftool_data = run_exiftool(video_path)
    
    # Get file size
    file_size_bytes = video_path_obj.stat().st_size
    file_size_formatted = format_file_size(file_size_bytes)
    
    # Structure the metadata with comprehensible format
    metadata = {
        'summary': {
            'filename': video_path_obj.name,
            'file_size': file_size_formatted['human_readable'],
            'file_path': str(video_path_obj.resolve()),
        },
        'file': {
            'name': video_path_obj.name,
            'path': str(video_path_obj.resolve()),
            'size': file_size_formatted,
        },
        'container': {},
        'video_streams': [],
        'audio_streams': [],
        'other_streams': [],
        'camera': {},
        'raw_tags': {},
    }
    
    # Extract container-level metadata
    if 'format' in ffprobe_data:
        format_info = ffprobe_data['format']
        
        # Format container size if available
        container_size = None
        if format_info.get('size'):
            try:
                container_size = format_file_size(int(format_info.get('size')))
            except (ValueError, TypeError):
                pass
        
        metadata['container'] = {
            'format': {
                'name': format_info.get('format_name'),
                'full_name': format_info.get('format_long_name'),
            },
            'duration': format_duration(format_info.get('duration')),
            'size': container_size,
            'bitrate': format_bitrate(format_info.get('bit_rate')),
            'streams': {
                'total': format_info.get('nb_streams'),
                'programs': format_info.get('nb_programs'),
            },
        }
        
        # Update summary with container info
        if metadata['container'].get('duration'):
            metadata['summary']['duration'] = metadata['container']['duration']['human_readable']
        if metadata['container'].get('bitrate'):
            metadata['summary']['bitrate'] = metadata['container']['bitrate']['human_readable']
        
        # Store all format tags (for advanced users)
        if 'tags' in format_info:
            metadata['raw_tags']['format'] = format_info['tags']
    
    # Extract stream metadata
    if 'streams' in ffprobe_data:
        for stream in ffprobe_data['streams']:
            codec_type = stream.get('codec_type', 'unknown')
            
            if codec_type == 'video':
                video_meta = extract_video_stream_metadata(stream)
                metadata['video_streams'].append(video_meta)
                
                # Add video info to summary (from first video stream)
                if len(metadata['video_streams']) == 1:
                    if video_meta.get('resolution'):
                        metadata['summary']['resolution'] = video_meta['resolution']['resolution']
                        metadata['summary']['resolution_name'] = video_meta['resolution']['name']
                    if video_meta.get('frame_rate', {}).get('human_readable'):
                        metadata['summary']['frame_rate'] = video_meta['frame_rate']['human_readable']
                    if video_meta.get('codec', {}).get('name'):
                        metadata['summary']['video_codec'] = video_meta['codec']['name']
                        
            elif codec_type == 'audio':
                audio_meta = extract_audio_stream_metadata(stream)
                metadata['audio_streams'].append(audio_meta)
                
                # Add audio info to summary (from first audio stream)
                if len(metadata['audio_streams']) == 1:
                    if audio_meta.get('codec', {}).get('name'):
                        metadata['summary']['audio_codec'] = audio_meta['codec']['name']
                    if audio_meta.get('channels', {}).get('human_readable'):
                        metadata['summary']['audio_channels'] = audio_meta['channels']['human_readable']
                    if audio_meta.get('sample_rate', {}).get('human_readable'):
                        metadata['summary']['sample_rate'] = audio_meta['sample_rate']['human_readable']
            else:
                # Subtitle, data, or other stream types
                metadata['other_streams'].append({
                    'codec_type': codec_type,
                    'codec_name': stream.get('codec_name'),
                    'index': stream.get('index'),
                    'tags': stream.get('tags', {}),
                })
    
    # Extract camera/device metadata
    camera_meta = extract_camera_metadata(ffprobe_data, exiftool_data)
    metadata['camera'] = camera_meta
    
    # Add camera info to summary if available
    if camera_meta.get('make') or camera_meta.get('model'):
        device_info = []
        if camera_meta.get('make'):
            device_info.append(camera_meta['make'])
        if camera_meta.get('model'):
            device_info.append(camera_meta['model'])
        if device_info:
            metadata['summary']['device'] = ' '.join(device_info)
    
    if camera_meta.get('creation_time'):
        metadata['summary']['creation_time'] = camera_meta['creation_time']
    
    # Extract chapters if available
    if 'chapters' in ffprobe_data:
        metadata['chapters'] = ffprobe_data['chapters']
    
    return metadata


def main():
    """CLI entry point for the metadata extraction tool."""
    parser = argparse.ArgumentParser(
        description='Extract comprehensive metadata from .MOV video files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python extract_metadata.py video.mov
    # Automatically saves to Data/video_metadata.json in script directory
  
  python extract_metadata.py video.mov --out custom_metadata.json
    # Saves to custom_metadata.json (custom path)
  
  python extract_metadata.py video.mov --out Data/custom.json
    # Saves to Data/custom.json
  
  python extract_metadata.py video.mov --no-save
    # Prints to stdout only, does not save file
  
  python extract_metadata.py video.mov --camera-only
    # Extracts only camera/GPS metadata
  
  python extract_metadata.py video.mov --no-exiftool
    # Skips ExifTool extraction (faster)
  
  python extract_metadata.py video.mov --ffprobe-path "C:\\ffmpeg\\bin\\ffprobe.exe"
    # Uses custom ffprobe path
        """
    )
    
    parser.add_argument(
        'input',
        type=str,
        help='Path to the .MOV video file'
    )
    
    parser.add_argument(
        '--out', '-o',
        type=str,
        default=None,
        help='Output JSON file path (default: Data/{filename}_metadata.json in script directory)'
    )
    
    parser.add_argument(
        '--no-save',
        action='store_true',
        help='Do not save JSON file (print to stdout only)'
    )
    
    parser.add_argument(
        '--camera-only',
        action='store_true',
        help='Extract only camera/GPS metadata'
    )
    
    parser.add_argument(
        '--no-exiftool',
        action='store_true',
        help='Skip ExifTool metadata extraction'
    )
    
    parser.add_argument(
        '--pretty',
        action='store_true',
        default=True,
        help='Pretty-print JSON output (default: True)'
    )
    
    parser.add_argument(
        '--ffprobe-path',
        type=str,
        default=None,
        help='Custom path to ffprobe executable (if not in PATH)'
    )
    
    args = parser.parse_args()
    
    try:
        # Extract metadata
        metadata = extract_mov_metadata(
            args.input,
            include_exiftool=not args.no_exiftool,
            ffprobe_path=args.ffprobe_path
        )
        
        # Filter to camera-only if requested
        if args.camera_only:
            output = {
                'file': metadata['file'],
                'camera': metadata['camera'],
            }
        else:
            output = metadata
        
        # Format JSON
        json_output = json.dumps(
            output,
            indent=2 if args.pretty else None,
            ensure_ascii=False
        )
        
        # Determine output file path
        if not args.no_save:
            if args.out:
                # Use user-specified path
                output_path = Path(args.out)
            else:
                # Auto-generate filename and save to Data folder in script's root directory
                script_dir = Path(__file__).parent.resolve()
                data_dir = script_dir / "Data"
                
                # Create Data directory if it doesn't exist
                data_dir.mkdir(exist_ok=True)
                
                # Generate filename from input video
                input_path = Path(args.input)
                output_filename = f"{input_path.stem}_metadata.json"
                output_path = data_dir / output_filename
            
            # Save JSON file
            output_path.write_text(json_output, encoding='utf-8')
            print(f"✓ Metadata saved to: {output_path}", file=sys.stderr)
            print(f"  File size: {format_file_size(output_path.stat().st_size)['human_readable']}", file=sys.stderr)
        
        # Also print to stdout (can be redirected)
        print(json_output)
            
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
    # Example usage
    if len(sys.argv) == 1:
        print("MOV Metadata Extraction Tool", file=sys.stderr)
        print("Usage: python extract_metadata.py <input.mov> [options]", file=sys.stderr)
        print("Run with --help for more information.", file=sys.stderr)
        sys.exit(0)
    
    main()
