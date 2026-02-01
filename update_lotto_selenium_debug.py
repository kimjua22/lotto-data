#!/usr/bin/env python3
# update_lotto_selenium_debug.py
"""
Selenium 디버깅 버전
HTML 응답 확인 및 상세 로그
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import json
import sys
import time
import re
from datetime import datetime

# 설정
JSON_FILE = 'lotto_json.json'
LOTTO_URL = 'https://www.dhlottery.co.kr/lt645/result'
DEBUG_HTML_FILE = 'debug_page.html'

def setup_driver():
    """WebDriver 설정"""
    print("🌐 Chrome WebDriver 초기화 중...")
    
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    try:
        service = Service('/usr/bin/chromedriver')
        driver = webdriver.Chrome(service=service, options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        print("✅ WebDriver 초기화 완료")
        return driver
    except Exception as e:
        print(f"❌ WebDriver 초기화 실패: {e}")
        sys.exit(1)

def save_page_source(driver, filename=DEBUG_HTML_FILE):
    """페이지 소스 저장 (디버깅용)"""
    try:
        html = driver.page_source
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"📄 페이지 소스 저장: {filename} ({len(html)} bytes)")
        
        # HTML 내용 일부 출력
        print(f"\n페이지 내용 앞부분 (500자):")
        print("=" * 60)
        print(html[:500])
        print("=" * 60)
        
        # 404 체크
        if '404' in html or 'Not Found' in html or 'ERROR' in html:
            print("⚠️  404 에러 페이지일 가능성!")
        
        # DOCTYPE 체크
        if '<!DOCTYPE' in html or '<html' in html:
            print("✅ HTML 응답 확인")
        else:
            print("❓ HTML이 아닐 수도?")
        
        return html
    except Exception as e:
        print(f"❌ 페이지 소스 저장 실패: {e}")
        return ""

def check_page_content(driver):
    """페이지 내용 분석"""
    print("\n🔍 페이지 내용 분석:")
    
    try:
        # 제목
        title = driver.title
        print(f"  제목: {title}")
        
        # URL
        current_url = driver.current_url
        print(f"  현재 URL: {current_url}")
        
        # body 텍스트
        body = driver.find_element(By.TAG_NAME, 'body')
        body_text = body.text[:200]
        print(f"  body 텍스트: {body_text}...")
        
        # 특정 요소 확인
        elements_to_check = [
            ('h4.title', '제목'),
            ('.win .num.ball', '당첨번호'),
            ('.bonus .num.ball', '보너스'),
            ('#drwNo', '회차 선택'),
        ]
        
        for selector, name in elements_to_check:
            try:
                elems = driver.find_elements(By.CSS_SELECTOR, selector)
                print(f"  {name} ({selector}): {len(elems)}개")
            except:
                print(f"  {name} ({selector}): 없음")
        
    except Exception as e:
        print(f"  ❌ 분석 실패: {e}")

def try_alternative_url(driver):
    """대체 URL 시도"""
    alternative_urls = [
        'https://www.dhlottery.co.kr/gameResult.do?method=byWin',
        'https://dhlottery.co.kr/lt645/result',
        'http://www.dhlottery.co.kr/lt645/result',
    ]
    
    print("\n🔄 대체 URL 시도:")
    
    for url in alternative_urls:
        try:
            print(f"\n  시도: {url}")
            driver.get(url)
            time.sleep(3)
            
            html = driver.page_source
            print(f"    응답 크기: {len(html)} bytes")
            
            if '<!DOCTYPE' in html and '404' not in html:
                print(f"    ✅ 정상 응답!")
                check_page_content(driver)
                return True
            else:
                print(f"    ❌ 실패")
        except Exception as e:
            print(f"    ❌ 오류: {e}")
    
    return False

def extract_from_json_endpoint(driver):
    """JSON 엔드포인트 직접 접근 시도"""
    json_url = 'https://www.dhlottery.co.kr/lt645/selectPastLt645Info.do?srchLtEpsd=all'
    
    print(f"\n🎯 JSON 엔드포인트 직접 접근:")
    print(f"  URL: {json_url}")
    
    try:
        driver.get(json_url)
        time.sleep(3)
        
        # pre 태그에서 JSON 찾기
        try:
            pre = driver.find_element(By.TAG_NAME, 'pre')
            json_text = pre.text
            print(f"  ✅ pre 태그에서 JSON 발견: {len(json_text)} bytes")
            print(f"  내용 앞부분: {json_text[:200]}...")
            
            # JSON 파싱 시도
            data = json.loads(json_text)
            print(f"  ✅ JSON 파싱 성공!")
            return data
        except:
            pass
        
        # body에서 JSON 찾기
        try:
            body = driver.find_element(By.TAG_NAME, 'body')
            body_text = body.text
            print(f"  body 텍스트: {len(body_text)} bytes")
            
            if body_text.strip().startswith('{'):
                data = json.loads(body_text)
                print(f"  ✅ body에서 JSON 파싱 성공!")
                return data
        except:
            pass
        
        print(f"  ❌ JSON을 찾을 수 없음")
        
        # HTML 저장
        save_page_source(driver, 'debug_json_endpoint.html')
        
    except Exception as e:
        print(f"  ❌ 오류: {e}")
    
    return None

def main():
    print("=" * 60)
    print("🐛 Selenium 디버깅 모드")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    driver = None
    
    try:
        # 1. WebDriver 초기화
        driver = setup_driver()
        
        # 2. 메인 페이지 접속
        print(f"\n📡 메인 페이지 접속: {LOTTO_URL}")
        driver.get(LOTTO_URL)
        time.sleep(5)
        
        # 3. 페이지 소스 저장
        html = save_page_source(driver)
        
        # 4. 페이지 내용 분석
        check_page_content(driver)
        
        # 5. 대체 URL 시도
        if not try_alternative_url(driver):
            print("\n⚠️  모든 대체 URL 실패")
        
        # 6. JSON 엔드포인트 직접 접근
        json_data = extract_from_json_endpoint(driver)
        
        if json_data:
            print("\n🎉 JSON 데이터 추출 성공!")
            
            # 간단한 저장
            with open(JSON_FILE, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=4)
            
            print(f"💾 JSON 파일 저장: {JSON_FILE}")
            return 0
        else:
            print("\n❌ JSON 데이터를 추출할 수 없습니다")
            print("\n📋 디버깅 정보:")
            print(f"  - 페이지 소스: {DEBUG_HTML_FILE}")
            print(f"  - JSON 엔드포인트: debug_json_endpoint.html")
            print("\n💡 이 파일들을 확인해서 문제를 파악하세요")
            return 1
            
    except Exception as e:
        print(f"\n❌ 오류: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        if driver:
            driver.quit()
            print("\n🌐 WebDriver 종료")

if __name__ == '__main__':
    sys.exit(main())
