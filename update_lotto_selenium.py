#!/usr/bin/env python3
# update_lotto_selenium.py
"""
Selenium 완전 자동화 - 안정성 강화 버전
재시도 로직 및 대기 시간 증가
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
from datetime import datetime

# 설정
JSON_FILE = 'lotto_json.json'
JSON_ENDPOINT = 'https://www.dhlottery.co.kr/lt645/selectPastLt645Info.do?srchLtEpsd=all'
MAX_RETRIES = 3  # 최대 재시도 횟수

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

def get_json_from_endpoint(driver, retry=0):
    """JSON 엔드포인트에서 데이터 가져오기 (재시도 로직)"""
    
    if retry > 0:
        print(f"\n🔄 재시도 {retry}/{MAX_RETRIES}")
    
    print(f"\n📡 JSON 엔드포인트 접속: {JSON_ENDPOINT}")
    
    try:
        driver.get(JSON_ENDPOINT)
        
        # ⭐ 충분히 대기 (10초)
        print("  ⏳ 페이지 로딩 대기 (10초)...")
        time.sleep(10)
        
        print("  🔍 JSON 추출 시도...")
        
        # 방법 1: pre 태그에서 추출 (명시적 대기 사용)
        try:
            print("  [방법 1] pre 태그 검색...")
            wait = WebDriverWait(driver, 10)
            pre_elem = wait.until(EC.presence_of_element_located((By.TAG_NAME, 'pre')))
            
            json_text = pre_elem.text
            print(f"  ✅ pre 태그에서 JSON 발견: {len(json_text)} bytes")
            
            data = json.loads(json_text)
            
            if 'data' in data and 'list' in data['data']:
                count = len(data['data']['list'])
                if count > 0:
                    latest = max(item['ltEpsd'] for item in data['data']['list'])
                    print(f"  ✅ 총 {count}개 회차 (최신: {latest}회)")
                    return data
            
        except Exception as e:
            print(f"  ⚠️  pre 태그 실패: {e}")
        
        # 방법 2: body 텍스트에서 추출
        try:
            print("  [방법 2] body 텍스트 검색...")
            body_elem = driver.find_element(By.TAG_NAME, 'body')
            body_text = body_elem.text.strip()
            print(f"  body 텍스트: {len(body_text)} bytes")
            
            if body_text.startswith('{') or body_text.startswith('['):
                data = json.loads(body_text)
                
                if 'data' in data and 'list' in data['data']:
                    count = len(data['data']['list'])
                    if count > 0:
                        latest = max(item['ltEpsd'] for item in data['data']['list'])
                        print(f"  ✅ 총 {count}개 회차 (최신: {latest}회)")
                        return data
            
        except Exception as e:
            print(f"  ⚠️  body 추출 실패: {e}")
        
        # 방법 3: 페이지 소스 전체에서 추출
        try:
            print("  [방법 3] 페이지 소스 검색...")
            page_source = driver.page_source
            print(f"  페이지 소스: {len(page_source)} bytes")
            
            # <pre> 태그 내용 추출
            import re
            pre_match = re.search(r'<pre[^>]*>(.*?)</pre>', page_source, re.DOTALL)
            if pre_match:
                json_text = pre_match.group(1).strip()
                print(f"  정규식으로 pre 발견: {len(json_text)} bytes")
                
                data = json.loads(json_text)
                
                if 'data' in data and 'list' in data['data']:
                    count = len(data['data']['list'])
                    if count > 0:
                        latest = max(item['ltEpsd'] for item in data['data']['list'])
                        print(f"  ✅ 총 {count}개 회차 (최신: {latest}회)")
                        return data
            
            # JSON 객체 직접 찾기
            json_start = page_source.find('{"resultCode"')
            if json_start >= 0:
                json_end = page_source.rfind('}') + 1
                json_text = page_source[json_start:json_end]
                
                data = json.loads(json_text)
                
                if 'data' in data and 'list' in data['data']:
                    count = len(data['data']['list'])
                    if count > 0:
                        latest = max(item['ltEpsd'] for item in data['data']['list'])
                        print(f"  ✅ 페이지 소스에서 추출 성공: {count}개 회차 (최신: {latest}회)")
                        return data
            
        except Exception as e:
            print(f"  ⚠️  페이지 소스 추출 실패: {e}")
        
        # 모든 방법 실패
        if retry < MAX_RETRIES:
            print(f"\n  ⚠️  모든 추출 방법 실패, 재시도...")
            time.sleep(5)  # 5초 대기 후 재시도
            return get_json_from_endpoint(driver, retry + 1)
        else:
            print(f"\n  ❌ 최대 재시도 횟수 도달, JSON을 찾을 수 없습니다")
            return None
        
    except Exception as e:
        print(f"  ❌ 오류: {e}")
        
        if retry < MAX_RETRIES:
            print(f"\n  🔄 오류 발생, 재시도...")
            time.sleep(5)
            return get_json_from_endpoint(driver, retry + 1)
        else:
            return None

def save_json(data, filename=JSON_FILE):
    """JSON 파일로 저장"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        
        if 'data' in data and 'list' in data['data']:
            count = len(data['data']['list'])
            latest = max(item['ltEpsd'] for item in data['data']['list']) if count > 0 else 0
            
            print(f"\n💾 JSON 파일 저장 완료: {filename}")
            print(f"   총 {count}개 회차 (1~{latest}회)")
            
            # 최신 3개 회차 출력
            if count > 0:
                print(f"\n   최신 3개 회차:")
                sorted_list = sorted(data['data']['list'], key=lambda x: x['ltEpsd'], reverse=True)
                for item in sorted_list[:3]:
                    print(f"   - {item['ltEpsd']}회: {item['tm1WnNo']}, {item['tm2WnNo']}, {item['tm3WnNo']}, {item['tm4WnNo']}, {item['tm5WnNo']}, {item['tm6WnNo']} + {item['bnsWnNo']}")
        
        return True
    except Exception as e:
        print(f"❌ JSON 저장 실패: {e}")
        return False

def main():
    print("=" * 60)
    print("🤖 동행복권 Selenium 자동 크롤링 (안정성 강화)")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    driver = None
    
    try:
        # 1. WebDriver 초기화
        driver = setup_driver()
        
        # 2. JSON 데이터 가져오기 (재시도 포함)
        json_data = get_json_from_endpoint(driver)
        
        if not json_data:
            print("\n❌ JSON 데이터를 가져올 수 없습니다")
            print("\n💡 가능한 원인:")
            print("   - 동행복권 서버 일시 차단")
            print("   - 페이지 로딩 지연")
            print("   - 네트워크 문제")
            print("\n📌 다음 주 자동 재시도 예정")
            return 1
        
        # 3. JSON 저장
        if save_json(json_data):
            print("\n🎉 완료!")
            return 0
        else:
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
if __name__ == '__main__':
    sys.exit(main())
