"""이미지 생성/다운로드"""
import requests
import os
import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from scripts.utils import get_output_dir, load_metadata, get_env_var, save_metadata

UNSPLASH_ACCESS_KEY = get_env_var("UNSPLASH_ACCESS_KEY", "")


def download_image(url, filepath):
    """이미지 다운로드"""
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    
    with open(filepath, "wb") as f:
        f.write(response.content)
    
    return filepath


def get_image_from_unsplash(query, width=1080, height=1920):
    """Unsplash에서 이미지 가져오기"""
    if not UNSPLASH_ACCESS_KEY:
        # API 키가 없으면 placeholder 이미지 URL 반환
        return f"https://via.placeholder.com/{width}x{height}?text={query.replace(' ', '+')}"
    
    url = "https://api.unsplash.com/photos/random"
    headers = {"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"}
    params = {
        "query": query,
        "orientation": "portrait",
        "w": width,
        "h": height
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data["urls"]["regular"]
    except Exception as e:
        print(f"⚠️ Unsplash API 오류: {e}")
        # Fallback: placeholder 이미지
        return f"https://via.placeholder.com/{width}x{height}?text={query.replace(' ', '+')}"


def generate_images():
    """이미지 생성/다운로드"""
    metadata = load_metadata()
    if not metadata:
        print("❌ 메타데이터를 찾을 수 없습니다. generate_prompt.py를 먼저 실행하세요.")
        return
    
    output_dir = get_output_dir()
    image_prompts = metadata.get("image_prompts", [])
    
    if not image_prompts:
        print("❌ 이미지 프롬프트가 없습니다.")
        return
    
    image_paths = []
    
    print(f"🖼️ {len(image_prompts)}개의 이미지 생성 중...")
    
    for i, prompt in enumerate(image_prompts, 1):
        print(f"  [{i}/{len(image_prompts)}] {prompt[:50]}...")
        
        # Unsplash에서 이미지 가져오기
        image_url = get_image_from_unsplash(prompt)
        
        # 이미지 다운로드
        image_filename = f"image_{i:02d}.jpg"
        image_path = output_dir / image_filename
        
        try:
            download_image(image_url, image_path)
            image_paths.append(str(image_path))
            print(f"  ✅ {image_filename} 저장 완료")
        except Exception as e:
            print(f"  ❌ 이미지 다운로드 실패: {e}")
            # 빈 이미지 파일 생성 (에러 방지)
            image_path.touch()
            image_paths.append(str(image_path))
    
    # 메타데이터 업데이트
    metadata["image_paths"] = image_paths
    save_metadata(metadata)
    
    print(f"✅ 이미지 생성 완료! ({len(image_paths)}개)")
    return image_paths


if __name__ == "__main__":
    generate_images()

