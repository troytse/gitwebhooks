"""
Coverage Runner for git-webhooks-server Test Suite

This module provides a CoverageRunner class for generating code coverage
reports using Python's trace module.
"""

import os
import sys
import trace
import unittest
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Dict, List


class CoverageReport:
    """
    Coverage report data structure.

    Attributes:
        total_lines: Total number of lines in covered files
        covered_lines: Number of covered lines
        coverage_percent: Coverage percentage
        by_file: Dictionary mapping file paths to FileCoverage
    """

    def __init__(self):
        """Initialize empty coverage report."""
        self.total_lines = 0
        self.covered_lines = 0
        self.coverage_percent = 0.0
        self.by_file: Dict[str, FileCoverage] = {}

    def add_file(self, file_path: str, coverage: 'FileCoverage'):
        """
        Add file coverage data.

        Args:
            file_path: Path to source file
            coverage: FileCoverage object
        """
        self.by_file[file_path] = coverage
        self._recalculate()

    def _recalculate(self):
        """Recalculate totals from file coverage data."""
        self.total_lines = sum(f.total_lines for f in self.by_file.values())
        self.covered_lines = sum(f.covered_lines for f in self.by_file.values())

        if self.total_lines > 0:
            self.coverage_percent = (self.covered_lines / self.total_lines) * 100
        else:
            self.coverage_percent = 0.0

    def __str__(self) -> str:
        """Generate string representation of report."""
        lines = [
            "Coverage Report:",
            f"Total Lines: {self.total_lines}",
            f"Covered Lines: {self.covered_lines}",
            f"Coverage: {self.coverage_percent:.1f}%",
            "",
            "By File:"
        ]

        for file_path, coverage in sorted(self.by_file.items()):
            lines.append(f"  {file_path}: {coverage.coverage_percent:.1f}%")

        return "\n".join(lines)


class FileCoverage:
    """
    Coverage data for a single file.

    Attributes:
        file_path: Path to source file
        total_lines: Total lines in file
        covered_lines: Number of covered lines
        missing_lines: List of uncovered line numbers
        coverage_percent: Coverage percentage
    """

    def __init__(self, file_path: str, total_lines: int = 0,
                 covered_lines: int = 0, missing_lines: List[int] = None):
        """
        Initialize file coverage.

        Args:
            file_path: Path to source file
            total_lines: Total lines in file
            covered_lines: Number of covered lines
            missing_lines: List of uncovered line numbers
        """
        self.file_path = file_path
        self.total_lines = total_lines
        self.covered_lines = covered_lines
        self.missing_lines = missing_lines or []

        if total_lines > 0:
            self.coverage_percent = (covered_lines / total_lines) * 100
        else:
            self.coverage_percent = 0.0


class CoverageRunner:
    """
    Code coverage runner using Python's trace module.

    This class runs tests and generates coverage reports for the
    git-webhooks-server codebase.

    Usage:
        runner = CoverageRunner(cover_dir="coverage")
        report = runner.run_tests("tests")
        print(report.generate_report())
        runner.check_threshold(85.0)
    """

    def __init__(self, cover_dir: str = "coverage"):
        """
        Initialize coverage runner.

        Args:
            cover_dir: Directory for coverage output files
        """
        self.cover_dir = Path(cover_dir)
        self.report = CoverageReport()

    def run_tests(self, test_module: str = "tests",
                  verbosity: int = 1) -> CoverageReport:
        """
        Run tests with coverage tracking.

        Args:
            test_module: Test module name or path
            verbosity: Test verbosity level

        Returns:
            CoverageReport: Generated coverage report
        """
        # Create cover directory
        self.cover_dir.mkdir(parents=True, exist_ok=True)

        # Create trace object
        tracer = trace.Trace(
            trace=False,
            count=True,
            coverdir=str(self.cover_dir)
        )

        # Run tests under trace
        tracer.runfunc(self._run_unittest, test_module, verbosity)

        # Generate report from coverage files
        self._parse_coverage_files()

        return self.report

    def _run_unittest(self, test_module: str, verbosity: int):
        """
        Run unittest tests.

        Args:
            test_module: Test module name
            verbosity: Verbosity level
        """
        loader = unittest.TestLoader()
        suite = loader.discover(test_module, pattern="test_*.py")
        runner = unittest.TextTestRunner(verbosity=verbosity)
        result = runner.run(suite)

        # Exit with error code if tests failed
        if not result.wasSuccessful():
            sys.exit(1)

    def _parse_coverage_files(self):
        """Parse coverage files generated by trace module."""
        self.report = CoverageReport()

        # Find all .cover files in cover directory
        for cover_file in self.cover_dir.glob("*.cover"):
            # Extract file path from cover file name
            # The cover file format is: /path/to/module.py.cover
            source_path = cover_file.stem
            self._parse_cover_file(cover_file, source_path)

    def _parse_cover_file(self, cover_file: Path, source_path: str):
        """
        Parse a single coverage file.

        Args:
            cover_file: Path to .cover file
            source_path: Path to source file
        """
        try:
            with open(cover_file, 'r') as f:
                lines = f.readlines()

            # Parse coverage data
            # Format: line_number: hit_count
            total_lines = 0
            covered_lines = 0
            missing_lines = []

            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                parts = line.split(':')
                if len(parts) == 2:
                    try:
                        line_num = int(parts[0].strip())
                        hit_count = int(parts[1].strip())

                        total_lines += 1
                        if hit_count > 0:
                            covered_lines += 1
                        else:
                            missing_lines.append(line_num)
                    except ValueError:
                        pass

            # Only track files that are part of our project
            if self._is_project_file(source_path):
                file_coverage = FileCoverage(
                    file_path=source_path,
                    total_lines=total_lines,
                    covered_lines=covered_lines,
                    missing_lines=missing_lines
                )
                self.report.add_file(source_path, file_coverage)

        except (IOError, OSError):
            pass

    def _is_project_file(self, file_path: str) -> bool:
        """
        Check if file is part of the project.

        Args:
            file_path: Path to check

        Returns:
            bool: True if file is a project source file
        """
        # Skip standard library and test files
        skip_patterns = [
            '/usr/lib',
            '/usr/local/lib',
            'tests/',
            'test_',
            '/Library/Frameworks',
            '/System/Library'
        ]

        file_path_norm = file_path.replace('\\', '/')
        for pattern in skip_patterns:
            if pattern in file_path_norm:
                return False

        return True

    def generate_report(self) -> str:
        """
        Generate text format coverage report.

        Returns:
            str: Report text
        """
        return str(self.report)

    def check_threshold(self, threshold: float = 85.0) -> bool:
        """
        Check if coverage meets threshold.

        Args:
            threshold: Minimum coverage percentage

        Returns:
            bool: True if coverage meets or exceeds threshold
        """
        return self.report.coverage_percent >= threshold

    def print_report(self):
        """Print coverage report to stdout."""
        print(self.generate_report())

    def save_report(self, output_path: str):
        """
        Save coverage report to file.

        Args:
            output_path: Path to output file
        """
        with open(output_path, 'w') as f:
            f.write(self.generate_report())


def run_coverage(test_dir: str = "tests",
                 cover_dir: str = "coverage",
                 threshold: Optional[float] = None) -> int:
    """
    Convenience function to run tests with coverage.

    Args:
        test_dir: Test directory
        cover_dir: Coverage output directory
        threshold: Optional coverage threshold to check

    Returns:
        int: Exit code (0 if coverage meets threshold, 1 otherwise)
    """
    runner = CoverageRunner(cover_dir)
    runner.run_tests(test_dir)
    runner.print_report()

    if threshold is not None:
        if runner.check_threshold(threshold):
            print(f"\nCoverage {runner.report.coverage_percent:.1f}% meets threshold {threshold}%")
            return 0
        else:
            print(f"\nCoverage {runner.report.coverage_percent:.1f}% below threshold {threshold}%")
            return 1

    return 0
