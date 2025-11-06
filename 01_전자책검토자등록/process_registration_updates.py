"""
process_registration 함수 내 검증 결과 통합 부분 수정

[개발중] 전자책자동등록.py 파일의 process_registration 함수에서 검토자 추가 결과 처리 부분을 
다음과 같이 수정하세요.
"""

# process_registration 함수 내 다음 부분을 찾아서 (약 1200번째 줄 근처):

# 검토자 추가
if self.add_reviewer(email):
    result = {
        'name': name,
        'book_title': book_title,
        'book_code': book_code,
        'isbn': isbn,
        'publisher': publisher,
        'email': email,
        'status': 'SUCCESS',
        'error': None
    }
    self.logger.info(f"✅ [{idx+1}/{reviewer_count}] 검토자 '{name}' (이메일: {email}) 등록 성공")
else:
    self.logger.warning(f"❌ [{idx+1}/{reviewer_count}] 검토자 '{name}' (이메일: {email}) 등록 실패")
    
    # 실패시 다음 검토자를 위해 현재 페이지 상태 초기화
    self.current_review_page = None
    
    result = {
        'name': name,
        'book_title': book_title,
        'book_code': book_code,
        'isbn': isbn,
        'publisher': publisher,
        'email': email,
        'status': 'FAILED',
        'error': f'검토자 추가 실패 (이메일: {email})'
    }

# 위 부분을 아래 코드로 대체:

# 검토자 추가
add_result = self.add_reviewer(email)

if add_result:
    result = {
        'name': name,
        'book_title': book_title,
        'book_code': book_code,
        'isbn': isbn,
        'publisher': publisher,
        'email': email,
        'status': 'SUCCESS',
        'error': None,
        'verified': True  # 검증 상태 추가
    }
    self.logger.info(f"✅ [{idx+1}/{reviewer_count}] 검토자 '{name}' (이메일: {email}) 등록 성공")
else:
    self.logger.warning(f"❌ [{idx+1}/{reviewer_count}] 검토자 '{name}' (이메일: {email}) 등록 실패")
    
    # 실패시 다음 검토자를 위해 현재 페이지 상태 초기화
    self.current_review_page = None
    
    result = {
        'name': name,
        'book_title': book_title,
        'book_code': book_code,
        'isbn': isbn,
        'publisher': publisher,
        'email': email,
        'status': 'FAILED',
        'error': f'검토자 추가 실패 (이메일: {email})',
        'verified': False  # 검증 상태 추가
    }

# 그리고 결과 요약 부분 (약 1300번째 줄 근처)에 다음 내용을 추가:

# 결과 요약
success_count = len([r for r in self.registration_results if r['status'] == 'SUCCESS'])
failed_count = len([r for r in self.registration_results if r['status'] == 'FAILED'])

# 검증 상태에 따른 요약 추가 (새로운 코드)
verified_count = len([r for r in self.registration_results if r.get('verified', False)])
not_verified_count = len([r for r in self.registration_results if r.get('status') == 'SUCCESS' and not r.get('verified', True)])

self.logger.info(f"등록 완료 - 성공: {success_count}, 실패: {failed_count}")
# 검증 요약 로그 추가 (새로운 코드)
if not_verified_count > 0:
    self.logger.warning(f"⚠️ 주의: {not_verified_count}개의 등록이 성공했지만 확인되지 않았습니다. 검토가 필요합니다.")
