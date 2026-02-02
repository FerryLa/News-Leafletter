from app.super_controller import super_controller

config = super_controller.get_clustering_config()
print("클러스터링 설정:")
print(f"  enabled: {config.get('enabled')}")
print(f"  similarity_threshold: {config.get('similarity_threshold')}")

# config.json 직접 확인
import json
with open('data/config.json', 'r', encoding='utf-8') as f:
    cfg = json.load(f)
    print(f"\nconfig.json 클러스터링:")
    print(f"  enabled: {cfg['clustering']['enabled']}")
