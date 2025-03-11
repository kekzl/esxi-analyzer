#!/usr/bin/env python3
"""
ESXi Issue Analyzer - Log Collector Module
"""
import os
import tempfile
import shutil
import socket
import paramiko
import time
from pathlib import Path

class LogCollector:
    """Collects logs and system information from ESXi hosts"""
    
    def __init__(self, host, username, password, verbose=False):
        """
        Initialize the collector
        
        Args:
            host (str): ESXi host IP or hostname
            username (str): ESXi host username
            password (str): ESXi host password
            verbose (bool): Whether to print verbose output
        """
        self.host = host
        self.username = username
        self.password = password
        self.verbose = verbose
        self.collection_dir = None
        
    def collect(self):
        """
        Collect logs and system information from the ESXi host
        
        Returns:
            str: Path to the directory containing collected logs
        """
        # Create a temporary directory for log collection
        self.collection_dir = tempfile.mkdtemp(prefix="esxi_analyzer_")
        
        if self.verbose:
            print(f"Collecting logs to {self.collection_dir}")
        
        try:
            # Connect to ESXi host via SSH
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(self.host, username=self.username, password=self.password)
            
            # Collect core system information
            self._collect_system_info(ssh)
            
            # Collect performance metrics
            self._collect_performance_metrics(ssh)
            
            # Collect hardware status
            self._collect_hardware_status(ssh)
            
            # Collect VM states
            self._collect_vm_states(ssh)
            
            # Collect network configuration
            self._collect_network_config(ssh)
            
            # Collect essential logs
            self._collect_logs(ssh)
            
            ssh.close()
            
            return self.collection_dir
            
        except Exception as e:
            shutil.rmtree(self.collection_dir, ignore_errors=True)
            raise Exception(f"Failed to collect logs: {str(e)}")
    
    def _run_command(self, ssh, command, output_file):
        """Run a command and save output to a file"""
        if self.verbose:
            print(f"Running command: {command}")
            
        stdin, stdout, stderr = ssh.exec_command(command)
        with open(os.path.join(self.collection_dir, output_file), 'w') as f:
            f.write(stdout.read().decode('utf-8'))
    
    def _collect_system_info(self, ssh):
        """Collect basic system information"""
        commands = {
            "version": "vmware -v",
            "system_info": "esxcli system version get",
            "uptime": "uptime",
            "hostname": "hostname",
            "time_info": "esxcli system time get",
            "boot_device": "esxcli system boot device get",
            "licenses": "esxcli software license list"
        }
        
        for name, cmd in commands.items():
            self._run_command(ssh, cmd, f"system_{name}.txt")
    
    def _collect_performance_metrics(self, ssh):
        """Collect performance metrics"""
        commands = {
            "cpu_info": "esxcli hardware cpu list",
            "cpu_stats": "esxtop -b -n 1 -d 5 -c",
            "memory_info": "esxcli hardware memory get",
            "system_stats": "esxcli system stats system get",
            "disk_latency": "esxcli storage core device stats get",
            "io_stats": "esxtop -b -n 1 -d 5 -d"
        }
        
        for name, cmd in commands.items():
            self._run_command(ssh, cmd, f"perf_{name}.txt")
    
    def _collect_hardware_status(self, ssh):
        """Collect hardware status information"""
        commands = {
            "storage_devices": "esxcli storage core device list",
            "hba_info": "esxcli storage core adapter list",
            "health_status": "esxcli hardware platform get",
            "sensors": "esxcli hardware sensor list",
            "pci_devices": "lspci"
        }
        
        for name, cmd in commands.items():
            self._run_command(ssh, cmd, f"hw_{name}.txt")
    
    def _collect_vm_states(self, ssh):
        """Collect VM state information"""
        commands = {
            "vm_list": "esxcli vm process list",
            "vm_stats": "esxtop -b -n 1 -d 5 -v",
            "datastore_info": "esxcli storage filesystem list"
        }
        
        for name, cmd in commands.items():
            self._run_command(ssh, cmd, f"vm_{name}.txt")
    
    def _collect_network_config(self, ssh):
        """Collect network configuration"""
        commands = {
            "interfaces": "esxcli network ip interface list",
            "vswitches": "esxcli network vswitch standard list",
            "portgroups": "esxcli network vswitch standard portgroup list",
            "vmkernel": "esxcli network ip interface ipv4 get",
            "neighbors": "esxcli network ip neighbor list",
            "dns_info": "esxcli network ip dns server list",
            "firewall_status": "esxcli network firewall get"
        }
        
        for name, cmd in commands.items():
            self._run_command(ssh, cmd, f"net_{name}.txt")
    
    def _collect_logs(self, ssh):
        """Collect important log files"""
        # Create logs directory
        logs_dir = os.path.join(self.collection_dir, "logs")
        os.makedirs(logs_dir, exist_ok=True)
        
        # List of important logs to collect
        log_files = [
            "/var/log/vmkernel.log",
            "/var/log/hostd.log",
            "/var/log/auth.log",
            "/var/log/syslog.log",
            "/var/log/vpxa.log",
            "/var/log/fdm.log",
            "/var/log/esxi_install.log"
        ]
        
        # Use SCP to copy logs
        for log_file in log_files:
            try:
                if self.verbose:
                    print(f"Collecting log: {log_file}")
                    
                transport = ssh.get_transport()
                scp = paramiko.SFTPClient.from_transport(transport)
                
                # Get the filename part
                filename = os.path.basename(log_file)
                local_path = os.path.join(logs_dir, filename)
                
                # Download the file
                scp.get(log_file, local_path)
                
            except Exception as e:
                # Continue if a log file doesn't exist
                if self.verbose:
                    print(f"Could not collect {log_file}: {str(e)}")