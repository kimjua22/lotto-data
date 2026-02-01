#!/usr/bin/env python3
# update_lotto_selenium.py
"""
디버그에서 성공한 방식 그대로 사용
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import json, sys, time
from datetime import datetime

JSON_FILE = 'lotto_json.json'
JSON_URL = 'https://www.dhlottery.co.kr/lt645/result'

def setup_driver():
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

def main():
    print("="*60)
    print("🤖 동행복권 JSON 다운로드")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    driver = None
    try:
        driver = setup_driver()
        
        print(f"\n📡 접속: {JSON_URL}")
        driver.get(JSON_URL)
        time.sleep(5)
        
        # pre 태그에서 추출
        pre = driver.find_element(By.TAG_NAME, 'pre')
        json_text = pre.text
        print(f"✅ JSON 발견: {len(json_text)} bytes")
        
        # 파싱 & 저장
        data = json.loads(json_text)
        
        with open(JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        
        count = len(data['data']['list'])
        latest = max(item['ltEpsd'] for item in data['data']['list'])
        print(f"💾 저장 완료: {count}개 회차 (최신: {latest}회)")
        print("🎉 완료!")
        return 0
        
    except Exception as e:
        print(f"❌ 실패: {e}")
        return 1
    finally:
        if driver:
            driver.quit()

if __name__ == '__main__':
    sys.exit(main())
