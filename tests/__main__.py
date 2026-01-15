#!/usr/bin/env python3
"""
Test Suite Entry Point for gitwebhooks

This module provides the main entry point for running the test suite.
It supports test discovery, execution, and reporting.

Usage:
    python -m tests                    # Run all tests
    python -m tests --verbose          # Run with verbose output
    python -m tests.unit               # Run only unit tests
    python -m tests.integration        # Run only integration tests
"""

import sys
import unittest
import argparse
from pathlib import Path


def main(argv=None) -> int:
    """
    Run the test suite and return exit code.

    Args:
        argv: Command line arguments (defaults to sys.argv[1:])

    Returns:
        int: 0 if all tests pass, 1 otherwise
    """
    parser = argparse.ArgumentParser(
        description="Run gitwebhooks test suite"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Minimal output"
    )
    parser.add_argument(
        "-f", "--failfast",
        action="store_true",
        help="Stop on first failure"
    )
    parser.add_argument(
        "-c", "--catch",
        action="store_true",
        help="Catch Ctrl-C and display results"
    )
    parser.add_argument(
        "pattern",
        nargs="?",
        default="test_*.py",
        help="Test file pattern (default: test_*.py)"
    )
    parser.add_argument(
        "start_dir",
        nargs="?",
        default=Path(__file__).parent,
        help="Directory to start discovery (default: tests/)"
    )

    args = parser.parse_args(argv)

    # Configure verbosity
    verbosity = 2 if args.verbose else (0 if args.quiet else 1)

    # Discover tests
    loader = unittest.TestLoader()
    start_dir = Path(args.start_dir)

    if start_dir.name in ("unit", "integration"):
        # Running specific test subdirectory
        suite = loader.discover(str(start_dir), pattern=args.pattern)
    else:
        # Running all tests
        suite = loader.discover(str(start_dir), pattern=args.pattern)

    # Run tests
    runner = unittest.TextTestRunner(
        verbosity=verbosity,
        failfast=args.failfast
    )

    result = runner.run(suite)

    # Return exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
