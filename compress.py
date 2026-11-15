#!/usr/bin/env python3
"""
Video Compressor - High Quality & Small File Size
Compresses video files while preserving visual clarity using modern codecs (AV1 / HEVC).
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
BIN_DIR = BASE_DIR / "bin"
FFMPEG_BIN = BIN_DIR / "ffmpeg.exe" if (BIN_DIR / "ffmpeg.exe").exists() else "ffmpeg"
HANDBRAKE_BIN = BIN_DIR / "HandBrakeCLI.exe" if (BIN_DIR / "HandBrakeCLI.exe").exists() else "HandBrakeCLI"

# Codec CRF configurations for "visually lossless" quality
# At these CRF values, the human eye cannot distinguish compressed output from original.
PRESETS = {
    "av1": {
        "encoder": "libsvtav1",
        "crf_default": 26,
        "preset_default": "5",
        "description": "AV1 (SVT-AV1) - Best compression ratio, cutting 50-75% file size at identical clarity."
    },
    "hevc": {
        "encoder": "libx265",
        "crf_default": 22,
        "preset_default": "slow",
        "description": "H.265 (HEVC) - Great compression (40-60% reduction) and universal device playback."
    },
    "h264": {
        "encoder": "libx264",
        "crf_default": 19,
        "preset_default": "slow",
        "description": "H.264 - Maximum legacy compatibility."
    }
}

VIDEO_EXTENSIONS = {".mp4", ".mkv", ".mov", ".avi", ".wmv", ".flv", ".webm", ".m4v", ".ts"}

def format_size(bytes_val):
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_val < 1024.0:
            return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.2f} PB"

def compress_video(input_path: Path, output_path: Path, codec: str = "av1", crf: int = None, preset: str = None) -> bool:
    config = PRESETS[codec]
    target_crf = crf if crf is not None else config["crf_default"]
    target_preset = preset if preset is not None else config["preset_default"]
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    orig_size = input_path.stat().st_size
    print(f"\n[+] Compressing: {input_path.name}")
    print(f"    - Original size: {format_size(orig_size)}")
    print(f"    - Codec: {codec.upper()} ({config['encoder']})")
    print(f"    - CRF (Visual Quality): {target_crf} (Visually Lossless)")
    print(f"    - Preset Speed: {target_preset}")
    
    # FFmpeg command
    # -c:a copy keeps the exact original audio stream with zero audio quality loss
    # -map_metadata 0 preserves tags and rotation
    cmd = [
        str(FFMPEG_BIN),
        "-y",
        "-i", str(input_path),
        "-c:v", config["encoder"],
        "-crf", str(target_crf),
        "-preset", target_preset,
        "-pix_fmt", "yuv420p10le" if codec == "av1" else "yuv420p",
        "-c:a", "copy",
        "-map_metadata", "0",
        str(output_path)
    ]
    
    try:
        process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
        if process.returncode != 0:
            print(f"[!] Error during compression of {input_path.name}:")
            print(process.stderr[-800:] if process.stderr else "Unknown error")
            return False
            
        if not output_path.exists():
            print(f"[!] Output file was not created: {output_path}")
            return False
            
        new_size = output_path.stat().st_size
        saved_bytes = orig_size - new_size
        saved_pct = (saved_bytes / orig_size) * 100 if orig_size > 0 else 0
        
        print(f"[OK] Done: {output_path.name}")
        print(f"     Compressed size: {format_size(new_size)}")
        if saved_bytes > 0:
            print(f"     Reduction: Saved {format_size(saved_bytes)} ({saved_pct:.1f}% smaller!)")
        else:
            print(f"     Note: Original was already heavily compressed (Diff: {format_size(abs(saved_bytes))})")
        return True
    except Exception as e:
        print(f"[!] Exception: {e}")
        return False

def generate_sample_video(sample_path: Path):
    """Generates a high-bitrate 5-second synthetic test video using ffmpeg."""
    print(f"[+] Generating sample video at: {sample_path}")
    sample_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        str(FFMPEG_BIN),
        "-y",
        "-f", "lavfi",
        "-i", "testsrc=duration=5:size=1920x1080:rate=30",
        "-f", "lavfi",
        "-i", "sine=frequency=1000:duration=5",
        "-c:v", "libx264",
        "-crf", "10",
        "-c:a", "aac",
        "-b:a", "192k",
        str(sample_path)
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    print(f"[OK] Created sample video ({format_size(sample_path.stat().st_size)})")

def main():
    parser = argparse.ArgumentParser(
        description="High-Quality Video Compressor (Lossless clarity, minimal file size)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python compress.py -i myvideo.mp4
  python compress.py -i C:\\Videos\\Holiday -o C:\\Videos\\Compressed
  python compress.py -i myvideo.mp4 -c hevc
  python compress.py --test
"""
    )
    parser.add_argument("-i", "--input", help="Path to input video file or folder")
    parser.add_argument("-o", "--output", default="compressed", help="Output directory (default: 'compressed')")
    parser.add_argument("-c", "--codec", choices=["av1", "hevc", "h264"], default="av1",
                        help="Video codec: 'av1' (smallest size), 'hevc' (great size + compatibility), 'h264' (legacy)")
    parser.add_argument("--crf", type=int, default=None,
                        help="Quality level (Lower = higher quality). AV1 default: 26, HEVC default: 22")
    parser.add_argument("--preset", default=None,
                        help="Encoding preset (e.g. 5 for AV1, 'slow' or 'medium' for HEVC)")
    parser.add_argument("--test", action="store_true", help="Generate a test video and run compression on it")
    
    args = parser.parse_args()
    
    if args.test:
        test_dir = BASE_DIR / "test_run"
        sample_file = test_dir / "sample_source.mp4"
        generate_sample_video(sample_file)
        out_file = test_dir / f"sample_compressed_{args.codec}.mp4"
        compress_video(sample_file, out_file, codec=args.codec, crf=args.crf, preset=args.preset)
        return

    if not args.input:
        print("[!] No input specified. Checking for any videos in current folder...")
        local_videos = [f for f in BASE_DIR.iterdir() if f.is_file() and f.suffix.lower() in VIDEO_EXTENSIONS]
        if local_videos:
            print(f"[+] Found {len(local_videos)} video(s) in current directory:")
            for v in local_videos:
                print(f"    - {v.name}")
            confirm = input("\nDo you want to compress these videos now? (Y/n): ").strip().lower()
            if confirm in ["", "y", "yes"]:
                target_inputs = local_videos
            else:
                return
        else:
            parser.print_help()
            print("\n[TIP] You can also test immediately with: python compress.py --test")
            return
    else:
        in_path = Path(args.input).resolve()
        if not in_path.exists():
            print(f"[!] Path does not exist: {in_path}")
            sys.exit(1)
        if in_path.is_file():
            target_inputs = [in_path]
        else:
            target_inputs = [f for f in in_path.rglob("*") if f.is_file() and f.suffix.lower() in VIDEO_EXTENSIONS]
            if not target_inputs:
                print(f"[!] No supported video files found in: {in_path}")
                sys.exit(0)

    out_dir = Path(args.output).resolve()
    print(f"\n==========================================")
    print(f" Video Compressor Started")
    print(f" Codec: {args.codec.upper()}")
    print(f" Total files to process: {len(target_inputs)}")
    print(f" Output folder: {out_dir}")
    print(f"==========================================")
    
    success_count = 0
    total_orig = 0
    total_new = 0
    
    for f in target_inputs:
        total_orig += f.stat().st_size
        dest_filename = f"{f.stem}_compressed.mp4"
        out_file = out_dir / dest_filename
        
        ok = compress_video(f, out_file, codec=args.codec, crf=args.crf, preset=args.preset)
        if ok:
            success_count += 1
            total_new += out_file.stat().st_size

    print("\n================ SUMMARY ================")
    print(f"Processed: {success_count}/{len(target_inputs)} files successfully.")
    if total_orig > 0:
        saved_bytes = total_orig - total_new
        pct = (saved_bytes / total_orig) * 100 if total_orig > 0 else 0
        print(f"Original total size:   {format_size(total_orig)}")
        print(f"Compressed total size: {format_size(total_new)}")
        print(f"Total space saved:     {format_size(saved_bytes)} ({pct:.1f}% reduction)")
    print("=========================================\n")

if __name__ == "__main__":
    main()
