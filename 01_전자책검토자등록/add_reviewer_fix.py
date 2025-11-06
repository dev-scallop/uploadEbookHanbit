"""
add_reviewer 함수 수정본
이 함수를 [개발중] 전자책자동등록.py 파일에 있는 동일한 함수와 교체하세요.
"""

# 콘텐츠 검토 페이지 상태를 추적하기 위한 클래스 속성 추가
current_review_page = None

def add_reviewer(self, email):
    """검토자 추가"""
    try:
        self.logger.info(f"검토자 추가 시작: {email}")
        
        wait = WebDriverWait(self.driver, 10)  # 웨이팅 시간을 10초로 줄임
        
        # 현재 URL 확인
        current_url = self.driver.current_url
        
        # 이미 검토자 추가 페이지에 있는지 확인
        if self.current_review_page and "/review/" in current_url:
            self.logger.info("이미 콘텐츠 검토 페이지에 있습니다. 검토자 추가 진행...")
        else:
            # 4단계: 콘텐츠 검토 아이템 클릭
            try:
                self.logger.info("콘텐츠 검토 아이템 클릭 시도...")
                
                # 콘텐츠 검토 화면으로의 이동을 최적화
                # 먼저 더 일반적인 셀렉터를 시도하고, 그 후에 구체적인 XPath를 시도
                content_review_selectors = [
                    "//a[contains(@href, 'review')]",
                    "//a[contains(text(), '콘텐츠') and contains(text(), '검토')]",
                    "//content-review-item[1]//a",
                    "//content-review-item//span[contains(text(), '콘텐츠')]",
                    "//div[contains(@class, 'review-item')]//a",
                    "/html/body/pfe-app/partner-center/div[2]/div/ng-component/ng-component/div/ng-component/div/div[2]/content-review-item[1]/a/div/div[2]/span[2]"
                ]
                
                clicked = False
                for selector in content_review_selectors:
                    try:
                        # 대기 시간을 줄이고, visibility를 먼저 확인
                        elements = self.driver.find_elements(By.XPATH, selector)
                        if elements:
                            element = elements[0]  # 첫 번째 요소 선택
                            element.click()
                            self.logger.info(f"콘텐츠 검토 아이템 클릭 성공: {selector}")
                            clicked = True
                            time.sleep(1)  # 로딩 대기 시간 줄임
                            break
                    except Exception as e:
                        self.logger.debug(f"셀렉터 {selector} 시도 실패: {str(e)}")
                        continue
                
                if not clicked:
                    # 현재 페이지의 모든 링크 확인
                    all_links = self.driver.find_elements(By.TAG_NAME, "a")
                    for link in all_links:
                        try:
                            link_text = link.text.lower()
                            link_href = link.get_attribute("href") or ""
                            
                            if ("review" in link_href or "검토" in link_text or "content" in link_href):
                                link.click()
                                self.logger.info(f"검토 관련 링크 찾아서 클릭: {link_text} ({link_href})")
                                clicked = True
                                time.sleep(1)
                                break
                        except:
                            continue
                
                if not clicked:
                    self.logger.error("콘텐츠 검토 아이템을 찾을 수 없습니다")
                    # 페이지 스크린샷 저장 시도
                    try:
                        screenshot_path = f"error_screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                        self.driver.save_screenshot(screenshot_path)
                        self.logger.info(f"오류 상황 스크린샷 저장: {screenshot_path}")
                    except:
                        pass
                    return False
                
                # 콘텐츠 검토 페이지 상태 저장
                self.current_review_page = self.driver.current_url
            
            except Exception as e:
                self.logger.error(f"콘텐츠 검토 아이템 클릭 실패: {str(e)}")
                return False
        
        # 5단계: 이메일 입력 필드에 지메일 주소 입력
        try:
            email_input_id = "mat-input-1"
            self.logger.info(f"이메일 입력 필드에 '{email}' 입력 시도...")
            
            # 이메일 입력 필드 찾기 최적화
            # 여러 셀렉터를 시도하되, 기다리지 않고 바로 확인
            email_selectors = [
                f"//*[@id='{email_input_id}']",
                "//input[contains(@placeholder, 'email') or contains(@placeholder, '이메일')]",
                "//input[contains(@type, 'email')]",
                "//mat-form-field//input",
                "//input[contains(@class, 'mat-input')]"
            ]
            
            email_field = None
            for selector in email_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    if elements:
                        email_field = elements[0]
                        self.logger.info(f"이메일 입력 필드 찾음: {selector}")
                        break
                except:
                    continue
            
            if not email_field:
                self.logger.error("이메일 입력 필드를 찾을 수 없습니다")
                return False
            
            # 이메일 입력
            email_field.clear()
            email_field.send_keys(email)
            self.logger.info("이메일 입력 완료")
            time.sleep(1)  # 대기 시간 줄임
            
            # Enter 키 또는 제출 버튼 클릭
            try:
                from selenium.webdriver.common.keys import Keys
                email_field.send_keys(Keys.ENTER)
                self.logger.info("Enter 키로 제출 시도")
                time.sleep(1)  # 대기 시간 줄임
            except:
                # 제출 버튼 찾아서 클릭
                submit_selectors = [
                    "//button[contains(text(), '추가') or contains(text(), 'Add')]",
                    "//button[contains(text(), '저장') or contains(text(), 'Save')]",
                    "//button[contains(text(), '확인') or contains(text(), 'OK')]",
                    "//button[@type='submit']",
                    "//mat-button-toggle[contains(text(), '추가')]"
                ]
                
                submit_clicked = False
                for selector in submit_selectors:
                    try:
                        elements = self.driver.find_elements(By.XPATH, selector)
                        if elements:
                            submit_btn = elements[0]
                            submit_btn.click()
                            self.logger.info(f"제출 버튼 클릭: {selector}")
                            submit_clicked = True
                            break
                    except:
                        continue
                
                if not submit_clicked:
                    self.logger.warning("제출 버튼을 찾지 못했습니다. Enter 키로 시도했으므로 계속 진행합니다.")
            
            time.sleep(2)  # 제출 후 대기 시간 설정
            self.logger.info(f"검토자 '{email}' 추가 완료")
            return True
            
        except Exception as e:
            import traceback
            self.logger.error(f"이메일 입력 실패: {str(e)}")
            self.logger.error(f"상세 오류: {traceback.format_exc()}")
            return False
        
    except Exception as e:
        import traceback
        self.logger.error(f"검토자 추가 실패: {str(e)}")
        self.logger.error(f"상세 오류: {traceback.format_exc()}")
        return False
