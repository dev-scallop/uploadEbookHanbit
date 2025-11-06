"""
도서 데이터 모델
"""
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class Book:
    """도서 정보를 담는 데이터 클래스"""
    
    # 필수 필드
    isbn: str
    title: str
    author: str
    publisher: str
    publish_date: str
    price: int
    
    # 선택 필드
    keywords: List[str] = field(default_factory=list)
    description: str = ""
    table_of_contents: str = ""
    cover_image_url: str = ""
    
    # 생성된 콘텐츠 (AI로 생성)
    generated_intro: Optional[str] = None
    generated_marketing_copy: Optional[str] = None
    generated_author_bio: Optional[str] = None
    generated_images: List[str] = field(default_factory=list)
    
    # 메타 정보
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """초기화 후 처리"""
        # 키워드가 문자열인 경우 리스트로 변환
        if isinstance(self.keywords, str):
            self.keywords = [k.strip() for k in self.keywords.split(',') if k.strip()]
        
        # 생성 시간 설정
        if self.created_at is None:
            self.created_at = datetime.now()
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Book':
        """딕셔너리로부터 Book 객체 생성"""
        # 필수 필드만 추출
        book_data = {
            'isbn': str(data.get('isbn', '')),
            'title': str(data.get('title', '')),
            'author': str(data.get('author', '')),
            'publisher': str(data.get('publisher', '')),
            'publish_date': str(data.get('publish_date', '')),
            'price': int(data.get('price', 0)),
        }
        
        # 선택 필드 추가
        if 'keywords' in data:
            book_data['keywords'] = data['keywords']
        if 'description' in data:
            book_data['description'] = data['description']
        if 'table_of_contents' in data:
            book_data['table_of_contents'] = data['table_of_contents']
        if 'cover_image_url' in data:
            book_data['cover_image_url'] = data['cover_image_url']
        
        return cls(**book_data)
    
    def to_dict(self) -> dict:
        """Book 객체를 딕셔너리로 변환"""
        return {
            'isbn': self.isbn,
            'title': self.title,
            'author': self.author,
            'publisher': self.publisher,
            'publish_date': self.publish_date,
            'price': self.price,
            'keywords': self.keywords,
            'description': self.description,
            'table_of_contents': self.table_of_contents,
            'cover_image_url': self.cover_image_url,
            'generated_intro': self.generated_intro,
            'generated_marketing_copy': self.generated_marketing_copy,
            'generated_author_bio': self.generated_author_bio,
            'generated_images': self.generated_images,
        }
    
    def is_valid(self) -> bool:
        """필수 필드가 모두 채워져 있는지 검증"""
        required_fields = [
            self.isbn,
            self.title,
            self.author,
            self.publisher,
            self.publish_date,
        ]
        return all(field for field in required_fields)
    
    def get_keywords_string(self) -> str:
        """키워드를 문자열로 반환"""
        return ', '.join(self.keywords)
    
    def __repr__(self) -> str:
        return f"Book(isbn='{self.isbn}', title='{self.title}', author='{self.author}')"
