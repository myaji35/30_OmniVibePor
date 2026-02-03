#!/usr/bin/env python3
"""
Load Testing Script for OmniVibe Pro API

This script performs load testing on critical endpoints:
- Audio generation
- Voice cloning
- Presentation generation
- Performance tracking

Usage:
    python scripts/load_test.py --users 10 --duration 60
    python scripts/load_test.py --endpoint /api/v1/audio/generate --users 50
"""
import asyncio
import aiohttp
import argparse
import time
import statistics
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path


@dataclass
class RequestResult:
    """Result of a single request"""
    endpoint: str
    method: str
    status_code: int
    response_time_ms: float
    timestamp: str
    success: bool
    error: Optional[str] = None


@dataclass
class LoadTestReport:
    """Load test summary report"""
    total_requests: int
    successful_requests: int
    failed_requests: int
    success_rate: float
    duration_seconds: float
    requests_per_second: float
    avg_response_time_ms: float
    min_response_time_ms: float
    max_response_time_ms: float
    p50_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    error_summary: Dict[str, int]


class LoadTester:
    """Load testing client for OmniVibe Pro API"""

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        timeout: int = 30
    ):
        self.base_url = base_url
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.results: List[RequestResult] = []

    async def run_load_test(
        self,
        endpoint: str,
        method: str = "GET",
        concurrent_users: int = 10,
        total_requests: int = 100,
        payload: Optional[Dict[str, Any]] = None
    ) -> LoadTestReport:
        """
        Run load test on specified endpoint

        Args:
            endpoint: API endpoint to test (e.g., "/api/v1/health")
            method: HTTP method (GET, POST, etc.)
            concurrent_users: Number of concurrent users
            total_requests: Total number of requests to make
            payload: Request payload for POST/PUT requests

        Returns:
            Load test report
        """
        print(f"\n{'='*60}")
        print(f"Load Test Configuration:")
        print(f"  Endpoint: {endpoint}")
        print(f"  Method: {method}")
        print(f"  Concurrent Users: {concurrent_users}")
        print(f"  Total Requests: {total_requests}")
        print(f"  Target URL: {self.base_url}{endpoint}")
        print(f"{'='*60}\n")

        self.results = []
        start_time = time.time()

        # Create task queue
        requests_per_user = total_requests // concurrent_users
        remaining_requests = total_requests % concurrent_users

        # Run concurrent users
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            tasks = []

            for i in range(concurrent_users):
                num_requests = requests_per_user
                if i < remaining_requests:
                    num_requests += 1

                task = self._run_user_requests(
                    session=session,
                    endpoint=endpoint,
                    method=method,
                    num_requests=num_requests,
                    user_id=i,
                    payload=payload
                )
                tasks.append(task)

            # Wait for all users to complete
            await asyncio.gather(*tasks)

        end_time = time.time()
        duration = end_time - start_time

        # Generate report
        report = self._generate_report(duration)

        # Print report
        self._print_report(report)

        return report

    async def _run_user_requests(
        self,
        session: aiohttp.ClientSession,
        endpoint: str,
        method: str,
        num_requests: int,
        user_id: int,
        payload: Optional[Dict[str, Any]]
    ) -> None:
        """Execute requests for a single user"""
        for i in range(num_requests):
            result = await self._make_request(
                session=session,
                endpoint=endpoint,
                method=method,
                payload=payload
            )
            self.results.append(result)

            # Progress indicator
            if (i + 1) % 10 == 0:
                print(f"User {user_id}: {i + 1}/{num_requests} requests completed")

    async def _make_request(
        self,
        session: aiohttp.ClientSession,
        endpoint: str,
        method: str,
        payload: Optional[Dict[str, Any]]
    ) -> RequestResult:
        """Make a single HTTP request"""
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        error = None
        status_code = 0

        try:
            if method.upper() == "GET":
                async with session.get(url) as response:
                    status_code = response.status
                    await response.text()

            elif method.upper() == "POST":
                async with session.post(url, json=payload) as response:
                    status_code = response.status
                    await response.text()

            elif method.upper() == "PUT":
                async with session.put(url, json=payload) as response:
                    status_code = response.status
                    await response.text()

            elif method.upper() == "DELETE":
                async with session.delete(url) as response:
                    status_code = response.status
                    await response.text()

            success = 200 <= status_code < 300

        except Exception as e:
            error = str(e)
            success = False

        response_time = (time.time() - start_time) * 1000  # Convert to ms

        return RequestResult(
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            response_time_ms=response_time,
            timestamp=datetime.utcnow().isoformat(),
            success=success,
            error=error
        )

    def _generate_report(self, duration: float) -> LoadTestReport:
        """Generate load test report from results"""
        successful = [r for r in self.results if r.success]
        failed = [r for r in self.results if not r.success]

        response_times = [r.response_time_ms for r in self.results]

        # Count errors by type
        error_summary = {}
        for result in failed:
            error_key = result.error or f"HTTP {result.status_code}"
            error_summary[error_key] = error_summary.get(error_key, 0) + 1

        return LoadTestReport(
            total_requests=len(self.results),
            successful_requests=len(successful),
            failed_requests=len(failed),
            success_rate=(len(successful) / len(self.results) * 100) if self.results else 0,
            duration_seconds=duration,
            requests_per_second=len(self.results) / duration if duration > 0 else 0,
            avg_response_time_ms=statistics.mean(response_times) if response_times else 0,
            min_response_time_ms=min(response_times) if response_times else 0,
            max_response_time_ms=max(response_times) if response_times else 0,
            p50_response_time_ms=self._percentile(response_times, 50),
            p95_response_time_ms=self._percentile(response_times, 95),
            p99_response_time_ms=self._percentile(response_times, 99),
            error_summary=error_summary
        )

    @staticmethod
    def _percentile(data: List[float], percentile: int) -> float:
        """Calculate percentile value"""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]

    def _print_report(self, report: LoadTestReport) -> None:
        """Print formatted load test report"""
        print(f"\n{'='*60}")
        print(f"Load Test Results:")
        print(f"{'='*60}")
        print(f"\nOverall Performance:")
        print(f"  Total Requests:       {report.total_requests}")
        print(f"  Successful:           {report.successful_requests} "
              f"({report.success_rate:.1f}%)")
        print(f"  Failed:               {report.failed_requests}")
        print(f"  Duration:             {report.duration_seconds:.2f}s")
        print(f"  Throughput:           {report.requests_per_second:.2f} req/s")

        print(f"\nResponse Time Statistics:")
        print(f"  Average:              {report.avg_response_time_ms:.0f}ms")
        print(f"  Minimum:              {report.min_response_time_ms:.0f}ms")
        print(f"  Maximum:              {report.max_response_time_ms:.0f}ms")
        print(f"  P50 (Median):         {report.p50_response_time_ms:.0f}ms")
        print(f"  P95:                  {report.p95_response_time_ms:.0f}ms")
        print(f"  P99:                  {report.p99_response_time_ms:.0f}ms")

        if report.error_summary:
            print(f"\nError Summary:")
            for error, count in sorted(
                report.error_summary.items(),
                key=lambda x: x[1],
                reverse=True
            ):
                print(f"  {error}: {count}")

        # Performance evaluation
        print(f"\nPerformance Evaluation:")
        if report.avg_response_time_ms < 2000:
            print(f"  ✅ Average response time is excellent (< 2s)")
        elif report.avg_response_time_ms < 5000:
            print(f"  ⚠️  Average response time is acceptable (2-5s)")
        else:
            print(f"  ❌ Average response time is too high (> 5s)")

        if report.success_rate >= 99:
            print(f"  ✅ Success rate is excellent (≥ 99%)")
        elif report.success_rate >= 95:
            print(f"  ⚠️  Success rate is acceptable (95-99%)")
        else:
            print(f"  ❌ Success rate is too low (< 95%)")

        print(f"\n{'='*60}\n")

    def save_report(
        self,
        report: LoadTestReport,
        output_file: str = "load_test_report.json"
    ) -> None:
        """Save report to JSON file"""
        report_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "summary": asdict(report),
            "detailed_results": [asdict(r) for r in self.results]
        }

        with open(output_file, "w") as f:
            json.dump(report_data, f, indent=2)

        print(f"Report saved to: {output_file}")


# Predefined test scenarios

SCENARIOS = {
    "health_check": {
        "endpoint": "/health",
        "method": "GET",
        "payload": None
    },
    "root": {
        "endpoint": "/",
        "method": "GET",
        "payload": None
    },
    "audio_status": {
        "endpoint": "/api/v1/audio/status/test-task-id",
        "method": "GET",
        "payload": None
    }
}


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Load test OmniVibe Pro API"
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="API base URL (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--endpoint",
        default="/health",
        help="API endpoint to test (default: /health)"
    )
    parser.add_argument(
        "--method",
        default="GET",
        choices=["GET", "POST", "PUT", "DELETE"],
        help="HTTP method (default: GET)"
    )
    parser.add_argument(
        "--users",
        type=int,
        default=10,
        help="Number of concurrent users (default: 10)"
    )
    parser.add_argument(
        "--requests",
        type=int,
        default=100,
        help="Total number of requests (default: 100)"
    )
    parser.add_argument(
        "--scenario",
        choices=list(SCENARIOS.keys()),
        help="Predefined test scenario"
    )
    parser.add_argument(
        "--output",
        default="load_test_report.json",
        help="Output report file (default: load_test_report.json)"
    )

    args = parser.parse_args()

    # Use scenario if specified
    if args.scenario:
        scenario = SCENARIOS[args.scenario]
        endpoint = scenario["endpoint"]
        method = scenario["method"]
        payload = scenario["payload"]
    else:
        endpoint = args.endpoint
        method = args.method
        payload = None

    # Create tester
    tester = LoadTester(base_url=args.base_url)

    # Run load test
    report = await tester.run_load_test(
        endpoint=endpoint,
        method=method,
        concurrent_users=args.users,
        total_requests=args.requests,
        payload=payload
    )

    # Save report
    tester.save_report(report, args.output)


if __name__ == "__main__":
    asyncio.run(main())
