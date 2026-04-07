"""
测试审查结果格式
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

# 1. 登录
print("登录...")
login_resp = requests.post(f"{BASE_URL}/auth/login", json={
    'email': 'newuser@example.com',
    'password': 'demo1234'
})
token = login_resp.json().get('access_token')
headers = {"Authorization": f"Bearer {token}"}

# 2. 获取合同列表
print("获取合同列表...")
list_resp = requests.get(f"{BASE_URL}/contracts/", headers=headers)
contracts = list_resp.json()
print(f"合同数量：{len(contracts)}")

# 3. 找到大兴机场合同
for contract in contracts:
    if 'daxing' in contract.get('file_name', '').lower() or '大兴' in contract.get('file_name', ''):
        print(f"\n找到大兴机场合同：{contract['id']}")
        print(f"文件名：{contract['file_name']}")
        print(f"审查状态：{contract['review_status']}")

        # 4. 获取审查结果
        if contract['review_status'] == 'completed':
            print("\n获取审查结果...")
            review_resp = requests.get(f"{BASE_URL}/contracts/{contract['id']}/review", headers=headers)
            print(f"审查结果状态：{review_resp.status_code}")

            if review_resp.status_code == 200:
                result = review_resp.json()
                print(f"\n审查结果 keys: {result.keys()}")

                if 'risk_clauses' in result and result['risk_clauses']:
                    print(f"\n风险条款数量：{len(result['risk_clauses'])}")
                    print(f"第一条风险条款 keys: {result['risk_clauses'][0].keys()}")
                    print(f"第一条风险条款内容：")
                    print(json.dumps(result['risk_clauses'][0], ensure_ascii=False, indent=2))

                if 'missing_clauses' in result and result['missing_clauses']:
                    print(f"\n缺失条款数量：{len(result['missing_clauses'])}")
                    print(f"第一条缺失条款 keys: {result['missing_clauses'][0].keys()}")
                    print(f"第一条缺失条款内容：")
                    print(json.dumps(result['missing_clauses'][0], ensure_ascii=False, indent=2))
        break
else:
    print("未找到大兴机场合同")
