"""
Bannerbear 템플릿 정보 확인 스크립트
"""
from src.ai.bannerbear_generator import BannerbearGenerator
import json

generator = BannerbearGenerator()

print("=" * 60)
print("Bannerbear 템플릿 정보 확인")
print("=" * 60)

template_info = generator.get_template_info()

if template_info:
    print(f"\n템플릿 이름: {template_info.get('name')}")
    print(f"템플릿 ID: {template_info.get('uid')}")
    print(f"\n사용 가능한 레이어:")
    print("-" * 60)
    
    # 레이어 정보 출력
    if 'available_modifications' in template_info:
        for mod in template_info['available_modifications']:
            print(f"  - 이름: {mod.get('name')}")
            print(f"    타입: {mod.get('type')}")
            if mod.get('type') == 'text':
                print(f"    샘플: {mod.get('text', 'N/A')}")
            print()
    
    print("\n전체 템플릿 정보 (JSON):")
    print("-" * 60)
    print(json.dumps(template_info, indent=2, ensure_ascii=False))
else:
    print("템플릿 정보를 가져올 수 없습니다.")
    print("API 키와 템플릿 ID를 확인하세요.")
