"""
ESXi Analyzer Library

This package provides modules for analyzing VMware ESXi hosts:
- collector: SSH-based log and data collection
- analyzer: Issue detection and analysis
- report: HTML report generation
- web_interface: Web-based user interface
"""

__version__ = "1.0.0"
__author__ = "ESXi Analyzer Contributors"

from . import collector
from . import analyzer
from . import report
from . import web_interface

__all__ = ['collector', 'analyzer', 'report', 'web_interface']
