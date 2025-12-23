"""ElevenLabs TTS를 사용한 음성 생성"""
import requests
import os
from pathlib import Path
from scripts.utils import get_output_dir, load_metadata, get_env_var, save_metadata

ELEVENLABS_API_KEY = get_env_var("ELEVENLABS_API_KEY", "")


def generate_audio_with_elevenlabs(text, output_path):
    """ElevenLabs TTS API를 사용한 음성 생성"""
    if not ELEVENLABS_API_KEY:
        print("⚠️ ElevenLabs API 키가 없습니다.")
        return None
    
    url = "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM"  # 기본 한국어 음성 ID
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY
    }
    
    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=60)
        response.raise_for_status()
        
        with open(output_path, "wb") as f:
            f.write(response.content)
        
        print(f"✅ 음성 생성 완료: {output_path}")
        return str(output_path)
    except Exception as e:
        print(f"❌ ElevenLabs API 오류: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   응답: {e.response.text}")
        return None


def generate_audio_fallback(text, output_path):
    """Fallback: gTTS 사용 (완전 무료)"""
    try:
        from gtts import gTTS
        
        tts = gTTS(text=text, lang='ko', slow=False)
        tts.save(str(output_path))
        
        print(f"✅ 음성 생성 완료 (gTTS): {output_path}")
        return str(output_path)
    except ImportError:
        print("⚠️ gTTS가 설치되어 있지 않습니다. requirements.txt에 gTTS를 추가하세요.")
        return None
    except Exception as e:
        print(f"❌ gTTS 오류: {e}")
        return None


def generate_audio():
    """음성 생성"""
    metadata = load_metadata()
    if not metadata:
        print("❌ 메타데이터를 찾을 수 없습니다.")
        return
    
    script_text = metadata.get("script", "")
    if not script_text:
        print("❌ 스크립트가 없습니다.")
        return
    
    output_dir = get_output_dir()
    audio_path = output_dir / "audio.mp3"
    
    print(f"🔊 음성 생성 중... (텍스트 길이: {len(script_text)}자)")
    
    # ElevenLabs 시도
    if ELEVENLABS_API_KEY:
        result = generate_audio_with_elevenlabs(script_text, audio_path)
        if result:
            metadata["audio_path"] = result
            save_metadata(metadata)
            return result
    
    # Fallback: gTTS 사용
    print("  gTTS로 음성 생성 시도...")
    result = generate_audio_fallback(script_text, audio_path)
    if result:
        metadata["audio_path"] = result
        save_metadata(metadata)
        return result
    
    print("❌ 음성 생성 실패")
    return None


if __name__ == "__main__":
    generate_audio()

