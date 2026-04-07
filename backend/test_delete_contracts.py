"""
删除旧的测试合同并重新上传
"""
import requests
import time

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

# 3. 删除所有测试合同
for contract in contracts:
    file_name = contract.get('file_name', '')
    if 'daxing' in file_name.lower() or '大兴' in file_name or 'labor_contract' in file_name.lower():
        print(f"删除合同：{contract['id']} - {file_name}")
        delete_resp = requests.delete(f"{BASE_URL}/contracts/{contract['id']}", headers=headers)
        print(f"删除状态：{delete_resp.status_code}")

# 4. 验证删除
list_resp2 = requests.get(f"{BASE_URL}/contracts/", headers=headers)
contracts2 = list_resp2.json()
print(f"删除后合同数量：{len(contracts2)}")

print("删除完成！")
