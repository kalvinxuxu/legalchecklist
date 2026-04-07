"""
Legal AI SaaS 性能测试脚本

使用 Locust 进行负载测试
安装：pip install locust
运行：locust -f performance_tests.py --headless -u 100 -r 10 --run-time 3m --host http://localhost:8000
"""
from locust import HttpUser, task, between, events
import json
import random
import string


class TestUser(HttpUser):
    """模拟真实用户行为"""

    wait_time = between(1, 3)  # 用户操作间隔 1-3 秒

    def on_start(self):
        """用户开始时的初始化"""
        # 模拟登录获取 token
        self.token = None
        self.client_id = None

        # 尝试登录（使用测试账号）
        response = self.client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "test123"
        })
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.headers = {}

    @task(5)
    def get_homepage(self):
        """访问首页"""
        self.client.get("/")

    @task(3)
    def get_login_page(self):
        """访问登录页"""
        self.client.get("/login")

    @task(10)
    def list_workspaces(self):
        """获取工作区列表"""
        if self.token:
            self.client.get("/api/v1/workspaces/", headers=self.headers)
        else:
            self.client.get("/api/v1/workspaces/")

    @task(8)
    def list_contracts(self):
        """获取合同列表"""
        if self.token:
            self.client.get("/api/v1/contracts/", headers=self.headers)
        else:
            self.client.get("/api/v1/contracts/")

    @task(4)
    def get_contract_detail(self):
        """获取合同详情"""
        if self.token:
            # 使用随机 ID 模拟不同合同
            contract_id = f"test-{random.randint(1, 100)}"
            self.client.get(f"/api/v1/contracts/{contract_id}", headers=self.headers)

    @task(2)
    def get_review_result(self):
        """获取审查结果"""
        if self.token:
            contract_id = f"test-{random.randint(1, 100)}"
            self.client.get(f"/api/v1/contracts/{contract_id}/review", headers=self.headers)


class ApiLoadTest(HttpUser):
    """API 负载测试 - 只测试 API 端点"""

    wait_time = between(0.5, 1)  # 更短的操作间隔

    def on_start(self):
        self.token = None
        self.headers = {}

        # 尝试登录
        response = self.client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "test123"
        })
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}

    @task(10)
    def health_check(self):
        """健康检查端点"""
        self.client.get("/api/v1/auth/me", headers=self.headers)

    @task(5)
    def workspaces_list(self):
        """工作区列表 API"""
        self.client.get("/api/v1/workspaces/", headers=self.headers)

    @task(5)
    def contracts_list(self):
        """合同列表 API"""
        self.client.get("/api/v1/contracts/", headers=self.headers)

    @task(3)
    def create_workspace(self):
        """创建工作区 API"""
        if self.token:
            workspace_name = f"测试工作区-{''.join(random.choices(string.ascii_lowercase, k=8))}"
            self.client.post("/api/v1/workspaces/", json={
                "name": workspace_name
            }, headers=self.headers)


# 自定义事件处理
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """测试开始时执行"""
    print("=" * 60)
    print("Legal AI SaaS 性能测试开始")
    print("=" * 60)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """测试结束时执行"""
    print("=" * 60)
    print("性能测试完成")
    print(f"总请求数：{environment.stats.total.num_requests}")
    print(f"失败请求数：{environment.stats.total.num_failures}")
    print(f"失败率：{environment.stats.total.fail_ratio:.2%}")
    print("=" * 60)


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, response, context, exception, **kwargs):
    """每个请求完成时执行"""
    if exception:
        print(f"请求失败：{name} - {exception}")