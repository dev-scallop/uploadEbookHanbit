"""
WordPress 자동 업로드 모듈
"""
from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods import posts, media
from wordpress_xmlrpc.compat import xmlrpc_client
from typing import Optional
import logging
from pathlib import Path

import config
from src.data.book_model import Book

logger = logging.getLogger(__name__)


class WordPressUploader:
    """WordPress에 자동으로 포스트를 업로드하는 클래스"""
    
    def __init__(self, url: str = None, username: str = None, password: str = None):
        """
        초기화
        
        Args:
            url: WordPress 사이트 URL
            username: 사용자명
            password: 앱 비밀번호
        """
        self.url = url or config.WORDPRESS_URL
        self.username = username or config.WORDPRESS_USERNAME
        self.password = password or config.WORDPRESS_PASSWORD
        
        if not all([self.url, self.username, self.password]):
            logger.warning("WordPress 인증 정보가 완전하지 않습니다.")
            self.client = None
        else:
            try:
                xmlrpc_url = f"{self.url}/xmlrpc.php"
                self.client = Client(xmlrpc_url, self.username, self.password)
                logger.info(f"WordPress 클라이언트 초기화 완료: {self.url}")
            except Exception as e:
                logger.error(f"WordPress 클라이언트 초기화 실패: {e}")
                self.client = None
    
    def upload_image(self, image_path: Path, title: str = "") -> Optional[str]:
        """
        이미지를 WordPress 미디어 라이브러리에 업로드
        
        Args:
            image_path: 이미지 파일 경로
            title: 이미지 제목
            
        Returns:
            업로드된 이미지 URL
        """
        if not self.client:
            logger.error("WordPress 클라이언트가 초기화되지 않았습니다.")
            return None
        
        try:
            # 이미지 파일 읽기
            with open(image_path, 'rb') as img_file:
                data = {
                    'name': image_path.name,
                    'type': 'image/jpeg' if image_path.suffix.lower() in ['.jpg', '.jpeg'] else 'image/png',
                    'bits': xmlrpc_client.Binary(img_file.read()),
                }
                
                if title:
                    data['title'] = title
            
            # 업로드
            response = self.client.call(media.UploadFile(data))
            image_url = response['url']
            
            logger.info(f"이미지 업로드 완료: {image_url}")
            return image_url
            
        except Exception as e:
            logger.error(f"이미지 업로드 실패: {e}")
            return None
    
    def create_post(
        self,
        book: Book,
        html_content: str,
        cover_image_path: Path = None,
        status: str = 'draft'
    ) -> Optional[str]:
        """
        WordPress 포스트 생성
        
        Args:
            book: Book 객체
            html_content: HTML 콘텐츠
            cover_image_path: 표지 이미지 경로
            status: 포스트 상태 (draft, publish)
            
        Returns:
            생성된 포스트 ID
        """
        if not self.client:
            logger.error("WordPress 클라이언트가 초기화되지 않았습니다.")
            return None
        
        try:
            # 포스트 생성
            post = WordPressPost()
            post.title = book.title
            post.content = html_content
            post.post_status = status
            
            # 카테고리 및 태그 설정
            post.terms_names = {
                'post_tag': book.keywords,
                'category': ['도서']
            }
            
            # 커스텀 필드 설정
            post.custom_fields = [
                {'key': 'author', 'value': book.author},
                {'key': 'publisher', 'value': book.publisher},
                {'key': 'isbn', 'value': book.isbn},
                {'key': 'price', 'value': str(book.price)},
                {'key': 'publish_date', 'value': book.publish_date},
            ]
            
            # 표지 이미지 업로드 및 설정
            if cover_image_path and cover_image_path.exists():
                image_url = self.upload_image(cover_image_path, title=f"{book.title} 표지")
                if image_url:
                    # 썸네일로 설정 (추가 구현 필요)
                    pass
            
            # 포스트 업로드
            post_id = self.client.call(posts.NewPost(post))
            
            logger.info(f"WordPress 포스트 생성 완료: {book.title} (ID: {post_id})")
            return post_id
            
        except Exception as e:
            logger.error(f"WordPress 포스트 생성 실패: {e}")
            return None
    
    def update_post(
        self,
        post_id: str,
        book: Book,
        html_content: str,
        status: str = None
    ) -> bool:
        """
        기존 WordPress 포스트 업데이트
        
        Args:
            post_id: 포스트 ID
            book: Book 객체
            html_content: HTML 콘텐츠
            status: 포스트 상태
            
        Returns:
            성공 여부
        """
        if not self.client:
            logger.error("WordPress 클라이언트가 초기화되지 않았습니다.")
            return False
        
        try:
            post = WordPressPost()
            post.title = book.title
            post.content = html_content
            
            if status:
                post.post_status = status
            
            post.terms_names = {
                'post_tag': book.keywords,
            }
            
            # 업데이트
            self.client.call(posts.EditPost(post_id, post))
            
            logger.info(f"WordPress 포스트 업데이트 완료: {book.title} (ID: {post_id})")
            return True
            
        except Exception as e:
            logger.error(f"WordPress 포스트 업데이트 실패: {e}")
            return False
    
    def publish_post(self, post_id: str) -> bool:
        """
        드래프트 포스트를 발행
        
        Args:
            post_id: 포스트 ID
            
        Returns:
            성공 여부
        """
        if not self.client:
            logger.error("WordPress 클라이언트가 초기화되지 않았습니다.")
            return False
        
        try:
            post = self.client.call(posts.GetPost(post_id))
            post.post_status = 'publish'
            self.client.call(posts.EditPost(post_id, post))
            
            logger.info(f"포스트 발행 완료 (ID: {post_id})")
            return True
            
        except Exception as e:
            logger.error(f"포스트 발행 실패: {e}")
            return False
    
    def batch_upload(
        self,
        books: list[Book],
        html_contents: list[str],
        status: str = 'draft'
    ) -> list[str]:
        """
        여러 포스트를 배치로 업로드
        
        Args:
            books: Book 객체 리스트
            html_contents: HTML 콘텐츠 리스트
            status: 포스트 상태
            
        Returns:
            생성된 포스트 ID 리스트
        """
        post_ids = []
        
        for book, html in zip(books, html_contents):
            try:
                post_id = self.create_post(book, html, status=status)
                if post_id:
                    post_ids.append(post_id)
            except Exception as e:
                logger.error(f"배치 업로드 실패 ({book.title}): {e}")
                continue
        
        logger.info(f"배치 업로드 완료: {len(post_ids)}개 포스트 생성")
        return post_ids
