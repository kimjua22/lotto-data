#!/usr/bin/env python3
# update_lotto_selenium.py
"""
Selenium을 사용한 동행복권 완전 자동화
차단 우회 기능 강화
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
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

def setup_driver():
    """Selenium WebDriver 설정 - 차단 우회 강화"""
    print("🌐 Chrome WebDriver 초기화 중...")
    
    options = Options()
    
    # Headless 모드
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    
    # ⭐ 차단 우회 옵션들
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # User Agent (실제 브라우저처럼)
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    try:
        # ChromeDriver 경로 (GitHub Actions 환경)
        service = Service('/usr/bin/chromedriver')
        driver = webdriver.Chrome(service=service, options=options)
        
        # ⭐ WebDriver 감지 우회
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        print("✅ WebDriver 초기화 완료")
        return driver
        
    except Exception as e:
        print(f"❌ WebDriver 초기화 실패: {e}")
        sys.exit(1)

def wait_for_page_load(driver, timeout=10):
    """페이지 로딩 대기"""
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )
        return True
    except:
        return False

def extract_draw_number(driver):
    """현재 페이지에서 회차 번호 추출"""
    try:
        # "제 1208회 추첨 결과" 형식
        title = driver.find_element(By.CSS_SELECTOR, 'h4.title').text
        match = re.search(r'(\d+)회', title)
        if match:
            return int(match.group(1))
        return 0
    except:
        return 0

def extract_draw_data(driver):
    """현재 페이지에서 당첨 정보 추출"""
    try:
        # 회차
        draw_no = extract_draw_number(driver)
        if draw_no == 0:
            return None
        
        # 당첨번호 6개
        numbers = []
        ball_selector = '.win .num.ball'  # 당첨번호 공
        ball_elements = driver.find_elements(By.CSS_SELECTOR, ball_selector)
        
        if len(ball_elements) < 6:
            # 다른 셀렉터 시도
            ball_elements = driver.find_elements(By.CSS_SELECTOR, '.num.ball')
        
        for elem in ball_elements[:6]:
            try:
                num = int(elem.text.strip())
                if 1 <= num <= 45:
                    numbers.append(num)
            except:
                continue
        
        if len(numbers) != 6:
            print(f"  ⚠️ 당첨번호 {len(numbers)}개만 찾음")
            return None
        
        # 보너스 번호
        bonus = 0
        bonus_selector = '.bonus .num.ball'
        bonus_elements = driver.find_elements(By.CSS_SELECTOR, bonus_selector)
        if bonus_elements:
            try:
                bonus = int(bonus_elements[0].text.strip())
            except:
                pass
        
        # 추첨일 - "2026.01.24 추첨" 형식
        date_str = ""
        try:
            date_elem = driver.find_element(By.CSS_SELECTOR, '.desc')
            date_text = date_elem.text.strip()
            # "2026.01.24" 추출
            date_match = re.search(r'(\d{4})\.(\d{2})\.(\d{2})', date_text)
            if date_match:
                date_str = date_match.group(1) + date_match.group(2) + date_match.group(3)
        except:
            pass
        
        print(f"  ✅ {draw_no}회: {numbers} + {bonus} ({date_str})")
        
        # JSON 객체 생성 (동행복권 형식)
        return {
            "winType0": 0,
            "winType1": 0,
            "winType2": 0,
            "winType3": 0,
            "gmSqNo": 5133,
            "ltEpsd": draw_no,
            "tm1WnNo": numbers[0],
            "tm2WnNo": numbers[1],
            "tm3WnNo": numbers[2],
            "tm4WnNo": numbers[3],
            "tm5WnNo": numbers[4],
            "tm6WnNo": numbers[5],
            "bnsWnNo": bonus,
            "ltRflYmd": date_str,
            "rnk1WnNope": 0,
            "rnk1WnAmt": 0,
            "rnk1SumWnAmt": 0,
            "rnk2WnNope": 0,
            "rnk2WnAmt": 0,
            "rnk2SumWnAmt": 0,
            "rnk3WnNope": 0,
            "rnk3WnAmt": 0,
            "rnk3SumWnAmt": 0,
            "rnk4WnNope": 0,
            "rnk4WnAmt": 0,
            "rnk4SumWnAmt": 0,
            "rnk5WnNope": 0,
            "rnk5WnAmt": 0,
            "rnk5SumWnAmt": 0,
            "sumWnNope": 0,
            "rlvtEpsdSumNtslAmt": 0,
            "wholEpsdSumNtslAmt": 0,
            "excelRnk": "1등"
        }
        
    except Exception as e:
        print(f"  ❌ 데이터 추출 실패: {e}")
        return None

def select_draw_number(driver, draw_no):
    """드롭다운에서 회차 선택"""
    try:
        # 드롭다운 찾기
        select_elem = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'drwNo'))
        )
        
        # 회차 선택
        select = Select(select_elem)
        select.select_by_value(str(draw_no))
        
        # 페이지 로딩 대기
        time.sleep(2)
        wait_for_page_load(driver)
        
        return True
    except Exception as e:
        print(f"  ❌ 회차 선택 실패: {e}")
        return False

def crawl_all_draws(driver, start=1, end=None):
    """전체 회차 크롤링"""
    
    # 첫 페이지 로드
    print(f"\n📡 사이트 접속: {LOTTO_URL}")
    driver.get(LOTTO_URL)
    time.sleep(3)
    wait_for_page_load(driver)
    
    # 최신 회차 확인
    latest = extract_draw_number(driver)
    if latest == 0:
        print("❌ 최신 회차 확인 실패")
        return []
    
    print(f"📊 현재 최신 회차: {latest}회")
    
    if end is None:
        end = latest
    
    print(f"\n🎰 크롤링 시작: {start}회 ~ {end}회 (총 {end - start + 1}회)")
    
    all_data = []
    failed = []
    
    for draw_no in range(start, end + 1):
        print(f"\n[{draw_no}/{end}] {draw_no}회 크롤링 중...")
        
        # 회차 선택
        if draw_no != latest:  # 첫 페이지는 이미 로드됨
            if not select_draw_number(driver, draw_no):
                failed.append(draw_no)
                continue
        
        # 데이터 추출
        data = extract_draw_data(driver)
        
        if data:
            all_data.append(data)
        else:
            failed.append(draw_no)
        
        # 서버 부하 방지
        time.sleep(1)
    
    print(f"\n✅ 크롤링 완료: {len(all_data)}개 성공, {len(failed)}개 실패")
    if failed:
        print(f"⚠️  실패한 회차: {failed[:10]}{'...' if len(failed) > 10 else ''}")
    
    return all_data

def save_json(data, filename=JSON_FILE):
    """JSON 파일로 저장"""
    try:
        # 회차 번호로 정렬
        sorted_data = sorted(data, key=lambda x: x['ltEpsd'])
        
        json_data = {
            "resultCode": None,
            "resultMessage": None,
            "data": {
                "list": sorted_data
            }
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)
        
        latest = max(d['ltEpsd'] for d in data) if data else 0
        
        print(f"\n💾 JSON 파일 저장 완료: {filename}")
        print(f"   총 {len(data)}개 회차 (1~{latest}회)")
        
        return True
    except Exception as e:
        print(f"❌ JSON 저장 실패: {e}")
        return False

def main():
    print("=" * 60)
    print("🤖 동행복권 Selenium 자동 크롤링")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    driver = None
    
    try:
        # 1. WebDriver 초기화
        driver = setup_driver()
        
        # 2. 전체 크롤링 (1회부터 최신까지)
        all_data = crawl_all_draws(driver, start=1)
        
        if not all_data:
            print("\n❌ 크롤링 실패")
            return 1
        
        # 3. JSON 저장
        if save_json(all_data):
            print("\n🎉 완료!")
            return 0
        else:
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⚠️  중단됨")
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
