"""FFmpeg를 사용한 영상 생성"""
import subprocess
from pathlib import Path
from scripts.utils import get_output_dir, load_metadata

# 숏츠 설정
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
FPS = 30
IMAGE_DURATION = 3  # 각 이미지당 3초


def create_video_from_images():
    """이미지 슬라이드쇼 영상 생성"""
    metadata = load_metadata()
    if not metadata:
        print("❌ 메타데이터를 찾을 수 없습니다.")
        return
    
    image_paths = metadata.get("image_paths", [])
    if not image_paths:
        print("❌ 이미지 경로를 찾을 수 없습니다.")
        return
    
    output_dir = get_output_dir()
    video_path = output_dir / "video_raw.mp4"
    
    # 이미지 경로 확인
    valid_images = []
    for img_path in image_paths:
        path = Path(img_path)
        if path.exists() and path.stat().st_size > 0:
            valid_images.append(str(path.absolute()))
    
    if not valid_images:
        print("❌ 유효한 이미지가 없습니다.")
        return
    
    print(f"🎬 영상 생성 중... ({len(valid_images)}개 이미지)")
    
    # FFmpeg 명령어 구성 - 더 간단하고 안정적인 방법
    inputs = []
    filter_parts = []
    
    # 각 이미지를 입력으로 추가하고 크기 조정
    for i, img_path in enumerate(valid_images):
        inputs.extend(["-loop", "1", "-t", str(IMAGE_DURATION), "-i", img_path])
        filter_parts.append(
            f"[{i}:v]scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=decrease,"
            f"pad={VIDEO_WIDTH}:{VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={FPS}[v{i}]"
        )
    
    # 이미지들을 연결
    if len(valid_images) == 1:
        filter_complex = filter_parts[0].replace("[v0]", "[0:v]").replace("[vout]", "[vout]")
        if "[vout]" not in filter_complex:
            filter_complex += "[vout]"
    else:
        scale_filters = ";".join(filter_parts)
        concat_inputs = "".join([f"[v{i}]" for i in range(len(valid_images))])
        filter_complex = f"{scale_filters};{concat_inputs}concat=n={len(valid_images)}:v=1:a=0[vout]"
    
    # FFmpeg 명령어 실행
    cmd = [
        "ffmpeg",
        "-y",  # 덮어쓰기
        *inputs,
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-pix_fmt", "yuv420p",
        str(video_path)
    ]
    
    try:
        print("  FFmpeg 실행 중...")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        print(f"✅ 영상 생성 완료: {video_path}")
        
        # 메타데이터 업데이트
        metadata["video_path"] = str(video_path)
        metadata["video_duration"] = len(valid_images) * IMAGE_DURATION
        from scripts.utils import save_metadata
        save_metadata(metadata)
        
        return str(video_path)
    except subprocess.CalledProcessError as e:
        print(f"❌ FFmpeg 오류: {e.stderr}")
        return None
    except FileNotFoundError:
        print("❌ FFmpeg가 설치되어 있지 않습니다.")
        return None


if __name__ == "__main__":
    create_video_from_images()

