"""
Google Sheets 연동 모듈
"""
import gspread
from google.oauth2.service_account import Credentials
from typing import List, Optional
import logging
from pathlib import Path
from datetime import datetime
import re
import requests
import csv
import io

from .book_model import Book
import config

logger = logging.getLogger(__name__)


class GoogleSheetsConnector:
    """Google Sheets와 연동하여 도서 데이터를 가져오는 클래스"""
    
    def __init__(self, credentials_file: str = None, sheet_id: str = None):
        """
        초기화
        
        Args:
            credentials_file: Google Sheets API 인증 파일 경로
            sheet_id: Google Sheets ID
        """
        self.credentials_file = credentials_file or config.GOOGLE_SHEETS_CREDENTIALS
        self.sheet_id = sheet_id or config.GOOGLE_SHEET_ID
        self.client = None
        self.spreadsheet = None
        
    def connect(self):
        """Google Sheets API에 연결"""
        try:
            # 인증 정보 설정
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            
            credentials_path = Path(self.credentials_file)
            if not credentials_path.exists():
                raise FileNotFoundError(
                    f"인증 파일을 찾을 수 없습니다: {self.credentials_file}\n"
                    "Google Cloud Console에서 서비스 계정을 생성하고 credentials.json을 다운로드하세요."
                )
            
            creds = Credentials.from_service_account_file(
                self.credentials_file, scopes=scope
            )
            self.client = gspread.authorize(creds)
            
            # 스프레드시트 열기
            self.spreadsheet = self.client.open_by_key(self.sheet_id)
            logger.info(f"Google Sheets 연결 성공: {self.spreadsheet.title}")
            
        except Exception as e:
            logger.error(f"Google Sheets 연결 실패: {e}")
            raise
    
    def _normalize_record(self, record: dict) -> Book:
        """시트 레코드를 Book 모델로 정규화"""
        lowered = {str(k).strip().lower(): v for k, v in record.items()}

        normalized = {
            'title': str(lowered.get('title', '')).strip(),
            'author': str(lowered.get('author', '')).strip(),
            'keywords': lowered.get('keywords', ''),
            'description': lowered.get('description', ''),
            'cover_image_url': lowered.get('cover_url', '') or lowered.get('cover image url', '') or lowered.get('cover_image_url', ''),
        }

        # 혼용 필드 우선 적용
        for key in ['isbn', 'publisher', 'publish_date', 'price', 'table_of_contents']:
            if key in lowered and str(lowered[key]).strip():
                normalized[key] = lowered[key]

        # 필수값 보정
        isbn = str(normalized.get('isbn', '')).strip()
        if not isbn:
            ts = datetime.now().strftime('%y%m%d%H%M%S')
            isbn = f"978{ts}"[-13:]
        normalized['isbn'] = isbn

        publisher = str(normalized.get('publisher', '')).strip() or 'N/A'
        normalized['publisher'] = publisher

        publish_date = str(normalized.get('publish_date', '')).strip() or datetime.now().strftime('%Y-%m-%d')
        normalized['publish_date'] = publish_date

        price = normalized.get('price', 0)
        if isinstance(price, str):
            price = re.sub(r"[^0-9]", "", price)
            price = int(price) if price else 0
        elif price is None:
            price = 0
        normalized['price'] = int(price)

        if not isinstance(normalized.get('keywords'), list):
            normalized['keywords'] = str(normalized.get('keywords', '')).strip()

        return Book.from_dict(normalized)

    def _get_books_from_public_csv(self, gid: Optional[str] = None) -> List[Book]:
        """공개 시트를 CSV로 읽어 Book 리스트로 반환 (자격 증명 불필요)"""
        if not config.GOOGLE_SHEET_ID:
            raise ValueError("GOOGLE_SHEET_ID가 설정되어 있지 않습니다 (.env).")
        gid = gid or config.GOOGLE_SHEET_GID or '0'
        csv_url = f"https://docs.google.com/spreadsheets/d/{config.GOOGLE_SHEET_ID}/export?format=csv&gid={gid}"

        try:
            resp = requests.get(csv_url, timeout=20)
            resp.raise_for_status()
        except Exception as e:
            logger.error(f"공개 시트 CSV 요청 실패: {e}")
            raise

        text = resp.content.decode('utf-8-sig', errors='replace')
        reader = csv.DictReader(io.StringIO(text))
        records = list(reader)
        logger.info(f"공개 시트에서 {len(records)}개 행 로드 (gid={gid})")

        books: List[Book] = []
        for record in records:
            try:
                book = self._normalize_record(record)
                if book.is_valid():
                    books.append(book)
                else:
                    logger.warning(f"유효하지 않은 도서 데이터: {record.get('title', 'Unknown')}")
            except Exception as e:
                logger.error(f"도서 데이터 변환 실패: {e}")
                continue
        logger.info(f"공개 시트 유효 도서: {len(books)}개")
        return books

    def get_all_books(self, worksheet_name: str = None) -> List[Book]:
        """
        모든 도서 데이터를 가져옴
        
        Args:
            worksheet_name: 워크시트 이름 (기본값: 첫 번째 시트)
            
        Returns:
            Book 객체 리스트
        """
        # 공개 시트 모드 또는 자격증명 파일이 없으면 CSV로 조회
        cred_path = Path(self.credentials_file) if self.credentials_file else None
        if config.GOOGLE_SHEET_PUBLIC or not cred_path or not cred_path.exists():
            return self._get_books_from_public_csv()

        if not self.client:
            self.connect()
        
        try:
            # 워크시트 선택
            if worksheet_name:
                worksheet = self.spreadsheet.worksheet(worksheet_name)
            else:
                worksheet = self.spreadsheet.get_worksheet(0)
            
            # 모든 데이터 가져오기
            records = worksheet.get_all_records()
            logger.info(f"{len(records)}개의 도서 데이터를 가져왔습니다.")
            
            # Book 객체로 변환
            books = []
            for record in records:
                try:
                    book = self._normalize_record(record)
                    if book.is_valid():
                        books.append(book)
                    else:
                        logger.warning(f"유효하지 않은 도서 데이터: {record.get('title', 'Unknown')}")
                except Exception as e:
                    logger.error(f"도서 데이터 변환 실패: {e}")
                    continue
            
            logger.info(f"{len(books)}개의 유효한 도서 데이터를 로드했습니다.")
            return books
            
        except Exception as e:
            logger.error(f"도서 데이터 가져오기 실패: {e}")
            raise
    
    def get_book_by_isbn(self, isbn: str, worksheet_name: str = None) -> Optional[Book]:
        """
        ISBN으로 특정 도서 데이터를 가져옴
        
        Args:
            isbn: 검색할 ISBN
            worksheet_name: 워크시트 이름
            
        Returns:
            Book 객체 또는 None
        """
        books = self.get_all_books(worksheet_name)
        
        for book in books:
            if book.isbn == isbn:
                return book
        
        logger.warning(f"ISBN {isbn}에 해당하는 도서를 찾을 수 없습니다.")
        return None
    
    def add_book(self, book: Book, worksheet_name: str = None):
        """
        새 도서 데이터를 시트에 추가
        
        Args:
            book: 추가할 Book 객체
            worksheet_name: 워크시트 이름
        """
        if not self.client:
            self.connect()
        
        try:
            # 워크시트 선택
            if worksheet_name:
                worksheet = self.spreadsheet.worksheet(worksheet_name)
            else:
                worksheet = self.spreadsheet.get_worksheet(0)
            
            # 데이터 행 추가
            row = [
                book.isbn,
                book.title,
                book.author,
                book.publisher,
                book.publish_date,
                book.price,
                book.get_keywords_string(),
                book.description,
                book.table_of_contents,
                book.cover_image_url,
            ]
            
            worksheet.append_row(row)
            logger.info(f"도서 추가 완료: {book.title}")
            
        except Exception as e:
            logger.error(f"도서 추가 실패: {e}")
            raise
    
    def update_book(self, book: Book, worksheet_name: str = None):
        """
        기존 도서 데이터를 업데이트
        
        Args:
            book: 업데이트할 Book 객체
            worksheet_name: 워크시트 이름
        """
        if not self.client:
            self.connect()
        
        try:
            # 워크시트 선택
            if worksheet_name:
                worksheet = self.spreadsheet.worksheet(worksheet_name)
            else:
                worksheet = self.spreadsheet.get_worksheet(0)
            
            # ISBN으로 행 찾기
            cell = worksheet.find(book.isbn)
            if cell:
                row_number = cell.row
                
                # 데이터 업데이트
                row = [
                    book.isbn,
                    book.title,
                    book.author,
                    book.publisher,
                    book.publish_date,
                    book.price,
                    book.get_keywords_string(),
                    book.description,
                    book.table_of_contents,
                    book.cover_image_url,
                ]
                
                worksheet.delete_rows(row_number)
                worksheet.insert_row(row, row_number)
                logger.info(f"도서 업데이트 완료: {book.title}")
            else:
                logger.warning(f"ISBN {book.isbn}에 해당하는 도서를 찾을 수 없습니다.")
                
        except Exception as e:
            logger.error(f"도서 업데이트 실패: {e}")
            raise
