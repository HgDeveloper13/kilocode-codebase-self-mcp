#!/usr/bin/env python3
"""
Professional Ollama Embedding Models Speed Tester.

This module provides comprehensive testing capabilities for Ollama embedding models
running in Docker containers. Designed for weak hardware with extended timeout handling.

Usage:
    python test_ollama_speed_pro.py --config config.yaml
    python test_ollama_speed_pro.py --models qwen3-embedding:0.6b-q8_0 all-minilm:l6-v2
    python test_ollama_speed_pro.py --help
"""

from __future__ import annotations

import os
import sys

# Настройка кодировки для Windows
if sys.platform.startswith('win'):
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    # Попытка настроить консоль Windows для UTF-8
    try:
        import codecs
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass  # Игнорируем ошибки настройки консоли

import argparse
import asyncio
import csv
import json
import logging
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Self

import pydantic
import requests
import yaml
from rich import box
from rich.console import Console
from rich.table import Table
from tenacity import (
    RetryError,
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

# Константы
DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_TIMEOUT = 120  # seconds for slow hardware
DEFAULT_RETRIES = 3
DEFAULT_RETRY_DELAY = 5  # seconds
DEFAULT_TESTS_PER_MODEL = 5
DEFAULT_INTERVAL_BETWEEN_TESTS = 2  # seconds

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ============================================================================
# Data Classes (Pydantic Models)
# ============================================================================


class TestConfig(pydantic.BaseModel):
    """Конфигурация тестирования."""

    ollama_url: str = DEFAULT_OLLAMA_URL
    timeout: int = DEFAULT_TIMEOUT
    max_retries: int = DEFAULT_RETRIES
    retry_delay: int = DEFAULT_RETRY_DELAY
    tests_per_model: int = DEFAULT_TESTS_PER_MODEL
    interval_between_tests: int = DEFAULT_INTERVAL_BETWEEN_TESTS
    models: list[str] | None = None
    output_dir: str = "."

    model_config = {
        "extra": "forbid",
    }


class ModelInfo(pydantic.BaseModel):
    """Информация о модели из Ollama."""

    name: str
    size: int | None = None
    digest: str | None = None
    modified_at: str | None = None
    embedding_dim: int | None = None


class EmbeddingResult(pydantic.BaseModel):
    """Результат одиночного embedding запроса."""

    success: bool
    duration: float
    text_length: int | None = None
    embedding_dim: int | None = None
    tokens_per_second: float | None = None
    error: str | None = None
    model: str | None = None
    text: str | None = None


class ModelTestResult(pydantic.BaseModel):
    """Результаты тестирования одной модели."""

    model: str
    status: str  # "SUCCESS", "FAILED", "ERROR"
    total_tests: int
    successful_tests: int
    avg_duration: float | None = None
    min_duration: float | None = None
    max_duration: float | None = None
    std_duration: float | None = None
    avg_embedding_dim: float | None = None
    avg_tokens_per_second: float | None = None
    model_info: dict[str, Any] | None = None
    error: str | None = None
    individual_results: list[EmbeddingResult] = field(default_factory=list)


class TestSummary(pydantic.BaseModel):
    """Сводка результатов тестирования."""

    total_models: int
    successful_models: int
    failed_models: int
    ranking_by_speed: list[dict[str, Any]] = field(default_factory=list)
    ranking_by_quality: list[dict[str, Any]] = field(default_factory=list)


class TestReport(pydantic.BaseModel):
    """Полный отчет тестирования."""

    timestamp: str
    ollama_url: str
    config: TestConfig
    results: list[ModelTestResult]
    summary: TestSummary


# ============================================================================
# Exceptions
# ============================================================================


class OllamaConnectionError(Exception):
    """Ошибка подключения к Ollama."""


class OllamaAPIError(Exception):
    """Ошибка API Ollama."""


class ModelNotFoundError(Exception):
    """Модель не найдена."""


# ============================================================================
# Ollama Client
# ============================================================================


class OllamaClient:
    """Клиент для взаимодействия с Ollama API."""

    def __init__(
        self,
        base_url: str = DEFAULT_OLLAMA_URL,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_RETRIES,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self._session = requests.Session()
        self._session.headers.update({"Content-Type": "application/json"})

    def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> requests.Response:
        """Выполняет HTTP запрос к Ollama API."""
        url = f"{self.base_url}{endpoint}"

        @retry(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(multiplier=1, min=2, max=10),
            retry=retry_if_exception_type((requests.RequestException, TimeoutError)),
        )
        def _do_request() -> requests.Response:
            response = self._session.request(
                method=method,
                url=url,
                timeout=self.timeout,
                **kwargs,
            )
            response.raise_for_status()
            return response

        try:
            return _do_request()
        except RetryError as e:
            raise OllamaConnectionError(f"Failed to connect to Ollama: {e}") from e

    def health_check(self) -> bool:
        """Проверяет доступность Ollama."""
        try:
            response = self._make_request("GET", "/api/tags")
            return response.status_code == 200
        except requests.RequestException:
            return False

    def list_models(self) -> list[str]:
        """Возвращает список доступных моделей."""
        response = self._make_request("GET", "/api/tags")
        data = response.json()
        return [model["name"] for model in data.get("models", [])]

    def get_model_info(self, model_name: str) -> dict[str, Any]:
        """Получает информацию о модели."""
        response = self._make_request(
            "POST",
            "/api/show",
            json={"name": model_name},
        )
        return response.json()

    def get_embedding(
        self,
        model: str,
        prompt: str,
    ) -> dict[str, Any]:
        """Получает embedding для текста."""
        response = self._make_request(
            "POST",
            "/api/embeddings",
            json={"model": model, "prompt": prompt},
        )
        return response.json()


# ============================================================================
# Embedding Tester
# ============================================================================


class EmbeddingTester:
    """Тестер скорости embedding моделей."""

    # Тестовые тексты для проверки embedding моделей
    DEFAULT_TEST_TEXTS = [
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

    # Список всех доступных моделей для тестирования
    ALL_MODELS = [
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

    def __init__(
        self,
        config: TestConfig | None = None,
        console: Console | None = None,
    ) -> None:
        self.config = config or TestConfig()
        self.console = console or Console()
        self.client = OllamaClient(
            base_url=self.config.ollama_url,
            timeout=self.config.timeout,
            max_retries=self.config.max_retries,
        )
        self.test_texts = self.DEFAULT_TEST_TEXTS

    def _calculate_stats(self, values: list[float]) -> dict[str, float]:
        """Вычисляет статистики для списка значений."""
        if not values:
            return {"mean": 0.0, "min": 0.0, "max": 0.0, "std": 0.0}

        import statistics

        mean_val = statistics.mean(values)
        return {
            "mean": mean_val,
            "min": min(values),
            "max": max(values),
            "std": statistics.stdev(values) if len(values) > 1 else 0.0,
        }

    def test_single_embedding(
        self,
        model: str,
        text: str,
    ) -> EmbeddingResult:
        """Тестирует одиночный embedding запрос."""
        start_time = time.perf_counter()

        try:
            response = self.client.get_embedding(model=model, prompt=text)
            duration = time.perf_counter() - start_time

            embedding = response.get("embedding", [])
            embedding_dim = len(embedding) if embedding else 0
            tokens_per_second = (
                embedding_dim / duration if embedding_dim > 0 and duration > 0 else 0.0
            )

            return EmbeddingResult(
                success=True,
                duration=duration,
                text_length=len(text),
                embedding_dim=embedding_dim,
                tokens_per_second=tokens_per_second,
                model=model,
                text=text[:50] + "..." if len(text) > 50 else text,
            )

        except requests.RequestException as e:
            duration = time.perf_counter() - start_time
            return EmbeddingResult(
                success=False,
                duration=duration,
                error=str(e),
                model=model,
                text=text[:50] + "..." if len(text) > 50 else text,
            )
        except TimeoutError as e:
            duration = time.perf_counter() - start_time
            return EmbeddingResult(
                success=False,
                duration=duration,
                error=f"Timeout after {self.config.timeout}s",
                model=model,
                text=text[:50] + "..." if len(text) > 50 else text,
            )

    def test_model(
        self,
        model: str,
        num_tests: int | None = None,
    ) -> ModelTestResult:
        """Тестирует одну модель."""
        num_tests = num_tests or self.config.tests_per_model
        logger.info(f"Testing model: {model}")

        results: list[EmbeddingResult] = []

        for i in range(num_tests):
            text = self.test_texts[i % len(self.test_texts)]
            result = self.test_single_embedding(model, text)
            results.append(result)

            status_icon = "[OK]" if result.success else "[FAIL]"
            logger.info(
                f"  {status_icon} Test {i+1}/{num_tests}: "
                f"{result.duration:.3f}s, dim={result.embedding_dim}"
            )

            # Пауза между тестами для стабильности
            if i < num_tests - 1:
                time.sleep(self.config.interval_between_tests)

        # Анализируем результаты
        successful_results = [r for r in results if r.success]

        if not successful_results:
            return ModelTestResult(
                model=model,
                status="FAILED",
                total_tests=num_tests,
                successful_tests=0,
                error="All tests failed",
                individual_results=results,
            )

        # Вычисляем статистики
        durations = [r.duration for r in successful_results]
        embedding_dims = [r.embedding_dim for r in successful_results if r.embedding_dim]
        tokens_per_sec = [
            r.tokens_per_second for r in successful_results if r.tokens_per_second
        ]

        duration_stats = self._calculate_stats(durations)
        dim_stats = self._calculate_stats(embedding_dims) if embedding_dims else {}
        tps_stats = self._calculate_stats(tokens_per_sec) if tokens_per_sec else {}

        # Получаем информацию о модели
        try:
            model_info = self.client.get_model_info(model)
        except requests.RequestException:
            model_info = {}

        return ModelTestResult(
            model=model,
            status="SUCCESS",
            total_tests=num_tests,
            successful_tests=len(successful_results),
            avg_duration=duration_stats["mean"],
            min_duration=duration_stats["min"],
            max_duration=duration_stats["max"],
            std_duration=duration_stats["std"],
            avg_embedding_dim=dim_stats.get("mean"),
            avg_tokens_per_second=tps_stats.get("mean"),
            model_info=model_info,
            individual_results=results,
        )

    def run_tests(
        self,
        models: list[str] | None = None,
    ) -> TestReport:
        """Запускает полное тестирование моделей."""
        models = models or self.config.models or self.ALL_MODELS

        logger.info(f"Starting tests for {len(models)} models")
        logger.info(f"Ollama URL: {self.config.ollama_url}")

        # Проверяем доступность Ollama
        if not self.client.health_check():
            raise OllamaConnectionError(
                f"Ollama is not available at {self.config.ollama_url}"
            )

        logger.info("Ollama is healthy and ready")

        results: list[ModelTestResult] = []

        for model in models:
            try:
                result = self.test_model(model)
                results.append(result)
            except Exception as e:
                logger.error(f"Error testing {model}: {e}")
                results.append(
                    ModelTestResult(
                        model=model,
                        status="ERROR",
                        total_tests=self.config.tests_per_model,
                        successful_tests=0,
                        error=str(e),
                    )
                )

        # Создаем сводку
        summary = self._create_summary(results)

        return TestReport(
            timestamp=datetime.now().isoformat(),
            ollama_url=self.config.ollama_url,
            config=self.config,
            results=results,
            summary=summary,
        )

    def _create_summary(self, results: list[ModelTestResult]) -> TestSummary:
        """Создает сводку результатов."""
        successful = [r for r in results if r.status == "SUCCESS"]

        # Рейтинг по скорости
        ranking_by_speed = []
        if successful:
            sorted_by_speed = sorted(
                successful,
                key=lambda x: x.avg_duration or float("inf"),
            )
            for i, r in enumerate(sorted_by_speed, 1):
                ranking_by_speed.append({
                    "rank": i,
                    "model": r.model,
                    "avg_duration": r.avg_duration,
                    "embedding_dim": r.avg_embedding_dim,
                    "tokens_per_second": r.avg_tokens_per_second,
                })

        # Рейтинг по размерности (качество)
        ranking_by_quality = []
        if successful:
            sorted_by_quality = sorted(
                successful,
                key=lambda x: x.avg_embedding_dim or 0,
                reverse=True,
            )
            for i, r in enumerate(sorted_by_quality, 1):
                ranking_by_quality.append({
                    "rank": i,
                    "model": r.model,
                    "avg_duration": r.avg_duration,
                    "embedding_dim": r.avg_embedding_dim,
                    "tokens_per_second": r.avg_tokens_per_second,
                })

        return TestSummary(
            total_models=len(results),
            successful_models=len(successful),
            failed_models=len(results) - len(successful),
            ranking_by_speed=ranking_by_speed,
            ranking_by_quality=ranking_by_quality,
        )

    def save_results(
        self,
        report: TestReport,
        output_dir: str | None = None,
    ) -> dict[str, str]:
        """Сохраняет результаты тестирования."""
        output_dir = Path(output_dir or self.config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"ollama_embedding_test_{timestamp}"

        filenames: dict[str, str] = {}

        # Сохраняем JSON
        json_path = output_dir / f"{base_filename}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report.model_dump(), f, indent=2, ensure_ascii=False)
        filenames["json"] = str(json_path)

        # Сохраняем CSV
        csv_path = output_dir / f"{base_filename}.csv"
        self._save_csv(report, csv_path)
        filenames["csv"] = str(csv_path)

        # Сохраняем текстовый отчет
        txt_path = output_dir / f"{base_filename}_report.txt"
        self._save_text_report(report, txt_path)
        filenames["txt"] = str(txt_path)

        return filenames

    def _save_csv(self, report: TestReport, path: Path) -> None:
        """Сохраняет результаты в CSV."""
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Model",
                "Status",
                "Successful Tests",
                "Avg Duration (s)",
                "Min Duration (s)",
                "Max Duration (s)",
                "Std Dev (s)",
                "Embedding Dim",
                "Tokens/sec",
            ])

            for result in report.results:
                if result.status == "SUCCESS":
                    writer.writerow([
                        result.model,
                        result.status,
                        result.successful_tests,
                        f"{result.avg_duration:.4f}" if result.avg_duration else "",
                        f"{result.min_duration:.4f}" if result.min_duration else "",
                        f"{result.max_duration:.4f}" if result.max_duration else "",
                        f"{result.std_duration:.4f}" if result.std_duration else "",
                        int(result.avg_embedding_dim) if result.avg_embedding_dim else "",
                        f"{result.avg_tokens_per_second:.2f}" if result.avg_tokens_per_second else "",
                    ])
                else:
                    writer.writerow([
                        result.model,
                        result.status,
                        0,
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                    ])

    def _save_text_report(self, report: TestReport, path: Path) -> None:
        """Сохраняет текстовый отчет."""
        with open(path, "w", encoding="utf-8") as f:
            f.write("=" * 80 + "\n")
            f.write("OLLAMA EMBEDDING MODELS PERFORMANCE TEST REPORT\n")
            f.write("=" * 80 + "\n\n")

            f.write(f"Timestamp: {report.timestamp}\n")
            f.write(f"Ollama URL: {report.ollama_url}\n")
            f.write(f"Tests per model: {report.config.tests_per_model}\n")
            f.write(f"Timeout: {report.config.timeout}s\n\n")

            # Сводка
            f.write("-" * 40 + "\n")
            f.write("SUMMARY\n")
            f.write("-" * 40 + "\n")
            f.write(f"Total models: {report.summary.total_models}\n")
            f.write(f"Successful: {report.summary.successful_models}\n")
            f.write(f"Failed: {report.summary.failed_models}\n\n")

            # Рейтинг по скорости
            if report.summary.ranking_by_speed:
                f.write("-" * 40 + "\n")
                f.write("RANKING BY SPEED (fastest first)\n")
                f.write("-" * 40 + "\n")
                f.write(f"{'Rank':<5} {'Model':<35} {'Time (s)':<12} {'Dim':<8} {'Tokens/s':<10}\n")
                f.write("-" * 80 + "\n")

                for entry in report.summary.ranking_by_speed:
                    f.write(
                        f"{entry['rank']:<5} "
                        f"{entry['model']:<35} "
                        f"{entry['avg_duration']:.4f}    "
                        f"{int(entry['embedding_dim']) if entry['embedding_dim'] else 'N/A':<8} "
                        f"{entry['tokens_per_second']:.2f}" if entry['tokens_per_second'] else "N/A"
                        + "\n"
                    )
                f.write("\n")

            # Детальные результаты
            f.write("-" * 40 + "\n")
            f.write("DETAILED RESULTS\n")
            f.write("-" * 40 + "\n\n")

            for result in report.results:
                f.write(f"Model: {result.model}\n")
                f.write(f"Status: {result.status}\n")

                if result.status == "SUCCESS":
                    f.write(f"Successful tests: {result.successful_tests}/{result.total_tests}\n")
                    f.write(f"Avg duration: {result.avg_duration:.4f}s\n")
                    f.write(f"Duration range: {result.min_duration:.4f}s - {result.max_duration:.4f}s\n")
                    f.write(f"Std deviation: {result.std_duration:.4f}s\n")
                    f.write(f"Embedding dim: {int(result.avg_embedding_dim)}\n")
                    f.write(f"Tokens/sec: {result.avg_tokens_per_second:.2f}\n")
                else:
                    f.write(f"Error: {result.error}\n")

                f.write("\n" + "-" * 40 + "\n\n")

    def print_summary(self, report: TestReport) -> None:
        """Выводит краткую сводку в консоль."""
        console = self.console

        # Заголовок
        console.print("\n[bold cyan]Ollama Embedding Models Test Results[/bold cyan]\n")

        # Общая статистика
        table = Table(box=box.SIMPLE)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Total Models", str(report.summary.total_models))
        table.add_row("Successful", str(report.summary.successful_models))
        table.add_row("Failed", str(report.summary.failed_models))

        console.print(table)

        # Рейтинг по скорости
        if report.summary.ranking_by_speed:
            console.print("\n[bold cyan]Top 5 by Speed[/bold cyan]")

            speed_table = Table(box=box.SIMPLE)
            speed_table.add_column("Rank", justify="center", style="yellow")
            speed_table.add_column("Model", style="magenta")
            speed_table.add_column("Time (s)", justify="right", style="green")
            speed_table.add_column("Dim", justify="right", style="blue")
            speed_table.add_column("Tokens/s", justify="right", style="blue")

            for entry in report.summary.ranking_by_speed[:5]:
                speed_table.add_row(
                    str(entry["rank"]),
                    entry["model"],
                    f"{entry['avg_duration']:.4f}" if entry["avg_duration"] else "N/A",
                    str(int(entry["embedding_dim"])) if entry["embedding_dim"] else "N/A",
                    f"{entry['tokens_per_second']:.2f}" if entry["tokens_per_second"] else "N/A",
                )

            console.print(speed_table)


# ============================================================================
# CLI
# ============================================================================


def load_config(config_path: str) -> TestConfig:
    """Загружает конфигурацию из YAML файла."""
    with open(config_path, "r", encoding="utf-8") as f:
        config_data = yaml.safe_load(f)
    return TestConfig(**config_data)


def parse_args() -> argparse.Namespace:
    """Парсит аргументы командной строки."""
    parser = argparse.ArgumentParser(
        description="Professional Ollama Embedding Models Speed Tester",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Запуск с конфигурацией из файла
  python test_ollama_speed_pro.py --config config.yaml

  # Тестирование конкретных моделей
  python test_ollama_speed_pro.py --models qwen3-embedding:0.6b-q8_0 all-minilm:l6-v2

  # Тестирование всех моделей с 10 тестами на модель
  python test_ollama_speed_pro.py --tests-per-model 10

  # Изменение URL Ollama
  python test_ollama_speed_pro.py --url http://ollama:11434
        """,
    )

    parser.add_argument(
        "-c", "--config",
        type=str,
        help="Path to YAML configuration file",
    )

    parser.add_argument(
        "-u", "--url",
        type=str,
        default=DEFAULT_OLLAMA_URL,
        help=f"Ollama API URL (default: {DEFAULT_OLLAMA_URL})",
    )

    parser.add_argument(
        "-m", "--models",
        type=str,
        nargs="+",
        help="Models to test (space-separated)",
    )

    parser.add_argument(
        "-t", "--tests-per-model",
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
        "-o", "--output-dir",
        type=str,
        default=".",
        help="Output directory for results",
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    return parser.parse_args()


def main() -> int:
    """Основная функция."""
    args = parse_args()

    # Настройка уровня логирования
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        # Загружаем конфигурацию
        if args.config:
            config = load_config(args.config)
            # Обновляем из аргументов командной строки
            if args.url != DEFAULT_OLLAMA_URL:
                config.ollama_url = args.url
            if args.tests_per_model != DEFAULT_TESTS_PER_MODEL:
                config.tests_per_model = args.tests_per_model
            if args.output_dir != ".":
                config.output_dir = args.output_dir
        else:
            config = TestConfig(
                ollama_url=args.url,
                tests_per_model=args.tests_per_model,
                timeout=args.timeout,
                models=args.models,
                output_dir=args.output_dir,
            )

        # Создаем тестер и запускаем тесты
        console = Console()
        tester = EmbeddingTester(config=config, console=console)

        with console.status("[bold green]Running embedding tests...", spinner="dots"):
            report = tester.run_tests()

        # Выводим результаты
        tester.print_summary(report)

        # Сохраняем результаты
        filenames = tester.save_results(report)

        console.print("\n[bold green]Results saved:[/bold green]")
        for key, path in filenames.items():
            console.print(f"  • {key.upper()}: {path}")

        console.print(f"\n[bold green]Testing complete! {report.summary.successful_models}/{report.summary.total_models} models tested.[/bold green]")

        return 0

    except OllamaConnectionError as e:
        logger.error(str(e))
        console = Console()
        console.print(f"[bold red]Error: {e}[/bold red]")
        return 1

    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        return 130

    except Exception as e:
        logger.exception("Unexpected error")
        console = Console()
        console.print(f"[bold red]Unexpected error: {e}[/bold red]")
        return 1


if __name__ == "__main__":
    sys.exit(main())