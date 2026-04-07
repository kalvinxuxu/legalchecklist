"""
API 基准测试脚本

不使用 Locust，直接用 asyncio + httpx 进行简单的性能测试

运行：python backend/scripts/benchmark.py
"""
import asyncio
import time
import httpx
from statistics import mean, median, stdev
from typing import List, Dict
import json


# 测试配置
BASE_URL = "http://localhost:8000"
CONCURRENT_USERS = [1, 5, 10, 20, 50]  # 不同并发级别
REQUESTS_PER_USER = 10  # 每个用户发送的请求数


class PerformanceTester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.results: Dict[str, List[float]] = {
            "login": [],
            "workspaces": [],
            "contracts": [],
        }

    async def login(self, client: httpx.AsyncClient) -> tuple:
        """登录并获取 token"""
        start = time.perf_counter()
        response = await client.post(
            f"{self.base_url}/api/v1/auth/login",
            json={"email": "test@example.com", "password": "test123"}
        )
        elapsed = (time.perf_counter() - start) * 1000  # 转换为毫秒
        token = None
        if response.status_code == 200:
            token = response.json().get("access_token")
        return token, elapsed

    async def get_workspaces(self, client: httpx.AsyncClient, token: str) -> float:
        """获取工作区列表"""
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        start = time.perf_counter()
        response = await client.get(
            f"{self.base_url}/api/v1/workspaces/",
            headers=headers
        )
        elapsed = (time.perf_counter() - start) * 1000
        return elapsed, response.status_code

    async def get_contracts(self, client: httpx.AsyncClient, token: str) -> float:
        """获取合同列表"""
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        start = time.perf_counter()
        response = await client.get(
            f"{self.base_url}/api/v1/contracts/",
            headers=headers
        )
        elapsed = (time.perf_counter() - start) * 1000
        return elapsed, response.status_code

    async def run_benchmark(self, concurrent_users: int, requests_per_user: int):
        """运行基准测试"""
        print(f"\n{'='*60}")
        print(f"并发用户数：{concurrent_users}, 每用户请求数：{requests_per_user}")
        print(f"{'='*60}")

        login_times = []
        workspace_times = []
        contract_times = []
        errors = 0
        total_requests = 0

        async def user_task(user_id: int):
            nonlocal errors, total_requests
            async with httpx.AsyncClient(timeout=30.0) as client:
                # 登录
                try:
                    token, login_time = await self.login(client)
                    login_times.append(login_time)
                    total_requests += 1

                    for _ in range(requests_per_user):
                        # 获取工作区列表
                        try:
                            ws_time, ws_status = await self.get_workspaces(client, token)
                            workspace_times.append(ws_time)
                            total_requests += 1
                            if ws_status >= 400:
                                errors += 1
                        except Exception as e:
                            errors += 1

                        # 获取合同列表
                        try:
                            ct_time, ct_status = await self.get_contracts(client, token)
                            contract_times.append(ct_time)
                            total_requests += 1
                            if ct_status >= 400:
                                errors += 1
                        except Exception as e:
                            errors += 1

                        # 模拟用户思考时间
                        await asyncio.sleep(0.1)

                except Exception as e:
                    errors += 1
                    print(f"用户 {user_id} 错误：{e}")

        # 并发运行所有用户任务
        start_time = time.time()
        tasks = [user_task(i) for i in range(concurrent_users)]
        await asyncio.gather(*tasks)
        total_time = time.time() - start_time

        # 输出结果
        self._print_results(
            login_times, workspace_times, contract_times,
            errors, total_requests, total_time
        )

    def _print_results(
        self, login_times: List[float], workspace_times: List[float],
        contract_times: List[float], errors: int, total_requests: int,
        total_time: float
    ):
        """打印测试结果"""

        def format_stats(times: List[float], name: str):
            if not times:
                return f"{name}: 无数据"
            return (
                f"{name}: 平均={mean(times):.2f}ms, "
                f"中位数={median(times):.2f}ms, "
                f"P95={sorted(times)[int(len(times)*0.95)]:.2f}ms, "
                f"标准差={stdev(times) if len(times) > 1 else 0:.2f}ms"
            )

        print(f"\n--- 结果 ---")
        print(format_stats(login_times, "登录 API"))
        print(format_stats(workspace_times, "工作区列表 API"))
        print(format_stats(contract_times, "合同列表 API"))

        throughput = total_requests / total_time
        error_rate = (errors / total_requests * 100) if total_requests > 0 else 0

        print(f"\n总体统计:")
        print(f"  总请求数：{total_requests}")
        print(f"  总耗时：{total_time:.2f} 秒")
        print(f"  吞吐量：{throughput:.2f} 请求/秒")
        print(f"  错误数：{errors} ({error_rate:.2f}%)")


async def main():
    print("=" * 60)
    print("Legal AI SaaS API 基准测试")
    print("=" * 60)
    print(f"目标 URL: {BASE_URL}")
    print(f"并发级别：{CONCURRENT_USERS}")
    print(f"每用户请求数：{REQUESTS_PER_USER}")

    tester = PerformanceTester(BASE_URL)

    for users in CONCURRENT_USERS:
        await tester.run_benchmark(users, REQUESTS_PER_USER)
        # 间隔时间，让服务器恢复
        await asyncio.sleep(2)

    print("\n" + "=" * 60)
    print("基准测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
