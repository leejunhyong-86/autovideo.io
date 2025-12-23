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

# PIL/Pillow import (fallback용)
try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


def download_image(url, filepath):
    """이미지 다운로드"""
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    
    with open(filepath, "wb") as f:
        f.write(response.content)
    
    return filepath


def create_text_image(text, width=1080, height=1920, output_path=None):
    """텍스트 기반 이미지 생성 (fallback)"""
    if not HAS_PIL:
        return None
    
    try:
        # 이미지 생성
        img = Image.new('RGB', (width, height), color=(30, 30, 50))
        draw = ImageDraw.Draw(img)
        
        # 폰트 설정 (기본 폰트 사용)
        font_size = 60
        font = None
        
        # 여러 폰트 경로 시도
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/System/Library/Fonts/Arial.ttf",
        ]
        
        for font_path in font_paths:
            try:
                if os.path.exists(font_path):
                    font = ImageFont.truetype(font_path, font_size)
                    break
            except:
                continue
        
        # 폰트를 찾지 못한 경우 기본 폰트 사용
        if font is None:
            try:
                font = ImageFont.load_default()
                font_size = 20  # 기본 폰트는 작음
            except:
                font = None
        
        # 텍스트 줄바꿈 처리
        words = text.split()
        lines = []
        current_line = []
        max_width = width - 100
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            text_width = bbox[2] - bbox[0]
            
            if text_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        # 텍스트 그리기 (중앙 정렬)
        total_height = len(lines) * 80
        start_y = (height - total_height) // 2
        
        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (width - text_width) // 2
            y = start_y + i * 80
            
            # 그림자 효과
            draw.text((x + 2, y + 2), line, font=font, fill=(0, 0, 0, 180))
            draw.text((x, y), line, font=font, fill=(255, 255, 255))
        
        # 이미지 저장
        if output_path:
            img.save(output_path, 'JPEG', quality=85)
            return str(output_path)
        
        return img
    except Exception as e:
        print(f"  ⚠️ 텍스트 이미지 생성 실패: {e}")
        return None


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
        
        success = False
        try:
            download_image(image_url, image_path)
            # 파일이 제대로 생성되었는지 확인
            if image_path.exists() and image_path.stat().st_size > 0:
                image_paths.append(str(image_path))
                print(f"  ✅ {image_filename} 저장 완료")
                success = True
        except Exception as e:
            print(f"  ⚠️ 이미지 다운로드 실패: {e}")
        
        # 다운로드 실패 시 텍스트 기반 이미지 생성 (fallback)
        if not success:
            print(f"  🔄 텍스트 기반 이미지 생성 시도...")
            result = create_text_image(prompt, width=1080, height=1920, output_path=image_path)
            if result:
                image_paths.append(str(image_path))
                print(f"  ✅ {image_filename} 생성 완료 (텍스트 기반)")
            else:
                print(f"  ❌ 이미지 생성 실패, 빈 파일 생성")
                # 최후의 수단: 빈 파일이라도 생성 (에러 방지)
                image_path.touch()
                image_paths.append(str(image_path))
    
    # 메타데이터 업데이트
    metadata["image_paths"] = image_paths
    save_metadata(metadata)
    
    print(f"✅ 이미지 생성 완료! ({len(image_paths)}개)")
    return image_paths


if __name__ == "__main__":
    generate_images()

