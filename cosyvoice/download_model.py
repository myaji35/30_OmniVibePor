"""CosyVoice2 모델 다운로드 스크립트"""
import os
from huggingface_hub import snapshot_download

MODEL_DIR = os.environ.get("MODEL_DIR", "pretrained_models/CosyVoice2-0.5B")

if not os.path.exists(MODEL_DIR):
    print(f"Downloading CosyVoice2-0.5B to {MODEL_DIR}...")
    snapshot_download(
        "FunAudioLLM/CosyVoice2-0.5B",
        local_dir=MODEL_DIR,
    )
    print("Download complete!")
else:
    print(f"Model already exists at {MODEL_DIR}")
