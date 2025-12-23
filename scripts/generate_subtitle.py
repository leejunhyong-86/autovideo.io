"""Whisper를 사용한 자막 생성"""
import os
import sys
import subprocess
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from scripts.utils import get_output_dir, load_metadata, get_env_var, save_metadata

OPENAI_API_KEY = get_env_var("OPENAI_API_KEY", "")


def generate_subtitle_with_whisper_api(video_path, script_text):
    """OpenAI Whisper API를 사용한 자막 생성"""
    if not OPENAI_API_KEY:
        print("⚠️ OpenAI API 키가 없습니다. 스크립트 기반 자막을 생성합니다.")
        return None
    
    try:
        import openai
        openai.api_key = OPENAI_API_KEY
        
        # Whisper API 호출
        with open(video_path, "rb") as video_file:
            transcript = openai.Audio.transcribe(
                model="whisper-1",
                file=video_file,
                language="ko"
            )
        
        return transcript["text"]
    except ImportError:
        print("⚠️ openai 라이브러리가 설치되어 있지 않습니다.")
        return None
    except Exception as e:
        print(f"⚠️ Whisper API 오류: {e}")
        return None


def generate_subtitle_from_script(script_text, duration):
    """스크립트 텍스트를 기반으로 자막 생성 (간단한 타이밍)"""
    output_dir = get_output_dir()
    subtitle_path = output_dir / "subtitle.srt"
    
    # 스크립트를 문장 단위로 분리
    sentences = [s.strip() for s in script_text.replace(".", ".\n").split("\n") if s.strip()]
    
    if not sentences:
        sentences = [script_text]
    
    # 각 문장의 예상 길이 계산 (대략 1초에 3자)
    subtitle_entries = []
    current_time = 0.0
    
    for i, sentence in enumerate(sentences):
        # 문장 길이에 따라 지속 시간 계산
        estimated_duration = max(2.0, len(sentence) / 3.0)
        end_time = min(current_time + estimated_duration, duration)
        
        # SRT 형식으로 변환
        start_str = format_srt_time(current_time)
        end_str = format_srt_time(end_time)
        
        subtitle_entries.append(f"{i + 1}\n{start_str} --> {end_str}\n{sentence}\n\n")
        
        current_time = end_time + 0.5  # 0.5초 간격
    
    # SRT 파일 저장
    with open(subtitle_path, "w", encoding="utf-8") as f:
        f.write("".join(subtitle_entries))
    
    print(f"✅ 자막 생성 완료: {subtitle_path}")
    return str(subtitle_path)


def format_srt_time(seconds):
    """초를 SRT 시간 형식으로 변환 (HH:MM:SS,mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def generate_subtitle():
    """자막 생성"""
    metadata = load_metadata()
    if not metadata:
        print("❌ 메타데이터를 찾을 수 없습니다.")
        return
    
    script_text = metadata.get("script", "")
    video_path = metadata.get("video_path", "")
    duration = metadata.get("video_duration", 15)
    
    if not script_text:
        print("❌ 스크립트가 없습니다.")
        return
    
    subtitle_path = None
    
    # Whisper API 시도 (비디오가 있는 경우)
    if video_path and Path(video_path).exists() and OPENAI_API_KEY:
        print("🎤 Whisper API로 자막 생성 시도...")
        transcript = generate_subtitle_with_whisper_api(video_path, script_text)
        if transcript:
            # Whisper 결과를 사용하여 더 정확한 자막 생성
            subtitle_path = generate_subtitle_from_script(transcript, duration)
    
    # Whisper 실패 시 스크립트 기반 자막 생성
    if not subtitle_path:
        print("📝 스크립트 기반 자막 생성...")
        subtitle_path = generate_subtitle_from_script(script_text, duration)
    
    # 메타데이터 업데이트
    metadata["subtitle_path"] = subtitle_path
    save_metadata(metadata)
    
    return subtitle_path


if __name__ == "__main__":
    result = generate_subtitle()
    if not result:
        print("❌ 자막 생성 실패!")
        sys.exit(1)

