"""
测试大兴机场 PDF 上传
"""
import requests
import time

BASE_URL = "http://localhost:8000/api/v1"

# 1. 登录
print("=" * 50)
print("步骤 1: 登录")
login_resp = requests.post(f"{BASE_URL}/auth/login", json={
    'email': 'newuser@example.com',
    'password': 'demo1234'
})
print(f"登录状态：{login_resp.status_code}")
token = login_resp.json().get('access_token')
if not token:
    print("登录失败，退出")
    exit(1)
print(f"Token: {token[:50]}...")

headers = {"Authorization": f"Bearer {token}"}

# 2. 获取工作区
print("=" * 50)
print("步骤 2: 获取工作区列表")
ws_resp = requests.get(f"{BASE_URL}/workspaces/", headers=headers)
print(f"工作区状态：{ws_resp.status_code}")
workspaces = ws_resp.json()
print(f"工作区：{workspaces}")
workspace_id = workspaces[0]['id']

# 3. 上传测试 PDF
print("=" * 50)
print("步骤 3: 上传测试 PDF")
file_path = r"C:\Users\kalvi\Documents\claude application\ai saas legal\backend\test_nda_v2.pdf"
print(f"使用文件：{file_path}")

try:
    with open(file_path, 'rb') as f:
        files = {'file': ('daxing_nda.pdf', f, 'application/pdf')}
        data = {
            'workspace_id': workspace_id,
            'contract_type': 'NDA'
        }
        print("正在上传...")
        upload_resp = requests.post(f"{BASE_URL}/contracts/upload", headers=headers, files=files, data=data)
        print(f"上传状态：{upload_resp.status_code}")
        if upload_resp.status_code == 200:
            contract = upload_resp.json()
            contract_id = contract['id']
            print(f"合同 ID: {contract_id}")
            print(f"文件名：{contract.get('file_name')}")
            print(f"审查状态：{contract.get('review_status')}")
        else:
            print(f"上传失败：{upload_resp.text}")
            exit(1)
except FileNotFoundError as e:
    print(f"文件未找到：{e}")
    exit(1)
except Exception as e:
    print(f"上传出错：{e}")
    import traceback
    traceback.print_exc()
    exit(1)

# 4. 等待审查完成
print("=" * 50)
print("步骤 4: 等待审查完成（最多 60 秒）")
for i in range(30):
    time.sleep(2)
    review_resp = requests.get(f"{BASE_URL}/contracts/{contract_id}", headers=headers)
    if review_resp.status_code == 200:
        contract_data = review_resp.json()
        status = contract_data.get('review_status')
        print(f"  [{i*2}s] 审查状态：{status}")
        if status == 'completed':
            print("审查完成！")
            break
        elif status == 'failed':
            print("审查失败！")
            break
    else:
        print(f"  [{i*2}s] 查询失败：{review_resp.status_code}")

# 5. 查看合同详情（审查结果）
print("=" * 50)
print("步骤 5: 查看审查结果")
detail_resp = requests.get(f"{BASE_URL}/contracts/{contract_id}", headers=headers)
print(f"详情状态：{detail_resp.status_code}")
detail = detail_resp.json()
print(f"审查状态：{detail.get('review_status')}")
print(f"风险等级：{detail.get('risk_level')}")

if detail.get('review_status') == 'failed':
    print("审查失败，可能原因：异步任务处理出错")
    print("请检查后端日志")
elif detail.get('review_status') == 'processing':
    print("审查仍在进行中，可能卡住了")
    print("请检查后端日志查看异步任务状态")
elif detail.get('review_status') == 'completed':
    print("审查完成")
    if detail.get('review_result'):
        result = detail['review_result']
        print(f"审查结果 keys: {result.keys() if isinstance(result, dict) else 'N/A'}")

# 6. 获取合同列表
print("=" * 50)
print("步骤 6: 获取合同列表")
list_resp = requests.get(f"{BASE_URL}/contracts/", headers=headers)
print(f"列表状态：{list_resp.status_code}")
contracts = list_resp.json()
print(f"合同数量：{len(contracts)}")
for c in contracts:
    print(f"  - {c.get('file_name')} ({c.get('review_status')})")

print("=" * 50)
print("测试完成！")
