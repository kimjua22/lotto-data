#!/usr/bin/env python3
# update_lotto_selenium.py
"""
HTML에서 최신 회차만 추출해서 기존 JSON에 추가
드롭다운에서 최신 회차 자동 선택
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
    print("✅ 완료")
    return driver

def find_latest_draw_number(html):
    """HTML에서 최신 회차 번호 찾기 (드롭다운 옵션에서)"""
    
    # 드롭다운 옵션에서 모든 회차 찾기
    # 패턴: <button type="button" class="option-il" data-value="1209">1209회</button>
    
    pattern = r'data-value="(\d+)">(\d+)회</button>'
    matches = re.findall(pattern, html)
    
    if matches:
        # 가장 큰 회차 번호
        draw_numbers = [int(m[0]) for m in matches]
        latest = max(draw_numbers)
        print(f"  드롭다운에서 발견한 회차: {min(draw_numbers)}~{latest}회")
        return latest
    
    # 대안: input value에서
    value_match = re.search(r'<input[^>]*id="opt_val"[^>]*value="(\d+)"', html)
    if value_match:
        return int(value_match.group(1))
    
    return None

def extract_draw_data_from_html(html, target_draw_no=None):
    """HTML에서 특정 회차 데이터 추출"""
    
    print(f"\n🔍 HTML 분석 중...")
    
    try:
        # 최신 회차 번호 찾기
        if target_draw_no is None:
            target_draw_no = find_latest_draw_number(html)
            if not target_draw_no:
                print("  ❌ 회차 번호를 찾을 수 없습니다")
                return None
        
        print(f"  🎯 목표 회차: {target_draw_no}회")
        
        # 해당 회차의 슬라이드 찾기
        # swiper-slide로 분리
        slides = html.split('swiper-slide')
        
        found_slide = None
        for slide in slides:
            # 이 슬라이드가 목표 회차인지 확인
            if f'ltEpsd">{target_draw_no}</span>회' in slide or f'{target_draw_no}회 추첨 결과' in slide:
                found_slide = slide
                break
        
        if not found_slide:
            # 현재 표시된 회차 정보 (첫 번째 슬라이드)
            print(f"  ⚠️  {target_draw_no}회 슬라이드를 찾을 수 없음, 현재 표시된 회차 사용")
            
            # 전체 HTML에서 추출
            draw_match = re.search(r'제 <span class="color-g ltEpsd">(\d+)</span>회 추첨 결과', html)
            if draw_match:
                current_draw = int(draw_match.group(1))
                print(f"  현재 표시: {current_draw}회")
                
                if current_draw != target_draw_no:
                    print(f"  ⚠️  {current_draw}회가 표시됨 (목표: {target_draw_no}회)")
                    # 그래도 진행 - 최신 정보일 수 있음
                
                found_slide = html
            else:
                print("  ❌ 회차 정보를 찾을 수 없습니다")
                return None
        
        # 추첨일 추출
        date_match = re.search(r'(\d{4})\.(\d{2})\.(\d{2})\s*추첨', found_slide)
        if not date_match:
            print("  ❌ 추첨일을 찾을 수 없습니다")
            return None
        
        date_str = f"{date_match.group(1)}{date_match.group(2)}{date_match.group(3)}"
        print(f"  ✅ 추첨일: {date_str}")
        
        # 당첨번호 추출
        ball_pattern = r'<div class="result-ball num-\dn">(\d+)</div>'
        balls = re.findall(ball_pattern, found_slide)
        
        if len(balls) >= 7:
            numbers = [int(b) for b in balls[:7]]
        else:
            print(f"  ⚠️  번호 부족: {len(balls)}개, 전체 HTML에서 재시도")
            
            # 전체 HTML에서 모든 번호 찾기
            all_balls = re.findall(ball_pattern, html)
            
            if len(all_balls) >= 7:
                # 마지막 7개 (최신)
                numbers = [int(b) for b in all_balls[:7]]
                print(f"  ✅ 전체에서 추출: {numbers}")
            else:
                print(f"  ❌ 당첨번호를 찾을 수 없습니다")
                return None
        
        print(f"  ✅ 당첨번호: {numbers[:6]} + 보너스 {numbers[6]}")
        
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
        import traceback
        traceback.print_exc()
        return None

def load_existing_json():
    """기존 JSON 파일 로드"""
    try:
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        count = len(data['data']['list'])
        latest = max(item['ltEpsd'] for item in data['data']['list'])
        print(f"\n📂 기존 JSON 로드")
        print(f"   총 {count}개 회차 (최신: {latest}회)")
        
        return data, latest
    except FileNotFoundError:
        print(f"\n⚠️  기존 JSON 파일 없음, 새로 생성")
        return {
            "resultCode": None,
            "resultMessage": None,
            "data": {"list": []}
        }, 0
    except Exception as e:
        print(f"\n❌ JSON 로드 실패: {e}")
        return None, 0

def update_json(existing_data, new_entry):
    """기존 JSON에 새 회차 추가"""
    
    new_draw_no = new_entry['ltEpsd']
    
    # 이미 존재하는지 확인
    existing_draws = [item['ltEpsd'] for item in existing_data['data']['list']]
    
    if new_draw_no in existing_draws:
        print(f"\n⚠️  {new_draw_no}회는 이미 존재합니다")
        print(f"   → 데이터 업데이트하지 않음 (변경사항 없음)")
        return existing_data, False
    
    # 새로 추가
    existing_data['data']['list'].append(new_entry)
    
    # 회차 번호로 정렬
    existing_data['data']['list'].sort(key=lambda x: x['ltEpsd'])
    
    print(f"\n✅ {new_draw_no}회 추가 완료!")
    print(f"   당첨번호: {new_entry['tm1WnNo']}, {new_entry['tm2WnNo']}, {new_entry['tm3WnNo']}, {new_entry['tm4WnNo']}, {new_entry['tm5WnNo']}, {new_entry['tm6WnNo']} + {new_entry['bnsWnNo']}")
    
    return existing_data, True

def main():
    print("="*60)
    print("🎯 점진적 업데이트 (HTML → JSON)")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    driver = None
    
    try:
        # 1. WebDriver 초기화
        driver = setup_driver()
        
        # 2. 결과 페이지 접속
        print(f"\n📡 페이지 접속: {RESULT_URL}")
        driver.get(RESULT_URL)
        time.sleep(5)
        
        # 3. HTML 가져오기
        html = driver.page_source
        print(f"   HTML 크기: {len(html)} bytes")
        
        # 4. 기존 JSON 로드
        existing_data, existing_latest = load_existing_json()
        
        if existing_data is None:
            return 1
        
        # 5. HTML에서 최신 회차 번호 찾기
        html_latest = find_latest_draw_number(html)
        
        if html_latest:
            print(f"\n🔍 HTML의 최신 회차: {html_latest}회")
            print(f"   JSON의 최신 회차: {existing_latest}회")
            
            if html_latest <= existing_latest:
                print(f"\n✅ 이미 최신 상태입니다")
                print(f"   변경사항 없음")
                return 0
            
            target_draw = html_latest
        else:
            print(f"\n⚠️  HTML에서 최신 회차를 찾을 수 없음, 현재 표시된 회차 사용")
            target_draw = None
        
        # 6. 데이터 추출
        new_entry = extract_draw_data_from_html(html, target_draw)
        
        if not new_entry:
            print("\n❌ 데이터 추출 실패")
            return 1
        
        # 7. 업데이트
        updated_data, is_new = update_json(existing_data, new_entry)
        
        if not is_new:
            print("\n✅ 변경사항 없음")
            return 0
        
        # 8. 저장
        with open(JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(updated_data, f, ensure_ascii=False, indent=4)
        
        total = len(updated_data['data']['list'])
        latest = max(item['ltEpsd'] for item in updated_data['data']['list'])
        
        print(f"\n💾 JSON 저장 완료")
        print(f"   총 {total}개 회차 (1~{latest}회)")
        print("\n🎉 새 회차 추가 완료!")
        
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
