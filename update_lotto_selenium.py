#!/usr/bin/env python3
# update_lotto_selenium.py
"""
드롭다운 실제 동작 기반 업데이트
표시된 회차를 그대로 사용하여 안정적으로 처리
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
MAX_FAILED_ATTEMPTS = 3

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

def get_current_displayed_draw(driver):
    """현재 표시된 회차 번호 확인"""
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

def click_next_draw_button(driver):
    """다음 회차 버튼 클릭 (오른쪽 화살표)"""
    try:
        # 다음 버튼 JavaScript로 클릭
        script = """
        // 다음 버튼 찾기 (여러 가능성 시도)
        var nextBtn = document.querySelector('.swiper-button-next');
        if (!nextBtn) nextBtn = document.querySelector('[class*="next"]');
        if (!nextBtn) nextBtn = document.querySelector('button[aria-label*="다음"]');
        
        if (nextBtn && !nextBtn.classList.contains('swiper-button-disabled')) {
            nextBtn.click();
            return true;
        }
        return false;
        """
        
        result = driver.execute_script(script)
        
        if result:
            time.sleep(2)  # 슬라이드 애니메이션 대기
            return True
        
        return False
        
    except Exception as e:
        print(f"  ⚠️  다음 버튼 클릭 실패: {e}")
        return False

def extract_current_draw_data(driver):
    """현재 표시된 회차 데이터 추출"""
    
    try:
        html = driver.page_source
        
        # 회차 추출
        draw_match = re.search(r'제 <span class="color-g ltEpsd">(\d+)</span>회 추첨 결과', html)
        if not draw_match:
            draw_match = re.search(r'ltEpsd">(\d+)</span>회', html)
        
        if not draw_match:
            return None
        
        draw_no = int(draw_match.group(1))
        
        # 추첨일 추출
        date_match = re.search(r'(\d{4})\.(\d{2})\.(\d{2})\s*추첨', html)
        if not date_match:
            return None
        
        date_str = f"{date_match.group(1)}{date_match.group(2)}{date_match.group(3)}"
        
        # 당첨번호 추출
        ball_pattern = r'<div class="result-ball num-\dn">(\d+)</div>'
        balls = re.findall(ball_pattern, html)
        
        if len(balls) < 7:
            return None
        
        numbers = [int(b) for b in balls[:7]]
        
        # JSON 객체 생성
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

def try_update_from_current_position(driver, existing_data, target_latest):
    """현재 위치에서부터 순차적으로 업데이트"""
    
    print(f"🔄 현재 위치에서부터 업데이트 시작\n")
    
    added_count = 0
    failed_count = 0
    attempts = 0
    max_attempts = 20  # 최대 20회 시도
    
    existing_draws = [item['ltEpsd'] for item in existing_data['data']['list']]
    
    while failed_count < MAX_FAILED_ATTEMPTS and attempts < max_attempts:
        attempts += 1
        
        # 현재 표시된 회차 확인
        current_draw = get_current_displayed_draw(driver)
        
        if not current_draw:
            print(f"[시도 {attempts}] 회차 번호를 확인할 수 없음\n")
            failed_count += 1
            
            # 다음 버튼 클릭 시도
            if not click_next_draw_button(driver):
                print(f"  ⚠️  더 이상 진행 불가\n")
                break
            continue
        
        print(f"[시도 {attempts}] 현재 표시: {current_draw}회")
        
        # 이미 존재하는 회차면 건너뛰기
        if current_draw in existing_draws:
            print(f"  ℹ️  {current_draw}회는 이미 존재함, 다음으로...\n")
            
            # 다음 버튼 클릭
            if not click_next_draw_button(driver):
                print(f"  ⚠️  다음 버튼 클릭 실패, 종료\n")
                break
            
            failed_count = 0  # 존재하는 건 실패 아님
            continue
        
        # 목표 회차보다 작으면 건너뛰기
        if current_draw < target_latest:
            print(f"  ℹ️  {current_draw}회는 이미 처리된 범위, 다음으로...\n")
            
            if not click_next_draw_button(driver):
                print(f"  ⚠️  다음 버튼 클릭 실패, 종료\n")
                break
            
            continue
        
        # 데이터 추출
        new_entry = extract_current_draw_data(driver)
        
        if new_entry:
            actual_draw = new_entry['ltEpsd']
            
            # 중복 체크
            if actual_draw in existing_draws:
                print(f"  ⚠️  {actual_draw}회는 이미 존재함\n")
                
                if not click_next_draw_button(driver):
                    break
                
                continue
            
            print(f"  ✅ {actual_draw}회 추출 성공")
            print(f"     당첨번호: {new_entry['tm1WnNo']}, {new_entry['tm2WnNo']}, {new_entry['tm3WnNo']}, {new_entry['tm4WnNo']}, {new_entry['tm5WnNo']}, {new_entry['tm6WnNo']} + {new_entry['bnsWnNo']}")
            print(f"     추첨일: {new_entry['ltRflYmd']}\n")
            
            # 추가
            existing_data['data']['list'].append(new_entry)
            existing_data['data']['list'].sort(key=lambda x: x['ltEpsd'])
            existing_draws.append(actual_draw)
            
            added_count += 1
            failed_count = 0
            
            # 다음 버튼 클릭
            if not click_next_draw_button(driver):
                print(f"  ℹ️  다음 버튼 없음 (최신 회차 도달)\n")
                break
            
        else:
            print(f"  ⚠️  {current_draw}회 데이터 추출 실패\n")
            failed_count += 1
            
            if failed_count >= MAX_FAILED_ATTEMPTS:
                print(f"  ℹ️  {MAX_FAILED_ATTEMPTS}회 연속 실패, 중단\n")
                break
            
            # 다음 시도
            if not click_next_draw_button(driver):
                break
    
    return existing_data, added_count

def main():
    print("="*60)
    print("🎯 스마트 점진적 업데이트 (순차 진행)")
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
        
        # 3. 페이지 접속
        print(f"📡 페이지 접속: {RESULT_URL}")
        driver.get(RESULT_URL)
        time.sleep(3)
        print(f"   페이지 로드 완료\n")
        
        # 4. 현재 표시된 회차 확인
        initial_draw = get_current_displayed_draw(driver)
        print(f"🎯 시작 위치: {initial_draw}회")
        print(f"   목표: {existing_latest + 1}회부터 추가\n")
        
        # 5. 현재 위치에서부터 순차 업데이트
        updated_data, added_count = try_update_from_current_position(
            driver, existing_data, existing_latest + 1
        )
        
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
