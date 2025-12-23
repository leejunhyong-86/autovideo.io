"""FFmpeg를 사용한 최종 영상 편집"""
import subprocess
import sys
import os
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from scripts.utils import get_output_dir, load_metadata

VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920


def add_subtitle_to_video(video_path, subtitle_path, output_path):
    """영상에 자막 추가"""
    if not Path(subtitle_path).exists():
        print("⚠️ 자막 파일이 없습니다. 자막 없이 진행합니다.")
        return video_path
    
    # 자막 스타일 설정
    subtitle_style = (
        "FontName=Malgun Gothic,"
        "FontSize=24,"
        "PrimaryColour=&Hffffff,"
        "OutlineColour=&H000000,"
        "Outline=2,"
        "Shadow=1,"
        "Alignment=2,"  # 하단 중앙
        "MarginV=100"
    )
    
    cmd = [
        "ffmpeg",
        "-y",
        "-i", video_path,
        "-vf", f"subtitles={subtitle_path}:force_style='{subtitle_style}'",
        "-c:v", "libx264",
        "-c:a", "copy",
        str(output_path)
    ]
    
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"✅ 자막 추가 완료: {output_path}")
        return str(output_path)
    except subprocess.CalledProcessError as e:
        print(f"⚠️ 자막 추가 실패: {e.stderr}")
        return video_path
    except FileNotFoundError:
        print("❌ FFmpeg가 설치되어 있지 않습니다.")
        return video_path


def add_audio_to_video(video_path, audio_path, output_path):
    """영상에 음성 추가"""
    if not Path(audio_path).exists():
        print("⚠️ 오디오 파일이 없습니다. 음성 없이 진행합니다.")
        return video_path
    
    # 오디오 길이에 맞춰 영상 길이 조정
    cmd = [
        "ffmpeg",
        "-y",
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",  # 짧은 쪽에 맞춤
        "-map", "0:v:0",
        "-map", "1:a:0",
        str(output_path)
    ]
    
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"✅ 음성 추가 완료: {output_path}")
        return str(output_path)
    except subprocess.CalledProcessError as e:
        print(f"⚠️ 음성 추가 실패: {e.stderr}")
        return video_path
    except FileNotFoundError:
        print("❌ FFmpeg가 설치되어 있지 않습니다.")
        return video_path


def edit_video():
    """최종 영상 편집"""
    metadata = load_metadata()
    if not metadata:
        print("❌ 메타데이터를 찾을 수 없습니다.")
        return
    
    video_path = metadata.get("video_path", "")
    subtitle_path = metadata.get("subtitle_path", "")
    audio_path = metadata.get("audio_path", "")
    
    if not video_path or not Path(video_path).exists():
        print("❌ 원본 영상 파일을 찾을 수 없습니다.")
        return
    
    output_dir = get_output_dir()
    
    # 1단계: 자막 추가
    video_with_subtitle = output_dir / "video_with_subtitle.mp4"
    if subtitle_path:
        current_video = add_subtitle_to_video(video_path, subtitle_path, video_with_subtitle)
    else:
        current_video = video_path
    
    # 2단계: 음성 추가
    final_video = output_dir / "final_shorts.mp4"
    if audio_path:
        final_path = add_audio_to_video(current_video, audio_path, final_video)
    else:
        # 음성이 없으면 자막만 있는 영상을 복사
        import shutil
        shutil.copy(current_video, final_video)
        final_path = str(final_video)
    
    # 메타데이터 업데이트
    metadata["final_video_path"] = final_path
    save_metadata(metadata)
    
    print(f"\n🎉 최종 영상 생성 완료!")
    print(f"📁 파일 위치: {final_path}")
    
    return final_path


if __name__ == "__main__":
    edit_video()

