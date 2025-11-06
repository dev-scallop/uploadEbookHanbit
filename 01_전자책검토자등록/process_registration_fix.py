"""
process_registration 함수 수정본
이 함수를 [개발중] 전자책자동등록.py 파일에 있는 동일한 함수와 교체하세요.
"""

def process_registration(self, data_df, progress_callback=None):
    """전체 등록 프로세스 실행"""
    try:
        self.registration_results = []
        
        # 이미 도서 데이터베이스가 로드되어 있는지 확인
        if not hasattr(self, 'book_database') or not self.book_database:
            # 도서 데이터베이스 로드
            self.logger.info("도서 데이터베이스 로드 시작...")
            if progress_callback:
                progress_callback(0, len(data_df), "도서 데이터베이스 로드 중...")
                
            if not self.load_book_database():
                error_msg = "도서 데이터베이스 로드 실패 - 인터넷 연결을 확인하고 스프레드시트 접근 권한을 확인하세요."
                self.logger.error(error_msg)
                raise Exception(error_msg)
        
        # 드라이버 설정
        self.logger.info("웹 드라이버 설정 시작...")
        if progress_callback:
            progress_callback(0, len(data_df), "웹 드라이버 설정 중...")
            
        if not self.setup_driver():
            error_msg = "드라이버 설정 실패 - 크롬 브라우저가 설치되어 있고 최신 버전인지 확인하세요.\n" \
                       "config.py 파일에서 CHROME_DRIVER_PATH를 직접 지정해보세요."
            self.logger.error(error_msg)
            raise Exception(error_msg)
        
        # 로그인
        self.logger.info("Google 로그인 시도...")
        if progress_callback:
            progress_callback(0, len(data_df), "Google 로그인 중...")
            
        if not self.login_to_google():
            error_msg = "Google 로그인 실패 - 인터넷 연결과 계정 정보를 확인하세요"
            self.logger.error(error_msg)
            raise Exception(error_msg)
        
        total_count = len(data_df)
        
        # 출판사별, 도서코드별로 데이터 그룹화
        grouped_data = {}
        
        # 데이터 프레임을 그룹화하기 위한 처리
        for index, row in data_df.iterrows():
            try:
                book_code = str(row.get('도서코드', 'N/A')).strip()
                
                # 도서 데이터베이스에서 도서 정보 확인
                book_info = self.get_book_info_by_code(book_code)
                
                if book_info:
                    publisher = book_info.get('publisher', 'unknown')
                    
                    # 출판사별로 먼저 분류
                    if publisher not in grouped_data:
                        grouped_data[publisher] = {}
                    
                    # 도서코드별로 검토자 정보 그룹화
                    if book_code not in grouped_data[publisher]:
                        grouped_data[publisher][book_code] = {
                            'book_info': book_info,
                            'reviewers': []
                        }
                    
                    # 검토자 정보 추가
                    grouped_data[publisher][book_code]['reviewers'].append({
                        'name': row['이름'],
                        'email': row['지메일'],
                        'index': index
                    })
                else:
                    self.logger.warning(f"도서코드 '{book_code}'를 데이터베이스에서 찾을 수 없습니다.")
                    result = {
                        'name': row['이름'],
                        'book_title': row.get('도서명', 'Unknown'),
                        'book_code': book_code,
                        'email': row['지메일'],
                        'status': 'FAILED',
                        'error': f'도서코드 {book_code}를 데이터베이스에서 찾을 수 없음'
                    }
                    self.registration_results.append(result)
            except Exception as e:
                self.logger.error(f"행 {index + 1} 처리 중 오류 발생: {str(e)}")
                result = {
                    'name': row.get('이름', 'Unknown'),
                    'book_title': row.get('도서명', 'Unknown'),
                    'book_code': row.get('도서코드', 'N/A'),
                    'email': row.get('지메일', 'Unknown'),
                    'status': 'FAILED',
                    'error': str(e)
                }
                self.registration_results.append(result)
        
        # 출판사별로 처리
        processed_count = 0
        for publisher, books in grouped_data.items():
            self.logger.info(f"====== 출판사 '{publisher}' 처리 시작 ======")
            
            # 도서별로 처리
            for book_code, book_data in books.items():
                try:
                    book_info = book_data['book_info']
                    reviewers = book_data['reviewers']
                    book_title = book_info.get('title', 'Unknown')
                    isbn = book_info.get('isbn', 'N/A')
                    
                    self.logger.info(f"도서 '{book_title}' (코드: {book_code}, ISBN: {isbn}) 처리 시작")
                    self.logger.info(f"검토자 {len(reviewers)}명 등록 예정")
                    
                    # 진행률 업데이트
                    if progress_callback:
                        progress_callback(processed_count, total_count, f"처리 중: {book_title} (코드: {book_code})")
                    
                    # 한 번만 도서 검색 (이전 방문 정보 저장)
                    if book_code == self.last_visited_book:
                        self.logger.info(f"이미 방문한 도서 (코드: {book_code})입니다. 재검색 건너뜁니다.")
                    else:
                        # 도서 검색
                        if not self.search_book(book_code):
                            self.logger.warning(f"도서 검색 실패 - 도서코드 {book_code}")
                            
                            # 모든 검토자에 대해 실패 처리
                            for reviewer in reviewers:
                                result = {
                                    'name': reviewer['name'],
                                    'book_title': book_title,
                                    'book_code': book_code,
                                    'isbn': isbn,
                                    'publisher': publisher,
                                    'email': reviewer['email'],
                                    'status': 'FAILED',
                                    'error': f'도서 검색 실패 (도서코드: {book_code})'
                                }
                                self.registration_results.append(result)
                                processed_count += 1
                            continue
                        
                        # 성공 시 마지막 방문 도서 저장
                        self.last_visited_book = book_code
                    
                    # 검토자 수 파악
                    reviewer_count = len(reviewers)
                    self.logger.info(f"총 {reviewer_count}명의 검토자를 일괄 등록합니다")
                    
                    # 검색 성공 시 모든 검토자를 한 번에 등록
                    for idx, reviewer in enumerate(reviewers):
                        try:
                            email = reviewer['email']
                            name = reviewer['name']
                            
                            self.logger.info(f"[{idx+1}/{reviewer_count}] 검토자 '{name}' (이메일: {email}) 등록 시도 중...")
                            
                            # 검토자 추가 전 상태 저장
                            if idx == 0:
                                # 첫 번째 검토자는 새로운 페이지로 이동
                                self.current_review_page = None
                            
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
                            
                            self.registration_results.append(result)
                            processed_count += 1
                            
                            # 마지막 검토자가 아닌 경우에만 요청 간격 조정
                            if idx < reviewer_count - 1:
                                # 같은 도서의 연속 검토자 등록 간 간격은 짧게 설정
                                time.sleep(0.5)
                        
                        except Exception as e:
                            self.logger.error(f"검토자 '{reviewer['email']}' 등록 중 오류 발생: {str(e)}")
                            
                            # 오류 발생 시 현재 페이지 상태 초기화
                            self.current_review_page = None
                            
                            result = {
                                'name': reviewer['name'],
                                'book_title': book_title,
                                'book_code': book_code,
                                'isbn': isbn,
                                'publisher': publisher,
                                'email': reviewer['email'],
                                'status': 'FAILED',
                                'error': f'처리 중 오류: {str(e)}'
                            }
                            self.registration_results.append(result)
                            processed_count += 1
                    
                    # 도서별 처리 완료 후 간격 조정
                    time.sleep(2)
                
                except Exception as e:
                    self.logger.error(f"도서코드 '{book_code}' 처리 중 오류 발생: {str(e)}")
                    for reviewer in book_data['reviewers']:
                        result = {
                            'name': reviewer['name'],
                            'book_title': book_info.get('title', 'Unknown'),
                            'book_code': book_code,
                            'email': reviewer['email'],
                            'status': 'FAILED',
                            'error': f'도서 처리 중 오류: {str(e)}'
                        }
                        self.registration_results.append(result)
                        processed_count += 1
        
        # 결과 요약
        success_count = len([r for r in self.registration_results if r['status'] == 'SUCCESS'])
        failed_count = len([r for r in self.registration_results if r['status'] == 'FAILED'])
        
        self.logger.info(f"등록 완료 - 성공: {success_count}, 실패: {failed_count}")
        
        # 출판사별 요약
        publisher_summary = {}
        for result in self.registration_results:
            publisher = result.get('publisher', 'unknown')
            if publisher not in publisher_summary:
                publisher_summary[publisher] = {
                    'total': 0,
                    'success': 0,
                    'failed': 0,
                    'books': {}
                }
            
            publisher_summary[publisher]['total'] += 1
            if result['status'] == 'SUCCESS':
                publisher_summary[publisher]['success'] += 1
            else:
                publisher_summary[publisher]['failed'] += 1
            
            # 도서별 요약 정보
            book_code = result.get('book_code', 'unknown')
            book_title = result.get('book_title', 'unknown')
            
            if book_code not in publisher_summary[publisher]['books']:
                publisher_summary[publisher]['books'][book_code] = {
                    'title': book_title,
                    'total': 0,
                    'success': 0,
                    'failed': 0
                }
            
            publisher_summary[publisher]['books'][book_code]['total'] += 1
            if result['status'] == 'SUCCESS':
                publisher_summary[publisher]['books'][book_code]['success'] += 1
            else:
                publisher_summary[publisher]['books'][book_code]['failed'] += 1
        
        # 요약 정보 로깅
        self.logger.info("===== 출판사별 등록 결과 요약 =====")
        for publisher, stats in publisher_summary.items():
            self.logger.info(f"출판사: {publisher} - 총 {stats['total']}건 (성공: {stats['success']}, 실패: {stats['failed']})")
            
            # 상세 도서별 정보는 로그에만 기록
            self.logger.info(f"  도서별 등록 결과:")
            for book_code, book_stats in stats['books'].items():
                self.logger.info(f"  - {book_stats['title']} (코드: {book_code}): 총 {book_stats['total']}건 (성공: {book_stats['success']}, 실패: {book_stats['failed']})")
        
        self.logger.info("===================================")
        
        return self.registration_results
        
    except Exception as e:
        self.logger.error(f"등록 프로세스 실패: {str(e)}")
        raise
    finally:
        if self.driver:
            try:
                # 브라우저를 완전히 닫지 않고 세션 유지
                # self.driver.quit()
                pass
            except:
                pass
