#!/usr/bin/env python3
"""
ESXi Issue Analyzer - Main entry point
"""

import argparse
import sys
from pathlib import Path

from lib.analyzer import IssueAnalyzer
from lib.collector import LogCollector
from lib.report import ReportGenerator
from lib.web_interface import start_web_server


def main():
    """Main entry point for ESXi Analyzer"""
    parser = argparse.ArgumentParser(
        description="ESXi Issue Analyzer - Diagnose and suggest solutions for ESXi problems"
    )
    parser.add_argument("-H", "--host", required=False, help="ESXi host IP or hostname")
    parser.add_argument("-u", "--username", required=False, help="ESXi host username")
    parser.add_argument("-p", "--password", required=False, help="ESXi host password")
    parser.add_argument(
        "-d", "--directory", required=False, help="Directory containing ESXi logs (if already collected)"
    )
    parser.add_argument("-o", "--output", required=False, default="report.html", help="Output report file")
    parser.add_argument("-w", "--web", action="store_true", help="Start web interface")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")

    args = parser.parse_args()

    if args.web:
        print("Starting web interface on http://localhost:8080")
        start_web_server()
        return

    if not args.directory and not (args.host and args.username and args.password):
        parser.error("Either --directory or (--host, --username, and --password) must be provided")

    # Create the output directory if it doesn't exist
    output_path = Path(args.output)
    if output_path.parent != Path():
        output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        if args.verbose:
            print("ESXi Issue Analyzer - Starting analysis")

        # Step 1: Collect logs (if not already provided)
        if args.directory:
            log_path = args.directory
            if args.verbose:
                print(f"Using logs from directory: {log_path}")
        else:
            if args.verbose:
                print(f"Collecting logs from ESXi host: {args.host}")
            collector = LogCollector(args.host, args.username, args.password, verbose=args.verbose)
            log_path = collector.collect()

        # Step 2: Analyze logs and find issues
        if args.verbose:
            print("Analyzing logs and identifying issues")
        analyzer = IssueAnalyzer(log_path, verbose=args.verbose)
        issues = analyzer.analyze()

        # Step 3: Generate report with suggestions
        if args.verbose:
            print(f"Generating report to {args.output}")
        report_gen = ReportGenerator(issues, args.host if args.host else "unknown")
        report_gen.generate_report(args.output)

        print(f"Analysis complete. Report saved to: {args.output}")

    except Exception as e:
        print(f"Error: {e!s}")
        sys.exit(1)


if __name__ == "__main__":
    main()
