"""
Placid 템플릿 정보 확인 스크립트
"""
from src.ai.placid_generator import PlacidGenerator
import json

generator = PlacidGenerator()

print("=" * 60)
print("Placid 템플릿 정보 확인")
print("=" * 60)

# 템플릿 목록 조회
print("\n사용 가능한 템플릿 목록:")
print("-" * 60)
templates = generator.list_templates()

try:
    # 방어적 처리: 응답 형태가 list/dict/str 모두 가능
    if templates:
        if isinstance(templates, dict):
            # 일반적으로 { data: [...] } 또는 { templates: [...] } 형태일 수 있음
            templates_list = templates.get('data') or templates.get('templates') or []
            if not templates_list:
                # 혹시 단일 템플릿 딕셔너리일 수 있음
                templates_list = [templates]
        elif isinstance(templates, list):
            templates_list = templates
        else:
            # 문자열 등 알 수 없는 형태는 그대로 출력하고 종료
            print(f"원시 응답: {templates}")
            templates_list = []

        if templates_list:
            for i, template in enumerate(templates_list, 1):
                if isinstance(template, dict):
                    name = template.get('name') or template.get('title')
                    tid = template.get('id') or template.get('uuid')
                    print(f"{i}. {name}")
                    print(f"   ID: {tid}")
                    # 키가 다를 수 있어 생성일은 존재할 때만 출력
                    created = template.get('created_at') or template.get('createdAt')
                    if created:
                        print(f"   생성일: {created}")
                    print()
                else:
                    print(f"{i}. {template}")
        else:
            print("템플릿이 없거나 조회할 수 없습니다.")
            print("API 토큰 또는 권한을 확인하세요.")
    else:
        print("템플릿이 없거나 조회할 수 없습니다.")
        print("API 토큰 또는 권한을 확인하세요.")
except Exception as e:
    print(f"템플릿 목록 파싱 중 오류: {e}")
    print(f"원시 응답: {templates}")

# 특정 템플릿 상세 정보
if generator.template_id and generator.template_id != "your_placid_template_id_here":
    print("\n현재 템플릿 상세 정보:")
    print("-" * 60)
    
    template_info = generator.get_template_info()
    
    if template_info:
        name = template_info.get('name') or template_info.get('title')
        tid = template_info.get('id') or template_info.get('uuid')
        print(f"\n템플릿 이름: {name}")
        print(f"템플릿 ID: {tid}")
        print(f"\n사용 가능한 레이어:")
        print("-" * 60)
        
        # 레이어 정보 출력
        if 'layers' in template_info:
            for layer in template_info['layers']:
                print(f"  - 이름: {layer.get('name')}")
                print(f"    타입: {layer.get('type')}")
                print()
        
        print("\n전체 템플릿 정보 (JSON):")
        print("-" * 60)
        print(json.dumps(template_info, indent=2, ensure_ascii=False))
    else:
        print("템플릿 정보를 가져올 수 없습니다.")
        print("템플릿 ID를 확인하세요.")
