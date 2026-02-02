#!/usr/bin/env python3
# update_lotto_selenium.py
"""
최종 완성 버전
다음 버튼이 비활성화되어도 한 번 더 시도
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

def click_prev_button(driver):
    """이전 버튼 클릭"""
    try:
        script = """
        var prevBtn = document.querySelector('.swiper-button-prev');
        if (!prevBtn) prevBtn = document.querySelector('[class*="prev"]');
        
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

def click_next_button(driver, force=False):
    """다음 버튼 클릭 (force=True면 비활성화 상태에서도 시도)"""
    try:
        if force:
            # 강제 클릭 (비활성화 상태 무시)
            script = """
            var nextBtn = document.querySelector('.swiper-button-next');
            if (!nextBtn) nextBtn = document.querySelector('[class*="next"]');
            
            if (nextBtn) {
                nextBtn.click();
                return true;
            }
            return false;
            """
        else:
            # 일반 클릭 (활성화 상태만)
            script = """
            var nextBtn = document.querySelector('.swiper-button-next');
            if (!nextBtn) nextBtn = document.querySelector('[class*="next"]');
            
            if (nextBtn && !nextBtn.classList.contains('swiper-button-disabled')) {
                nextBtn.click();
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

def navigate_to_draw(driver, target_draw):
    """특정 회차로 이동"""
    
    print(f"🎯 {target_draw}회로 이동 중...")
    
    max_moves = 20
    moves = 0
    
    while moves < max_moves:
        current = get_current_displayed_draw(driver)
        
        if not current:
            print(f"  ⚠️  현재 회차 확인 실패")
            return False
        
        if current == target_draw:
            print(f"  ✅ {target_draw}회 도착!\n")
            return True
        
        if current > target_draw:
            if not click_prev_button(driver):
                print(f"  ⚠️  이전 버튼 클릭 실패")
                return False
        else:
            if not click_next_button(driver):
                print(f"  ⚠️  다음 버튼 클릭 실패")
                return False
        
        moves += 1
    
    print(f"  ⚠️  {target_draw}회로 이동 실패")
    return False

def extract_current_draw_data(driver):
    """현재 표시된 회차 데이터 추출"""
    
    try:
        html = driver.page_source
        
        draw_match = re.search(r'제 <span class="color-g ltEpsd">(\d+)</span>회 추첨 결과', html)
        if not draw_match:
            draw_match = re.search(r'ltEpsd">(\d+)</span>회', html)
        
        if not draw_match:
            return None
        
        draw_no = int(draw_match.group(1))
        
        date_match = re.search(r'(\d{4})\.(\d{2})\.(\d{2})\s*추첨', html)
        if not date_match:
            return None
        
        date_str = f"{date_match.group(1)}{date_match.group(2)}{date_match.group(3)}"
        
        ball_pattern = r'<div class="result-ball num-\dn">(\d+)</div>'
        balls = re.findall(ball_pattern, html)
        
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

def collect_missing_draws(driver, existing_data, start_draw):
    """누락된 회차들 수집"""
    
    print(f"🔄 수집 시작: {start_draw}회부터\n")
    
    added_count = 0
    failed_count = 0
    
    existing_draws = [item['ltEpsd'] for item in existing_data['data']['list']]
    
    # 1. 시작 회차로 이동
    if not navigate_to_draw(driver, start_draw):
        print(f"⚠️  시작 회차로 이동 실패\n")
        return existing_data, 0
    
    # 2. 앞으로 진행하면서 수집
    last_draw = None
    stuck_count = 0
    
    while failed_count < MAX_FAILED_ATTEMPTS and stuck_count < 5:
        current = get_current_displayed_draw(driver)
        
        if not current:
            print(f"  ⚠️  회차 확인 실패")
            failed_count += 1
            
            # ⭐ 강제로 다음 버튼 클릭 시도
            if not click_next_button(driver, force=True):
                break
            continue
        
        # 같은 회차에 멈춰있는지 확인
        if current == last_draw:
            stuck_count += 1
            if stuck_count >= 3:
                print(f"  ℹ️  {current}회에서 더 이상 진행 불가\n")
                break
        else:
            stuck_count = 0
        
        last_draw = current
        
        print(f"[{current}회]")
        
        # 이미 존재?
        if current in existing_draws:
            print(f"  ℹ️  이미 존재함, 건너뛰기\n")
            
            if not click_next_button(driver, force=False):
                # ⭐ 일반 클릭 실패 시 강제 클릭 시도
                if not click_next_button(driver, force=True):
                    print(f"  ℹ️  더 이상 진행 불가\n")
                    break
            
            failed_count = 0
            continue
        
        # 데이터 추출
        new_entry = extract_current_draw_data(driver)
        
        if new_entry:
            actual_draw = new_entry['ltEpsd']
            
            if actual_draw in existing_draws:
                print(f"  ⚠️  {actual_draw}회는 이미 존재함\n")
            else:
                print(f"  ✅ {actual_draw}회 추출 성공")
                print(f"     당첨번호: {new_entry['tm1WnNo']}, {new_entry['tm2WnNo']}, {new_entry['tm3WnNo']}, {new_entry['tm4WnNo']}, {new_entry['tm5WnNo']}, {new_entry['tm6WnNo']} + {new_entry['bnsWnNo']}")
                print(f"     추첨일: {new_entry['ltRflYmd']}\n")
                
                existing_data['data']['list'].append(new_entry)
                existing_data['data']['list'].sort(key=lambda x: x['ltEpsd'])
                existing_draws.append(actual_draw)
                
                added_count += 1
            
            failed_count = 0
            
        else:
            print(f"  ⚠️  데이터 추출 실패 (아직 추첨 안 됨)\n")
            failed_count += 1
            
            if failed_count >= MAX_FAILED_ATTEMPTS:
                print(f"  ℹ️  {MAX_FAILED_ATTEMPTS}회 연속 실패, 중단\n")
                break
        
        # 다음으로
        if not click_next_button(driver, force=False):
            # ⭐ 일반 클릭 실패 시 강제 클릭 시도
            print(f"  ℹ️  일반 버튼 비활성화, 강제 클릭 시도...")
            if not click_next_button(driver, force=True):
                print(f"  ℹ️  더 이상 진행 불가\n")
                break
    
    return existing_data, added_count

def main():
    print("="*60)
    print("🎯 스마트 점진적 업데이트 (완성 버전)")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")
    
    driver = None
    
    try:
        existing_data, existing_latest = load_existing_json()
        
        if existing_data is None:
            return 1
        
        driver = setup_driver()
        
        print(f"📡 페이지 접속: {RESULT_URL}")
        driver.get(RESULT_URL)
        time.sleep(3)
        print(f"   페이지 로드 완료\n")
        
        initial_draw = get_current_displayed_draw(driver)
        print(f"📍 현재 위치: {initial_draw}회")
        print(f"   JSON 최신: {existing_latest}회")
        print(f"   목표: {existing_latest + 1}회부터 수집\n")
        
        start_draw = existing_latest + 1
        updated_data, added_count = collect_missing_draws(driver, existing_data, start_draw)
        
        if added_count == 0:
            print("✅ 이미 최신 상태입니다")
            print("   변경사항 없음\n")
            return 0
        
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
