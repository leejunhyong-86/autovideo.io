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
    print(f"✅ PIL/Pillow 로드 성공")
except ImportError as e:
    HAS_PIL = False
    print(f"❌ PIL/Pillow 로드 실패: {e}")


def download_image(url, filepath):
    """이미지 다운로드"""
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    
    with open(filepath, "wb") as f:
        f.write(response.content)
    
    return filepath


def create_image_with_ffmpeg(text, width=1080, height=1920, output_path=None):
    """FFmpeg를 사용한 이미지 생성 (가장 안정적인 fallback)"""
    import subprocess
    
    if not output_path:
        return None
    
    output_path_str = str(output_path)
    
    # 텍스트를 줄여서 표시 (FFmpeg drawtext 제한)
    short_text = text[:50].replace("'", "").replace('"', '').replace(':', ' ')
    
    try:
        # FFmpeg로 단색 배경 + 텍스트 이미지 생성
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"color=c=#1e1e32:s={width}x{height}:d=1",
            "-vframes", "1",
            "-vf", f"drawtext=text='{short_text}':fontsize=48:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2",
            output_path_str
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0 and os.path.exists(output_path_str) and os.path.getsize(output_path_str) > 0:
            print(f"  [DEBUG] FFmpeg 이미지 생성 성공: {output_path_str}")
            return output_path_str
        else:
            print(f"  [DEBUG] FFmpeg 이미지 생성 실패: {result.stderr}")
            
            # drawtext 없이 단색 이미지만 생성 시도
            cmd_simple = [
                "ffmpeg", "-y",
                "-f", "lavfi",
                "-i", f"color=c=#1e1e32:s={width}x{height}:d=1",
                "-vframes", "1",
                output_path_str
            ]
            result2 = subprocess.run(cmd_simple, capture_output=True, text=True, timeout=30)
            
            if result2.returncode == 0 and os.path.exists(output_path_str) and os.path.getsize(output_path_str) > 0:
                print(f"  [DEBUG] FFmpeg 단색 이미지 생성 성공: {output_path_str}")
                return output_path_str
            
    except Exception as e:
        print(f"  [DEBUG] FFmpeg 이미지 생성 오류: {e}")
    
    return None


def create_text_image(text, width=1080, height=1920, output_path=None):
    """텍스트 기반 이미지 생성 (PIL fallback)"""
    print(f"  [DEBUG] create_text_image 호출됨, HAS_PIL={HAS_PIL}")
    
    if not HAS_PIL:
        print(f"  [DEBUG] PIL 없음, FFmpeg fallback 시도")
        return create_image_with_ffmpeg(text, width, height, output_path)
    
    try:
        # 이미지 생성
        print(f"  [DEBUG] 이미지 객체 생성 중...")
        img = Image.new('RGB', (width, height), color=(30, 30, 50))
        draw = ImageDraw.Draw(img)
        print(f"  [DEBUG] 이미지 객체 생성 완료")
        
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
        
        print(f"  [DEBUG] 폰트 검색 시작...")
        for font_path in font_paths:
            try:
                if os.path.exists(font_path):
                    font = ImageFont.truetype(font_path, font_size)
                    print(f"  [DEBUG] 폰트 발견: {font_path}")
                    break
            except Exception as fe:
                print(f"  [DEBUG] 폰트 로드 실패 {font_path}: {fe}")
                continue
        
        # 폰트를 찾지 못한 경우 기본 폰트 사용
        if font is None:
            print(f"  [DEBUG] 시스템 폰트 없음, 기본 폰트 사용")
            try:
                font = ImageFont.load_default()
                font_size = 20  # 기본 폰트는 작음
                print(f"  [DEBUG] 기본 폰트 로드 성공")
            except Exception as de:
                print(f"  [DEBUG] 기본 폰트 로드 실패: {de}")
                font = None
        
        # 폰트가 여전히 없으면 단순 이미지만 저장
        if font is None:
            print(f"  [DEBUG] 폰트 없이 단색 이미지 저장")
            if output_path:
                img.save(output_path, 'JPEG', quality=85)
                print(f"  [DEBUG] 단색 이미지 저장 완료: {output_path}")
                return str(output_path)
            return img
        
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
        
        print(f"  [DEBUG] 텍스트 라인 수: {len(lines)}")
        
        # 텍스트 그리기 (중앙 정렬)
        total_height = len(lines) * 80
        start_y = (height - total_height) // 2
        
        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (width - text_width) // 2
            y = start_y + i * 80
            
            # 그림자 효과
            draw.text((x + 2, y + 2), line, font=font, fill=(0, 0, 0))
            draw.text((x, y), line, font=font, fill=(255, 255, 255))
        
        # 이미지 저장
        if output_path:
            output_path_str = str(output_path)
            print(f"  [DEBUG] 이미지 저장 시도: {output_path_str}")
            img.save(output_path_str, 'JPEG', quality=85)
            print(f"  [DEBUG] 이미지 저장 완료: {output_path_str}")
            # 저장 후 파일 확인
            if os.path.exists(output_path_str):
                file_size = os.path.getsize(output_path_str)
                print(f"  [DEBUG] 저장된 파일 크기: {file_size} bytes")
            else:
                print(f"  [DEBUG] 저장 후 파일이 존재하지 않음!")
            return output_path_str
        
        return img
    except Exception as e:
        import traceback
        print(f"  ⚠️ 텍스트 이미지 생성 실패: {e}")
        print(f"  [DEBUG] 상세 오류: {traceback.format_exc()}")
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
            print(f"  🔄 Fallback 이미지 생성 시도...")
            
            # 1차 시도: FFmpeg로 이미지 생성 (가장 안정적)
            result = create_image_with_ffmpeg(prompt, width=1080, height=1920, output_path=str(image_path))
            
            # 2차 시도: PIL로 이미지 생성
            if not result:
                print(f"  🔄 PIL 이미지 생성 시도...")
                result = create_text_image(prompt, width=1080, height=1920, output_path=str(image_path))
            
            if result and os.path.exists(result) and os.path.getsize(result) > 0:
                image_paths.append(str(image_path))
                print(f"  ✅ {image_filename} 생성 완료 (fallback)")
            else:
                print(f"  ❌ 이미지 생성 완전 실패")
                # 빈 파일은 생성하지 않음 - 유효한 이미지만 추가
    
    # 메타데이터 업데이트
    metadata["image_paths"] = image_paths
    save_metadata(metadata)
    
    print(f"✅ 이미지 생성 완료! ({len(image_paths)}개)")
    return image_paths


if __name__ == "__main__":
    result = generate_images()
    if not result or len(result) == 0:
        print("❌ 이미지 생성 실패!")
        sys.exit(1)
    
    # 유효한 이미지가 있는지 확인
    valid_count = 0
    for path in result:
        if os.path.exists(path) and os.path.getsize(path) > 0:
            valid_count += 1
    
    if valid_count == 0:
        print("❌ 유효한 이미지가 없습니다!")
        sys.exit(1)
    
    print(f"✅ {valid_count}개의 유효한 이미지 생성 완료")

