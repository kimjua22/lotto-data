#!/usr/bin/env python3
# update_lotto_selenium.py
"""
스마트 점진적 업데이트
- 기존 JSON의 최신 회차 확인
- 다음 회차부터 순차적으로 시도
- 추첨 안 된 회차 만나면 중단
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
MAX_ATTEMPTS = 5  # 최대 시도 회차 (미추첨 5회 연속 시 중단)

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

def select_draw_number(driver, draw_no):
    """드롭다운에서 특정 회차 선택"""
    try:
        # JavaScript로 직접 변경
        script = f"""
        var select = document.getElementById('opt_val');
        if (select) {{
            select.value = '{draw_no}';
            // 변경 이벤트 트리거
            var event = new Event('change');
            select.dispatchEvent(event);
        }}
        """
        driver.execute_script(script)
        
        # 페이지 로딩 대기
        time.sleep(2)
        
        return True
    except Exception as e:
        print(f"  회차 선택 실패: {e}")
        return False

def extract_draw_data(driver, target_draw_no):
    """현재 페이지에서 특정 회차 데이터 추출"""
    
    try:
        html = driver.page_source
        
        # 회차 확인
        draw_match = re.search(r'제 <span class="color-g ltEpsd">(\d+)</span>회 추첨 결과', html)
        if not draw_match:
            draw_match = re.search(r'ltEpsd">(\d+)</span>회', html)
        
        if not draw_match:
            return None
        
        current_draw = int(draw_match.group(1))
        
        # 목표 회차와 일치하는지 확인
        if current_draw != target_draw_no:
            print(f"  ⚠️  회차 불일치: 목표 {target_draw_no}회, 실제 {current_draw}회")
            # 그래도 계속 진행 (HTML 구조 문제일 수 있음)
        
        # 추첨일 추출
        date_match = re.search(r'(\d{4})\.(\d{2})\.(\d{2})\s*추첨', html)
        if not date_match:
            print(f"  ❌ 추첨일 없음 (아직 추첨 안 됨)")
            return None
        
        date_str = f"{date_match.group(1)}{date_match.group(2)}{date_match.group(3)}"
        
        # 당첨번호 추출
        ball_pattern = r'<div class="result-ball num-\dn">(\d+)</div>'
        balls = re.findall(ball_pattern, html)
        
        if len(balls) < 7:
            print(f"  ❌ 당첨번호 부족: {len(balls)}개")
            return None
        
        numbers = [int(b) for b in balls[:7]]
        
        # JSON 객체 생성
        new_entry = {
            "winType0": 0,
            "winType1": 0,
            "winType2": 0,
            "winType3": 0,
            "gmSqNo": 5133,
            "ltEpsd": target_draw_no,
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

def try_update_multiple_draws(driver, existing_data, start_draw):
    """여러 회차 순차적으로 시도"""
    
    print(f"🔄 연속 업데이트 시작: {start_draw}회부터\n")
    
    added_count = 0
    failed_count = 0
    current_draw = start_draw
    
    while failed_count < MAX_ATTEMPTS:
        print(f"[{current_draw}회 시도]")
        
        # 이미 존재하는지 확인
        existing_draws = [item['ltEpsd'] for item in existing_data['data']['list']]
        if current_draw in existing_draws:
            print(f"  ℹ️  이미 존재함, 건너뛰기\n")
            current_draw += 1
            continue
        
        # 회차 선택 시도
        select_draw_number(driver, current_draw)
        
        # 데이터 추출
        new_entry = extract_draw_data(driver, current_draw)
        
        if new_entry:
            # 성공!
            print(f"  ✅ {current_draw}회 추출 성공")
            print(f"     당첨번호: {new_entry['tm1WnNo']}, {new_entry['tm2WnNo']}, {new_entry['tm3WnNo']}, {new_entry['tm4WnNo']}, {new_entry['tm5WnNo']}, {new_entry['tm6WnNo']} + {new_entry['bnsWnNo']}")
            print(f"     추첨일: {new_entry['ltRflYmd']}\n")
            
            # JSON에 추가
            existing_data['data']['list'].append(new_entry)
            existing_data['data']['list'].sort(key=lambda x: x['ltEpsd'])
            
            added_count += 1
            failed_count = 0  # 성공 시 실패 카운트 리셋
            
        else:
            # 실패 (아직 추첨 안 됨)
            print(f"  ⚠️  {current_draw}회 추출 실패 (아직 추첨 안 됨)\n")
            failed_count += 1
            
            if failed_count >= MAX_ATTEMPTS:
                print(f"  ℹ️  {MAX_ATTEMPTS}회 연속 실패, 중단\n")
                break
        
        current_draw += 1
        time.sleep(1)  # 서버 부하 방지
    
    return existing_data, added_count

def main():
    print("="*60)
    print("🎯 스마트 점진적 업데이트")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")
    
    driver = None
    
    try:
        # 1. 기존 JSON 로드
        existing_data, existing_latest = load_existing_json()
        
        if existing_data is None:
            return 1
        
        # 2. WebDriver 초기화
        driver = setup_driver()
        
        # 3. 결과 페이지 접속
        print(f"📡 페이지 접속: {RESULT_URL}")
        driver.get(RESULT_URL)
        time.sleep(3)
        print(f"   페이지 로드 완료\n")
        
        # 4. 다음 회차부터 시도
        start_draw = existing_latest + 1
        
        print(f"🎯 업데이트 대상: {start_draw}회부터\n")
        
        # 5. 여러 회차 순차 업데이트
        updated_data, added_count = try_update_multiple_draws(driver, existing_data, start_draw)
        
        # 6. 결과 확인
        if added_count == 0:
            print("✅ 이미 최신 상태입니다")
            print("   변경사항 없음\n")
            return 0
        
        # 7. 저장
        with open(JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(updated_data, f, ensure_ascii=False, indent=4)
        
        total = len(updated_data['data']['list'])
        new_latest = max(item['ltEpsd'] for item in updated_data['data']['list'])
        
        print("="*60)
        print("💾 JSON 저장 완료")
        print(f"   총 {total}개 회차 (1~{new_latest}회)")
        print(f"   추가된 회차: {added_count}개")
        print(f"   {existing_latest}회 → {new_latest}회")
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

if __name__ == '__main__':
    sys.exit(main())
