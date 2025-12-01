"""
ESXi Analyzer Library

This package provides modules for analyzing VMware ESXi hosts:
- collector: SSH-based log and data collection
- analyzer: Issue detection and analysis
- report: HTML report generation
- web_interface: Web-based user interface
"""

__version__ = "1.2.0"
__author__ = "ESXi Analyzer Contributors"

from . import analyzer, collector, report, web_interface

__all__ = ["analyzer", "collector", "report", "web_interface"]
