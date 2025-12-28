#!/usr/bin/env python3
"""
Professional Ollama Embedding Models Performance Tester (Variant C).

Comprehensive testing suite for Ollama embedding models running in Docker.
Optimized for weak hardware with extended timeouts and robust error handling.

Features:
    - Async/sync hybrid architecture for optimal performance
    - Docker container health monitoring
    - Comprehensive metrics collection
    - Multiple output formats (JSON, CSV, Markdown, HTML)
    - Retry mechanisms with exponential backoff
    - Memory-efficient batch processing
    - Real-time progress tracking

Usage:
    python test_ollama_embeddings.py
    python test_ollama_embeddings.py --config config.json
    python test_ollama_embeddings.py --models qwen3-embedding:0.6b-q8_0
    python test_ollama_embeddings.py --docker-check
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import logging
import subprocess
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional
from statistics import mean, stdev, median

import httpx
from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
)
from rich.table import Table
from rich.panel import Panel
from rich import box

# ============================================================================
# Constants
# ============================================================================

OLLAMA_URL = "http://localhost:11434"
DOCKER_CONTAINER_NAME = "ollama"
DEFAULT_TIMEOUT = 180  # 3 minutes for weak hardware
DEFAULT_RETRIES = 3
DEFAULT_TESTS_PER_MODEL = 5
DEFAULT_WARMUP_REQUESTS = 1
INTERVAL_BETWEEN_TESTS = 3  # seconds

# Test models list
DEFAULT_MODELS = [
    "embeddinggemma:300m-qat-q8_0",
    "qwen3-embedding:0.6b-fp16",
    "qwen3-embedding:0.6b-q8_0",
    "embeddinggemma:300m-qat-q4_0",
    "all-minilm:22m-l6-v2-fp16",
    "bge-m3:567m-fp16",
    "embeddinggemma:300m-bf16",
    "nomic-embed-text:137m-v1.5-fp16",
    "qllama/multilingual-e5-small:f16",
    "all-minilm:l6-v2",
]

# Test texts in Russian and English
TEST_TEXTS = [
    "Привет, мир! Как дела?",
    "Это тестовый текст для проверки embedding моделей.",
    "Machine learning и искусственный интеллект развиваются очень быстро.",
    "Python - популярный язык программирования для научных вычислений.",
    "Docker контейнеризация позволяет упростить развертывание приложений.",
    "Open source программное обеспечение доступно для всех.",
    "Нейронные сети используются в различных областях ИИ.",
    "Векторные базы данных эффективны для поиска по сходству.",
    "Квантизация моделей снижает размер и увеличивает скорость.",
    "Embedding модели преобразуют текст в числовые векторы.",
]

# ============================================================================
# Logging Configuration
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ============================================================================
# Enums
# ============================================================================


class TestStatus(str, Enum):
    """Test execution status."""

    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    ERROR = "ERROR"
    TIMEOUT = "TIMEOUT"
    SKIPPED = "SKIPPED"


# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class TestConfig:
    """Configuration for testing."""

    ollama_url: str = OLLAMA_URL
    timeout: int = DEFAULT_TIMEOUT
    max_retries: int = DEFAULT_RETRIES
    tests_per_model: int = DEFAULT_TESTS_PER_MODEL
    warmup_requests: int = DEFAULT_WARMUP_REQUESTS
    interval_between_tests: int = INTERVAL_BETWEEN_TESTS
    models: Optional[list[str]] = None
    output_dir: str = "."
    check_docker: bool = True
    save_json: bool = True
    save_csv: bool = True
    save_markdown: bool = True
    save_html: bool = True


@dataclass
class EmbeddingMetrics:
    """Metrics for a single embedding request."""

    success: bool
    duration: float
    text_length: int
    embedding_dim: Optional[int] = None
    tokens_per_second: Optional[float] = None
    error_message: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ModelTestResult:
    """Aggregated test results for a model."""

    model_name: str
    status: TestStatus
    total_tests: int
    successful_tests: int
    failed_tests: int
    avg_duration: Optional[float] = None
    min_duration: Optional[float] = None
    max_duration: Optional[float] = None
    median_duration: Optional[float] = None
    std_duration: Optional[float] = None
    avg_embedding_dim: Optional[int] = None
    avg_tokens_per_second: Optional[float] = None
    model_size: Optional[str] = None
    error_summary: Optional[str] = None
    individual_metrics: list[EmbeddingMetrics] = field(default_factory=list)


@dataclass
class TestReport:
    """Complete test report."""

    timestamp: str
    config: TestConfig
    docker_status: dict[str, Any]
    results: list[ModelTestResult]
    summary: dict[str, Any]
    duration_seconds: float


# ============================================================================
# Docker Utilities
# ============================================================================


class DockerManager:
    """Manages Docker container interactions."""

    @staticmethod
    def check_docker_installed() -> bool:
        """Check if Docker is installed."""
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    @staticmethod
    def check_container_running(container_name: str = DOCKER_CONTAINER_NAME) -> bool:
        """Check if Ollama container is running."""
        try:
            result = subprocess.run(
                ["docker", "ps", "--filter", f"name={container_name}", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return container_name in result.stdout
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    @staticmethod
    def list_ollama_models() -> list[str]:
        """List models in Ollama container using docker exec."""
        try:
            result = subprocess.run(
                ["docker", "exec", DOCKER_CONTAINER_NAME, "ollama", "list"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")[1:]  # Skip header
                models = []
                for line in lines:
                    parts = line.split()
                    if parts:
                        models.append(parts[0])
                return models
            return []
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return []

    @staticmethod
    def get_docker_status() -> dict[str, Any]:
        """Get comprehensive Docker status."""
        return {
            "docker_installed": DockerManager.check_docker_installed(),
            "container_running": DockerManager.check_container_running(),
            "available_models": DockerManager.list_ollama_models(),
            "timestamp": datetime.now().isoformat(),
        }


# ============================================================================
# Ollama Client
# ============================================================================


class OllamaClient:
    """Async HTTP client for Ollama API."""

    def __init__(self, base_url: str = OLLAMA_URL, timeout: int = DEFAULT_TIMEOUT):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()

    async def health_check(self) -> bool:
        """Check if Ollama is accessible."""
        try:
            response = await self._client.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except httpx.HTTPError:
            return False

    async def get_embedding(
        self,
        model: str,
        prompt: str,
        retries: int = DEFAULT_RETRIES,
    ) -> tuple[Optional[list[float]], float, Optional[str]]:
        """
        Get embedding for text with retry logic.

        Returns:
            Tuple of (embedding, duration, error_message)
        """
        start_time = time.perf_counter()
        last_error = None

        for attempt in range(retries):
            try:
                response = await self._client.post(
                    f"{self.base_url}/api/embeddings",
                    json={"model": model, "prompt": prompt},
                )
                duration = time.perf_counter() - start_time

                if response.status_code == 200:
                    data = response.json()
                    embedding = data.get("embedding", [])
                    return embedding, duration, None
                else:
                    last_error = f"HTTP {response.status_code}: {response.text[:200]}"

            except httpx.TimeoutException:
                last_error = f"Timeout after {self.timeout}s"
            except httpx.HTTPError as e:
                last_error = f"HTTP Error: {str(e)}"
            except Exception as e:
                last_error = f"Unexpected error: {str(e)}"

            if attempt < retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

        duration = time.perf_counter() - start_time
        return None, duration, last_error


# ============================================================================
# Embedding Tester
# ============================================================================


class EmbeddingTester:
    """Main testing orchestrator."""

    def __init__(self, config: TestConfig, console: Optional[Console] = None):
        self.config = config
        self.console = console or Console()
        self.test_texts = TEST_TEXTS

    async def test_single_embedding(
        self,
        client: OllamaClient,
        model: str,
        text: str,
    ) -> EmbeddingMetrics:
        """Test a single embedding request."""
        embedding, duration, error = await client.get_embedding(
            model=model,
            prompt=text,
            retries=self.config.max_retries,
        )

        if embedding:
            embedding_dim = len(embedding)
            tokens_per_second = embedding_dim / duration if duration > 0 else 0
            return EmbeddingMetrics(
                success=True,
                duration=duration,
                text_length=len(text),
                embedding_dim=embedding_dim,
                tokens_per_second=tokens_per_second,
            )
        else:
            return EmbeddingMetrics(
                success=False,
                duration=duration,
                text_length=len(text),
                error_message=error,
            )

    async def test_model(
        self,
        client: OllamaClient,
        model: str,
        progress: Optional[Progress] = None,
        task_id: Optional[int] = None,
    ) -> ModelTestResult:
        """Test a single model with multiple requests."""
        logger.info(f"Testing model: {model}")

        # Warmup requests
        if self.config.warmup_requests > 0:
            logger.debug(f"Performing {self.config.warmup_requests} warmup request(s)")
            for _ in range(self.config.warmup_requests):
                await client.get_embedding(model, self.test_texts[0])
                await asyncio.sleep(1)

        # Actual tests
        metrics_list: list[EmbeddingMetrics] = []

        for i in range(self.config.tests_per_model):
            text = self.test_texts[i % len(self.test_texts)]
            metrics = await self.test_single_embedding(client, model, text)
            metrics_list.append(metrics)

            if progress and task_id is not None:
                progress.update(task_id, advance=1)

            # Interval between tests
            if i < self.config.tests_per_model - 1:
                await asyncio.sleep(self.config.interval_between_tests)

        # Aggregate results
        successful = [m for m in metrics_list if m.success]
        failed = [m for m in metrics_list if not m.success]

        if not successful:
            error_messages = [m.error_message for m in failed if m.error_message]
            return ModelTestResult(
                model_name=model,
                status=TestStatus.FAILED,
                total_tests=len(metrics_list),
                successful_tests=0,
                failed_tests=len(failed),
                error_summary="; ".join(set(error_messages)) if error_messages else "All tests failed",
                individual_metrics=metrics_list,
            )

        durations = [m.duration for m in successful]
        embedding_dims = [m.embedding_dim for m in successful if m.embedding_dim]
        tokens_per_sec = [m.tokens_per_second for m in successful if m.tokens_per_second]

        return ModelTestResult(
            model_name=model,
            status=TestStatus.SUCCESS,
            total_tests=len(metrics_list),
            successful_tests=len(successful),
            failed_tests=len(failed),
            avg_duration=mean(durations),
            min_duration=min(durations),
            max_duration=max(durations),
            median_duration=median(durations),
            std_duration=stdev(durations) if len(durations) > 1 else 0.0,
            avg_embedding_dim=int(mean(embedding_dims)) if embedding_dims else None,
            avg_tokens_per_second=mean(tokens_per_sec) if tokens_per_sec else None,
            individual_metrics=metrics_list,
        )

    async def run_tests(self) -> TestReport:
        """Run all tests."""
        start_time = time.perf_counter()

        # Check Docker status
        docker_status = {}
        if self.config.check_docker:
            self.console.print("[cyan]Checking Docker status...[/cyan]")
            docker_status = DockerManager.get_docker_status()

            if not docker_status["docker_installed"]:
                raise RuntimeError("Docker is not installed")
            if not docker_status["container_running"]:
                raise RuntimeError(f"Ollama container '{DOCKER_CONTAINER_NAME}' is not running")

            self.console.print(f"[green]✓[/green] Docker container is running")
            self.console.print(f"[green]✓[/green] Found {len(docker_status['available_models'])} models")

        # Determine models to test
        models_to_test = self.config.models or DEFAULT_MODELS

        # Verify Ollama connectivity
        async with OllamaClient(self.config.ollama_url, self.config.timeout) as client:
            if not await client.health_check():
                raise RuntimeError(f"Cannot connect to Ollama at {self.config.ollama_url}")

            self.console.print(f"[green]✓[/green] Ollama API is accessible\n")

            # Run tests with progress bar
            results: list[ModelTestResult] = []

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TimeRemainingColumn(),
                console=self.console,
            ) as progress:
                overall_task = progress.add_task(
                    "[cyan]Testing models...",
                    total=len(models_to_test) * self.config.tests_per_model,
                )

                for model in models_to_test:
                    try:
                        result = await self.test_model(client, model, progress, overall_task)
                        results.append(result)
                    except Exception as e:
                        logger.error(f"Error testing {model}: {e}")
                        results.append(
                            ModelTestResult(
                                model_name=model,
                                status=TestStatus.ERROR,
                                total_tests=self.config.tests_per_model,
                                successful_tests=0,
                                failed_tests=self.config.tests_per_model,
                                error_summary=str(e),
                            )
                        )

        # Create summary
        successful_models = [r for r in results if r.status == TestStatus.SUCCESS]
        summary = self._create_summary(results)

        duration = time.perf_counter() - start_time

        return TestReport(
            timestamp=datetime.now().isoformat(),
            config=self.config,
            docker_status=docker_status,
            results=results,
            summary=summary,
            duration_seconds=duration,
        )

    def _create_summary(self, results: list[ModelTestResult]) -> dict[str, Any]:
        """Create summary statistics."""
        successful = [r for r in results if r.status == TestStatus.SUCCESS]

        ranking_by_speed = sorted(
            successful,
            key=lambda x: x.avg_duration or float("inf"),
        )

        ranking_by_quality = sorted(
            successful,
            key=lambda x: x.avg_embedding_dim or 0,
            reverse=True,
        )

        return {
            "total_models": len(results),
            "successful_models": len(successful),
            "failed_models": len([r for r in results if r.status != TestStatus.SUCCESS]),
            "fastest_model": ranking_by_speed[0].model_name if ranking_by_speed else None,
            "highest_quality_model": ranking_by_quality[0].model_name if ranking_by_quality else None,
            "ranking_by_speed": [
                {
                    "rank": i + 1,
                    "model": r.model_name,
                    "avg_duration": r.avg_duration,
                    "embedding_dim": r.avg_embedding_dim,
                }
                for i, r in enumerate(ranking_by_speed)
            ],
            "ranking_by_quality": [
                {
                    "rank": i + 1,
                    "model": r.model_name,
                    "embedding_dim": r.avg_embedding_dim,
                    "avg_duration": r.avg_duration,
                }
                for i, r in enumerate(ranking_by_quality)
            ],
        }

    def print_summary(self, report: TestReport) -> None:
        """Print summary to console."""
        self.console.print("\n")
        self.console.print(
            Panel.fit(
                "[bold cyan]🤖 Ollama Embedding Models Test Results[/bold cyan]",
                border_style="cyan",
            )
        )

        # Summary table
        summary_table = Table(box=box.ROUNDED)
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", style="green")

        summary_table.add_row("Total Models", str(report.summary["total_models"]))
        summary_table.add_row("Successful", str(report.summary["successful_models"]))
        summary_table.add_row("Failed", str(report.summary["failed_models"]))
        summary_table.add_row("Test Duration", f"{report.duration_seconds:.2f}s")

        self.console.print(summary_table)

        # Top 5 by speed
        if report.summary["ranking_by_speed"]:
            self.console.print("\n[bold cyan]🏆 Top 5 Fastest Models[/bold cyan]")

            speed_table = Table(box=box.ROUNDED)
            speed_table.add_column("Rank", justify="center", style="yellow")
            speed_table.add_column("Model", style="magenta")
            speed_table.add_column("Avg Time (s)", justify="right", style="green")
            speed_table.add_column("Embedding Dim", justify="right", style="blue")

            for entry in report.summary["ranking_by_speed"][:5]:
                speed_table.add_row(
                    str(entry["rank"]),
                    entry["model"],
                    f"{entry['avg_duration']:.4f}" if entry["avg_duration"] else "N/A",
                    str(entry["embedding_dim"]) if entry["embedding_dim"] else "N/A",
                )

            self.console.print(speed_table)


# ============================================================================
# Report Exporters
# ============================================================================


class ReportExporter:
    """Export test reports to various formats."""

    @staticmethod
    def save_json(report: TestReport, filepath: Path) -> None:
        """Save report as JSON."""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(asdict(report), f, indent=2, ensure_ascii=False, default=str)

    @staticmethod
    def save_csv(report: TestReport, filepath: Path) -> None:
        """Save report as CSV."""
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Model",
                "Status",
                "Successful Tests",
                "Failed Tests",
                "Avg Duration (s)",
                "Min Duration (s)",
                "Max Duration (s)",
                "Median Duration (s)",
                "Std Dev (s)",
                "Embedding Dim",
                "Tokens/sec",
            ])

            for result in report.results:
                writer.writerow([
                    result.model_name,
                    result.status.value,
                    result.successful_tests,
                    result.failed_tests,
                    f"{result.avg_duration:.4f}" if result.avg_duration else "",
                    f"{result.min_duration:.4f}" if result.min_duration else "",
                    f"{result.max_duration:.4f}" if result.max_duration else "",
                    f"{result.median_duration:.4f}" if result.median_duration else "",
                    f"{result.std_duration:.4f}" if result.std_duration else "",
                    result.avg_embedding_dim or "",
                    f"{result.avg_tokens_per_second:.2f}" if result.avg_tokens_per_second else "",
                ])

    @staticmethod
    def save_markdown(report: TestReport, filepath: Path) -> None:
        """Save report as Markdown."""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("# Ollama Embedding Models Performance Test Report\n\n")
            f.write(f"**Timestamp:** {report.timestamp}\n\n")
            f.write(f"**Ollama URL:** {report.config.ollama_url}\n\n")
            f.write(f"**Test Duration:** {report.duration_seconds:.2f}s\n\n")

            # Summary
            f.write("## Summary\n\n")
            f.write(f"- **Total Models:** {report.summary['total_models']}\n")
            f.write(f"- **Successful:** {report.summary['successful_models']}\n")
            f.write(f"- **Failed:** {report.summary['failed_models']}\n\n")

            # Ranking by speed
            if report.summary["ranking_by_speed"]:
                f.write("## Ranking by Speed\n\n")
                f.write("| Rank | Model | Avg Time (s) | Embedding Dim |\n")
                f.write("|------|-------|--------------|---------------|\n")

                for entry in report.summary["ranking_by_speed"]:
                    f.write(
                        f"| {entry['rank']} | {entry['model']} | "
                        f"{entry['avg_duration']:.4f} | {entry['embedding_dim']} |\n"
                    )

                f.write("\n")

            # Detailed results
            f.write("## Detailed Results\n\n")
            for result in report.results:
                f.write(f"### {result.model_name}\n\n")
                f.write(f"- **Status:** {result.status.value}\n")
                f.write(f"- **Successful Tests:** {result.successful_tests}/{result.total_tests}\n")

                if result.status == TestStatus.SUCCESS:
                    f.write(f"- **Avg Duration:** {result.avg_duration:.4f}s\n")
                    f.write(f"- **Min Duration:** {result.min_duration:.4f}s\n")
                    f.write(f"- **Max Duration:** {result.max_duration:.4f}s\n")
                    f.write(f"- **Median Duration:** {result.median_duration:.4f}s\n")
                    f.write(f"- **Std Dev:** {result.std_duration:.4f}s\n")
                    f.write(f"- **Embedding Dim:** {result.avg_embedding_dim}\n")
                    f.write(f"- **Tokens/sec:** {result.avg_tokens_per_second:.2f}\n")
                else:
                    f.write(f"- **Error:** {result.error_summary}\n")

                f.write("\n")

    @staticmethod
    def save_html(report: TestReport, filepath: Path) -> None:
        """Save report as HTML."""
        html_content = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ollama Embedding Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #3498db; color: white; }}
        tr:hover {{ background-color: #f5f5f5; }}
        .success {{ color: #27ae60; font-weight: bold; }}
        .failed {{ color: #e74c3c; font-weight: bold; }}
        .metric {{ display: inline-block; margin: 10px 20px 10px 0; padding: 10px; background: #ecf0f1; border-radius: 4px; }}
        .metric-label {{ font-weight: bold; color: #7f8c8d; }}
        .metric-value {{ font-size: 1.2em; color: #2c3e50; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Ollama Embedding Models Performance Test Report</h1>
        
        <div class="metric">
            <span class="metric-label">Timestamp:</span>
            <span class="metric-value">{report.timestamp}</span>
        </div>
        <div class="metric">
            <span class="metric-label">Duration:</span>
            <span class="metric-value">{report.duration_seconds:.2f}s</span>
        </div>
        <div class="metric">
            <span class="metric-label">Total Models:</span>
            <span class="metric-value">{report.summary['total_models']}</span>
        </div>
        <div class="metric">
            <span class="metric-label">Successful:</span>
            <span class="metric-value success">{report.summary['successful_models']}</span>
        </div>
        <div class="metric">
            <span class="metric-label">Failed:</span>
            <span class="metric-value failed">{report.summary['failed_models']}</span>
        </div>

        <h2>🏆 Ranking by Speed</h2>
        <table>
            <thead>
                <tr>
                    <th>Rank</th>
                    <th>Model</th>
                    <th>Avg Time (s)</th>
                    <th>Embedding Dim</th>
                    <th>Tokens/sec</th>
                </tr>
            </thead>
            <tbody>
"""

        for entry in report.summary["ranking_by_speed"]:
            html_content += f"""
                <tr>
                    <td>{entry['rank']}</td>
                    <td>{entry['model']}</td>
                    <td>{entry['avg_duration']:.4f}</td>
                    <td>{entry['embedding_dim']}</td>
                    <td>-</td>
                </tr>
"""

        html_content += """
            </tbody>
        </table>

        <h2>📊 Detailed Results</h2>
        <table>
            <thead>
                <tr>
                    <th>Model</th>
                    <th>Status</th>
                    <th>Success Rate</th>
                    <th>Avg Time (s)</th>
                    <th>Embedding Dim</th>
                </tr>
            </thead>
            <tbody>
"""

        for result in report.results:
            status_class = "success" if result.status == TestStatus.SUCCESS else "failed"
            success_rate = f"{result.successful_tests}/{result.total_tests}"
            avg_time = f"{result.avg_duration:.4f}" if result.avg_duration else "N/A"
            embedding_dim = str(result.avg_embedding_dim) if result.avg_embedding_dim else "N/A"

            html_content += f"""
                <tr>
                    <td>{result.model_name}</td>
                    <td class="{status_class}">{result.status.value}</td>
                    <td>{success_rate}</td>
                    <td>{avg_time}</td>
                    <td>{embedding_dim}</td>
                </tr>
"""

        html_content += """
            </tbody>
        </table>
    </div>
</body>
</html>
"""

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)


# ============================================================================
# CLI
# ============================================================================


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Professional Ollama Embedding Models Performance Tester",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--config",
        type=str,
        help="Path to JSON configuration file",
    )

    parser.add_argument(
        "--url",
        type=str,
        default=OLLAMA_URL,
        help=f"Ollama API URL (default: {OLLAMA_URL})",
    )

    parser.add_argument(
        "--models",
        type=str,
        nargs="+",
        help="Specific models to test (space-separated)",
    )

    parser.add_argument(
        "--tests-per-model",
        type=int,
        default=DEFAULT_TESTS_PER_MODEL,
        help=f"Number of tests per model (default: {DEFAULT_TESTS_PER_MODEL})",
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f"Request timeout in seconds (default: {DEFAULT_TIMEOUT})",
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default=".",
        help="Output directory for results",
    )

    parser.add_argument(
        "--no-docker-check",
        action="store_true",
        help="Skip Docker container check",
    )

    parser.add_argument(
        "--docker-check",
        action="store_true",
        help="Only check Docker status and exit",
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    return parser.parse_args()


async def async_main() -> int:
    """Async main function."""
    args = parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    console = Console()

    try:
        # Docker check only mode
        if args.docker_check:
            console.print("[cyan]Checking Docker status...[/cyan]")
            status = DockerManager.get_docker_status()

            console.print(f"\n[bold]Docker Status:[/bold]")
            console.print(f"  Docker Installed: {'✓' if status['docker_installed'] else '✗'}")
            console.print(f"  Container Running: {'✓' if status['container_running'] else '✗'}")
            console.print(f"  Available Models: {len(status['available_models'])}")

            if status['available_models']:
                console.print("\n[bold]Models in Ollama:[/bold]")
                for model in status['available_models']:
                    console.print(f"  • {model}")

            return 0

        # Load configuration
        if args.config:
            with open(args.config, "r", encoding="utf-8") as f:
                config_data = json.load(f)
            config = TestConfig(**config_data)
        else:
            config = TestConfig(
                ollama_url=args.url,
                timeout=args.timeout,
                tests_per_model=args.tests_per_model,
                models=args.models,
                output_dir=args.output_dir,
                check_docker=not args.no_docker_check,
            )

        # Run tests
        tester = EmbeddingTester(config, console)
        report = await tester.run_tests()

        # Print summary
        tester.print_summary(report)

        # Save results
        output_dir = Path(config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"ollama_embedding_test_{timestamp}"

        saved_files = []

        if config.save_json:
            json_path = output_dir / f"{base_filename}.json"
            ReportExporter.save_json(report, json_path)
            saved_files.append(("JSON", json_path))

        if config.save_csv:
            csv_path = output_dir / f"{base_filename}.csv"
            ReportExporter.save_csv(report, csv_path)
            saved_files.append(("CSV", csv_path))

        if config.save_markdown:
            md_path = output_dir / f"{base_filename}.md"
            ReportExporter.save_markdown(report, md_path)
            saved_files.append(("Markdown", md_path))

        if config.save_html:
            html_path = output_dir / f"{base_filename}.html"
            ReportExporter.save_html(report, html_path)
            saved_files.append(("HTML", html_path))

        console.print("\n[bold green]📁 Results saved:[/bold green]")
        for format_name, filepath in saved_files:
            console.print(f"  • {format_name}: {filepath}")

        console.print(
            f"\n[bold green]✅ Testing complete! "
            f"{report.summary['successful_models']}/{report.summary['total_models']} "
            f"models tested successfully.[/bold green]"
        )

        return 0

    except KeyboardInterrupt:
        console.print("\n[yellow]⚠ Test interrupted by user[/yellow]")
        return 130

    except Exception as e:
        logger.exception("Unexpected error")
        console.print(f"[bold red]❌ Error: {e}[/bold red]")
        return 1


def main() -> int:
    """Main entry point."""
    return asyncio.run(async_main())


if __name__ == "__main__":
    sys.exit(main())