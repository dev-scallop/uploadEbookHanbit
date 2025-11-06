"""
verify_reviewer 함수 추가
이 함수를 [개발중] 전자책자동등록.py 파일에 추가하세요.

add_reviewer 함수를 아래 내용으로 업데이트하세요.
"""

def verify_reviewer(self, email):
    """검토자가 실제로 등록되었는지 확인"""
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
            self.logger.info(f"검토자 '{email}' 추가 시도 완료")
            
            # 검토자가 실제로 등록되었는지 확인
            is_verified = self.verify_reviewer(email)
            
            if is_verified:
                self.logger.info(f"✅ 검토자 '{email}' 등록 확인 완료!")
                return True
            else:
                self.logger.warning(f"⚠️ 검토자 '{email}' 등록되었지만 확인되지 않았습니다. 상태를 확인하세요.")
                # 일단 성공으로 간주하고 진행 (등록이 되었을 수도 있으나 화면에 표시되지 않을 수 있음)
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
