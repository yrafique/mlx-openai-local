#!/usr/bin/env python3
"""
Comprehensive Test Suite for ChatGPT-Level Platform
Tests all capabilities with real-world scenarios and generates detailed report.
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import tool definitions
from server.tools.code_execution import CODE_EXECUTION_TOOL_DEFINITIONS
from server.tools.financial_data import FINANCIAL_TOOL_DEFINITIONS
from server.tools.enhanced_web_search import ENHANCED_TOOL_DEFINITIONS
from server.tools.table_formatter import TABLE_FORMATTER_TOOL_DEFINITIONS

# Import enhanced system prompt
from server.prompts.system_prompt import get_system_prompt

# Combine all tools
ALL_TOOLS = []
ALL_TOOLS.extend(CODE_EXECUTION_TOOL_DEFINITIONS)
ALL_TOOLS.extend(FINANCIAL_TOOL_DEFINITIONS)
ALL_TOOLS.extend(ENHANCED_TOOL_DEFINITIONS)
ALL_TOOLS.extend(TABLE_FORMATTER_TOOL_DEFINITIONS)

# Get enhanced system prompt with reasoning
SYSTEM_PROMPT = get_system_prompt("reasoning")

# Configuration
API_BASE = "http://localhost:7007/v1"
MODEL = "mlx-community/Llama-3.2-3B-Instruct-4bit"
TIMEOUT = 120


class TestScenario:
    """Test scenario definition"""
    def __init__(self, name: str, category: str, description: str, user_input: str,
                 expected_tools: List[str] = None, success_criteria: Dict = None):
        self.name = name
        self.category = category
        self.description = description
        self.user_input = user_input
        self.expected_tools = expected_tools or []
        self.success_criteria = success_criteria or {}
        self.result = None
        self.score = 0
        self.execution_time = 0
        self.errors = []


class ComprehensiveTestSuite:
    """Comprehensive test suite for all platform capabilities"""

    def __init__(self):
        self.scenarios = []
        self.results = []
        self.start_time = None
        self.end_time = None

    def add_scenario(self, scenario: TestScenario):
        """Add a test scenario"""
        self.scenarios.append(scenario)

    def run_all_tests(self):
        """Run all test scenarios"""
        print("=" * 80)
        print("🧪 COMPREHENSIVE TEST SUITE - ChatGPT-Level Platform")
        print("=" * 80)
        print(f"Total Scenarios: {len(self.scenarios)}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        print()

        self.start_time = time.time()

        for i, scenario in enumerate(self.scenarios, 1):
            print(f"\n[{i}/{len(self.scenarios)}] Testing: {scenario.name}")
            print(f"Category: {scenario.category}")
            print(f"Description: {scenario.description}")
            print(f"Input: {scenario.user_input}")
            print("-" * 80)

            try:
                result = self._run_scenario(scenario)
                scenario.result = result
                score = self._evaluate_scenario(scenario, result)
                scenario.score = score

                print(f"✅ Score: {score}/100")
                if scenario.errors:
                    print(f"⚠️  Issues: {', '.join(scenario.errors)}")

            except Exception as e:
                scenario.errors.append(str(e))
                scenario.score = 0
                print(f"❌ Error: {e}")

            self.results.append(scenario)
            time.sleep(1)  # Rate limiting

        self.end_time = time.time()

    def _run_scenario(self, scenario: TestScenario) -> Dict:
        """Run a single test scenario"""
        start = time.time()

        # Prepare API call with tools and enhanced system prompt
        payload = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": scenario.user_input}
            ],
            "max_tokens": 1000,
            "temperature": 0.7,
            "tools": ALL_TOOLS,
            "tool_choice": "auto"
        }

        # Call API
        response = requests.post(
            f"{API_BASE}/chat/completions",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=TIMEOUT
        )

        scenario.execution_time = time.time() - start

        if response.status_code != 200:
            raise Exception(f"API returned status {response.status_code}: {response.text}")

        return response.json()

    def _evaluate_scenario(self, scenario: TestScenario, result: Dict) -> int:
        """Evaluate scenario result and return score (0-100)"""
        score = 0

        # Check if response exists
        if not result or "choices" not in result:
            scenario.errors.append("No response from API")
            return 0

        choice = result["choices"][0]
        message = choice.get("message", {})

        # Base score for successful response
        score += 20

        # Check for tool calls if expected
        if scenario.expected_tools:
            tool_calls = message.get("tool_calls", [])
            if tool_calls:
                score += 30

                # Check if expected tools were called
                called_tools = [tc["function"]["name"] for tc in tool_calls]
                for expected_tool in scenario.expected_tools:
                    if expected_tool in called_tools:
                        score += 10
                    else:
                        scenario.errors.append(f"Expected tool '{expected_tool}' not called")
            else:
                scenario.errors.append("No tools called")
        else:
            # If no tools expected, check for content
            if message.get("content"):
                score += 40

        # Check response quality
        content = message.get("content", "")
        if len(content) > 50:
            score += 10
        if len(content) > 200:
            score += 10

        # Check execution time
        if scenario.execution_time < 5:
            score += 10
        elif scenario.execution_time < 10:
            score += 5

        # Apply success criteria if provided
        for criterion, check in scenario.success_criteria.items():
            if callable(check):
                if check(result):
                    score += 10
                else:
                    scenario.errors.append(f"Failed criterion: {criterion}")

        return min(score, 100)

    def generate_report(self) -> str:
        """Generate comprehensive test report"""
        total_time = self.end_time - self.start_time
        total_scenarios = len(self.results)
        passed = sum(1 for r in self.results if r.score >= 70)
        failed = total_scenarios - passed
        avg_score = sum(r.score for r in self.results) / total_scenarios if total_scenarios > 0 else 0

        # Group by category
        by_category = {}
        for result in self.results:
            if result.category not in by_category:
                by_category[result.category] = []
            by_category[result.category].append(result)

        report = []
        report.append("=" * 80)
        report.append("📊 COMPREHENSIVE TEST REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Total Execution Time: {total_time:.2f} seconds")
        report.append("")
        report.append("## Summary")
        report.append("-" * 80)
        report.append(f"Total Scenarios: {total_scenarios}")
        report.append(f"Passed (≥70): {passed} ({passed/total_scenarios*100:.1f}%)")
        report.append(f"Failed (<70): {failed} ({failed/total_scenarios*100:.1f}%)")
        report.append(f"Average Score: {avg_score:.1f}/100")
        report.append("")

        # Results by category
        report.append("## Results by Category")
        report.append("-" * 80)
        for category, scenarios in sorted(by_category.items()):
            cat_avg = sum(s.score for s in scenarios) / len(scenarios)
            cat_passed = sum(1 for s in scenarios if s.score >= 70)
            report.append(f"\n### {category}")
            report.append(f"Scenarios: {len(scenarios)}")
            report.append(f"Average Score: {cat_avg:.1f}/100")
            report.append(f"Passed: {cat_passed}/{len(scenarios)}")
            report.append("")

            for scenario in scenarios:
                status = "✅" if scenario.score >= 70 else "❌"
                report.append(f"{status} {scenario.name}: {scenario.score}/100 ({scenario.execution_time:.2f}s)")
                if scenario.errors:
                    for error in scenario.errors:
                        report.append(f"   ⚠️  {error}")

        # Detailed results
        report.append("\n" + "=" * 80)
        report.append("## Detailed Test Results")
        report.append("=" * 80)

        for i, scenario in enumerate(self.results, 1):
            report.append(f"\n### Test {i}: {scenario.name}")
            report.append(f"Category: {scenario.category}")
            report.append(f"Score: {scenario.score}/100")
            report.append(f"Execution Time: {scenario.execution_time:.2f}s")
            report.append(f"Input: {scenario.user_input}")

            if scenario.result and "choices" in scenario.result:
                message = scenario.result["choices"][0].get("message", {})

                # Show tool calls
                if "tool_calls" in message:
                    report.append("\nTool Calls:")
                    for tc in message["tool_calls"]:
                        report.append(f"  • {tc['function']['name']}")
                        report.append(f"    Args: {tc['function']['arguments']}")

                # Show response preview
                if "content" in message and message["content"]:
                    content = message["content"]
                    preview = content[:200] + "..." if len(content) > 200 else content
                    report.append(f"\nResponse Preview:\n{preview}")

            if scenario.errors:
                report.append("\nIssues:")
                for error in scenario.errors:
                    report.append(f"  ⚠️  {error}")

            report.append("-" * 80)

        # Performance metrics
        report.append("\n" + "=" * 80)
        report.append("## Performance Metrics")
        report.append("=" * 80)
        avg_time = sum(s.execution_time for s in self.results) / total_scenarios
        fastest = min(self.results, key=lambda s: s.execution_time)
        slowest = max(self.results, key=lambda s: s.execution_time)

        report.append(f"Average Response Time: {avg_time:.2f}s")
        report.append(f"Fastest: {fastest.name} ({fastest.execution_time:.2f}s)")
        report.append(f"Slowest: {slowest.name} ({slowest.execution_time:.2f}s)")

        # Recommendations
        report.append("\n" + "=" * 80)
        report.append("## Recommendations")
        report.append("=" * 80)

        if avg_score >= 80:
            report.append("✅ Excellent! Platform is performing at ChatGPT level.")
        elif avg_score >= 70:
            report.append("✅ Good! Platform is working well with minor improvements needed.")
        elif avg_score >= 60:
            report.append("⚠️  Fair. Some features need attention.")
        else:
            report.append("❌ Needs improvement. Several features are not working as expected.")

        if failed > 0:
            report.append(f"\nFailed Scenarios ({failed}):")
            for scenario in [s for s in self.results if s.score < 70]:
                report.append(f"  • {scenario.name}: {scenario.score}/100")
                for error in scenario.errors[:3]:
                    report.append(f"    - {error}")

        report.append("\n" + "=" * 80)

        return "\n".join(report)


def create_test_scenarios() -> List[TestScenario]:
    """Create all test scenarios"""
    scenarios = []

    # ============================================================================
    # 1. CODE EXECUTION SCENARIOS
    # ============================================================================

    scenarios.append(TestScenario(
        name="Simple Calculation",
        category="Code Execution",
        description="Basic arithmetic calculation",
        user_input="Calculate 2^10 and tell me the result",
        expected_tools=["execute_python_code"],
        success_criteria={
            "contains_1024": lambda r: "1024" in str(r)
        }
    ))

    scenarios.append(TestScenario(
        name="Data Analysis",
        category="Code Execution",
        description="Analyze list of numbers",
        user_input="Given the numbers [10, 20, 30, 40, 50], calculate the mean, median, and standard deviation",
        expected_tools=["execute_python_code"]
    ))

    scenarios.append(TestScenario(
        name="Plot Generation",
        category="Code Execution",
        description="Generate a simple plot",
        user_input="Create a line plot showing y = x^2 for x from 0 to 10",
        expected_tools=["execute_python_code"]
    ))

    # ============================================================================
    # 2. FINANCIAL DATA SCENARIOS
    # ============================================================================

    scenarios.append(TestScenario(
        name="Current Stock Price",
        category="Financial Data",
        description="Get real-time stock price",
        user_input="What is the current price of Apple (AAPL) stock?",
        expected_tools=["get_stock_price"]
    ))

    scenarios.append(TestScenario(
        name="Crypto Price",
        category="Financial Data",
        description="Get cryptocurrency price",
        user_input="What is the current price of Bitcoin?",
        expected_tools=["get_crypto_price"]
    ))

    scenarios.append(TestScenario(
        name="Historical Stock Data",
        category="Financial Data",
        description="Get historical data with chart",
        user_input="Show me Tesla stock performance for the last 6 months",
        expected_tools=["get_stock_history"]
    ))

    # ============================================================================
    # 3. WEB SEARCH SCENARIOS
    # ============================================================================

    scenarios.append(TestScenario(
        name="Current Events",
        category="Web Search",
        description="Search for current information",
        user_input="What are the latest developments in AI technology?",
        expected_tools=["search_web_enhanced"]
    ))

    scenarios.append(TestScenario(
        name="Weather Query",
        category="Web Search",
        description="Get weather information",
        user_input="What's the weather like in London right now?",
        expected_tools=["get_weather_enhanced"]
    ))

    # ============================================================================
    # 4. DATA ANALYSIS SCENARIOS
    # ============================================================================

    scenarios.append(TestScenario(
        name="Statistical Analysis",
        category="Data Analysis",
        description="Perform statistical calculations",
        user_input="I have sales data: Jan=$10000, Feb=$12000, Mar=$11500, Apr=$15000. Calculate the growth rate and total",
        expected_tools=["execute_python_code"]
    ))

    scenarios.append(TestScenario(
        name="Comparison Table",
        category="Data Analysis",
        description="Create comparison table",
        user_input="Create a comparison table of Python vs JavaScript vs Go showing typing, speed, and use cases",
        expected_tools=["format_table"]
    ))

    # ============================================================================
    # 5. MULTI-STEP WORKFLOW SCENARIOS
    # ============================================================================

    scenarios.append(TestScenario(
        name="Financial Analysis Workflow",
        category="Multi-Step Workflow",
        description="Analyze stock and calculate investment",
        user_input="Get Tesla's current stock price, then calculate how many shares I can buy with $5000 and what my investment would be worth",
        expected_tools=["get_stock_price", "execute_python_code"]
    ))

    scenarios.append(TestScenario(
        name="Data Processing Pipeline",
        category="Multi-Step Workflow",
        description="Process data and visualize",
        user_input="Take the fibonacci sequence up to 100, calculate the ratio between consecutive numbers, and create a visualization",
        expected_tools=["execute_python_code"]
    ))

    # ============================================================================
    # 6. REASONING & PROBLEM SOLVING
    # ============================================================================

    scenarios.append(TestScenario(
        name="Mathematical Problem",
        category="Reasoning",
        description="Solve multi-step math problem",
        user_input="If I invest $10,000 at 5% annual interest compounded monthly for 10 years, how much will I have? Show the calculation.",
        expected_tools=["execute_python_code"]
    ))

    scenarios.append(TestScenario(
        name="Logical Reasoning",
        category="Reasoning",
        description="Apply logical thinking",
        user_input="If it takes 5 machines 5 minutes to make 5 widgets, how long would it take 100 machines to make 100 widgets?",
        expected_tools=[]  # Might not need tools, just reasoning
    ))

    # ============================================================================
    # 7. FORMAT & PRESENTATION
    # ============================================================================

    scenarios.append(TestScenario(
        name="Table Formatting",
        category="Formatting",
        description="Format data into table",
        user_input="Show me the top 5 most populous countries with their population in millions",
        expected_tools=[]  # May or may not use tools
    ))

    return scenarios


def main():
    """Main test execution"""
    # Create test suite
    suite = ComprehensiveTestSuite()

    # Add all scenarios
    scenarios = create_test_scenarios()
    for scenario in scenarios:
        suite.add_scenario(scenario)

    print(f"\n📋 Loaded {len(scenarios)} test scenarios")
    print("Categories:", set(s.category for s in scenarios))
    print()

    # Check if server is running
    try:
        response = requests.get(f"{API_BASE}/models", timeout=5)
        if response.status_code != 200:
            print("❌ Server not responding. Please start the server with:")
            print("   ./scripts/orchestrate.sh --start")
            return 1
    except Exception as e:
        print("❌ Cannot connect to server. Please start the server with:")
        print("   ./scripts/orchestrate.sh --start")
        return 1

    print("✅ Server is running\n")

    # Run tests
    suite.run_all_tests()

    # Generate report
    print("\n")
    report = suite.generate_report()
    print(report)

    # Save report to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = Path(__file__).parent / f"test_report_{timestamp}.md"

    with open(report_file, "w") as f:
        f.write(report)

    print(f"\n📄 Report saved to: {report_file}")

    # Return exit code based on results
    avg_score = sum(r.score for r in suite.results) / len(suite.results)
    return 0 if avg_score >= 70 else 1


if __name__ == "__main__":
    sys.exit(main())
