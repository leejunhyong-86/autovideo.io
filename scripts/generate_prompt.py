"""프롬프트 자동 생성"""
import json
import random
import sys
import os
from pathlib import Path

# #region agent log
try:
    log_data = {
        "sessionId": "debug-session",
        "runId": "run1",
        "hypothesisId": "A",
        "location": "generate_prompt.py:8",
        "message": "Before sys.path modification",
        "data": {
            "cwd": os.getcwd(),
            "sys_path": sys.path[:3],
            "script_path": __file__,
            "script_dir": os.path.dirname(os.path.abspath(__file__))
        },
        "timestamp": int(os.path.getmtime(__file__) * 1000) if os.path.exists(__file__) else 0
    }
    with open(r"c:\practice\autovideo\.cursor\debug.log", "a", encoding="utf-8") as f:
        f.write(json.dumps(log_data, ensure_ascii=False) + "\n")
except: pass
# #endregion

# 프로젝트 루트를 sys.path에 추가
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# #region agent log
try:
    log_data = {
        "sessionId": "debug-session",
        "runId": "run1",
        "hypothesisId": "A",
        "location": "generate_prompt.py:25",
        "message": "After sys.path modification",
        "data": {
            "project_root": project_root,
            "project_root_in_path": project_root in sys.path,
            "sys_path": sys.path[:3]
        },
        "timestamp": int(os.path.getmtime(__file__) * 1000) if os.path.exists(__file__) else 0
    }
    with open(r"c:\practice\autovideo\.cursor\debug.log", "a", encoding="utf-8") as f:
        f.write(json.dumps(log_data, ensure_ascii=False) + "\n")
except: pass
# #endregion

from scripts.utils import get_output_dir, save_metadata, get_env_var, load_metadata

# 주제 템플릿
TOPICS = [
    {
        "topic": "기술 트렌드",
        "image_prompts": [
            "futuristic technology, digital innovation, modern tech",
            "AI artificial intelligence, neural networks, data visualization",
            "smart devices, IoT internet of things, connected world"
        ],
        "script": "기술의 발전은 우리 삶을 변화시키고 있습니다. AI와 IoT가 만나 더 스마트한 세상이 만들어지고 있어요. 미래를 준비하는 지금, 기술과 함께 성장하세요."
    },
    {
        "topic": "건강한 라이프스타일",
        "image_prompts": [
            "healthy lifestyle, fitness, wellness, active living",
            "fresh fruits and vegetables, nutritious food, balanced diet",
            "yoga meditation, mindfulness, mental health, relaxation"
        ],
        "script": "건강한 삶은 하루아침에 만들어지지 않아요. 작은 습관의 변화가 큰 변화를 만듭니다. 오늘부터 시작하는 건강한 라이프스타일, 함께해요."
    },
    {
        "topic": "창의적 아이디어",
        "image_prompts": [
            "creative ideas, innovation, brainstorming, lightbulb concept",
            "artistic expression, colorful design, imagination",
            "problem solving, creative thinking, unique solutions"
        ],
        "script": "창의력은 제한이 없어요. 작은 아이디어가 세상을 바꿀 수 있습니다. 당신의 독특한 생각을 실현해보세요. 창의적인 순간이 기다리고 있어요."
    },
    {
        "topic": "자기계발",
        "image_prompts": [
            "self improvement, personal growth, learning, development",
            "books reading, knowledge, education, wisdom",
            "goal setting, achievement, success, motivation"
        ],
        "script": "자기계발은 투자입니다. 매일 조금씩 배우고 성장하는 당신, 그 모습이 아름다워요. 오늘도 한 걸음 더 나아가는 당신을 응원합니다."
    },
    {
        "topic": "환경 보호",
        "image_prompts": [
            "nature conservation, green energy, sustainability",
            "renewable energy, solar panels, wind turbines, eco friendly",
            "clean environment, recycling, zero waste, planet earth"
        ],
        "script": "지구를 지키는 것은 우리의 책임입니다. 작은 실천이 모여 큰 변화를 만듭니다. 함께 만들어가는 지속가능한 미래, 지금 시작해요."
    }
]


def generate_prompt():
    """프롬프트 자동 생성"""
    # 환경 변수에서 주제 가져오기 (선택사항)
    topic_input = get_env_var("TOPIC", "").strip()
    
    # 주제 선택
    if topic_input:
        # 입력된 주제와 유사한 것 찾기
        selected = next((t for t in TOPICS if topic_input.lower() in t["topic"].lower()), None)
        if not selected:
            selected = random.choice(TOPICS)
    else:
        selected = random.choice(TOPICS)
    
    # 이미지 프롬프트 선택 (3개)
    image_prompts = selected["image_prompts"][:3]
    
    # 스크립트 생성
    script = selected["script"]
    
    # 메타데이터 구성
    metadata = {
        "topic": selected["topic"],
        "image_prompts": image_prompts,
        "script": script,
        "num_images": len(image_prompts)
    }
    
    # 저장
    save_metadata(metadata)
    
    print(f"✅ 프롬프트 생성 완료!")
    print(f"📌 주제: {selected['topic']}")
    print(f"🖼️ 이미지 개수: {len(image_prompts)}")
    print(f"📝 스크립트 길이: {len(script)}자")
    
    return metadata


if __name__ == "__main__":
    generate_prompt()

