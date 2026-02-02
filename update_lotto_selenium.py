#!/usr/bin/env python3
# update_lotto_incremental.py
"""
HTML에서 최신 회차만 추출해서 기존 JSON에 추가
천재적인 아이디어! 🎉
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
    print("✅ 완료")
    return driver

def extract_latest_draw_from_html(html):
    """HTML에서 최신 회차 정보 추출"""
    
    print("\n🔍 HTML 분석 중...")
    
    try:
        # 1. 회차 번호 추출
        draw_match = re.search(r'제 <span class="color-g ltEpsd">(\d+)</span>회 추첨 결과', html)
        if not draw_match:
            # 다른 패턴 시도
            draw_match = re.search(r'제\s*(\d+)\s*회', html)
        
        if not draw_match:
            print("  ❌ 회차 번호를 찾을 수 없습니다")
            return None
        
        draw_no = int(draw_match.group(1))
        print(f"  ✅ 회차: {draw_no}회")
        
        # 2. 추첨일 추출
        date_match = re.search(r'(\d{4})\.(\d{2})\.(\d{2})\s*추첨', html)
        if not date_match:
            print("  ❌ 추첨일을 찾을 수 없습니다")
            return None
        
        date_str = f"{date_match.group(1)}{date_match.group(2)}{date_match.group(3)}"
        print(f"  ✅ 추첨일: {date_str}")
        
        # 3. 당첨번호 추출
        # 패턴: <div class="result-ball num-Xn">숫자</div> 형식
        numbers = []
        
        # 회차별로 분리 (swiper-slide로 구분)
        slides = html.split('swiper-slide')
        
        for slide in slides:
            if f'ltEpsd">{draw_no}</span>회' in slide or f'{draw_no}회 추첨 결과' in slide:
                # 이 슬라이드에서 번호 추출
                ball_pattern = r'<div class="result-ball num-\dn">(\d+)</div>'
                balls = re.findall(ball_pattern, slide)
                
                if len(balls) >= 7:
                    numbers = [int(b) for b in balls[:7]]
                    break
        
        if len(numbers) < 7:
            print(f"  ⚠️  번호 부족: {len(numbers)}개 발견")
            print(f"  발견된 번호: {numbers}")
            
            # 대안: 전체 HTML에서 찾기
            all_balls = re.findall(r'<div class="result-ball num-\dn">(\d+)</div>', html)
            if len(all_balls) >= 7:
                # 최신 7개 (보통 마지막)
                numbers = [int(b) for b in all_balls[-7:]]
                print(f"  ✅ 대안 방법으로 추출: {numbers}")
        
        if len(numbers) < 7:
            print("  ❌ 당첨번호를 찾을 수 없습니다")
            return None
        
        print(f"  ✅ 당첨번호: {numbers[:6]} + 보너스 {numbers[6]}")
        
        # 4. JSON 객체 생성
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
        
        return data
    except FileNotFoundError:
        print(f"\n⚠️  기존 JSON 파일 없음, 새로 생성")
        return {
            "resultCode": None,
            "resultMessage": None,
            "data": {"list": []}
        }
    except Exception as e:
        print(f"\n❌ JSON 로드 실패: {e}")
        return None

def update_json(existing_data, new_entry):
    """기존 JSON에 새 회차 추가"""
    
    new_draw_no = new_entry['ltEpsd']
    
    # 이미 존재하는지 확인
    existing_draws = [item['ltEpsd'] for item in existing_data['data']['list']]
    
    if new_draw_no in existing_draws:
        print(f"\n⚠️  {new_draw_no}회는 이미 존재합니다")
        
        # 기존 데이터 업데이트
        for i, item in enumerate(existing_data['data']['list']):
            if item['ltEpsd'] == new_draw_no:
                existing_data['data']['list'][i] = new_entry
                print(f"   → 기존 데이터 업데이트")
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
        
        # 4. 최신 회차 추출
        new_entry = extract_latest_draw_from_html(html)
        
        if not new_entry:
            print("\n❌ 최신 회차 추출 실패")
            return 1
        
        # 5. 기존 JSON 로드
        existing_data = load_existing_json()
        
        if not existing_data:
            print("\n❌ 기존 JSON 로드 실패")
            return 1
        
        # 6. 업데이트
        updated_data, is_new = update_json(existing_data, new_entry)
        
        # 7. 저장
        with open(JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(updated_data, f, ensure_ascii=False, indent=4)
        
        total = len(updated_data['data']['list'])
        latest = max(item['ltEpsd'] for item in updated_data['data']['list'])
        
        print(f"\n💾 JSON 저장 완료")
        print(f"   총 {total}개 회차 (1~{latest}회)")
        
        if is_new:
            print("\n🎉 새 회차 추가 완료!")
        else:
            print("\n✅ 기존 회차 업데이트 완료")
        
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
