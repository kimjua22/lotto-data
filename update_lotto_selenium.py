#!/usr/bin/env python3
# debug_check_1209.py
"""
1209회가 정말 있는지 HTML 소스 확인
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import re

RESULT_URL = 'https://www.dhlottery.co.kr/lt645/result'

def setup_driver():
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    service = Service('/usr/bin/chromedriver')
    return webdriver.Chrome(service=service, options=options)

def main():
    print("🔍 1209회 존재 여부 확인\n")
    
    driver = setup_driver()
    
    try:
        driver.get(RESULT_URL)
        import time
        time.sleep(5)
        
        html = driver.page_source
        
        # 1. 드롭다운 옵션에서 모든 회차 찾기
        print("1️⃣ 드롭다운 옵션 확인:")
        pattern = r'data-value="(\d+)">(\d+)회</button>'
        matches = re.findall(pattern, html)
        
        if matches:
            draw_numbers = [int(m[0]) for m in matches]
            draw_numbers.sort(reverse=True)
            print(f"   발견된 회차: {draw_numbers[:5]}... (최신 5개)")
            print(f"   최신 회차: {max(draw_numbers)}회")
            
            if 1209 in draw_numbers:
                print(f"   ✅ 1209회 발견!")
            else:
                print(f"   ❌ 1209회 없음")
        else:
            print(f"   ⚠️  드롭다운 옵션을 찾을 수 없음")
        
        print()
        
        # 2. 현재 표시된 회차
        print("2️⃣ 현재 표시된 회차:")
        draw_match = re.search(r'제 <span class="color-g ltEpsd">(\d+)</span>회 추첨 결과', html)
        if draw_match:
            current = int(draw_match.group(1))
            print(f"   현재 표시: {current}회")
        else:
            print(f"   ⚠️  현재 회차를 확인할 수 없음")
        
        print()
        
        # 3. input value 확인
        print("3️⃣ input value 확인:")
        value_match = re.search(r'<input[^>]*id="opt_val"[^>]*value="(\d+)"', html)
        if value_match:
            input_value = int(value_match.group(1))
            print(f"   input value: {input_value}회")
        else:
            print(f"   ⚠️  input value를 찾을 수 없음")
        
        print()
        
        # 4. swiper 슬라이드 개수
        print("4️⃣ swiper 슬라이드 개수:")
        slides = html.count('swiper-slide')
        print(f"   총 {slides}개 슬라이드")
        
        # 1209회 슬라이드 존재 확인
        if '1209회 추첨 결과' in html or 'ltEpsd">1209</span>' in html:
            print(f"   ✅ 1209회 슬라이드 발견!")
        else:
            print(f"   ❌ 1209회 슬라이드 없음")
        
        print()
        
        # 5. 결론
        print("="*60)
        if 1209 in draw_numbers and ('1209회 추첨 결과' in html or 'ltEpsd">1209</span>' in html):
            print("✅ 1209회가 페이지에 존재합니다!")
            print("   → 슬라이더 이동 로직 문제일 가능성")
        elif 1209 in draw_numbers:
            print("⚠️  1209회가 드롭다운에는 있지만 슬라이드는 없습니다")
            print("   → 페이지가 완전히 로드되지 않았을 가능성")
        else:
            print("❌ 1209회가 아직 페이지에 없습니다")
            print("   → 아직 추첨이 안 됐거나 페이지 업데이트 전")
        print("="*60)
        
    finally:
        driver.quit()

if __name__ == '__main__':
    main()
