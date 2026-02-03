#!/usr/bin/env python3
# debug_api.py
"""
API 응답 디버깅
"""

import requests
import json

API_URL = 'https://www.dhlottery.co.kr/lt645/selectPstLt645Info.do'

print("="*60)
print("🔍 API 응답 디버깅")
print("="*60 + "\n")

# 테스트 1: 1209회
print("[테스트 1] 1209회 요청")
print(f"URL: {API_URL}?srchLtEpsd=1209\n")

try:
    params = {'srchLtEpsd': 1209}
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://www.dhlottery.co.kr/lt645/result',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'X-Requested-With': 'XMLHttpRequest'
    }
    
    response = requests.get(API_URL, params=params, headers=headers, timeout=10)
    
    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type')}")
    print(f"Content Length: {len(response.content)} bytes\n")
    
    print("응답 내용 (처음 500자):")
    print("-" * 60)
    print(response.text[:500])
    print("-" * 60 + "\n")
    
    # JSON 파싱 시도
    try:
        data = response.json()
        print("✅ JSON 파싱 성공!")
        print(f"응답 구조:")
        print(json.dumps(data, indent=2, ensure_ascii=False)[:500])
    except json.JSONDecodeError as e:
        print(f"❌ JSON 파싱 실패: {e}")
        print(f"응답이 JSON이 아닙니다!")
    
except Exception as e:
    print(f"❌ 요청 실패: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)

# 테스트 2: all 요청
print("\n[테스트 2] 전체 데이터 요청 (srchLtEpsd=all)")
print(f"URL: {API_URL}?srchLtEpsd=all\n")

try:
    params = {'srchLtEpsd': 'all'}
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://www.dhlottery.co.kr/lt645/result',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'X-Requested-With': 'XMLHttpRequest'
    }
    
    response = requests.get(API_URL, params=params, headers=headers, timeout=15)
    
    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type')}")
    print(f"Content Length: {len(response.content)} bytes\n")
    
    print("응답 내용 (처음 500자):")
    print("-" * 60)
    print(response.text[:500])
    print("-" * 60 + "\n")
    
    # JSON 파싱 시도
    try:
        data = response.json()
        print("✅ JSON 파싱 성공!")
        
        if 'data' in data and 'list' in data['data']:
            items = data['data']['list']
            print(f"총 {len(items)}개 회차")
            
            if items:
                latest = max(item['ltEpsd'] for item in items)
                print(f"최신 회차: {latest}회")
                
                # 최신 3개 회차 출력
                print("\n최신 3개 회차:")
                for item in sorted(items, key=lambda x: x['ltEpsd'], reverse=True)[:3]:
                    print(f"  {item['ltEpsd']}회: {item.get('ltRflYmd', 'N/A')}")
    except json.JSONDecodeError as e:
        print(f"❌ JSON 파싱 실패: {e}")

except Exception as e:
    print(f"❌ 요청 실패: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
