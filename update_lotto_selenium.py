#!/usr/bin/env python3
# update_lotto_selenium.py
"""
최종 완성 버전 - 활성 슬라이드 정확 추출
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
RESULT_URL = 'https://www.dhlottery.co.kr/lt645/result'

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
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    service = Service('/usr/bin/chromedriver')
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    print("✅ 완료\n")
    return driver

def load_existing_json():
    """기존 JSON 파일 로드"""
    try:
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        count = len(data['data']['list'])
        latest = max(item['ltEpsd'] for item in data['data']['list'])
        
        print(f"📂 기존 JSON 로드")
        print(f"   총 {count}개 회차 (최신: {latest}회)\n")
        
        return data, latest
    except FileNotFoundError:
        print(f"⚠️  기존 JSON 파일 없음, 새로 생성\n")
        return {
            "resultCode": None,
            "resultMessage": None,
            "data": {"list": []}
        }, 0
    except Exception as e:
        print(f"❌ JSON 로드 실패: {e}\n")
        return None, 0

def wait_for_page_fully_loaded(driver):
    """페이지와 슬라이더가 완전히 로드될 때까지 대기"""
    
    print("⏳ 페이지 완전 로딩 대기...")
    
    try:
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "swiper-slide")))
        
        time.sleep(3)
        
        for attempt in range(5):
            html = driver.page_source
            
            pattern = r'data-value="(\d+)">(\d+)회</button>'
            matches = re.findall(pattern, html)
            
            if len(matches) >= 10:
                print(f"✅ 페이지 로딩 완료 (드롭다운 옵션: {len(matches)}개)\n")
                return True
            
            print(f"  대기 중... (옵션: {len(matches)}개)")
            time.sleep(2)
        
        print("⚠️  페이지 로딩 확인 실패, 계속 진행\n")
        return True
        
    except Exception as e:
        print(f"⚠️  대기 중 오류: {e}\n")
        return True

def get_latest_draw_from_dropdown(driver):
    """드롭다운에서 최신 회차 확인"""
    try:
        html = driver.page_source
        
        pattern = r'data-value="(\d+)">(\d+)회</button>'
        matches = re.findall(pattern, html)
        
        if matches:
            draw_numbers = [int(m[0]) for m in matches]
            latest = max(draw_numbers)
            print(f"📋 드롭다운 옵션: {len(matches)}개 (최신: {latest}회)")
            return latest
        
        return None
    except:
        return None

def get_active_slide_draw(driver):
    """활성 슬라이드에서 회차 번호 확인"""
    try:
        html = driver.page_source
        
        # ⭐ swiper-slide-active 클래스를 가진 슬라이드만 찾기
        active_pattern = r'swiper-slide-active[^>]*>.*?제 <span class="color-g ltEpsd">(\d+)</span>회'
        match = re.search(active_pattern, html, re.DOTALL)
        
        if match:
            return int(match.group(1))
        
        # 대안: swiper-slide-visible 클래스
        visible_pattern = r'swiper-slide-visible[^>]*>.*?제 <span class="color-g ltEpsd">(\d+)</span>회'
        match = re.search(visible_pattern, html, re.DOTALL)
        
        if match:
            return int(match.group(1))
        
        return None
    except:
        return None

def click_prev_button(driver):
    """이전 버튼 클릭"""
    try:
        script = """
        var prevBtn = document.querySelector('.swiper-button-prev');
        if (prevBtn && !prevBtn.classList.contains('swiper-button-disabled')) {
            prevBtn.click();
            return true;
        }
        return false;
        """
        
        result = driver.execute_script(script)
        
        if result:
            time.sleep(2)
            return True
        
        return False
        
    except:
        return False

def extract_active_slide_data(driver):
    """활성 슬라이드에서 데이터 추출"""
    
    try:
        html = driver.page_source
        
        # ⭐ 활성 슬라이드만 찾기
        active_slide_pattern = r'swiper-slide-active[^>]*>(.*?)</div>\s*<div class="swiper-slide'
        active_match = re.search(active_slide_pattern, html, re.DOTALL)
        
        if not active_match:
            # 대안: visible 슬라이드
            active_slide_pattern = r'swiper-slide-visible[^>]*>(.*?)</div>\s*<div class="swiper-slide'
            active_match = re.search(active_slide_pattern, html, re.DOTALL)
        
        if not active_match:
            return None
        
        slide_html = active_match.group(1)
        
        # 회차 추출
        draw_match = re.search(r'제 <span class="color-g ltEpsd">(\d+)</span>회', slide_html)
        if not draw_match:
            return None
        
        draw_no = int(draw_match.group(1))
        
        # 추첨일 추출
        date_match = re.search(r'(\d{4})\.(\d{2})\.(\d{2})\s*추첨', slide_html)
        if not date_match:
            return None
        
        date_str = f"{date_match.group(1)}{date_match.group(2)}{date_match.group(3)}"
        
        # 당첨번호 추출
        ball_pattern = r'<div class="result-ball num-\dn">(\d+)</div>'
        balls = re.findall(ball_pattern, slide_html)
        
        if len(balls) < 7:
            return None
        
        numbers = [int(b) for b in balls[:7]]
        
        new_entry = {
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
            "bnsWnNo": numbers[6],
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
        
        return new_entry
        
    except:
        return None

def collect_missing_draws_from_current(driver, existing_data, page_latest, json_latest):
    """현재 위치에서부터 역순으로 필요한 회차만 수집"""
    
    print(f"🔄 역순 수집: 현재 위치부터 {json_latest + 1}회까지\n")
    
    added_list = []
    existing_draws = [item['ltEpsd'] for item in existing_data['data']['list']]
    
    processed_draws = set()
    
    for attempt in range(20):
        # ⭐ 활성 슬라이드에서 회차 확인
        displayed = get_active_slide_draw(driver)
        
        if not displayed:
            print(f"  ⚠️  회차 확인 실패\n")
            break
        
        if displayed in processed_draws:
            print(f"  ℹ️  {displayed}회는 이미 처리함, 종료\n")
            break
        
        processed_draws.add(displayed)
        
        print(f"[{displayed}회]")
        
        if displayed <= json_latest:
            print(f"  ℹ️  {displayed}회는 JSON에 이미 있음, 종료\n")
            break
        
        if displayed in existing_draws or displayed in [e['ltEpsd'] for e in added_list]:
            print(f"  ℹ️  이미 처리됨, 다음으로\n")
            
            if not click_prev_button(driver):
                print(f"  ℹ️  이전 버튼 없음\n")
                break
            
            continue
        
        # ⭐ 활성 슬라이드에서 데이터 추출
        new_entry = extract_active_slide_data(driver)
        
        if new_entry:
            actual_draw = new_entry['ltEpsd']
            
            print(f"  ✅ {actual_draw}회 추출 성공")
            print(f"     당첨번호: {new_entry['tm1WnNo']}, {new_entry['tm2WnNo']}, {new_entry['tm3WnNo']}, {new_entry['tm4WnNo']}, {new_entry['tm5WnNo']}, {new_entry['tm6WnNo']} + {new_entry['bnsWnNo']}")
            print(f"     추첨일: {new_entry['ltRflYmd']}\n")
            
            added_list.append(new_entry)
        else:
            print(f"  ⚠️  데이터 추출 실패\n")
        
        if not click_prev_button(driver):
            print(f"  ℹ️  이전 버튼 없음, 종료\n")
            break
    
    if added_list:
        existing_data['data']['list'].extend(added_list)
        existing_data['data']['list'].sort(key=lambda x: x['ltEpsd'])
    
    return existing_data, len(added_list)

def main():
    print("="*60)
    print("🎯 스마트 점진적 업데이트 (활성 슬라이드)")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")
    
    driver = None
    
    try:
        existing_data, json_latest = load_existing_json()
        
        if existing_data is None:
            return 1
        
        driver = setup_driver()
        
        print(f"📡 페이지 접속: {RESULT_URL}")
        driver.get(RESULT_URL)
        
        wait_for_page_fully_loaded(driver)
        
        page_latest = get_latest_draw_from_dropdown(driver)
        
        if not page_latest:
            print("❌ 최신 회차를 확인할 수 없습니다\n")
            return 1
        
        initial_displayed = get_active_slide_draw(driver)
        
        print(f"📍 드롭다운 최신: {page_latest}회")
        print(f"   활성 슬라이드: {initial_displayed}회  ⭐")
        print(f"   JSON 최신: {json_latest}회\n")
        
        if page_latest <= json_latest:
            print(f"✅ 이미 최신 상태입니다\n")
            return 0
        
        updated_data, added_count = collect_missing_draws_from_current(
            driver, existing_data, page_latest, json_latest
        )
        
        if added_count == 0:
            print("✅ 변경사항 없음\n")
            return 0
        
        with open(JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(updated_data, f, ensure_ascii=False, indent=4)
        
        total = len(updated_data['data']['list'])
        new_latest = max(item['ltEpsd'] for item in updated_data['data']['list'])
        
        print("="*60)
        print("💾 JSON 저장 완료")
        print(f"   총 {total}개 회차 (1~{new_latest}회)")
        print(f"   추가된 회차: {added_count}개")
        print(f"   {json_latest}회 → {new_latest}회")
        print("\n🎉 업데이트 완료!")
        print("="*60)
        
        return 0
        
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
