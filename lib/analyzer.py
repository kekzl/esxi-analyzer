#!/usr/bin/env python3
"""
ESXi Issue Analyzer - Issue Analyzer Module

This module analyzes collected logs and system information from ESXi hosts
to detect potential issues and provide recommendations.
"""
import os
import re
import json
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Optional

from .logger import logger
from .config import config


@dataclass
class Issue:
    """
    Represents a detected issue in the ESXi environment.

    Attributes:
        title: Short title of the issue
        description: Detailed description of the issue
        category: Category of the issue (storage, network, etc.)
        severity: Severity level (low, medium, high, critical)
        evidence: List of evidence that led to this conclusion
        solution: Suggested solution to resolve the issue
        doc_links: List of documentation/KB article links for reference
    """

    # Severity levels
    SEVERITY_LOW = "low"
    SEVERITY_MEDIUM = "medium"
    SEVERITY_HIGH = "high"
    SEVERITY_CRITICAL = "critical"

    # Issue categories
    CATEGORY_STORAGE = "storage"
    CATEGORY_NETWORK = "network"
    CATEGORY_CPU = "cpu"
    CATEGORY_MEMORY = "memory"
    CATEGORY_VM = "vm"
    CATEGORY_CONFIG = "configuration"
    CATEGORY_SECURITY = "security"
    CATEGORY_HARDWARE = "hardware"

    title: str
    description: str
    category: str
    severity: str
    evidence: List[str] = field(default_factory=list)
    solution: str = ""
    doc_links: List[str] = field(default_factory=list)


class IssueAnalyzer:
    """
    Analyzes logs and system information to detect ESXi issues.

    Uses configurable thresholds and pattern matching to identify
    potential problems in storage, networking, performance, and more.
    """

    def __init__(self, log_path: str, verbose: bool = False):
        """
        Initialize the issue analyzer.

        Args:
            log_path: Path to directory containing collected logs
            verbose: Enable verbose logging output
        """
        self.log_path = log_path
        self.verbose = verbose
        self.issues: List[Issue] = []

    def analyze(self) -> List[Issue]:
        """
        Analyze all collected logs and detect issues.

        Returns:
            List of detected issues

        Raises:
            Exception: If analysis encounters critical errors
        """
        logger.info("Starting analysis of collected logs and information")

        try:
            # Analyze system information
            logger.info("Analyzing system information...")
            self._analyze_system_info()

            # Analyze performance metrics
            logger.info("Analyzing performance metrics...")
            self._analyze_performance()

            # Analyze hardware status
            logger.info("Analyzing hardware status...")
            self._analyze_hardware()

            # Analyze storage
            logger.info("Analyzing storage...")
            self._analyze_storage()

            # Analyze network configuration
            logger.info("Analyzing network configuration...")
            self._analyze_network()

            # Analyze VM states
            logger.info("Analyzing VM states...")
            self._analyze_vms()

            # Analyze logs
            logger.info("Analyzing log files...")
            self._analyze_logs()

            logger.info(f"Analysis complete. Found {len(self.issues)} issues")
            return self.issues

        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            raise

    def _read_file(self, filename: str) -> str:
        """
        Read a file from the log directory.

        Args:
            filename: Name of file to read (relative to log_path)

        Returns:
            File contents as string, or empty string if file doesn't exist
        """
        file_path = os.path.join(self.log_path, filename)
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', errors='ignore') as f:
                    return f.read()
            except Exception as e:
                logger.warning(f"Failed to read file {filename}: {e}")
                return ""
        else:
            logger.debug(f"File not found: {filename}")
            return ""
    
    def _analyze_system_info(self) -> None:
        """Analyze system information for version and uptime issues."""
        version_data = self._read_file("system_version.txt")
        uptime_data = self._read_file("system_uptime.txt")

        # Check for very old ESXi versions
        version_match = re.search(r'VMware ESXi (\d+\.\d+)', version_data)
        if version_match:
            version = version_match.group(1)
            try:
                version_num = float(version)

                if version_num < 6.5:
                    self.issues.append(Issue(
                        title="EOL ESXi Version",
                        description=f"ESXi version {version} has reached end of life and is no longer receiving security updates",
                        category=Issue.CATEGORY_SECURITY,
                        severity=Issue.SEVERITY_HIGH,
                        evidence=[f"Detected ESXi version: {version}"],
                        solution="Upgrade to a supported ESXi version (7.0 or newer recommended)",
                        doc_links=["https://kb.vmware.com/s/article/2145103"]
                    ))
                elif version_num < 7.0:
                    self.issues.append(Issue(
                        title="Outdated ESXi Version",
                        description=f"ESXi version {version} is outdated and will soon reach end of life",
                        category=Issue.CATEGORY_SECURITY,
                        severity=Issue.SEVERITY_MEDIUM,
                        evidence=[f"Detected ESXi version: {version}"],
                        solution="Consider upgrading to ESXi 7.0 or newer for the latest features and security updates",
                        doc_links=["https://kb.vmware.com/s/article/2145103"]
                    ))
            except ValueError:
                logger.warning(f"Could not parse ESXi version: {version}")

        # Check for excessive uptime (might indicate neglected patching)
        max_uptime_days = config.get_threshold('max_uptime_days') or 180
        uptime_match = re.search(r'up\s+(\d+)\s+days', uptime_data)
        if uptime_match:
            days = int(uptime_match.group(1))
            if days > max_uptime_days:
                self.issues.append(Issue(
                    title="Excessive Uptime",
                    description=f"The ESXi host has been running for {days} days without a reboot",
                    category=Issue.CATEGORY_SECURITY,
                    severity=Issue.SEVERITY_MEDIUM,
                    evidence=[f"System uptime: {days} days"],
                    solution="Schedule a maintenance window to apply pending updates and reboot the host",
                    doc_links=["https://kb.vmware.com/s/article/2032823"]
                ))
    
    def _analyze_performance(self) -> None:
        """Analyze performance metrics for CPU and memory issues."""
        cpu_stats = self._read_file("perf_cpu_stats.txt")
        memory_info = self._read_file("perf_memory_info.txt")

        # Get thresholds from config
        high_cpu_threshold = config.get_threshold('high_cpu_percent') or 80
        high_memory_threshold = config.get_threshold('high_memory_percent') or 90

        # Check for high CPU utilization
        if '%PCPU' in cpu_stats:
            high_cpu_matches = re.findall(r'(\w+)\s+\d+\s+\d+\s+(\d+\.\d+)', cpu_stats)
            high_cpu_processes = [
                f"{proc}: {usage}% CPU"
                for proc, usage in high_cpu_matches
                if float(usage) > high_cpu_threshold
            ]

            if high_cpu_processes:
                kb_article = config.get_kb_article('high_cpu') or "https://kb.vmware.com/s/article/2001003"
                self.issues.append(Issue(
                    title="High CPU Utilization",
                    description=f"Some processes are consuming excessive CPU resources (>{high_cpu_threshold}%)",
                    category=Issue.CATEGORY_CPU,
                    severity=Issue.SEVERITY_MEDIUM,
                    evidence=high_cpu_processes,
                    solution="Investigate high CPU consuming processes and consider optimizing workloads or adding resources",
                    doc_links=[kb_article]
                ))

        # Check for memory pressure
        mem_free_match = re.search(r'Free\s+Memory:\s+(\d+)\s+MB', memory_info)
        mem_total_match = re.search(r'Total\s+Memory:\s+(\d+)\s+MB', memory_info)

        if mem_free_match and mem_total_match:
            free_mem = int(mem_free_match.group(1))
            total_mem = int(mem_total_match.group(1))

            if total_mem > 0:
                free_percent = (free_mem / total_mem) * 100
                used_percent = 100 - free_percent

                if used_percent > high_memory_threshold:
                    self.issues.append(Issue(
                        title="Low Available Memory",
                        description=f"The ESXi host is running low on available memory ({free_percent:.1f}% free)",
                        category=Issue.CATEGORY_MEMORY,
                        severity=Issue.SEVERITY_HIGH,
                        evidence=[f"Free memory: {free_mem} MB out of {total_mem} MB ({free_percent:.1f}%)"],
                        solution="Consider adding more memory or reducing VM memory allocations",
                        doc_links=["https://kb.vmware.com/s/article/1003501"]
                    ))
    
    def _analyze_hardware(self) -> None:
        """Analyze hardware status for health and sensor issues."""
        hw_status = self._read_file("hw_health_status.txt")
        sensors = self._read_file("hw_sensors.txt")

        # Check hardware health status
        if 'HealthState:' in hw_status:
            health_match = re.search(r'HealthState:\s+(\w+)', hw_status)
            if health_match and health_match.group(1).lower() != "green":
                self.issues.append(Issue(
                    title="Hardware Health Warning",
                    description=f"The hardware health status is not optimal: {health_match.group(1)}",
                    category=Issue.CATEGORY_HARDWARE,
                    severity=Issue.SEVERITY_HIGH,
                    evidence=[f"Hardware health state: {health_match.group(1)}"],
                    solution="Check hardware sensors and logs for specific hardware failures",
                    doc_links=["https://kb.vmware.com/s/article/2004161"]
                ))

        # Check for sensor warnings
        sensor_issues = []
        for line in sensors.split('\n'):
            if any(keyword in line.lower() for keyword in ['red', 'yellow', 'warning', 'critical']):
                sensor_issues.append(line.strip())

        if sensor_issues:
            self.issues.append(Issue(
                title="Sensor Warning",
                description="One or more hardware sensors are reporting warnings or critical values",
                category=Issue.CATEGORY_HARDWARE,
                severity=Issue.SEVERITY_HIGH,
                evidence=sensor_issues,
                solution="Investigate the hardware component mentioned in the sensor warning",
                doc_links=["https://kb.vmware.com/s/article/2033588"]
            ))

    def _analyze_storage(self) -> None:
        """Analyze storage for device errors, latency, and space issues."""
        storage_devices = self._read_file("hw_storage_devices.txt")
        disk_latency = self._read_file("perf_disk_latency.txt")
        datastore_info = self._read_file("vm_datastore_info.txt")

        # Get thresholds from config
        high_latency_ms = config.get_threshold('high_latency_ms') or 20.0
        low_space_percent = config.get_threshold('low_datastore_space_percent') or 10

        # Check for storage devices with errors
        storage_issues = []
        for line in storage_devices.split('\n'):
            if any(keyword in line for keyword in ['Error', 'Degraded', 'Offline']):
                storage_issues.append(line.strip())

        if storage_issues:
            kb_article = config.get_kb_article('storage_latency') or "https://kb.vmware.com/s/article/1003659"
            self.issues.append(Issue(
                title="Storage Device Issues",
                description="One or more storage devices are reporting errors or degraded state",
                category=Issue.CATEGORY_STORAGE,
                severity=Issue.SEVERITY_HIGH,
                evidence=storage_issues,
                solution="Check the storage hardware and consider replacing faulty devices",
                doc_links=[kb_article]
            ))

        # Check for high latency
        latency_issues = []
        for line in disk_latency.split('\n'):
            latency_match = re.search(r'(\S+)\s+\S+\s+\S+\s+(\d+\.\d+)\s+ms', line)
            if latency_match and float(latency_match.group(2)) > high_latency_ms:
                latency_issues.append(f"Device {latency_match.group(1)}: {latency_match.group(2)}ms latency")

        if latency_issues:
            kb_article = config.get_kb_article('storage_latency') or "https://kb.vmware.com/s/article/2019131"
            self.issues.append(Issue(
                title="High Storage Latency",
                description=f"Some storage devices are experiencing high latency (>{high_latency_ms}ms)",
                category=Issue.CATEGORY_STORAGE,
                severity=Issue.SEVERITY_MEDIUM,
                evidence=latency_issues,
                solution="Investigate storage bottlenecks and consider storage optimization or upgrades",
                doc_links=[kb_article]
            ))

        # Check for datastores running out of space
        space_issues = []
        for line in datastore_info.split('\n'):
            space_match = re.search(r'(\S+)\s+\S+\s+(\d+)\s+(\d+)\s+(\d+)%', line)
            if space_match and int(space_match.group(4)) < low_space_percent:
                space_issues.append(f"Datastore {space_match.group(1)}: {space_match.group(4)}% free space")

        if space_issues:
            self.issues.append(Issue(
                title="Low Datastore Space",
                description=f"Some datastores are running low on free space (<{low_space_percent}%)",
                category=Issue.CATEGORY_STORAGE,
                severity=Issue.SEVERITY_HIGH,
                evidence=space_issues,
                solution="Free up space by removing unnecessary files or snapshots, or add more storage capacity",
                doc_links=["https://kb.vmware.com/s/article/1003412"]
            ))
    
    def _analyze_network(self):
        """Analyze network configuration for issues"""
        interfaces = self._read_file("net_interfaces.txt")
        vswitches = self._read_file("net_vswitches.txt")
        vmkernel = self._read_file("net_vmkernel.txt")
        
        # Check for network interfaces with issues
        interface_issues = []
        for line in interfaces.split('\n'):
            if 'Down' in line:
                interface_issues.append(line.strip())
        
        if interface_issues:
            self.issues.append(Issue(
                "Network Interface Down",
                "One or more network interfaces are down",
                Issue.CATEGORY_NETWORK,
                Issue.SEVERITY_HIGH,
                interface_issues,
                "Check network cables, switch ports, and network configuration",
                ["https://kb.vmware.com/s/article/2008144"]
            ))
        
        # Check for vSwitches with single uplinks (no redundancy)
        vswitch_issues = []
        current_vswitch = None
        uplinks_count = 0
        
        for line in vswitches.split('\n'):
            vswitch_match = re.search(r'vSwitch Name:\s+(\S+)', line)
            if vswitch_match:
                if current_vswitch and uplinks_count < 2:
                    vswitch_issues.append(f"vSwitch {current_vswitch}: Only {uplinks_count} uplink(s)")
                current_vswitch = vswitch_match.group(1)
                uplinks_count = 0
            
            if 'Uplinks:' in line:
                uplinks = line.split(':', 1)[1].strip()
                uplinks_count = len([u for u in uplinks.split(',') if u.strip()])
        
        # Check the last vSwitch
        if current_vswitch and uplinks_count < 2:
            vswitch_issues.append(f"vSwitch {current_vswitch}: Only {uplinks_count} uplink(s)")
            
        if vswitch_issues:
            self.issues.append(Issue(
                "Inadequate Network Redundancy",
                "Some vSwitches have insufficient uplink redundancy",
                Issue.CATEGORY_NETWORK,
                Issue.SEVERITY_MEDIUM,
                vswitch_issues,
                "Configure additional uplinks for affected vSwitches to provide redundancy",
                ["https://kb.vmware.com/s/article/1003806"]
            ))
    
    def _analyze_vms(self):
        """Analyze VM states for issues"""
        vm_list = self._read_file("vm_list.txt")
        vm_stats = self._read_file("vm_stats.txt")
        
        # Check for VMs in invalid states
        vm_state_issues = []
        for line in vm_list.split('\n'):
            if any(state in line for state in ['Invalid', 'Stuck', 'Suspended']):
                vm_state_issues.append(line.strip())
        
        if vm_state_issues:
            self.issues.append(Issue(
                "VMs in Problematic State",
                "Some virtual machines are in an invalid or problematic state",
                Issue.CATEGORY_VM,
                Issue.SEVERITY_MEDIUM,
                vm_state_issues,
                "Power cycle the affected VMs or migrate them to another host",
                ["https://kb.vmware.com/s/article/1004340"]
            ))
            
        # Check for excessive VM snapshots
        snapshot_issues = []
        for line in vm_list.split('\n'):
            snapshot_match = re.search(r'(\S+)\s+\S+\s+\S+\s+(\d+)\s+snapshot', line)
            if snapshot_match and int(snapshot_match.group(2)) > 3:
                snapshot_issues.append(f"VM {snapshot_match.group(1)}: {snapshot_match.group(2)} snapshots")
        
        if snapshot_issues:
            self.issues.append(Issue(
                "Excessive VM Snapshots",
                "Some VMs have an excessive number of snapshots which can impact performance and storage",
                Issue.CATEGORY_VM,
                Issue.SEVERITY_MEDIUM,
                snapshot_issues,
                "Consolidate or remove unnecessary snapshots",
                ["https://kb.vmware.com/s/article/1025279"]
            ))
    
    def _analyze_logs(self):
        """Analyze log files for issues"""
        log_dir = os.path.join(self.log_path, "logs")
        if not os.path.exists(log_dir):
            return
            
        # Common error patterns to look for in logs
        error_patterns = {
            r'SCSI\s+sense.*?Medium error': {
                "title": "Storage Medium Errors",
                "description": "Storage devices are reporting medium errors which may indicate failing hardware",
                "category": Issue.CATEGORY_STORAGE,
                "severity": Issue.SEVERITY_HIGH,
                "solution": "Run hardware diagnostics on the storage and consider replacing failing drives",
                "doc_links": ["https://kb.vmware.com/s/article/1008493"]
            },
            r'NMP: nmp_ThrottleLogForDevice.*?device is blocked': {
                "title": "Storage Device Throttling",
                "description": "One or more storage devices are being throttled due to errors or performance issues",
                "category": Issue.CATEGORY_STORAGE,
                "severity": Issue.SEVERITY_HIGH,
                "solution": "Check storage array health and connectivity",
                "doc_links": ["https://kb.vmware.com/s/article/2036778"]
            },
            r'out\s+of\s+memory': {
                "title": "Out of Memory Condition",
                "description": "The ESXi host is experiencing memory pressure and may be running out of available memory",
                "category": Issue.CATEGORY_MEMORY,
                "severity": Issue.SEVERITY_CRITICAL,
                "solution": "Add more physical memory or reduce memory consumption by VMs",
                "doc_links": ["https://kb.vmware.com/s/article/2005631"]
            },
            r'CPU\s+usage.*?above.*?threshold': {
                "title": "High CPU Utilization",
                "description": "The ESXi host is experiencing high CPU utilization above configured thresholds",
                "category": Issue.CATEGORY_CPU,
                "severity": Issue.SEVERITY_MEDIUM,
                "solution": "Identify resource-intensive VMs and consider load balancing or adding CPU resources",
                "doc_links": ["https://kb.vmware.com/s/article/2001003"]
            },
            r'watchdog\s+timeout': {
                "title": "Watchdog Timeout",
                "description": "System watchdog timeout events detected which may indicate system instability",
                "category": Issue.CATEGORY_HARDWARE,
                "severity": Issue.SEVERITY_HIGH,
                "solution": "Check for hardware issues and consider updating ESXi and firmware",
                "doc_links": ["https://kb.vmware.com/s/article/2042355"]
            },
            r'Purple\s+Screen': {
                "title": "PSoD (Purple Screen of Death)",
                "description": "The ESXi host has experienced one or more system crashes",
                "category": Issue.CATEGORY_HARDWARE,
                "severity": Issue.SEVERITY_CRITICAL,
                "solution": "Collect diagnostic information and contact VMware support",
                "doc_links": ["https://kb.vmware.com/s/article/1004250"]
            }
        }
        
        # Check each log file for error patterns
        for log_file in os.listdir(log_dir):
            log_path = os.path.join(log_dir, log_file)
            
            try:
                with open(log_path, 'r', errors='ignore') as f:
                    log_content = f.read()
                    
                    for pattern, issue_info in error_patterns.items():
                        matches = re.findall(pattern, log_content, re.IGNORECASE)
                        if matches:
                            evidence = [f"{log_file}: {len(matches)} occurrences of pattern '{pattern}'"]
                            
                            # Add a sample of actual matches (limit to 3)
                            for match_idx, match_text in enumerate(re.finditer(pattern, log_content, re.IGNORECASE)):
                                if match_idx >= 3:
                                    break
                                    
                                # Get a snippet of text around the match
                                start = max(0, match_text.start() - 50)
                                end = min(len(log_content), match_text.end() + 50)
                                snippet = log_content[start:end].replace('\n', ' ').strip()
                                evidence.append(f"Sample: ...{snippet}...")
                            
                            self.issues.append(Issue(
                                issue_info["title"],
                                issue_info["description"],
                                issue_info["category"],
                                issue_info["severity"],
                                evidence,
                                issue_info["solution"],
                                issue_info["doc_links"]
                            ))
            
            except Exception as e:
                if self.verbose:
                    print(f"Error analyzing log file {log_file}: {str(e)}")