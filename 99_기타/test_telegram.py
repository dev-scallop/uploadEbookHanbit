import json, requests, os

CONFIG = os.path.join(os.path.dirname(__file__), 'telegram_config.json')

def main():
    with open(CONFIG, 'r', encoding='utf-8') as f:
        cfg = json.load(f)
    token = str(cfg.get('token', '')).strip()
    chat_id = str(cfg.get('chat_id', '')).strip()
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    resp = requests.post(url, json={'chat_id': chat_id, 'text': '테스트: 설정 반영 완료 ✅'}, timeout=20)
    print(resp.status_code)
    print(resp.text[:500])

if __name__ == '__main__':
    main()
