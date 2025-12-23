"""공통 유틸리티 함수"""
import os
import json
import yaml
from pathlib import Path


def get_output_dir():
    """출력 디렉토리 경로 반환"""
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    return output_dir


def load_config():
    """설정 파일 로드"""
    config_path = Path("config.yaml")
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}


def save_metadata(data, filename="metadata.json"):
    """메타데이터 저장"""
    output_dir = get_output_dir()
    metadata_path = output_dir / filename
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_metadata(filename="metadata.json"):
    """메타데이터 로드"""
    output_dir = get_output_dir()
    metadata_path = output_dir / filename
    if metadata_path.exists():
        with open(metadata_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def get_env_var(key, default=None):
    """환경 변수 가져오기"""
    return os.getenv(key, default)

