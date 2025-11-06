"""
전자책 검토자 자동 등록 시스템
Google Partners Center에서 전자책 검토자를 자동으로 등록하는 프로그램

Author: AI Assistant
Date: 2025-09-14
Version: 1.0.0
"""

import logging
import platform
import subprocess
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from config import (
    GOOGLE_PLAY_BOOKS_PARTNER_CENTER, LOGIN_TIMEOUT, ELEMENT_WAIT_TIMEOUT, 
    CHROME_OPTIONS, GOOGLE_SHEET_URL
)

import os
from datetime import datetime
import time
import time
from io import StringIO
import requests
import tkinter as tk
from tkinter import messagebox, filedialog, ttk, scrolledtext, font
import threading
try:
    import korean_utils  # 한글 인코딩 처리를 위한 유틸리티 모듈
except:
    pass

# 설정 파일 import
try:
    from config import *
except ImportError:
    # config.py가 없는 경우 기본 설정 사용
    GOOGLE_PLAY_CONSOLE_BASE_URL = "https://play.google.com/console/"
    LOGIN_TIMEOUT = 300
    ELEMENT_WAIT_TIMEOUT = 15
    REQUEST_DELAY = 2


class EbookReviewerAutoRegister:
    """전자책 검토자 자동 등록 클래스"""
    
    def __init__(self):
        self.setup_logging()
        self.driver = None
        self.is_logged_in = False
        self.registration_results = []
        self.book_database = {}  # 도서 데이터베이스 추가
        self.current_review_page = None  # 현재 리뷰 페이지 상태 추적
        self.last_visited_book = None    # 마지막으로 방문한 책 추적
        
    def setup_logging(self):
        """로깅 설정"""
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        log_filename = f"ebook_registration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        log_filepath = os.path.join(log_dir, log_filename)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_filepath, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info("전자책 검토자 자동 등록 시스템 시작")
    
    def load_book_database(self):
        """구글 스프레드시트에서 도서 데이터베이스 로드"""
        try:
            # 스프레드시트 URL 설정
            if GOOGLE_SHEET_URL:
                spreadsheet_url = GOOGLE_SHEET_URL
            else:
                # 기본값 설정
                spreadsheet_id = "18uXAoTIz07WEBzFgCYC5asaOUkLujYgQtezDsmPWiGY"
                spreadsheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid=0"
            
            self.logger.info(f"구글 스프레드시트에서 도서 데이터베이스 로드 중: {spreadsheet_url}")
            
            # CSV 형태로 구글 스프레드시트 데이터 읽기 (한글 인코딩 자동 처리)
            response = requests.get(spreadsheet_url)
            response.raise_for_status()  # HTTP 오류 발생시 예외 발생
            
            # UTF-8로 강제 변환하여 일관성 유지
            try:
                # 응답 내용을 바이트로 취급하여 UTF-8으로 강제 디코딩
                response_content = response.content
                csv_text = response_content.decode('utf-8', errors='replace')
                book_df = pd.read_csv(StringIO(csv_text))
                row_count = len(book_df)
                
                if row_count == 0:
                    raise ValueError("스프레드시트에 데이터가 없습니다.")
                self.logger.info(f"스프레드시트 로드 성공: {row_count}행 발견")
                
            except requests.exceptions.RequestException as e:
                error_msg = str(e)
                if "404" in error_msg:
                    self.logger.error("스프레드시트를 찾을 수 없습니다. 문서 ID와 공유 설정을 확인하세요.")
                elif "403" in error_msg:
                    self.logger.error("스프레드시트 접근이 거부되었습니다. 공유 설정을 확인하세요.")
                else:
                    self.logger.error(f"스프레드시트 로드 실패: {error_msg}")
                raise
            except pd.errors.EmptyDataError:
                self.logger.error("시트가 비어있습니다.")
                raise
            except Exception as e:
                self.logger.error(f"데이터 처리 중 오류 발생: {str(e)}")
                raise
            
            # 컬럼명 확인 및 표준화
            # 실제 컬럼명 → 표준 한글 컬럼명 매핑
            column_map = {
                'code': '도서코드',
                'title': '도서명',
                'ISBN': 'ISBN',
                'eISBN': 'eISBN',
                'publisher': '출판사',
                'g_title': 'g_title',
                's_isbn': 's_isbn',
            }
            # 컬럼명 변환
            book_df.rename(columns=column_map, inplace=True)
            self.logger.info(f"컬럼명 변환 결과: {list(book_df.columns)}")
            # 컬럼 개수 경고만 남기고, 슬라이싱/재할당은 하지 않음
            expected_columns = ['도서코드', '도서명', 'ISBN', 'eISBN', '출판사', '식별자']
            if len(book_df.columns) != len(expected_columns):
                self.logger.warning(f"스프레드시트 컬럼 개수({len(book_df.columns)})와 기대값({len(expected_columns)})이 다릅니다. 실제 컬럼명: {list(book_df.columns)}")
            
            # 빈 행 제거
            book_df = book_df.dropna(subset=['도서코드', '도서명'])
            
            # 도서코드를 키로 하는 딕셔너리 생성
            self.book_database = {}
            for _, row in book_df.iterrows():
                book_code = str(row['도서코드']).strip()
                isbn_val = row.get('ISBN', '')
                eisbn_val = row.get('eISBN', '')
                publisher_val = row.get('출판사', '')
                # g_title 값을 가져와서 처리 (이제 인코딩 문제는 없음)
                g_title_val = row.get('g_title', '')
                if pd.isna(g_title_val):
                    g_title_val = ''
                else:
                    g_title_val = str(g_title_val).strip()


                # 문자열로 변환 및 공백 제거
                def normalize_isbn(val):
                    try:
                        if pd.isna(val):
                            return ''
                    except Exception:
                        pass
                    if val is None:
                        return ''
                    s = str(val).strip()
                    # 엑셀에서 숫자로 읽혀 '1234567890.0' 형태일 경우 '.0' 제거
                    if s.endswith('.0') and s.replace('.', '', 1).isdigit():
                        s = s[:-2]
                    # 경우에 따라 하이픈 제거
                    s = s.replace('-', '').strip()
                    return s

                isbn_val = normalize_isbn(isbn_val)
                eisbn_val = normalize_isbn(eisbn_val)
                publisher_val = str(publisher_val).strip() if not pd.isna(publisher_val) else ''

                # '식별자' 대신 's_isbn'을 identifier로 사용
                identifier_val = str(row.get('s_isbn', '')).strip() if not pd.isna(row.get('s_isbn', '')) else ''
                self.book_database[book_code] = {
                    'title': row['도서명'],
                    'isbn': isbn_val,
                    'eisbn': eisbn_val,
                    'publisher': publisher_val,
                    'identifier': identifier_val,
                    'g_title': g_title_val
                }
            
            self.logger.info(f"도서 데이터베이스 로드 완료: {len(self.book_database)}개 도서")
            
            # 출판사별 도서 수 확인
            publishers = {}
            for book_info in self.book_database.values():
                pub = book_info['publisher']
                publishers[pub] = publishers.get(pub, 0) + 1
            
            self.logger.info(f"출판사별 도서 수: {publishers}")
            return True
            
        except Exception as e:
            self.logger.error(f"도서 데이터베이스 로드 실패: {str(e)}")
            self.book_database = {}
            return False
    
    def get_book_info_by_code(self, book_code):
        """도서코드로 도서 정보 조회"""
        book_code = str(book_code).strip()
        return self.book_database.get(book_code, None)
    
    def debug_page_elements(self):
        """현재 페이지의 요소들을 디버깅"""
        try:
            self.logger.info("=== 페이지 디버깅 시작 ===")
            
            # 기본 정보
            self.logger.info(f"현재 URL: {self.driver.current_url}")
            self.logger.info(f"페이지 제목: {self.driver.title}")
            
            # 모든 nav 관련 요소 찾기
            try:
                nav_elements = self.driver.find_elements(By.TAG_NAME, "nav")
                self.logger.info(f"nav 태그 개수: {len(nav_elements)}")
                
                for i, nav in enumerate(nav_elements):
                    nav_text = nav.text[:100] if nav.text else "텍스트 없음"
                    self.logger.info(f"nav[{i}]: {nav_text}")
            except Exception as e:
                self.logger.warning(f"nav 요소 검색 실패: {str(e)}")
            
            # mat-nav-list 요소 찾기
            try:
                mat_nav_elements = self.driver.find_elements(By.CSS_SELECTOR, "mat-nav-list")
                self.logger.info(f"mat-nav-list 개수: {len(mat_nav_elements)}")
                
                for i, element in enumerate(mat_nav_elements):
                    links = element.find_elements(By.TAG_NAME, "a")
                    self.logger.info(f"mat-nav-list[{i}]의 링크 개수: {len(links)}")
                    
                    for j, link in enumerate(links):
                        link_text = link.text.strip()
                        link_href = link.get_attribute('href')
                        self.logger.info(f"  링크[{j}]: '{link_text}' - {link_href}")
            except Exception as e:
                self.logger.warning(f"mat-nav-list 검색 실패: {str(e)}")
            
            # ID가 gb인 요소 찾기
            try:
                gb_element = self.driver.find_element(By.ID, "gb")
                self.logger.info("ID='gb' 요소 발견")
                
                # gb 하위의 모든 링크 찾기
                gb_links = gb_element.find_elements(By.TAG_NAME, "a")
                self.logger.info(f"gb 하위 링크 개수: {len(gb_links)}")
                
                for i, link in enumerate(gb_links[:5]):  # 처음 5개만
                    link_text = link.text.strip()
                    link_href = link.get_attribute('href')
                    self.logger.info(f"  gb 링크[{i}]: '{link_text}' - {link_href}")
            except Exception as e:
                self.logger.warning(f"ID='gb' 요소 검색 실패: {str(e)}")
            
            self.logger.info("=== 페이지 디버깅 완료 ===")
            
        except Exception as e:
            self.logger.error(f"페이지 디버깅 실패: {str(e)}")
    
    def read_data_from_source(self, source_path):
        """사용자 지정 엑셀파일에서 데이터(도서코드, 이름, 지메일)를 읽어오고, 
        구글 스프레드시트에서 도서 상세 정보 데이터베이스를 구축함"""
        try:
            # 1. 먼저 사용자가 지정한 엑셀 파일에서 검토자 정보 로드
            if not source_path:
                self.logger.error("엑셀 파일이 지정되지 않았습니다. 파일을 선택해주세요.")
                return None
            
            # 사용자 지정 엑셀파일에서 검토자 정보 읽기
            reviewers_data = self.read_excel_file(source_path)
            
            if reviewers_data is None or reviewers_data.empty:
                self.logger.error("엑셀 파일에서 검토자 정보를 가져오지 못했습니다.")
                return None
                
            # 필수 컬럼 확인 (도서코드, 이름, 지메일)
            required_columns = ['도서코드', '이름', '지메일']
            missing_columns = [col for col in required_columns if col not in reviewers_data.columns]
            if missing_columns:
                self.logger.error(f"필수 컬럼 누락: {missing_columns}")
                return None
            
            # 2. 구글 스프레드시트에서 도서 정보 데이터베이스 구축 (도서코드로 검색 가능하게)
            if GOOGLE_SHEET_URL:
                self.logger.info("구글 스프레드시트에서 도서 정보 데이터베이스를 구축합니다...")
                self.book_database = self.read_google_sheet_csv()
            else:
                self.logger.warning("구글 스프레드시트 URL이 설정되지 않았습니다. 제한된 정보로만 작업을 진행합니다.")
                self.book_database = {}
            
            # 3. 검토자 데이터에 추가 정보 매핑 (표시용)
            self.logger.info("검토자 정보와 도서 데이터베이스 정보를 매핑합니다...")
            for idx, row in reviewers_data.iterrows():
                book_code = str(row['도서코드']).strip()
                if book_code in self.book_database:
                    book_info = self.book_database[book_code]
                    # 도서명 정보 추가
                    if '도서명' in book_info and '도서명' not in reviewers_data.columns:
                        reviewers_data.at[idx, '도서명'] = book_info['도서명']
                    # g_title 정보 추가
                    if 'g_title' in book_info and 'g_title' not in reviewers_data.columns:
                        reviewers_data.at[idx, 'g_title'] = book_info['g_title']
            
            # 콘솔에 검토자 정보 표시
            self.logger.info("\n===== 검토자 정보 =====")
            for idx, row in reviewers_data.head(5).iterrows():  # 처음 5개 행만 표시
                self.logger.info(f"[{idx+1}] 도서코드: {row.get('도서코드', 'N/A')}, 이름: {row.get('이름', '')}, 이메일: {row.get('지메일', '')}")
            if len(reviewers_data) > 5:
                self.logger.info(f"... 외 {len(reviewers_data) - 5}건")
            self.logger.info("=====================\n")
            
            return reviewers_data
            
        except Exception as e:
            self.logger.error(f"데이터 로딩 실패: {str(e)}")
            return None

    def read_google_sheet_csv(self):
        """공개된 Google 스프레드시트 URL(CSV 형식)에서 도서 정보 전체를 가져옴"""
        try:
            self.logger.info(f"Google 스프레드시트 URL에서 도서 정보 데이터베이스 읽기 시도: {GOOGLE_SHEET_URL}")
            
            response = requests.get(GOOGLE_SHEET_URL)
            response.raise_for_status()  # HTTP 오류가 발생하면 예외 발생
            
            # 모든 문자열을 UTF-8로 통일
            # UTF-8로 강제 디코딩 (오류 발생 시 대체 문자 사용)
            csv_data = response.content.decode('utf-8', errors='replace')
            self.logger.info("스프레드시트 데이터를 UTF-8로 디코딩했습니다.")

            # 스프레드시트 데이터를 데이터프레임으로 변환
            books_df = pd.read_csv(StringIO(csv_data))
            
            # 도서코드를 키로 사용하는 도서 정보 데이터베이스 생성
            book_database = {}
            
            # 스프레드시트의 컬럼명 출력
            self.logger.info(f"스프레드시트 컬럼: {list(books_df.columns)}")
            
            # 도서 정보 데이터베이스 구축
            for _, row in books_df.iterrows():
                book_code = str(row.get('도서코드', '')).strip()
                if book_code and book_code != 'nan':
                    book_info = {col: row.get(col, '') for col in books_df.columns}
                    # 결측값 처리
                    for key, value in book_info.items():
                        if pd.isna(value):
                            book_info[key] = ''
                        elif isinstance(value, str):
                            # 한글 인코딩 처리 유틸리티 함수 사용
                            if '%' in value or any(c in value for c in 'ë¥¼íì©íìëë¡ì´ëíë¡ê·¸ëë°'):
                                original = value
                                fixed_value = korean_utils.fix_korean_encoding(value)
                                
                                if fixed_value != original:
                                    self.logger.info(f"'{key}' 필드의 한글 인코딩 수정: '{original}' -> '{fixed_value}'")
                                    book_info[key] = fixed_value
                    
                    # g_title 컬럼이 없으면 도서명으로 설정
                    if 'g_title' not in book_info or not book_info['g_title']:
                        if '도서명' in book_info:
                            book_info['g_title'] = book_info['도서명']
                    
                    book_database[book_code] = book_info
            
            self.logger.info(f"도서 정보 데이터베이스 구축 완료: 총 {len(book_database)}개의 도서 정보 로드")
            
            # 데이터베이스 저장
            self.book_database = book_database
            return book_database
        
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Google 스프레드시트 URL에 접근할 수 없습니다: {e}")
            self.logger.error("1. URL이 정확한지 확인하세요.")
            self.logger.error("2. 스프레드시트가 '링크가 있는 모든 사용자에게 공개'로 설정되었는지 확인하세요.")
            raise
        except Exception as e:
            self.logger.error(f"Google 스프레드시트 데이터 처리 실패: {e}")
            raise

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Google 스프레드시트 URL에 접근할 수 없습니다: {e}")
            self.logger.error("1. URL이 정확한지 확인하세요.")
            self.logger.error("2. 스프레드시트가 '링크가 있는 모든 사용자에게 공개'로 설정되었는지 확인하세요.")
            raise
        except Exception as e:
            self.logger.error(f"Google 스프레드시트 데이터 처리 실패: {e}")
            raise

    def read_excel_file(self, file_path):
        """사용자 지정 엑셀 파일을 읽어서 검토자 데이터(도서코드, 이름, 지메일) 반환"""
        try:
            # 엑셀 파일 읽기 (여러 확장자 지원)
            if file_path.endswith('.csv'):
                # CSV 파일을 UTF-8로 통일하여 읽기
                try:
                    df = pd.read_csv(file_path, encoding='utf-8')
                except UnicodeDecodeError:
                    # 파일이 다른 인코딩으로 저장된 경우, 바이트로 읽은 후 UTF-8로 변환
                    with open(file_path, 'rb') as f:
                        content = f.read()
                    
                    # 바이트 데이터를 UTF-8로 변환 (errors='replace'로 변환 불가능한 문자 처리)
                    text_content = content.decode('utf-8', errors='replace')
                    df = pd.read_csv(StringIO(text_content))
                    self.logger.info("CSV 파일을 UTF-8로 강제 변환하여 읽었습니다.")
            else:
                df = pd.read_excel(file_path)
            
            self.logger.info(f"엑셀 파일 읽기 성공: {file_path}")
            self.logger.info(f"총 {len(df)}개의 행이 발견됨")
            
            # 컬럼명 확인 및 로깅
            self.logger.info(f"엑셀 파일 컬럼: {list(df.columns)}")
            
            # 컬럼명 매핑 (대체 가능한 컬럼명 지원)
            column_mappings = {
                '이름': ['이름', '성명', '검토자', '검토자명', '리뷰어', 'Name'],
                '도서코드': ['도서코드', '책코드', '코드', 'Book Code', 'Code'],
                '지메일': ['지메일', '이메일', '메일', '메일주소', '이메일주소', 'Email', 'Gmail']
            }
            
            # 컬럼 이름 매핑 (대체 컬럼명 지원)
            for target_col, alternatives in column_mappings.items():
                if target_col not in df.columns:
                    # 대체 컬럼명 중 존재하는 것이 있는지 확인
                    for alt_col in alternatives:
                        if alt_col in df.columns:
                            # 발견된 대체 컬럼을 표준 이름으로 변경
                            df.rename(columns={alt_col: target_col}, inplace=True)
                            self.logger.info(f"컬럼 '{alt_col}'을(를) '{target_col}'(으)로 매핑했습니다.")
                            break
            
            # 필수 컬럼 확인
            required_columns = ['이름', '도서코드', '지메일']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                self.logger.error(f"필수 컬럼이 누락됨: {missing_columns}")
                self.logger.error("엑셀 파일에는 '이름', '도서코드', '지메일' 컬럼이 반드시 포함되어야 합니다.")
                self.logger.error(f"현재 엑셀 컬럼: {list(df.columns)}")
                raise ValueError(f"필수 컬럼이 누락됨: {missing_columns}")
            
            # 빈 값 처리
            df['도서코드'] = df['도서코드'].fillna("N/A").astype(str)
            df = df.dropna(subset=['이름', '지메일'])  # 이름과 지메일이 없는 행 제거
            
            self.logger.info(f"유효한 데이터: {len(df)}개 행")
            
            # 처리된 데이터의 샘플 확인
            if len(df) > 0:
                sample_data = df[['이름', '도서코드', '지메일']].head(3)
                self.logger.info(f"검토자 데이터 샘플:\n{sample_data.to_string(index=False)}")
            
            return df
            
        except Exception as e:
            self.logger.error(f"엑셀 파일 읽기 실패: {str(e)}")
            raise
    
    def check_chrome_browser(self):
        """크롬 브라우저 설치 여부 및 버전 확인"""
        try:
            system = platform.system()
            chrome_path = None
            
            # OS별 기본 크롬 경로
            if system == "Windows":
                paths_to_check = [
                    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
                ]
                for path in paths_to_check:
                    if os.path.exists(path):
                        chrome_path = path
                        break
            elif system == "Darwin":  # macOS
                chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
            elif system == "Linux":
                chrome_paths = [
                    "/usr/bin/google-chrome",
                    "/usr/bin/chrome",
                    "/usr/bin/chromium",
                    "/usr/bin/chromium-browser"
                ]
                for path in chrome_paths:
                    if os.path.exists(path):
                        chrome_path = path
                        break
            
            if not chrome_path or not os.path.exists(chrome_path):
                self.logger.warning("Chrome 브라우저를 찾을 수 없습니다.")
                return False, None
            
            # 버전 확인
            try:
                if system == "Windows":
                    cmd = f'"{chrome_path}" --version'
                else:
                    cmd = f'"{chrome_path}" --version'
                
                result = subprocess.check_output(cmd, shell=True, text=True)
                version = result.strip()
                self.logger.info(f"Chrome 버전: {version}")
                return True, version
            except Exception as e:
                self.logger.warning(f"Chrome 버전 확인 실패: {str(e)}")
                return True, "Unknown"
                
        except Exception as e:
            self.logger.warning(f"Chrome 브라우저 확인 중 오류: {str(e)}")
            return False, None

    def setup_driver(self):
        """Chrome 드라이버 설정"""
        try:
            self.logger.info("Chrome 드라이버 설정 시작...")
            
            # Chrome 옵션 설정
            chrome_options = Options()
            
            # 크롬 브라우저 경로 자동 탐지 또는 직접 지정
            chrome_binary_path = None
            try:
                # config.py에서 경로가 지정되어 있는지 확인
                from config import CHROME_BINARY_PATH
                if os.path.exists(CHROME_BINARY_PATH):
                    chrome_binary_path = CHROME_BINARY_PATH
                    self.logger.info(f"config.py에서 크롬 브라우저 경로 사용: {chrome_binary_path}")
                else:
                    self.logger.warning(f"config.py의 크롬 경로가 존재하지 않음: {CHROME_BINARY_PATH}")
            except (ImportError, AttributeError):
                self.logger.info("config.py에 크롬 경로가 지정되지 않음. 자동 탐지 시도...")
            
            # 크롬 경로가 없으면 자동 탐지
            if not chrome_binary_path:
                chrome_installed, chrome_version = self.check_chrome_browser()
                if chrome_installed:
                    # 기본 경로들 확인
                    possible_paths = [
                        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
                    ]
                    for path in possible_paths:
                        if os.path.exists(path):
                            chrome_binary_path = path
                            self.logger.info(f"자동 탐지된 크롬 브라우저 경로: {chrome_binary_path}")
                            break
                else:
                    self.logger.error("Chrome 브라우저를 찾을 수 없습니다. Chrome을 설치해주세요.")
                    return False
            
            # 크롬 경로 설정
            if chrome_binary_path:
                chrome_options.binary_location = chrome_binary_path
            
            # Chrome 옵션 추가
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--disable-features=VizDisplayCompositor")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)

            # 크롬 드라이버 자동 다운로드 및 설정
            self.logger.info("ChromeDriverManager를 사용하여 드라이버 다운로드 중...")
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                driver_path = ChromeDriverManager().install()
                self.logger.info(f"크롬 드라이버 다운로드 성공: {driver_path}")
                
                service = Service(executable_path=driver_path)
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                
                # 자동화 감지 방지 스크립트 실행
                try:
                    self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                    self.logger.info("자동화 감지 방지 스크립트 실행 완료")
                except Exception as e:
                    self.logger.warning(f"자동화 감지 방지 스크립트 실행 실패: {str(e)}")
                
                self.logger.info("Chrome 드라이버 설정 완료")
                return True
                
            except Exception as driver_error:
                self.logger.error(f"ChromeDriverManager 실패: {str(driver_error)}")
                # 추가적인 오류 정보 로깅
                import traceback
                self.logger.error(f"상세 오류: {traceback.format_exc()}")
                return False
                
        except Exception as e:
            self.logger.error(f"드라이버 설정 실패: {str(e)}")
            import traceback
            self.logger.error(f"상세 오류: {traceback.format_exc()}")
            return False
    
    def login_to_google(self, email=None, password=None):
        """Google 파트너스 센터 수동 로그인"""
        try:
            # Google Play Books 파트너스 센터로 이동
            partners_url = "https://play.google.com/books/publish/u/0/?hl=ko"
            self.logger.info(f"Google Play Books 파트너스 센터로 이동: {partners_url}")
            self.driver.get(partners_url)
            
            # 페이지 로드 대기
            time.sleep(3)
            
            # 현재 URL 확인
            current_url = self.driver.current_url
            self.logger.info(f"현재 URL: {current_url}")
            
            # 이미 로그인되어 있는지 확인
            if "play.google.com/books/publish" in current_url and "accounts.google.com" not in current_url:
                self.logger.info("이미 Google Play Books 파트너스 센터에 로그인되어 있습니다.")
                self.is_logged_in = True
                return True
            
            # 로그인이 필요한 경우 사용자에게 안내
            self.logger.info("=" * 60)
            self.logger.info("🔐 Google Play Books 파트너스 센터 로그인이 필요합니다.")
            self.logger.info("📌 브라우저 창에서 다음 단계를 진행해주세요:")
            self.logger.info("   1. Google 계정으로 로그인")
            self.logger.info("   2. 2단계 인증 완료 (필요한 경우)")
            self.logger.info("   3. Google Play Books 파트너스 센터 대시보드가 표시될 때까지 대기")
            self.logger.info("=" * 60)

            # 초기 로딩 대기
            time.sleep(5)
            
            # 로그인 완료 확인 대화상자 표시
            msg_box = messagebox.askquestion(
                "로그인 확인",
                "Google Play Books 파트너스 센터에 로그인이 완료되었습니까?",
                icon='question'
            )
            
            if msg_box == 'yes':
                current_url = self.driver.current_url
                if "play.google.com/books/publish" in current_url and "accounts.google.com" not in current_url:
                    self.logger.info("✅ 사용자가 로그인 완료를 확인했습니다.")
                    self.is_logged_in = True
                    return True
                else:
                    self.logger.error("❌ URL 확인 실패: 파트너스 센터 페이지가 아닙니다.")
                    return False
            else:
                self.logger.error("❌ 사용자가 로그인 완료를 확인하지 않았습니다.")
                return False
            return False
            
        except Exception as e:
            self.logger.error(f"로그인 프로세스 실패: {str(e)}")
            import traceback
            self.logger.error(f"상세 오류: {traceback.format_exc()}")
            return False
    
    # 마지막으로 방문한 도서 기억 (재방문 최적화용)
    last_visited_book = None
    
    def search_book(self, book_code):
        """도서코드를 기반으로 도서 검색"""
        try:
            # 이전에 방문한 도서인지 확인 (재검색 방지)
            if self.last_visited_book == book_code:
                self.logger.info(f"이미 방문한 도서 (코드: {book_code})입니다. 재검색 건너뜁니다.")
                # 현재 URL이 도서 상세 페이지인지 확인
                current_url = self.driver.current_url
                if "books/publish" in current_url and "/book/" in current_url:
                    return True
            
            self.logger.info(f"도서 검색 시작 - 도서코드: {book_code}")
            
            # 도서 데이터베이스에서 정보 조회
            book_info = self.get_book_info_by_code(book_code)
            if not book_info:
                self.logger.error(f"도서코드 '{book_code}'에 해당하는 도서를 찾을 수 없습니다")
                return False

            book_title = book_info.get('title', '')
            isbn = book_info.get('isbn', '')
            eisbn = book_info.get('eisbn', '')
            publisher = book_info.get('publisher', '')
            
            self.logger.info(f"도서 정보 - 제목: {book_title}, ISBN: {isbn}, eISBN: {eisbn}, 출판사: {publisher}")
            
            wait = WebDriverWait(self.driver, 15)
            
            # 직접 도서 목록 페이지로 이동 (출판사별로 URL 최적화)
            try:
                if publisher == '한빛아카데미':
                    catalog_url = "https://play.google.com/books/publish/a/535699340789858766#list?sortby=last_updated&sortdir=desc&publisher=한빛아카데미"
                elif publisher == '한빛미디어':
                    catalog_url = "https://play.google.com/books/publish/a/535699340789858766#list?sortby=last_updated&sortdir=desc&publisher=한빛미디어"
                else:
                    catalog_url = "https://play.google.com/books/publish/a/535699340789858766#list?sortby=last_updated&sortdir=desc"
                
                self.logger.info(f"출판사 '{publisher}'의 도서 목록 페이지로 이동: {catalog_url}")
                self.driver.get(catalog_url)
                time.sleep(2)  # 페이지 로드 대기 시간 단축
                self.logger.info("도서 목록 페이지 로드 완료")
                    
            except Exception as e:
                self.logger.error(f"도서 목록 페이지 이동 실패: {str(e)}")
                return False
            
            # 페이지가 완전히 로드될 때까지 대기
            try:
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                time.sleep(2)
                self.logger.info("페이지 요소 로드 대기 완료")
            except Exception as e:
                self.logger.warning(f"페이지 로드 대기 실패: {str(e)}")
            
            # 출판사 선택 - 출판사에 따라 선택
            try:
                publisher_select_id = "mat-select-0"
                self.logger.info(f"출판사 선택 드롭다운 클릭 시도... (대상 출판사: {publisher})")
                
                # 셀렉트 박스 클릭
                publisher_select = wait.until(EC.element_to_be_clickable((By.ID, publisher_select_id)))
                publisher_select.click()
                self.logger.info("출판사 선택 드롭다운 열기 성공")
                time.sleep(2)  # 드롭다운 로드 대기
                
                # 출판사에 따라 옵션 선택
                target_publisher = None
                if "한빛아카데미" in publisher or "아카데미" in publisher:
                    target_publisher = "한빛아카데미"
                elif "한빛미디어" in publisher or "미디어" in publisher or "한빛" in publisher:
                    target_publisher = "한빛미디어"
                else:
                    self.logger.warning(f"알 수 없는 출판사: {publisher}. 한빛아카데미로 기본 설정")
                    target_publisher = "한빛아카데미"
                
                self.logger.info(f"선택할 출판사: {target_publisher}")
                
                # 출판사 옵션 찾기 및 클릭
                publisher_selectors = [
                    f"//mat-option[contains(., '{target_publisher}')]",
                    f"//span[contains(text(), '{target_publisher}')]/parent::mat-option",
                    f"//mat-option//span[text()='{target_publisher}']",
                    f"//*[contains(text(), '{target_publisher}')]"
                ]
                
                publisher_selected = False
                for selector in publisher_selectors:
                    try:
                        publisher_option = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                        publisher_option.click()
                        self.logger.info(f"{target_publisher} 출판사 선택 성공")
                        publisher_selected = True
                        time.sleep(2)
                        break
                    except TimeoutException:
                        continue
                
                if not publisher_selected:
                    self.logger.warning(f"{target_publisher} 옵션을 찾을 수 없습니다. 기본값으로 진행...")
                    # ESC 키로 드롭다운 닫기
                    from selenium.webdriver.common.keys import Keys
                    publisher_select.send_keys(Keys.ESCAPE)
                    time.sleep(1)
                    
            except TimeoutException:
                self.logger.warning("출판사 선택 드롭다운을 찾을 수 없습니다. 기본값으로 진행...")
            except Exception as e:
                self.logger.warning(f"출판사 선택 실패: {str(e)}. 기본값으로 진행...")
            
            # 검색창에 g_title(한글 도서명) 입력
            try:
                search_input_id = "mat-input-0"
                search_value = book_info.get('g_title', '')
                
                # 검색어 전처리 - 한글 인코딩 처리 유틸리티 사용
                if search_value:
                    original = search_value
                    
                    # 한글 인코딩 처리 유틸리티로 통합 처리
                    search_value = korean_utils.fix_korean_encoding(search_value)
                    
                    # 변경사항 있으면 로그에 기록
                    if search_value != original:
                        self.logger.info(f"도서명 인코딩 수정: '{original}' -> '{search_value}'")
                    
                    # 정규화: 공백, 특수문자 등 처리
                    search_value = search_value.strip()
                
                if not search_value:
                    self.logger.error(f"도서코드 '{book_code}'의 g_title(한글 도서명)이 비어있습니다.")
                    return False
                self.logger.info(f"검색창에 도서명 '{search_value}' 입력 시도...")
                search_input = wait.until(EC.element_to_be_clickable((By.ID, search_input_id)))
                search_input.click()
                time.sleep(1)
                search_input.clear()
                search_input.send_keys(search_value)
                time.sleep(2)
                from selenium.webdriver.common.keys import Keys
                search_input.send_keys(Keys.ENTER)
                time.sleep(3)
                self.logger.info("도서명 검색 입력 완료")
            except TimeoutException:
                self.logger.error("검색창을 찾을 수 없습니다")
                return False
            
            # 검색 결과 중 첫 번째 도서 클릭
            try:
                self.logger.info("검색 결과 중 첫 번째 도서 클릭 시도...")
                
                # 검색 결과 첫 번째 항목을 찾기 위한 여러 셀렉터 시도
                first_book_selectors = [
                    "/html/body/pfe-app/partner-center/div[2]/div/ng-component/ng-component/div/catalog-table/div/table/tbody/tr/td[1]/div/div/a",
                    "//div[contains(@class, 'book-item')][1]//a",
                    "//mat-option[1]",
                    "//div[contains(@class, 'search-result')][1]//a",
                    "//div[contains(@class, 'book-list')]//div[1]//a",
                    "//*[contains(@class, 'mat-option')][1]",
                    "//table//tr[1]//a",
                    "//book-item[1]//a",
                    "//div[@class='book-row'][1]//a"
                ]
                
                first_book_clicked = False
                for selector in first_book_selectors:
                    try:
                        first_book = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                        first_book.click()
                        self.logger.info(f"첫 번째 도서 클릭 성공: {selector}")
                        first_book_clicked = True
                        time.sleep(3)
                        break
                    except TimeoutException:
                        continue
                
                if not first_book_clicked:
                    # 검색 결과를 더 자세히 분석
                    self.logger.warning("기본 셀렉터로 도서를 찾지 못함. 페이지 분석 시도...")
                    
                    try:
                        # 페이지의 모든 클릭 가능한 요소 확인
                        clickable_elements = self.driver.find_elements(By.XPATH, "//a | //button")
                        self.logger.info(f"클릭 가능한 요소 수: {len(clickable_elements)}")
                        
                        for i, element in enumerate(clickable_elements[:5]):  # 처음 5개만 확인
                            try:
                                element_text = element.text.strip()
                                element_href = element.get_attribute('href')
                                if element_text and (book_title[:20] in element_text or isbn in element_text):
                                    self.logger.info(f"관련 요소 발견 [{i}]: '{element_text}' - {element_href}")
                                    element.click()
                                    first_book_clicked = True
                                    time.sleep(3)
                                    break
                            except:
                                continue
                    except Exception as e:
                        self.logger.warning(f"요소 분석 실패: {str(e)}")
                
                if not first_book_clicked:
                    self.logger.error("검색 결과에서 첫 번째 도서를 찾을 수 없습니다")
                    return False
                    
            except Exception as e:
                self.logger.error(f"검색 결과 클릭 실패: {str(e)}")
                return False
            
            self.logger.info(f"도서 '{book_title}' (ISBN: {isbn}) 검색 및 선택 완료")
            return True
            
        except Exception as e:
            import traceback
            self.logger.error(f"도서 검색 실패: {str(e)}")
            self.logger.error(f"상세 오류: {traceback.format_exc()}")
            return False
    
    def verify_reviewer(self, email):
        """개별 검토자가 실제로 등록되었는지 확인"""
        try:
            self.logger.info(f"검토자 '{email}' 등록 확인 시작...")
            
            # 검토자 목록 컨테이너를 찾기 위한 XPath
            reviewers_container_xpath = "/html/body/pfe-app/partner-center/div[2]/div/ng-component/ng-component/div/ng-component/div[2]/quality-reviewers"
            
            try:
                # 검토자 목록이 로드될 때까지 짧게 대기
                time.sleep(1.5)
                
                # 검토자 목록 컨테이너 찾기
                container_elements = self.driver.find_elements(By.XPATH, reviewers_container_xpath)
                
                if not container_elements:
                    self.logger.warning(f"검토자 목록 컨테이너를 찾을 수 없습니다. 등록 확인 불가")
                    return False
                
                # 컨테이너 내부의 모든 텍스트 가져오기
                container_text = container_elements[0].text.lower()
                
                # 이메일 주소를 소문자로 변환하여 검색
                email_lower = email.lower()
                
                if email_lower in container_text:
                    self.logger.info(f"✅ 검토자 '{email}' 성공적으로 등록 확인!")
                    return True
                else:
                    # 더 광범위한 검색 시도 (목록 내의 모든 요소 확인)
                    reviewer_elements = container_elements[0].find_elements(By.XPATH, ".//div[contains(@class, 'reviewer')]") or \
                                        container_elements[0].find_elements(By.XPATH, ".//li") or \
                                        container_elements[0].find_elements(By.XPATH, ".//*")
                    
                    for element in reviewer_elements:
                        if email_lower in element.text.lower():
                            self.logger.info(f"✅ 검토자 '{email}' 성공적으로 등록 확인!")
                            return True
                    
                    self.logger.warning(f"⚠️ 검토자 '{email}' 등록이 확인되지 않음. 등록이 실패했거나 화면에 표시되지 않았을 수 있습니다.")
                    
                    # 스크린샷 저장 시도
                    try:
                        screenshot_path = f"reviewer_not_found_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                        self.driver.save_screenshot(screenshot_path)
                        self.logger.info(f"검토자 미확인 상황 스크린샷 저장: {screenshot_path}")
                    except:
                        pass
                    
                    return False
                    
            except Exception as e:
                self.logger.error(f"검토자 확인 과정에서 오류 발생: {str(e)}")
                return False
                
        except Exception as e:
            self.logger.error(f"검토자 확인 실패: {str(e)}")
            return False
    
    def batch_verify_reviewers(self, emails, book_title, book_code):
        """해당 도서에 등록된 모든 검토자 이메일을 한 번에 확인"""
        try:
            self.logger.info(f"도서 '{book_title}' (코드: {book_code})에 등록된 검토자 일괄 확인 시작...")
            verified_emails = []
            unverified_emails = []
            
            # 현재 URL이 검토 페이지인지 확인
            current_url = self.driver.current_url
            if "/review/" not in current_url:
                self.logger.warning(f"현재 검토 페이지에 있지 않습니다. 검증을 수행할 수 없습니다.")
                return {email: False for email in emails}
            
            # 검토자 목록 컨테이너를 찾기 위한 XPath
            reviewers_container_xpath = "/html/body/pfe-app/partner-center/div[2]/div/ng-component/ng-component/div/ng-component/div[2]/quality-reviewers"
            
            # 검토자 목록 컨테이너 찾기
            try:
                # 모든 등록이 완료될 때까지 충분히 대기
                time.sleep(3)
                
                container_elements = self.driver.find_elements(By.XPATH, reviewers_container_xpath)
                if not container_elements:
                    self.logger.error(f"검토자 목록 컨테이너를 찾을 수 없습니다. 검증을 수행할 수 없습니다.")
                    # 스크린샷 저장
                    try:
                        screenshot_path = f"reviewers_container_not_found_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                        self.driver.save_screenshot(screenshot_path)
                        self.logger.info(f"컨테이너 미확인 상황 스크린샷 저장: {screenshot_path}")
                    except:
                        pass
                    return {email: False for email in emails}
                
                # 컨테이너 내부의 모든 텍스트 가져오기
                container_text = container_elements[0].text.lower()
                
                # 각 이메일에 대해 확인
                verification_results = {}
                for email in emails:
                    email_lower = email.lower()
                    if email_lower in container_text:
                        self.logger.info(f"✅ 검토자 '{email}' 성공적으로 등록 확인!")
                        verified_emails.append(email)
                        verification_results[email] = True
                    else:
                        # 더 광범위한 검색 시도
                        reviewer_elements = container_elements[0].find_elements(By.XPATH, ".//div[contains(@class, 'reviewer')]") or \
                                            container_elements[0].find_elements(By.XPATH, ".//li") or \
                                            container_elements[0].find_elements(By.XPATH, ".//*")
                        
                        found = False
                        for element in reviewer_elements:
                            if email_lower in element.text.lower():
                                self.logger.info(f"✅ 검토자 '{email}' 성공적으로 등록 확인!")
                                verified_emails.append(email)
                                verification_results[email] = True
                                found = True
                                break
                        
                        if not found:
                            self.logger.warning(f"⚠️ 검토자 '{email}' 등록이 확인되지 않음")
                            unverified_emails.append(email)
                            verification_results[email] = False
                
                # 요약 로그
                if unverified_emails:
                    self.logger.warning(f"⚠️ 도서 '{book_title}'에 {len(unverified_emails)}개의 이메일이 확인되지 않았습니다: {', '.join(unverified_emails)}")
                    # 스크린샷 저장
                    try:
                        screenshot_path = f"reviewers_not_verified_{book_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                        self.driver.save_screenshot(screenshot_path)
                        self.logger.info(f"미확인 검토자 스크린샷 저장: {screenshot_path}")
                    except:
                        pass
                
                if verified_emails:
                    self.logger.info(f"✅ 도서 '{book_title}'에 {len(verified_emails)}개의 이메일 등록 확인 완료!")
                
                return verification_results
                
            except Exception as e:
                self.logger.error(f"일괄 검증 중 오류 발생: {str(e)}")
                return {email: False for email in emails}
                
        except Exception as e:
            self.logger.error(f"일괄 검증 실패: {str(e)}")
            return {email: False for email in emails}
    
    def add_reviewer(self, email, is_first_reviewer=False):
        """검토자 추가 (첫 번째만 콘텐츠 검토 아이템 클릭, 이후엔 입력만)"""
        try:
            self.logger.info(f"검토자 추가 시작: {email}")
            if is_first_reviewer:
                self.logger.info("콘텐츠 검토 페이지로 이동합니다...")
                try:
                    # 페이지 로딩 대기 (최대 10초)
                    wait = WebDriverWait(self.driver, 10)
                    xpath = "/html/body/pfe-app/partner-center/div[2]/div/ng-component/ng-component/mat-nav-list/div/nav/a[2]/span/span/div/span"
                    element = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
                    element.click()
                    self.logger.info("/html/body/pfe-app/partner-center/div[2]/div/ng-component/ng-component/mat-nav-list/div/nav/a[2]/span/span/div/span XPath 클릭 성공")
                    time.sleep(2)
                    self.current_review_page = self.driver.current_url
                except Exception as e:
                    self.logger.error(f"콘텐츠 메뉴 XPath 클릭 실패: {str(e)}")
                    return False
            else:
                self.logger.info("이미 콘텐츠 검토 페이지에 있습니다. 바로 이메일 입력을 시도합니다.")

            try:
                time.sleep(1)
                self.logger.info(f"이메일 '{email}' 입력 시도...")
                all_inputs = self.driver.find_elements(By.TAG_NAME, "input")
                email_field = None
                for input_elem in all_inputs:
                    try:
                        if input_elem.is_displayed() and input_elem.is_enabled():
                            email_field = input_elem
                            self.logger.info("이메일 입력 필드를 찾았습니다")
                            break
                    except Exception:
                        continue
                if not email_field and len(all_inputs) > 0:
                    email_field = all_inputs[0]
                    self.logger.info("첫 번째 입력 필드를 사용합니다")
                if not email_field:
                    self.logger.error("이메일 입력 필드를 찾을 수 없습니다")
                    try:
                        screenshot_path = f"no_input_field_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                        self.driver.save_screenshot(screenshot_path)
                        self.logger.info(f"입력 필드 없음 스크린샷 저장: {screenshot_path}")
                    except:
                        pass
                    return False
                email_field.clear()
                email_field.send_keys(email)
                self.logger.info(f"이메일 '{email}' 입력 완료")
                from selenium.webdriver.common.keys import Keys
                email_field.send_keys(Keys.ENTER)
                self.logger.info("Enter 키로 제출 완료")

                # 등록된 이메일이 리스트에 나타날 때까지 대기 (최대 30초)
                reviewers_container_xpath = "/html/body/pfe-app/partner-center/div[2]/div/ng-component/ng-component/div/ng-component/div[2]/quality-reviewers"
                email_found = False
                max_wait = 10
                poll_interval = 1  # 1초마다 리스트에서 검색
                waited = 0
                self.logger.info(f"이메일 '{email}'이(가) 검토자 목록에 나타날 때까지 대기...")
                while waited < max_wait:
                    try:
                        container_elements = self.driver.find_elements(By.XPATH, reviewers_container_xpath)
                        if container_elements:
                            container_text = container_elements[0].text.lower()
                            if email.lower() in container_text:
                                email_found = True
                                self.logger.info(f"이메일 '{email}'이(가) 검토자 목록에 표시됨. 3초 후 다음 등록으로 진행.")
                                time.sleep(3)
                                break
                    except Exception:
                        pass
                    time.sleep(poll_interval)
                    waited += poll_interval
                if not email_found:
                    self.logger.warning(f"이메일 '{email}'이(가) 30초 내에 검토자 목록에 표시되지 않음. 다음 등록으로 진행.")
                return email_found
            except Exception as e:
                self.logger.error(f"이메일 입력 실패: {str(e)}")
                try:
                    screenshot_path = f"email_input_failed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    self.driver.save_screenshot(screenshot_path)
                    self.logger.info(f"이메일 입력 실패 스크린샷 저장: {screenshot_path}")
                except:
                    pass
                return False
        except Exception as e:
            import traceback
            self.logger.error(f"검토자 추가 실패: {str(e)}")
            self.logger.error(f"상세 오류: {traceback.format_exc()}")
            return False

    def close_driver(self):
        """드라이버 종료"""
        try:
            if self.driver:
                self.driver.quit()
                self.logger.info("WebDriver 종료 완료")
        except Exception as e:
            self.logger.error(f"WebDriver 종료 실패: {str(e)}")

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
                        
                        # 한 번만 도서 검색
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
                        
                        # 검토자 수 파악
                        reviewer_count = len(reviewers)
                        self.logger.info(f"총 {reviewer_count}명의 검토자를 일괄 등록합니다")
                        
                        # 검색 성공 시 모든 검토자를 한 번에 등록
                        registered_emails = []  # 등록 시도한 이메일 목록
                        successful_reviewers = []  # 등록 성공한 검토자 정보
                        
                        for idx, reviewer in enumerate(reviewers):
                            try:
                                email = reviewer['email']
                                name = reviewer['name']
                                self.logger.info(f"[{idx+1}/{reviewer_count}] 검토자 '{name}' (이메일: {email}) 등록 시도 중...")
                                is_first = (idx == 0)
                                add_result = self.add_reviewer(email, is_first_reviewer=is_first)
                                import time
                                self.logger.info("[process_registration] 등록 후 5초 대기...")
                                time.sleep(5)
                                if add_result:
                                    registered_emails.append(email)
                                    successful_reviewers.append({
                                        'name': name,
                                        'email': email,
                                        'idx': idx
                                    })
                                    result = {
                                        'name': name,
                                        'book_title': book_title,
                                        'book_code': book_code,
                                        'isbn': isbn,
                                        'publisher': publisher,
                                        'email': email,
                                        'status': 'SUCCESS',
                                        'error': None,
                                        'verified': False
                                    }
                                    self.logger.info(f"✅ [{idx+1}/{reviewer_count}] 검토자 '{name}' (이메일: {email}) 등록 시도 성공 (5초 대기 후)")
                                else:
                                    self.logger.warning(f"❌ [{idx+1}/{reviewer_count}] 검토자 '{name}' (이메일: {email}) 등록 실패")
                                    result = {
                                        'name': name,
                                        'book_title': book_title,
                                        'book_code': book_code,
                                        'isbn': isbn,
                                        'publisher': publisher,
                                        'email': email,
                                        'status': 'FAILED',
                                        'error': f'검토자 추가 실패 (이메일: {email})',
                                        'verified': False
                                    }
                                self.registration_results.append(result)
                                processed_count += 1
                            except Exception as e:
                                self.logger.error(f"검토자 '{reviewer['email']}' 등록 중 오류 발생: {str(e)}")
                                result = {
                                    'name': reviewer['name'],
                                    'book_title': book_title,
                                    'book_code': book_code,
                                    'isbn': isbn,
                                    'publisher': publisher,
                                    'email': reviewer['email'],
                                    'status': 'FAILED',
                                    'error': f'처리 중 오류: {str(e)}',
                                    'verified': False
                                }
                                self.registration_results.append(result)
                                processed_count += 1
                        
                        # 모든 이메일 등록이 완료된 후 일괄 검증 수행
                        if registered_emails:
                            self.logger.info(f"도서 '{book_title}'에 등록된 {len(registered_emails)}개의 이메일 일괄 검증 시작...")
                            verification_results = self.batch_verify_reviewers(registered_emails, book_title, book_code)
                            
                            # 검증 결과를 등록 결과에 반영
                            for i, result in enumerate(self.registration_results):
                                if result.get('status') == 'SUCCESS' and result.get('email') in verification_results:
                                    is_verified = verification_results[result.get('email')]
                                    self.registration_results[i]['verified'] = is_verified
                                    
                                    if is_verified:
                                        self.logger.info(f"✅ 검토자 '{result.get('name')}' (이메일: {result.get('email')}) 등록 확인 완료")
                                    else:
                                        self.logger.warning(f"⚠️ 검토자 '{result.get('name')}' (이메일: {result.get('email')}) 등록 확인 실패")
                            
                            # 검증 결과 요약
                            verified_count = sum(1 for email, verified in verification_results.items() if verified)
                            self.logger.info(f"도서 '{book_title}' 일괄 검증 결과: 총 {len(registered_emails)}개 중 {verified_count}개 확인 완료")
                            
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
            
            # 검증 상태에 따른 요약 추가
            verified_count = len([r for r in self.registration_results if r.get('verified', False)])
            not_verified_count = len([r for r in self.registration_results if r.get('status') == 'SUCCESS' and not r.get('verified', True)])
            
            self.logger.info(f"등록 완료 - 성공: {success_count}, 실패: {failed_count}")
            # 검증 요약 로그 추가
            if not_verified_count > 0:
                self.logger.warning(f"⚠️ 주의: {not_verified_count}개의 등록이 성공했지만 확인되지 않았습니다. 검토가 필요합니다.")
            
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
    
    def save_results(self, output_file="registration_results.xlsx"):
        """결과를 엑셀 파일로 저장"""
        try:
            if not self.registration_results:
                self.logger.warning("저장할 결과가 없습니다.")
                return False
            
            df_results = pd.DataFrame(self.registration_results)
            
            # 결과 파일명에 타임스탬프 추가
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"registration_results_{timestamp}.xlsx"
            
            df_results.to_excel(output_file, index=False, encoding='utf-8')
            self.logger.info(f"결과 저장 완료: {output_file}")
            return output_file
            
        except Exception as e:
            self.logger.error(f"결과 저장 실패: {str(e)}")
            return False


class EbookRegistrationGUI:
    """토스/애플 스타일 전자책 검토자 등록 GUI"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("전자책 검토자 자동 등록")
        self.root.geometry("1000x700")
        self.root.configure(bg="#FFFFFF")  # 깔끔한 화이트 배경
        
        # 토스/애플 스타일 컬러 시스템
        self.colors = {
            'bg_primary': '#FFFFFF',       # 메인 배경 (화이트)
            'bg_secondary': '#F8F9FA',     # 서브 배경 (라이트 그레이)
            'card_bg': '#FFFFFF',          # 카드 배경
            'accent_blue': '#007AFF',      # 애플 블루 (메인 포인트)
            'accent_mint': '#32D74B',      # 민트 그린 (성공)
            'accent_red': '#FF3B30',       # 애플 레드 (위험)
            'accent_orange': '#FF9500',    # 오렌지 (경고)
            'text_primary': '#1D1D1F',     # 메인 텍스트
            'text_secondary': '#6D6D80',   # 서브 텍스트
            'text_tertiary': '#8E8E93',    # 보조 텍스트
            'border_light': '#E5E5EA',     # 라이트 보더
            'border_medium': '#C7C7CC',    # 미디엄 보더
            'shadow': 'rgba(0,0,0,0.1)',   # 카드 그림자
            'hover': '#F2F2F7'             # 호버 효과
        }
        
        # 폰트 설정
        self.setup_fonts()
        
        # 스타일 설정
        self.setup_styles()
        
        self.registerer = EbookReviewerAutoRegister()
        self.excel_file_path = None
        self.data_df = None
        self.is_dark_mode = False
        
        self.setup_gui()
    
    def setup_fonts(self):
        """토스/애플 스타일 폰트 설정"""
        try:
            # Pretendard 폰트 시도, 없으면 시스템 기본 폰트 사용
            self.fonts = {
                'display': font.Font(family="Pretendard", size=28, weight="bold"),    # 대제목
                'title': font.Font(family="Pretendard", size=20, weight="bold"),      # 제목
                'headline': font.Font(family="Pretendard", size=17, weight="bold"),   # 헤드라인
                'body': font.Font(family="Pretendard", size=15, weight="normal"),     # 본문
                'body_medium': font.Font(family="Pretendard", size=15, weight="500"), # 본문 미디엄
                'callout': font.Font(family="Pretendard", size=13, weight="normal"),  # 콜아웃
                'caption': font.Font(family="Pretendard", size=11, weight="normal"),  # 캡션
                'button': font.Font(family="Pretendard", size=16, weight="600"),      # 버튼
                'code': font.Font(family="SF Mono", size=12, weight="normal")         # 코드
            }
        except:
            # 시스템 기본 폰트로 폴백
            self.fonts = {
                'display': font.Font(family="맑은 고딕", size=28, weight="bold"),
                'title': font.Font(family="맑은 고딕", size=20, weight="bold"),
                'headline': font.Font(family="맑은 고딕", size=17, weight="bold"),
                'body': font.Font(family="맑은 고딕", size=15, weight="normal"),
                'body_medium': font.Font(family="맑은 고딕", size=15, weight="bold"),
                'callout': font.Font(family="맑은 고딕", size=13, weight="normal"),
                'caption': font.Font(family="맑은 고딕", size=11, weight="normal"),
                'button': font.Font(family="맑은 고딕", size=16, weight="bold"),
                'code': font.Font(family="Consolas", size=12, weight="normal")
            }
    
    def setup_styles(self):
        """토스/애플 스타일 설정"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # 프로그레스 바 스타일 (애플/토스 스타일)
        style.configure(
            "Toss.Horizontal.TProgressbar",
            background=self.colors['accent_blue'],
            troughcolor=self.colors['bg_secondary'],
            borderwidth=0,
            lightcolor=self.colors['accent_blue'],
            darkcolor=self.colors['accent_blue']
        )
    
    def create_card(self, parent, padding=24):
        """토스/애플 스타일 카드 생성"""
        # 카드 컨테이너 (그림자 효과)
        card_container = tk.Frame(
            parent,
            bg=self.colors['bg_primary'],
            relief='flat',
            bd=0
        )
        
        # 실제 카드 프레임
        card = tk.Frame(
            card_container,
            bg=self.colors['card_bg'],
            relief='flat',
            bd=1,
            highlightthickness=1,
            highlightcolor=self.colors['border_light'],
            highlightbackground=self.colors['border_light']
        )
        card.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # 내부 패딩을 위한 프레임
        content_frame = tk.Frame(
            card,
            bg=self.colors['card_bg'],
            relief='flat',
            bd=0
        )
        content_frame.pack(fill=tk.BOTH, expand=True, padx=padding, pady=padding)
        
        return card_container, content_frame
    
    def create_button(self, parent, text, command=None, style="primary", width=None):
        """토스/애플 스타일 버튼 생성"""
        if style == "primary":
            bg_color = self.colors['accent_blue']
            fg_color = '#FFFFFF'
            hover_color = '#0056CC'
        elif style == "success":
            bg_color = self.colors['accent_mint']
            fg_color = '#FFFFFF'
            hover_color = '#28CD47'
        elif style == "danger":
            bg_color = self.colors['accent_red']
            fg_color = '#FFFFFF'
            hover_color = '#D70015'
        elif style == "secondary":
            bg_color = self.colors['bg_secondary']
            fg_color = self.colors['text_primary']
            hover_color = self.colors['hover']
        else:
            bg_color = self.colors['accent_blue']
            fg_color = '#FFFFFF'
            hover_color = '#0056CC'
        
        button = tk.Button(
            parent,
            text=text,
            font=self.fonts['button'],
            bg=bg_color,
            fg=fg_color,
            relief='flat',
            bd=0,
            padx=24,
            pady=12,
            command=command,
            cursor='hand2',
            activebackground=hover_color,
            activeforeground=fg_color
        )
        
        if width:
            button.configure(width=width)
        
        return button
    
    def setup_gui(self):
        """토스/애플 스타일 GUI 구성"""
        # 메인 스크롤 가능한 컨테이너
        self.create_scrollable_main()
        
        # 헤더
        self.create_modern_header()
        
        # 카드 섹션들 (위에서 아래로)
        self.create_file_upload_card()
        self.create_data_preview_card()
        self.create_control_card()
        self.create_log_card()
        
        self.registration_thread = None
        self.stop_requested = False
    
    def create_scrollable_main(self):
        """스크롤 가능한 메인 컨테이너"""
        # 스크롤바가 있는 캔버스
        self.canvas = tk.Canvas(
            self.root,
            bg=self.colors['bg_primary'],
            highlightthickness=0
        )
        self.scrollbar = ttk.Scrollbar(
            self.root,
            orient="vertical",
            command=self.canvas.yview
        )
        self.scrollable_frame = tk.Frame(
            self.canvas,
            bg=self.colors['bg_primary']
        )
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # 마우스 휠 바인딩
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
    
    def _on_mousewheel(self, event):
        """마우스 휠 스크롤 핸들러"""
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def create_modern_header(self):
        """현대적인 헤더 생성"""
        header_frame = tk.Frame(
            self.scrollable_frame,
            bg=self.colors['bg_primary'],
            height=120
        )
        header_frame.pack(fill=tk.X, padx=40, pady=(40, 0))
        header_frame.pack_propagate(False)
        
        # 제목 영역
        title_frame = tk.Frame(header_frame, bg=self.colors['bg_primary'])
        title_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        # 메인 제목
        tk.Label(
            title_frame,
            text="전자책 검토자 자동 등록",
            font=self.fonts['display'],
            fg=self.colors['text_primary'],
            bg=self.colors['bg_primary']
        ).pack(anchor=tk.W, pady=(10, 5))
        
        # 서브타이틀
        tk.Label(
            title_frame,
            text="Google Books Partner Center에 검토자를 자동으로 등록합니다",
            font=self.fonts['body'],
            fg=self.colors['text_secondary'],
            bg=self.colors['bg_primary']
        ).pack(anchor=tk.W)
        
        # 우측 상태 표시
        status_frame = tk.Frame(header_frame, bg=self.colors['bg_primary'])
        status_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(20, 0))
        
        # 상태 인디케이터
        self.status_indicator = tk.Label(
            status_frame,
            text="●",
            font=("Arial", 20),
            fg=self.colors['text_tertiary'],
            bg=self.colors['bg_primary']
        )
        self.status_indicator.pack(anchor=tk.E, pady=(20, 5))
        
        self.status_label = tk.Label(
            status_frame,
            text="준비 대기 중",
            font=self.fonts['callout'],
            fg=self.colors['text_secondary'],
            bg=self.colors['bg_primary']
        )
        self.status_label.pack(anchor=tk.E)
    
    def create_file_upload_card(self):
        """📂 파일 선택 카드 (토스 스타일)"""
        card_container, content = self.create_card(self.scrollable_frame, padding=32)
        card_container.pack(fill=tk.X, padx=40, pady=(30, 20))
        
        # 카드 헤더
        header_frame = tk.Frame(content, bg=self.colors['card_bg'])
        header_frame.pack(fill=tk.X, pady=(0, 24))
        
        tk.Label(
            header_frame,
            text="📂 파일 선택",
            font=self.fonts['headline'],
            fg=self.colors['text_primary'],
            bg=self.colors['card_bg']
        ).pack(side=tk.LEFT)
        
        # 파일 업로드 영역 (토스 스타일 드래그앤드롭)
        upload_area = tk.Frame(
            content,
            bg=self.colors['bg_secondary'],
            relief='flat',
            bd=1,
            highlightthickness=2,
            highlightcolor=self.colors['border_light'],
            highlightbackground=self.colors['border_light']
        )
        upload_area.pack(fill=tk.X, pady=(0, 20))
        
        # 드래그앤드롭 영역 내용
        upload_content = tk.Frame(upload_area, bg=self.colors['bg_secondary'])
        upload_content.pack(expand=True, padx=40, pady=40)
        
        # 큰 업로드 아이콘
        tk.Label(
            upload_content,
            text="📄",
            font=("Arial", 48),
            fg=self.colors['text_tertiary'],
            bg=self.colors['bg_secondary']
        ).pack(pady=(0, 16))
        
        # 업로드 텍스트
        tk.Label(
            upload_content,
            text="드래그 앤 드롭 또는 파일 선택",
            font=self.fonts['body_medium'],
            fg=self.colors['text_primary'],
            bg=self.colors['bg_secondary']
        ).pack(pady=(0, 8))
        
        tk.Label(
            upload_content,
            text="Excel (xlsx, xls) 또는 CSV 파일을 선택해주세요",
            font=self.fonts['callout'],
            fg=self.colors['text_secondary'],
            bg=self.colors['bg_secondary']
        ).pack(pady=(0, 20))
        
        # 파일 선택 버튼
        self.file_select_button = self.create_button(
            upload_content,
            "파일 선택",
            command=self.select_file,
            style="primary"
        )
        self.file_select_button.pack()
        
        # 선택된 파일 정보 표시
        self.file_info_frame = tk.Frame(content, bg=self.colors['card_bg'])
        self.file_info_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.file_info_label = tk.Label(
            self.file_info_frame,
            text="",
            font=self.fonts['callout'],
            fg=self.colors['text_secondary'],
            bg=self.colors['card_bg']
        )
        self.file_info_label.pack(anchor=tk.W)
    
    def create_data_preview_card(self):
        """👀 데이터 미리보기 카드"""
        card_container, content = self.create_card(self.scrollable_frame, padding=32)
        card_container.pack(fill=tk.X, padx=40, pady=(0, 20))
        
        # 카드 헤더
        header_frame = tk.Frame(content, bg=self.colors['card_bg'])
        header_frame.pack(fill=tk.X, pady=(0, 24))
        
        # 제목과 통계
        title_stats_frame = tk.Frame(header_frame, bg=self.colors['card_bg'])
        title_stats_frame.pack(fill=tk.X)
        
        tk.Label(
            title_stats_frame,
            text="� 데이터 미리보기",
            font=self.fonts['headline'],
            fg=self.colors['text_primary'],
            bg=self.colors['card_bg']
        ).pack(side=tk.LEFT)
        
        # 통계 배지
        self.stats_badge = tk.Label(
            title_stats_frame,
            text="0개 행",
            font=self.fonts['caption'],
            fg='#FFFFFF',
            bg=self.colors['accent_blue'],
            relief='flat',
            padx=12,
            pady=4
        )
        self.stats_badge.pack(side=tk.RIGHT)
        
        # 데이터 테이블을 위한 컨테이너
        table_container = tk.Frame(
            content,
            bg=self.colors['bg_secondary'],
            relief='flat',
            bd=1,
            highlightthickness=1,
            highlightcolor=self.colors['border_light'],
            highlightbackground=self.colors['border_light']
        )
        table_container.pack(fill=tk.BOTH, expand=True)
        
        # 테이블 헤더
        table_header = tk.Frame(table_container, bg=self.colors['bg_secondary'], height=44)
        table_header.pack(fill=tk.X)
        table_header.pack_propagate(False)
        
        # 헤더 컬럼들
        header_columns = ['이름', '도서명', '지메일']
        for i, col in enumerate(header_columns):
            col_frame = tk.Frame(table_header, bg=self.colors['bg_secondary'])
            col_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(16 if i == 0 else 8, 8))
            
            tk.Label(
                col_frame,
                text=col,
                font=self.fonts['body_medium'],
                fg=self.colors['text_secondary'],
                bg=self.colors['bg_secondary']
            ).pack(anchor=tk.W, pady=12)
        
        # 구분선
        separator = tk.Frame(table_container, bg=self.colors['border_light'], height=1)
        separator.pack(fill=tk.X)
        
        # 데이터 영역 (스크롤 가능)
        data_frame = tk.Frame(table_container, bg=self.colors['card_bg'])
        data_frame.pack(fill=tk.BOTH, expand=True)
        
        # 스크롤바가 있는 리스트박스 대신 프레임 사용
        self.data_list_frame = tk.Frame(data_frame, bg=self.colors['card_bg'])
        self.data_list_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)
        
        # 초기 빈 상태 표시
        self.empty_state_label = tk.Label(
            self.data_list_frame,
            text="파일을 선택하면 데이터가 여기에 표시됩니다",
            font=self.fonts['body'],
            fg=self.colors['text_tertiary'],
            bg=self.colors['card_bg']
        )
        self.empty_state_label.pack(expand=True, pady=40)
    
    def create_control_card(self):
        """▶ 실행 제어 카드"""
        card_container, content = self.create_card(self.scrollable_frame, padding=32)
        card_container.pack(fill=tk.X, padx=40, pady=(0, 20))
        
        # 카드 헤더
        header_frame = tk.Frame(content, bg=self.colors['card_bg'])
        header_frame.pack(fill=tk.X, pady=(0, 24))
        
        tk.Label(
            header_frame,
            text="▶ 실행 제어",
            font=self.fonts['headline'],
            fg=self.colors['text_primary'],
            bg=self.colors['card_bg']
        ).pack(side=tk.LEFT)
        
        # 상태 표시 영역
        status_container = tk.Frame(
            content,
            bg=self.colors['bg_secondary'],
            relief='flat',
            bd=1,
            highlightthickness=1,
            highlightcolor=self.colors['border_light'],
            highlightbackground=self.colors['border_light']
        )
        status_container.pack(fill=tk.X, pady=(0, 24))
        
        status_content = tk.Frame(status_container, bg=self.colors['bg_secondary'])
        status_content.pack(fill=tk.X, padx=20, pady=16)
        
        # 진행률 텍스트
        self.progress_label = tk.Label(
            status_content,
            text="대기 중...",
            font=self.fonts['body_medium'],
            fg=self.colors['text_primary'],
            bg=self.colors['bg_secondary']
        )
        self.progress_label.pack(anchor=tk.W, pady=(0, 12))
        
        # 프로그레스 바
        self.progress_bar = ttk.Progressbar(
            status_content,
            mode='determinate',
            style="Toss.Horizontal.TProgressbar"
        )
        self.progress_bar.pack(fill=tk.X, pady=(0, 12))
        
        # 통계 정보
        stats_frame = tk.Frame(status_content, bg=self.colors['bg_secondary'])
        stats_frame.pack(fill=tk.X)
        
        self.success_label = tk.Label(
            stats_frame,
            text="성공: 0",
            font=self.fonts['callout'],
            fg=self.colors['accent_mint'],
            bg=self.colors['bg_secondary']
        )
        self.success_label.pack(side=tk.LEFT)
        
        tk.Label(
            stats_frame,
            text=" • ",
            font=self.fonts['callout'],
            fg=self.colors['text_tertiary'],
            bg=self.colors['bg_secondary']
        ).pack(side=tk.LEFT)
        
        self.failed_label = tk.Label(
            stats_frame,
            text="실패: 0",
            font=self.fonts['callout'],
            fg=self.colors['accent_red'],
            bg=self.colors['bg_secondary']
        )
        self.failed_label.pack(side=tk.LEFT)
        
        tk.Label(
            stats_frame,
            text=" • ",
            font=self.fonts['callout'],
            fg=self.colors['text_tertiary'],
            bg=self.colors['bg_secondary']
        ).pack(side=tk.LEFT)
        
        self.total_label = tk.Label(
            stats_frame,
            text="전체: 0",
            font=self.fonts['callout'],
            fg=self.colors['text_secondary'],
            bg=self.colors['bg_secondary']
        )
        self.total_label.pack(side=tk.LEFT)
        
        # 버튼 영역
        button_frame = tk.Frame(content, bg=self.colors['card_bg'])
        button_frame.pack(fill=tk.X)
        
        # 등록 시작 버튼 (토스 스타일 - 넓고 라운드)
        self.start_button = self.create_button(
            button_frame,
            "등록 시작",
            command=self.start_registration,
            style="success"
        )
        self.start_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 12))
        self.start_button.configure(state="disabled")
        
        # 중지 버튼
        self.stop_button = self.create_button(
            button_frame,
            "중지",
            command=self.stop_registration,
            style="danger"
        )
        self.stop_button.pack(side=tk.RIGHT)
        self.stop_button.configure(state="disabled")
    
    def create_log_card(self):
        """📝 실행 로그 카드"""
        card_container, content = self.create_card(self.scrollable_frame, padding=32)
        card_container.pack(fill=tk.X, padx=40, pady=(0, 40))
        
        # 카드 헤더
        header_frame = tk.Frame(content, bg=self.colors['card_bg'])
        header_frame.pack(fill=tk.X, pady=(0, 24))
        
        tk.Label(
            header_frame,
            text="� 실행 로그",
            font=self.fonts['headline'],
            fg=self.colors['text_primary'],
            bg=self.colors['card_bg']
        ).pack(side=tk.LEFT)
        
        # 로그 제어 버튼
        log_controls = tk.Frame(header_frame, bg=self.colors['card_bg'])
        log_controls.pack(side=tk.RIGHT)
        
        clear_button = self.create_button(
            log_controls,
            "지우기",
            command=self.clear_log,
            style="secondary"
        )
        clear_button.configure(padx=16, pady=6, font=self.fonts['callout'])
        clear_button.pack()
        
        # 로그 컨테이너
        log_container = tk.Frame(
            content,
            bg=self.colors['text_primary'],  # 다크 배경
            relief='flat',
            bd=1,
            highlightthickness=1,
            highlightcolor=self.colors['border_medium'],
            highlightbackground=self.colors['border_medium']
        )
        log_container.pack(fill=tk.BOTH, expand=True)
        
        # 로그 텍스트 (터미널 스타일)
        self.log_text = scrolledtext.ScrolledText(
            log_container,
            height=12,
            font=self.fonts['code'],
            bg=self.colors['text_primary'],
            fg='#FFFFFF',
            insertbackground='#FFFFFF',
            relief='flat',
            bd=0,
            wrap=tk.WORD,
            padx=16,
            pady=16
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 로그 색상 태그 설정 (토스/애플 스타일)
        self.log_text.tag_configure("SUCCESS", foreground=self.colors['accent_mint'])
        self.log_text.tag_configure("ERROR", foreground=self.colors['accent_red'])
        self.log_text.tag_configure("WARNING", foreground=self.colors['accent_orange'])
        self.log_text.tag_configure("INFO", foreground="#FFFFFF")
    
    def clear_log(self):
        """로그 지우기"""
        if messagebox.askyesno("로그 지우기", "모든 로그를 지우시겠습니까?"):
            self.log_text.delete(1.0, tk.END)
            self.log_message("🗑 로그가 지워졌습니다", "INFO")
    
    def save_results(self):
        """결과 저장"""
        try:
            output_file = self.registerer.save_results()
            if output_file:
                if messagebox.askyesno(
                    "저장 완료", 
                    f"결과가 저장되었습니다!\n\n📁 {os.path.basename(output_file)}\n\n파일을 열어보시겠습니까?"
                ):
                    os.startfile(output_file)
                self.log_message(f"💾 결과 저장 완료: {os.path.basename(output_file)}", "SUCCESS")
            else:
                messagebox.showerror("오류", "결과 저장에 실패했습니다.")
        except Exception as e:
            messagebox.showerror("저장 오류", f"결과 저장 실패:\n{str(e)}")
            self.log_message(f"❌ 결과 저장 실패: {str(e)}", "ERROR")
    
    def toggle_theme(self):
        """다크/라이트 모드 토글"""
        self.is_dark_mode = not self.is_dark_mode
        
        if self.is_dark_mode:
            # 다크 모드 색상
            self.colors.update({
                'bg_primary': '#1E1E1E',
                'bg_secondary': '#2D2D2D',
                'text_primary': '#FFFFFF',
                'text_secondary': '#B0B0B0',
                'shadow_light': '#404040',
                'shadow_dark': '#0D0D0D'
            })
            self.dark_mode_button.config(text="☀️")
        else:
            # 라이트 모드 색상
            self.colors.update({
                'bg_primary': '#F5F7FA',
                'bg_secondary': '#FFFFFF',
                'text_primary': '#2E2E2E',
                'text_secondary': '#8A8A8A',
                'shadow_light': '#E8ECEF',
                'shadow_dark': '#D1D9E6'
            })
            self.dark_mode_button.config(text="🌙")
        
        # UI 새로고침
        self.refresh_theme()
    
    def refresh_theme(self):
        """테마 변경 후 UI 새로고침"""
        # 이 메서드는 모든 위젯의 색상을 업데이트합니다
        # 실제 구현에서는 모든 위젯을 순회하며 색상을 업데이트해야 합니다
        self.root.configure(bg=self.colors['bg_primary'])
    

    
    def show_settings(self):
        """설정 창 표시"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("VibeFlow Studio - 설정")
        settings_window.geometry("500x400")
        settings_window.configure(bg=self.colors['bg_primary'])
        settings_window.resizable(False, False)
        
        # 중앙에 창 위치시키기
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # 설정 내용
        main_frame = tk.Frame(settings_window, bg=self.colors['bg_primary'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 제목
        tk.Label(
            main_frame,
            text="⚙️ 설정",
            font=self.fonts['heading'],
            fg=self.colors['text_primary'],
            bg=self.colors['bg_primary']
        ).pack(anchor=tk.W, pady=(0, 20))
        
        # 테마 설정
        theme_frame = tk.Frame(main_frame, bg=self.colors['bg_secondary'], relief='flat', bd=1)
        theme_frame.pack(fill=tk.X, pady=(0, 15), padx=5, ipady=15, ipadx=15)
        
        tk.Label(
            theme_frame,
            text="🎨 테마 설정",
            font=self.fonts['subheading'],
            fg=self.colors['text_primary'],
            bg=self.colors['bg_secondary']
        ).pack(anchor=tk.W, pady=(0, 10))
        
        theme_var = tk.StringVar(value="라이트 모드" if not self.is_dark_mode else "다크 모드")
        
        tk.Radiobutton(
            theme_frame,
            text="☀️ 라이트 모드",
            variable=theme_var,
            value="라이트 모드",
            font=self.fonts['body'],
            fg=self.colors['text_primary'],
            bg=self.colors['bg_secondary'],
            selectcolor=self.colors['accent_purple']
        ).pack(anchor=tk.W, pady=2)
        
        tk.Radiobutton(
            theme_frame,
            text="🌙 다크 모드",
            variable=theme_var,
            value="다크 모드",
            font=self.fonts['body'],
            fg=self.colors['text_primary'],
            bg=self.colors['bg_secondary'],
            selectcolor=self.colors['accent_purple']
        ).pack(anchor=tk.W, pady=2)
        
        # 자동화 설정
        auto_frame = tk.Frame(main_frame, bg=self.colors['bg_secondary'], relief='flat', bd=1)
        auto_frame.pack(fill=tk.X, pady=(0, 15), padx=5, ipady=15, ipadx=15)
        
        tk.Label(
            auto_frame,
            text="🤖 자동화 설정",
            font=self.fonts['subheading'],
            fg=self.colors['text_primary'],
            bg=self.colors['bg_secondary']
        ).pack(anchor=tk.W, pady=(0, 10))
        
        self.auto_save_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            auto_frame,
            text="결과 자동 저장",
            variable=self.auto_save_var,
            font=self.fonts['body'],
            fg=self.colors['text_primary'],
            bg=self.colors['bg_secondary'],
            selectcolor=self.colors['accent_mint']
        ).pack(anchor=tk.W, pady=2)
        
        self.auto_open_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            auto_frame,
            text="완료 후 결과 파일 자동 열기",
            variable=self.auto_open_var,
            font=self.fonts['body'],
            fg=self.colors['text_primary'],
            bg=self.colors['bg_secondary'],
            selectcolor=self.colors['accent_mint']
        ).pack(anchor=tk.W, pady=2)
        
        # 버튼
        button_frame = tk.Frame(main_frame, bg=self.colors['bg_primary'])
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(20, 0))
        
        tk.Button(
            button_frame,
            text="적용",
            font=self.fonts['body'],
            bg=self.colors['accent_purple'],
            fg='white',
            relief='flat',
            bd=0,
            padx=20,
            pady=8,
            command=lambda: self.apply_settings(theme_var.get(), settings_window),
            cursor='hand2'
        ).pack(side=tk.RIGHT, padx=(10, 0))
        
        tk.Button(
            button_frame,
            text="취소",
            font=self.fonts['body'],
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_primary'],
            relief='flat',
            bd=0,
            padx=20,
            pady=8,
            command=settings_window.destroy,
            cursor='hand2'
        ).pack(side=tk.RIGHT)
    
    def apply_settings(self, theme_choice, window):
        """설정 적용"""
        # 테마 변경
        if (theme_choice == "다크 모드") != self.is_dark_mode:
            self.toggle_theme()
        
        self.log_message("⚙️ 설정이 적용되었습니다.", "SUCCESS")
        window.destroy()
    
    def show_about(self):
        """정보 창 표시"""
        about_window = tk.Toplevel(self.root)
        about_window.title("VibeFlow Studio - 정보")
        about_window.geometry("450x350")
        about_window.configure(bg=self.colors['bg_primary'])
        about_window.resizable(False, False)
        
        # 중앙에 창 위치시키기
        about_window.transient(self.root)
        about_window.grab_set()
        
        # 정보 내용
        main_frame = tk.Frame(about_window, bg=self.colors['bg_primary'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        # 로고와 제목
        tk.Label(
            main_frame,
            text="✨ VibeFlow Studio",
            font=self.fonts['title'],
            fg=self.colors['accent_purple'],
            bg=self.colors['bg_primary']
        ).pack(pady=(0, 10))
        
        tk.Label(
            main_frame,
            text="전자책 검토자 자동 등록 시스템",
            font=self.fonts['subheading'],
            fg=self.colors['text_secondary'],
            bg=self.colors['bg_primary']
        ).pack(pady=(0, 20))
        
        # 정보 텍스트
        info_frame = tk.Frame(main_frame, bg=self.colors['bg_secondary'], relief='flat', bd=1)
        info_frame.pack(fill=tk.X, pady=(0, 20), padx=10, ipady=20, ipadx=20)
        
        about_text = """🚀 주요 기능:
• Google Books 파트너 센터 자동 등록
• 엑셀/CSV 파일 데이터 처리
• 실시간 진행률 모니터링
• 상세 로그 및 결과 리포트

🎨 디자인:
• 미니멀리즘 + 뉴모피즘 스타일
• 다크/라이트 모드 지원
• 반응형 레이아웃

📝 버전: 2.0.0
📅 업데이트: 2025년 9월"""
        
        tk.Label(
            info_frame,
            text=about_text,
            font=self.fonts['body'],
            fg=self.colors['text_primary'],
            bg=self.colors['bg_secondary'],
            justify=tk.LEFT
        ).pack(anchor=tk.W)
        
        # 닫기 버튼
        tk.Button(
            main_frame,
            text="확인",
            font=self.fonts['body'],
            bg=self.colors['accent_purple'],
            fg='white',
            relief='flat',
            bd=0,
            padx=30,
            pady=10,
            command=about_window.destroy,
            cursor='hand2'
        ).pack(pady=(10, 0))
    
    def animate_button_click(self, button):
        """버튼 클릭 애니메이션"""
        original_bg = button.cget('bg')
        button.configure(bg=self.colors['shadow_light'])
        self.root.after(100, lambda: button.configure(bg=original_bg))
    
    def select_file(self):
        """파일 선택 대화상자"""
        file_path = filedialog.askopenfilename(
            title="전자책 검토자 등록 - 엑셀 파일 선택",
            filetypes=[
                ("Excel files", "*.xlsx *.xls"),
                ("CSV files", "*.csv"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            self.excel_file_path = file_path
            self.load_data_preview()
            
            file_name = os.path.basename(file_path)
            self.log_message(f"📁 파일 선택됨: {file_name}", "INFO")
    
    def load_data_preview(self):
        """데이터 미리보기 로드"""
        try:
            self.data_df = self.registerer.read_data_from_source(self.excel_file_path)
            
            # 빈 상태 레이블 숨기기
            self.empty_state_label.pack_forget()
            
            # 기존 데이터 행들 제거
            for widget in self.data_list_frame.winfo_children():
                if widget != self.empty_state_label:
                    widget.destroy()
            
            # 데이터 행들을 카드 스타일로 표시 (최대 10행)
            for index, row in self.data_df.head(10).iterrows():
                self.create_data_row(row, index)
            
            # 더 많은 데이터가 있으면 표시
            if len(self.data_df) > 10:
                more_label = tk.Label(
                    self.data_list_frame,
                    text=f"... 그리고 {len(self.data_df) - 10}개 행 더",
                    font=self.fonts['callout'],
                    fg=self.colors['text_secondary'],
                    bg=self.colors['card_bg']
                )
                more_label.pack(pady=(12, 0))
            
            # UI 업데이트
            self.start_button.config(state="normal")
            self.stats_badge.config(text=f"{len(self.data_df)}개 행")
            self.total_label.config(text=f"전체: {len(self.data_df)}")
            
            # 파일 정보 업데이트
            file_name = os.path.basename(self.excel_file_path)
            file_size = os.path.getsize(self.excel_file_path)
            size_mb = file_size / (1024 * 1024)
            self.file_info_label.config(
                text=f"📄 {file_name} • {size_mb:.1f}MB • {len(self.data_df)}개 행"
            )
            
            # 상태 업데이트
            self.update_status("준비 완료", "success")
            
            self.log_message(f"✅ 데이터 로드 완료: {len(self.data_df)}개 행", "SUCCESS")
            
        except Exception as e:
            messagebox.showerror("오류", f"파일 읽기 실패:\n{str(e)}")
            self.log_message(f"❌ 파일 읽기 실패: {str(e)}", "ERROR")
    
    def create_data_row(self, row, index):
        """데이터 행을 카드 스타일로 생성"""
        row_frame = tk.Frame(
            self.data_list_frame,
            bg=self.colors['bg_secondary'] if index % 2 == 0 else self.colors['card_bg'],
            relief='flat',
            bd=0
        )
        row_frame.pack(fill=tk.X, pady=2)
        
        # 행 내용
        content_frame = tk.Frame(
            row_frame,
            bg=row_frame.cget('bg')
        )
        content_frame.pack(fill=tk.X, padx=16, pady=8)
        
        # 이름
        name_frame = tk.Frame(content_frame, bg=row_frame.cget('bg'))
        name_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tk.Label(
            name_frame,
            text=str(row['이름']),
            font=self.fonts['body_medium'],
            fg=self.colors['text_primary'],
            bg=row_frame.cget('bg')
        ).pack(anchor=tk.W)
        
        # 도서명
        book_frame = tk.Frame(content_frame, bg=row_frame.cget('bg'))
        book_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tk.Label(
            book_frame,
            text=str(row['도서명']),
            font=self.fonts['callout'],
            fg=self.colors['text_secondary'],
            bg=row_frame.cget('bg')
        ).pack(anchor=tk.W)
        
        # 이메일
        email_frame = tk.Frame(content_frame, bg=row_frame.cget('bg'))
        email_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tk.Label(
            email_frame,
            text=str(row['지메일']),
            font=self.fonts['callout'],
            fg=self.colors['accent_blue'],
            bg=row_frame.cget('bg')
        ).pack(anchor=tk.W)
    
    def update_status(self, text, status_type="normal"):
        """상태 업데이트"""
        self.status_label.config(text=text)
        
        if status_type == "success":
            self.status_indicator.config(fg=self.colors['accent_mint'])
        elif status_type == "error":
            self.status_indicator.config(fg=self.colors['accent_red'])
        elif status_type == "warning":
            self.status_indicator.config(fg=self.colors['accent_orange'])
        elif status_type == "running":
            self.status_indicator.config(fg=self.colors['accent_blue'])
        else:
            self.status_indicator.config(fg=self.colors['text_tertiary'])
    
    def log_message(self, message, level="INFO"):
        """로그 메시지 출력 (레벨별 색상 적용)"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        # 로그 레벨에 따른 색상 태그 적용
        start_index = self.log_text.index(tk.END)
        self.log_text.insert(tk.END, log_entry)
        end_index = self.log_text.index(tk.END)
        
        if level in ["INFO", "WARNING", "ERROR", "SUCCESS"]:
            self.log_text.tag_add(level, start_index, end_index)
        
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def update_progress(self, current, total, status_text="", success_count=0, failed_count=0):
        """진행률 업데이트"""
        percentage = (current / total) * 100 if total > 0 else 0
        self.progress_bar['value'] = percentage
        
        if status_text:
            progress_text = status_text
        else:
            progress_text = f"진행률: {current}/{total} ({percentage:.1f}%)"
        
        self.progress_label.config(text=progress_text)
        
        # 세부 통계 업데이트
        self.success_label.config(text=f"성공: {success_count}")
        self.failed_label.config(text=f"실패: {failed_count}")
        self.total_label.config(text=f"전체: {total}")
        
        # 상태 인디케이터 업데이트
        if current > 0:
            self.update_status(f"진행 중 {percentage:.0f}%", "running")
        
        self.root.update_idletasks()
    
    def start_registration(self):
        """등록 시작"""
        if self.data_df is None:
            messagebox.showerror("오류", "먼저 엑셀 파일을 선택해주세요.")
            return
        
        # 확인 대화상자
        if not messagebox.askyesno(
            "등록 시작", 
            f"총 {len(self.data_df)}개의 검토자를 등록하시겠습니까?\n\n⚠️ 주의사항:\n• 프로세스 중에 브라우저를 닫지 마세요\n• 로그인이 필요할 수 있습니다"
        ):
            return
        
        self.stop_requested = False
        
        # 버튼 상태 변경
        self.start_button.config(state="disabled", bg=self.colors['border_light'])
        self.stop_button.config(state="normal")
        
        # 진행률 초기화
        self.progress_bar['value'] = 0
        self.progress_label.config(text="시작 중...")
        self.success_label.config(text="성공: 0")
        self.failed_label.config(text="실패: 0")
        
        # 상태 업데이트
        self.update_status("등록 시작", "running")
        
        # 별도 스레드에서 등록 실행
        self.registration_thread = threading.Thread(target=self.run_registration)
        self.registration_thread.daemon = True
        self.registration_thread.start()
    
    def run_registration(self):
        """등록 실행 (별도 스레드)"""
        try:
            self.log_message("🚀 등록 프로세스 시작", "SUCCESS")
            self.log_message("� 브라우저가 열리면 Google Books Partner Center에 로그인해주세요", "INFO")
            self.log_message("⚠️ 프로세스 중에 브라우저를 닫지 마세요", "WARNING")
            
            results = self.registerer.process_registration(
                self.data_df,
                progress_callback=self.update_progress_with_details
            )
            
            # 결과 요약
            success_count = len([r for r in results if r['status'] == 'SUCCESS'])
            failed_count = len([r for r in results if r['status'] == 'FAILED'])
            
            if success_count > 0:
                self.log_message(f"🎉 등록 완료! 성공 {success_count}개, 실패 {failed_count}개", "SUCCESS")
                self.update_status("등록 완료", "success")
            else:
                self.log_message(f"⚠️ 등록 완료 - 성공 {success_count}개, 실패 {failed_count}개", "WARNING")
                self.update_status("완료 (오류 있음)", "warning")
            
            # UI 업데이트
            self.root.after(0, self.registration_completed)
            
        except Exception as e:
            self.log_message(f"❌ 등록 실패: {str(e)}", "ERROR")
            self.update_status("등록 실패", "error")
            self.root.after(0, self.registration_completed)
    
    def update_progress_with_details(self, current, total, status_text=""):
        """진행률 업데이트 (결과 포함)"""
        # 현재 결과 집계
        if hasattr(self.registerer, 'registration_results'):
            success_count = len([r for r in self.registerer.registration_results if r.get('status') == 'SUCCESS'])
            failed_count = len([r for r in self.registerer.registration_results if r.get('status') == 'FAILED'])
        else:
            success_count = 0
            failed_count = 0
        
        self.update_progress(current, total, status_text, success_count, failed_count)
    
    def stop_registration(self):
        """등록 중지"""
        self.stop_requested = True
        self.log_message("⏹ 등록 중지 요청", "WARNING")
        self.stop_button.config(state="disabled")
        self.update_status("중지 중...", "warning")
    
    def registration_completed(self):
        """등록 완료 후 UI 업데이트"""
        self.start_button.config(state="normal", bg=self.colors['accent_mint'])
        self.stop_button.config(state="disabled")
        
        self.progress_label.config(text="완료 ✅")
        if self.progress_bar['value'] < 100:
            self.progress_bar['value'] = 100
    
    def save_results(self):
        """결과 저장"""
        try:
            output_file = self.registerer.save_results()
            if output_file:
                messagebox.showinfo("완료", f"결과가 저장되었습니다:\n\n📁 {output_file}\n\n파일을 열어보시겠습니까?")
                self.log_message(f"💾 결과 저장 완료: {output_file}", "SUCCESS")
                # 파일 열기 옵션
                if messagebox.askyesno("파일 열기", "저장된 결과 파일을 열어보시겠습니까?"):
                    os.startfile(output_file)
            else:
                messagebox.showerror("오류", "결과 저장에 실패했습니다.")
        except Exception as e:
            messagebox.showerror("오류", f"결과 저장 실패:\n{str(e)}")
            self.log_message(f"❌ 결과 저장 실패: {str(e)}", "ERROR")
    
    def run(self):
        """GUI 실행"""
        self.root.mainloop()


def main():
    """메인 함수"""
    try:
        print("🚀 전자책 검토자 자동 등록 시스템 시작")
        print("🎨 토스/애플 스타일 UI 적용")
        print("=" * 50)
        
        # GUI 실행
        app = EbookRegistrationGUI()
        
        # 시작 로그 메시지
        app.log_message("🎉 전자책 검토자 자동 등록 시스템에 오신 것을 환영합니다!", "SUCCESS")
        app.log_message("� 1단계: 파일을 선택해주세요", "INFO")
        app.log_message("� 2단계: 데이터를 확인하세요", "INFO")
        app.log_message("▶ 3단계: 등록을 시작하세요", "INFO")
        
        app.run()
        
    except Exception as e:
        print(f"❌ 프로그램 실행 오류: {str(e)}")
        input("아무 키나 눌러 종료...")


if __name__ == "__main__":
    main()
