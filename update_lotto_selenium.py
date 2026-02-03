#!/usr/bin/env python3
# update_lotto_json_api.py
"""
JSON API 직접 호출 방식
Selenium 없이 requests만 사용
"""

import requests
import json
import sys
from datetime import datetime

# 설정
JSON_FILE = 'lotto_json.json'
API_URL = 'https://www.dhlottery.co.kr/lt645/selectPstLt645Info.do'

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

def fetch_draw_data(draw_no):
    """특정 회차 데이터 가져오기 (JSON API)"""
    
    try:
        # ⭐ JSON API 직접 호출
        params = {
            'srchLtEpsd': draw_no
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.dhlottery.co.kr/lt645/result',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest'
        }
        
        response = requests.get(API_URL, params=params, headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"  ❌ HTTP {response.status_code}")
            return None
        
        response_data = response.json()
        
        # 응답 구조 확인
        if not response_data or 'data' not in response_data:
            print(f"  ⚠️  응답 구조 오류")
            return None
        
        if 'list' not in response_data['data'] or not response_data['data']['list']:
            print(f"  ⚠️  데이터 없음")
            return None
        
        # 첫 번째 항목 가져오기
        data = response_data['data']['list'][0]
        
        # 회차 확인
        if data['ltEpsd'] != draw_no:
            print(f"  ⚠️  회차 불일치: 목표 {draw_no}, 실제 {data['ltEpsd']}")
            return None
        
        # 추첨일 확인
        if not data.get('ltRflYmd'):
            print(f"  ⚠️  추첨일 없음 (아직 추첨 안 됨)")
            return None
        
        return data
        
    except requests.exceptions.Timeout:
        print(f"  ❌ 타임아웃")
        return None
    except requests.exceptions.RequestException as e:
        print(f"  ❌ 요청 실패: {e}")
        return None
    except json.JSONDecodeError:
        print(f"  ❌ JSON 파싱 실패")
        return None
    except Exception as e:
        print(f"  ❌ 오류: {e}")
        return None

def collect_missing_draws(existing_data, start_draw, max_draw):
    """누락된 회차 수집"""
    
    print(f"🔄 데이터 수집: {max_draw}회부터 {start_draw}회까지\n")
    
    added_list = []
    existing_draws = [item['ltEpsd'] for item in existing_data['data']['list']]
    
    # 최신부터 역순으로
    for draw_no in range(max_draw, start_draw - 1, -1):
        print(f"[{draw_no}회]")
        
        # 이미 존재?
        if draw_no in existing_draws:
            print(f"  ℹ️  이미 존재함, 건너뛰기\n")
            continue
        
        # API 호출
        data = fetch_draw_data(draw_no)
        
        if data:
            print(f"  ✅ {draw_no}회 수집 성공")
            print(f"     당첨번호: {data['tm1WnNo']}, {data['tm2WnNo']}, {data['tm3WnNo']}, {data['tm4WnNo']}, {data['tm5WnNo']}, {data['tm6WnNo']} + {data['bnsWnNo']}")
            print(f"     추첨일: {data['ltRflYmd']}\n")
            
            added_list.append(data)
        else:
            print(f"  ⚠️  {draw_no}회 수집 실패\n")
    
    # 추가
    if added_list:
        existing_data['data']['list'].extend(added_list)
        existing_data['data']['list'].sort(key=lambda x: x['ltEpsd'])
    
    return existing_data, len(added_list)

def get_latest_draw():
    """최신 회차 번호 확인"""
    
    try:
        # 전체 데이터 요청 (srchLtEpsd=all)
        params = {
            'srchLtEpsd': 'all'
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.dhlottery.co.kr/lt645/result',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest'
        }
        
        response = requests.get(API_URL, params=params, headers=headers, timeout=15)
        
        if response.status_code != 200:
            return None
        
        data = response.json()
        
        # 최신 회차 찾기
        if 'data' in data and 'list' in data['data']:
            draws = [item['ltEpsd'] for item in data['data']['list']]
            return max(draws) if draws else None
        
        return None
        
    except:
        return None

def main():
    print("="*60)
    print("🎯 JSON API 직접 호출 방식")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")
    
    try:
        # 1. 기존 JSON 로드
        existing_data, json_latest = load_existing_json()
        
        if existing_data is None:
            return 1
        
        # 2. 최신 회차 확인
        print(f"📡 최신 회차 확인 중...")
        page_latest = get_latest_draw()
        
        if not page_latest:
            print("❌ 최신 회차를 확인할 수 없습니다\n")
            print("   대안: 현재 JSON 최신 + 5회까지 시도\n")
            page_latest = json_latest + 5
        else:
            print(f"   최신 회차: {page_latest}회\n")
        
        print(f"📍 API 최신: {page_latest}회")
        print(f"   JSON 최신: {json_latest}회")
        
        if page_latest <= json_latest:
            print(f"\n✅ 이미 최신 상태입니다\n")
            return 0
        
        print(f"   필요한 회차: {json_latest + 1}회 ~ {page_latest}회 (총 {page_latest - json_latest}개)\n")
        
        # 3. 누락 회차 수집
        updated_data, added_count = collect_missing_draws(
            existing_data, json_latest + 1, page_latest
        )
        
        if added_count == 0:
            print("✅ 변경사항 없음\n")
            return 0
        
        # 4. 저장
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

if __name__ == '__main__':
    sys.exit(main())
