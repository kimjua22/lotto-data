#!/usr/bin/env python3
# update_lotto_selenium.py
"""
최종 완성 버전 - URL 파라미터 + 충분한 대기
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
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

def get_displayed_draw(driver):
    """현재 표시된 회차 확인"""
    try:
        html = driver.page_source
        
        draw_match = re.search(r'제 <span class="color-g ltEpsd">(\d+)</span>회 추첨 결과', html)
        if not draw_match:
            draw_match = re.search(r'ltEpsd">(\d+)</span>회', html)
        
        if draw_match:
            return int(draw_match.group(1))
        
        return None
    except:
        return None

def load_specific_draw_and_wait(driver, draw_no):
    """특정 회차 페이지 로드 후 회차가 표시될 때까지 대기"""
    
    # ⭐ ltEpsd 파라미터 사용
    url = f"{RESULT_URL}?ltEpsd={draw_no}"
    
    print(f"  📡 {draw_no}회 페이지 로드: {url}")
    
    try:
        driver.get(url)
        
        # ⭐ 목표 회차가 표시될 때까지 최대 10초 대기
        for attempt in range(10):
            time.sleep(1)
            
            displayed = get_displayed_draw(driver)
            
            if displayed == draw_no:
                print(f"  ✅ {draw_no}회 표시 확인!")
                return True
            
            if attempt < 9:
                print(f"  ⏳ 대기 중... (현재: {displayed}회, 목표: {draw_no}회)")
        
        print(f"  ⚠️  {draw_no}회 표시 실패 (최종: {displayed}회)")
        return False
        
    except Exception as e:
        print(f"  ❌ 페이지 로드 실패: {e}")
        return False

def extract_draw_data_from_page(driver, target_draw_no):
    """페이지에서 회차 데이터 추출"""
    
    try:
        html = driver.page_source
        
        # 회차 확인
        draw_match = re.search(r'제 <span class="color-g ltEpsd">(\d+)</span>회 추첨 결과', html)
        if not draw_match:
            draw_match = re.search(r'ltEpsd">(\d+)</span>회', html)
        
        if not draw_match:
            return None
        
        draw_no = int(draw_match.group(1))
        
        # 회차 검증
        if draw_no != target_draw_no:
            print(f"  ⚠️  회차 불일치: 목표 {target_draw_no}회, 실제 {draw_no}회")
            return None
        
        # 추첨일 추출
        date_match = re.search(r'(\d{4})\.(\d{2})\.(\d{2})\s*추첨', html)
        if not date_match:
            print(f"  ⚠️  추첨일 없음 (아직 추첨 안 됨)")
            return None
        
        date_str = f"{date_match.group(1)}{date_match.group(2)}{date_match.group(3)}"
        
        # 당첨번호 추출
        ball_pattern = r'<div class="result-ball num-\dn">(\d+)</div>'
        balls = re.findall(ball_pattern, html)
        
        if len(balls) < 7:
            print(f"  ⚠️  당첨번호 부족: {len(balls)}개")
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
        
    except Exception as e:
        print(f"  ❌ 추출 실패: {e}")
        return None

def collect_missing_draws_by_url(driver, existing_data, page_latest, json_latest):
    """URL로 각 회차 직접 접근하여 수집"""
    
    print(f"🔄 URL 직접 접근: {page_latest}회부터 {json_latest + 1}회까지\n")
    
    added_list = []
    existing_draws = [item['ltEpsd'] for item in existing_data['data']['list']]
    
    # 최신 회차부터 역순으로
    for draw_no in range(page_latest, json_latest, -1):
        print(f"[{draw_no}회]")
        
        # 이미 존재?
        if draw_no in existing_draws:
            print(f"  ℹ️  이미 존재함, 건너뛰기\n")
            continue
        
        # ⭐ URL로 페이지 로드 + 목표 회차 표시까지 대기
        if not load_specific_draw_and_wait(driver, draw_no):
            print(f"  ⚠️  페이지 로드 실패\n")
            continue
        
        # 데이터 추출
        new_entry = extract_draw_data_from_page(driver, draw_no)
        
        if new_entry:
            print(f"  ✅ {draw_no}회 추출 성공")
            print(f"     당첨번호: {new_entry['tm1WnNo']}, {new_entry['tm2WnNo']}, {new_entry['tm3WnNo']}, {new_entry['tm4WnNo']}, {new_entry['tm5WnNo']}, {new_entry['tm6WnNo']} + {new_entry['bnsWnNo']}")
            print(f"     추첨일: {new_entry['ltRflYmd']}\n")
            
            added_list.append(new_entry)
        else:
            print(f"  ⚠️  {draw_no}회 데이터 없음 (아직 추첨 안 됨)\n")
    
    # 추가
    if added_list:
        existing_data['data']['list'].extend(added_list)
        existing_data['data']['list'].sort(key=lambda x: x['ltEpsd'])
    
    return existing_data, len(added_list)

def main():
    print("="*60)
    print("🎯 스마트 점진적 업데이트 (URL + 대기)")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")
    
    driver = None
    
    try:
        existing_data, json_latest = load_existing_json()
        
        if existing_data is None:
            return 1
        
        driver = setup_driver()
        
        # 초기 페이지 접속 (드롭다운 확인용)
        print(f"📡 초기 페이지 접속: {RESULT_URL}")
        driver.get(RESULT_URL)
        time.sleep(5)
        print(f"   페이지 로드 완료\n")
        
        # 드롭다운에서 최신 회차 확인
        page_latest = get_latest_draw_from_dropdown(driver)
        
        if not page_latest:
            print("❌ 최신 회차를 확인할 수 없습니다\n")
            return 1
        
        print(f"📍 페이지 최신: {page_latest}회")
        print(f"   JSON 최신: {json_latest}회")
        
        if page_latest <= json_latest:
            print(f"\n✅ 이미 최신 상태입니다\n")
            return 0
        
        print(f"   필요한 회차: {json_latest + 1}회 ~ {page_latest}회 (총 {page_latest - json_latest}개)\n")
        
        # ⭐ URL로 각 회차 직접 접근
        updated_data, added_count = collect_missing_draws_by_url(
            driver, existing_data, page_latest, json_latest
        )
        
        if added_count == 0:
            print("✅ 변경사항 없음\n")
            return 0
        
        # 저장
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
