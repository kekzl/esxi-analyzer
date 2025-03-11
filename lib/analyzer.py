#!/usr/bin/env python3
"""
ESXi Issue Analyzer - Issue Analyzer Module
"""
import os
import re
import json
from pathlib import Path
from collections import defaultdict

class Issue:
    """Represents a detected issue in the ESXi environment"""
    
    SEVERITY_LOW = "low"
    SEVERITY_MEDIUM = "medium"
    SEVERITY_HIGH = "high"
    SEVERITY_CRITICAL = "critical"
    
    CATEGORY_STORAGE = "storage"
    CATEGORY_NETWORK = "network"
    CATEGORY_CPU = "cpu"
    CATEGORY_MEMORY = "memory"
    CATEGORY_VM = "vm"
    CATEGORY_CONFIG = "configuration"
    CATEGORY_SECURITY = "security"
    CATEGORY_HARDWARE = "hardware"
    
    def __init__(self, title, description, category, severity, evidence, solution, doc_links=None):
        """
        Initialize an issue
        
        Args:
            title (str): Short title of the issue
            description (str): Detailed description of the issue
            category (str): Category of the issue (storage, network, etc.)
            severity (str): Severity of the issue (low, medium, high, critical)
            evidence (list): List of evidence that led to this conclusion
            solution (str): Suggested solution to resolve the issue
            doc_links (list): List of documentation links for reference
        """
        self.title = title
        self.description = description
        self.category = category
        self.severity = severity
        self.evidence = evidence if evidence else []
        self.solution = solution
        self.doc_links = doc_links if doc_links else []


class IssueAnalyzer:
    """Analyzes logs and system information to detect issues"""
    
    def __init__(self, log_path, verbose=False):
        """
        Initialize the analyzer
        
        Args:
            log_path (str): Path to the directory containing collected logs
            verbose (bool): Whether to print verbose output
        """
        self.log_path = log_path
        self.verbose = verbose
        self.issues = []
        
    def analyze(self):
        """
        Analyze the logs and detect issues
        
        Returns:
            list: List of detected issues
        """
        if self.verbose:
            print("Starting analysis of collected logs and information")
            
        # Analyze system information
        self._analyze_system_info()
        
        # Analyze performance metrics
        self._analyze_performance()
        
        # Analyze hardware status
        self._analyze_hardware()
        
        # Analyze storage
        self._analyze_storage()
        
        # Analyze network configuration
        self._analyze_network()
        
        # Analyze VM states
        self._analyze_vms()
        
        # Analyze logs
        self._analyze_logs()
            
        return self.issues
    
    def _read_file(self, filename):
        """Read a file from the log directory"""
        file_path = os.path.join(self.log_path, filename)
        if os.path.exists(file_path):
            with open(file_path, 'r', errors='ignore') as f:
                return f.read()
        return ""
    
    def _analyze_system_info(self):
        """Analyze system information for issues"""
        # Check ESXi version for end-of-life or outdated versions
        version_data = self._read_file("system_version.txt")
        uptime_data = self._read_file("system_uptime.txt")
        
        # Check for very old ESXi versions
        version_match = re.search(r'VMware ESXi (\d+\.\d+)', version_data)
        if version_match:
            version = version_match.group(1)
            version_num = float(version)
            
            if version_num < 6.5:
                self.issues.append(Issue(
                    "EOL ESXi Version",
                    f"ESXi version {version} has reached end of life and is no longer receiving security updates",
                    Issue.CATEGORY_SECURITY,
                    Issue.SEVERITY_HIGH,
                    [f"Detected ESXi version: {version}"],
                    "Upgrade to a supported ESXi version (7.0 or newer recommended)",
                    ["https://kb.vmware.com/s/article/2145103"]
                ))
            elif version_num < 7.0:
                self.issues.append(Issue(
                    "Outdated ESXi Version",
                    f"ESXi version {version} is outdated and will soon reach end of life",
                    Issue.CATEGORY_SECURITY,
                    Issue.SEVERITY_MEDIUM,
                    [f"Detected ESXi version: {version}"],
                    "Consider upgrading to ESXi 7.0 or newer for the latest features and security updates",
                    ["https://kb.vmware.com/s/article/2145103"]
                ))
        
        # Check for excessive uptime (might indicate neglected patching)
        uptime_match = re.search(r'up\s+(\d+)\s+days', uptime_data)
        if uptime_match:
            days = int(uptime_match.group(1))
            if days > 180:  # 6 months
                self.issues.append(Issue(
                    "Excessive Uptime",
                    f"The ESXi host has been running for {days} days without a reboot",
                    Issue.CATEGORY_SECURITY,
                    Issue.SEVERITY_MEDIUM,
                    [f"System uptime: {days} days"],
                    "Schedule a maintenance window to apply pending updates and reboot the host",
                    ["https://kb.vmware.com/s/article/2032823"]
                ))
    
    def _analyze_performance(self):
        """Analyze performance metrics for issues"""
        cpu_stats = self._read_file("perf_cpu_stats.txt")
        memory_info = self._read_file("perf_memory_info.txt")
        
        # Check for high CPU utilization
        if '%PCPU' in cpu_stats:
            high_cpu_matches = re.findall(r'(\w+)\s+\d+\s+\d+\s+(\d+\.\d+)', cpu_stats)
            high_cpu_processes = [f"{proc}: {usage}% CPU" for proc, usage in high_cpu_matches if float(usage) > 80]
            
            if high_cpu_processes:
                self.issues.append(Issue(
                    "High CPU Utilization",
                    "Some processes are consuming excessive CPU resources",
                    Issue.CATEGORY_CPU,
                    Issue.SEVERITY_MEDIUM,
                    high_cpu_processes,
                    "Investigate high CPU consuming processes and consider optimizing workloads or adding resources",
                    ["https://kb.vmware.com/s/article/2001003"]
                ))
        
        # Check for memory pressure
        mem_free_match = re.search(r'Free\s+Memory:\s+(\d+)\s+MB', memory_info)
        mem_total_match = re.search(r'Total\s+Memory:\s+(\d+)\s+MB', memory_info)
        
        if mem_free_match and mem_total_match:
            free_mem = int(mem_free_match.group(1))
            total_mem = int(mem_total_match.group(1))
            
            if total_mem > 0:
                free_percent = (free_mem / total_mem) * 100
                
                if free_percent < 10:
                    self.issues.append(Issue(
                        "Low Available Memory",
                        f"The ESXi host is running low on available memory ({free_percent:.1f}% free)",
                        Issue.CATEGORY_MEMORY,
                        Issue.SEVERITY_HIGH,
                        [f"Free memory: {free_mem} MB out of {total_mem} MB ({free_percent:.1f}%)"],
                        "Consider adding more memory or reducing VM memory allocations",
                        ["https://kb.vmware.com/s/article/1003501"]
                    ))
    
    def _analyze_hardware(self):
        """Analyze hardware status for issues"""
        hw_status = self._read_file("hw_health_status.txt")
        sensors = self._read_file("hw_sensors.txt")
        
        # Check hardware health status
        if 'HealthState:' in hw_status:
            health_match = re.search(r'HealthState:\s+(\w+)', hw_status)
            if health_match and health_match.group(1).lower() != "green":
                self.issues.append(Issue(
                    "Hardware Health Warning",
                    f"The hardware health status is not optimal: {health_match.group(1)}",
                    Issue.CATEGORY_HARDWARE,
                    Issue.SEVERITY_HIGH,
                    [f"Hardware health state: {health_match.group(1)}"],
                    "Check hardware sensors and logs for specific hardware failures",
                    ["https://kb.vmware.com/s/article/2004161"]
                ))
        
        # Check for sensor warnings
        sensor_issues = []
        for line in sensors.split('\n'):
            if 'red' in line.lower() or 'yellow' in line.lower() or 'warning' in line.lower() or 'critical' in line.lower():
                sensor_issues.append(line.strip())
        
        if sensor_issues:
            self.issues.append(Issue(
                "Sensor Warning",
                "One or more hardware sensors are reporting warnings or critical values",
                Issue.CATEGORY_HARDWARE,
                Issue.SEVERITY_HIGH,
                sensor_issues,
                "Investigate the hardware component mentioned in the sensor warning",
                ["https://kb.vmware.com/s/article/2033588"]
            ))
    
    def _analyze_storage(self):
        """Analyze storage for issues"""
        storage_devices = self._read_file("hw_storage_devices.txt")
        disk_latency = self._read_file("perf_disk_latency.txt")
        datastore_info = self._read_file("vm_datastore_info.txt")
        
        # Check for storage devices with errors
        storage_issues = []
        for line in storage_devices.split('\n'):
            if 'Error' in line or 'Degraded' in line or 'Offline' in line:
                storage_issues.append(line.strip())
        
        if storage_issues:
            self.issues.append(Issue(
                "Storage Device Issues",
                "One or more storage devices are reporting errors or degraded state",
                Issue.CATEGORY_STORAGE,
                Issue.SEVERITY_HIGH,
                storage_issues,
                "Check the storage hardware and consider replacing faulty devices",
                ["https://kb.vmware.com/s/article/1003659"]
            ))
        
        # Check for high latency
        latency_issues = []
        for line in disk_latency.split('\n'):
            # Look for latency values > 20ms which is generally considered high
            latency_match = re.search(r'(\S+)\s+\S+\s+\S+\s+(\d+\.\d+)\s+ms', line)
            if latency_match and float(latency_match.group(2)) > 20.0:
                latency_issues.append(f"Device {latency_match.group(1)}: {latency_match.group(2)}ms latency")
        
        if latency_issues:
            self.issues.append(Issue(
                "High Storage Latency",
                "Some storage devices are experiencing high latency",
                Issue.CATEGORY_STORAGE,
                Issue.SEVERITY_MEDIUM,
                latency_issues,
                "Investigate storage bottlenecks and consider storage optimization or upgrades",
                ["https://kb.vmware.com/s/article/2019131"]
            ))
        
        # Check for datastores running out of space
        space_issues = []
        for line in datastore_info.split('\n'):
            # Look for datastores with less than 10% free space
            space_match = re.search(r'(\S+)\s+\S+\s+(\d+)\s+(\d+)\s+(\d+)%', line)
            if space_match and int(space_match.group(4)) < 10:
                space_issues.append(f"Datastore {space_match.group(1)}: {space_match.group(4)}% free space")
        
        if space_issues:
            self.issues.append(Issue(
                "Low Datastore Space",
                "Some datastores are running low on free space",
                Issue.CATEGORY_STORAGE,
                Issue.SEVERITY_HIGH,
                space_issues,
                "Free up space by removing unnecessary files or snapshots, or add more storage capacity",
                ["https://kb.vmware.com/s/article/1003412"]
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