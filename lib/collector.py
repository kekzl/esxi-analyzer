#!/usr/bin/env python3
"""
ESXi Issue Analyzer - Log Collector Module

This module handles SSH connection to ESXi hosts and collects logs,
system information, and performance metrics for analysis.
"""
import os
import tempfile
import shutil
import socket
import paramiko
import time
from pathlib import Path
from typing import Optional, Dict, List
from contextlib import contextmanager

from .logger import logger
from .config import config


class LogCollector:
    """
    Collects logs and system information from ESXi hosts via SSH.

    Supports both password and SSH key authentication with configurable
    retry logic and timeout handling.
    """

    def __init__(
        self,
        host: str,
        username: str,
        password: Optional[str] = None,
        key_file: Optional[str] = None,
        verbose: bool = False
    ):
        """
        Initialize the log collector.

        Args:
            host: ESXi host IP address or hostname
            username: ESXi host username
            password: ESXi host password (required if key_file not provided)
            key_file: Path to SSH private key file (optional)
            verbose: Enable verbose logging output

        Raises:
            ValueError: If neither password nor key_file is provided
        """
        self.host = host
        self.username = username
        self.password = password
        self.key_file = key_file or config.get_ssh('key_file')
        self.verbose = verbose
        self.collection_dir: Optional[str] = None

        # SSH configuration from config
        self.timeout = config.get_ssh('timeout') or 30
        self.command_timeout = config.get_ssh('command_timeout') or 60
        self.retry_attempts = config.get_ssh('retry_attempts') or 3
        self.retry_delay = config.get_ssh('retry_delay') or 2
        self.verify_host_keys = config.get_ssh('verify_host_keys')
        self.known_hosts_file = config.get_ssh('known_hosts_file')
        self.use_key_auth = config.get_ssh('use_key_auth') or (key_file is not None)

        # Validate credentials
        if not self.use_key_auth and not password:
            raise ValueError("Either password or key_file must be provided")

        if self.use_key_auth and not self.key_file:
            raise ValueError("key_file must be provided when use_key_auth is enabled")
        
    @contextmanager
    def _ssh_connection(self):
        """
        Context manager for SSH connections with retry logic.

        Yields:
            paramiko.SSHClient: Connected SSH client

        Raises:
            ConnectionError: If connection fails after all retry attempts
        """
        ssh = paramiko.SSHClient()

        # Configure host key verification
        if self.verify_host_keys:
            try:
                known_hosts = os.path.expanduser(self.known_hosts_file)
                if os.path.exists(known_hosts):
                    ssh.load_host_keys(known_hosts)
                    ssh.set_missing_host_key_policy(paramiko.RejectPolicy())
                    logger.info(f"Loaded known hosts from {known_hosts}")
                else:
                    logger.warning(f"Known hosts file not found: {known_hosts}")
                    ssh.set_missing_host_key_policy(paramiko.WarningPolicy())
            except Exception as e:
                logger.warning(f"Error loading known hosts: {e}")
                ssh.set_missing_host_key_policy(paramiko.WarningPolicy())
        else:
            logger.warning("Host key verification disabled - potential security risk")
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Attempt connection with retry logic
        last_error = None
        for attempt in range(self.retry_attempts):
            try:
                logger.info(f"Connecting to {self.host} (attempt {attempt + 1}/{self.retry_attempts})")

                # Authentication
                if self.use_key_auth:
                    key_path = os.path.expanduser(self.key_file)
                    ssh.connect(
                        self.host,
                        username=self.username,
                        key_filename=key_path,
                        timeout=self.timeout,
                        banner_timeout=self.timeout
                    )
                    logger.info(f"Connected to {self.host} using SSH key authentication")
                else:
                    ssh.connect(
                        self.host,
                        username=self.username,
                        password=self.password,
                        timeout=self.timeout,
                        banner_timeout=self.timeout
                    )
                    logger.info(f"Connected to {self.host} using password authentication")

                yield ssh
                ssh.close()
                logger.info(f"Disconnected from {self.host}")
                return

            except (socket.timeout, socket.error) as e:
                last_error = e
                logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
                if attempt < self.retry_attempts - 1:
                    delay = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
            except paramiko.AuthenticationException as e:
                last_error = e
                logger.error(f"Authentication failed: {e}")
                ssh.close()
                raise ConnectionError(f"Authentication failed for {self.username}@{self.host}")
            except Exception as e:
                last_error = e
                logger.error(f"SSH connection error: {e}")
                ssh.close()
                if attempt < self.retry_attempts - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)

        # All attempts failed
        ssh.close()
        raise ConnectionError(
            f"Failed to connect to {self.host} after {self.retry_attempts} attempts: {last_error}"
        )

    def collect(self) -> str:
        """
        Collect logs and system information from the ESXi host.

        Returns:
            Path to the directory containing collected logs

        Raises:
            ConnectionError: If SSH connection fails
            Exception: If log collection fails
        """
        # Create a temporary directory for log collection
        self.collection_dir = tempfile.mkdtemp(prefix="esxi_analyzer_")
        logger.info(f"Created collection directory: {self.collection_dir}")

        try:
            with self._ssh_connection() as ssh:
                # Collect core system information
                logger.info("Collecting system information...")
                self._collect_system_info(ssh)

                # Collect performance metrics
                logger.info("Collecting performance metrics...")
                self._collect_performance_metrics(ssh)

                # Collect hardware status
                logger.info("Collecting hardware status...")
                self._collect_hardware_status(ssh)

                # Collect VM states
                logger.info("Collecting VM states...")
                self._collect_vm_states(ssh)

                # Collect network configuration
                logger.info("Collecting network configuration...")
                self._collect_network_config(ssh)

                # Collect essential logs
                logger.info("Collecting log files...")
                self._collect_logs(ssh)

            logger.info(f"Log collection completed successfully")
            return self.collection_dir

        except Exception as e:
            logger.error(f"Log collection failed: {e}")
            if self.collection_dir and os.path.exists(self.collection_dir):
                shutil.rmtree(self.collection_dir, ignore_errors=True)
                logger.info(f"Cleaned up collection directory")
            raise Exception(f"Failed to collect logs from {self.host}: {str(e)}")
    
    def _run_command(
        self,
        ssh: paramiko.SSHClient,
        command: str,
        output_file: str
    ) -> None:
        """
        Execute a command via SSH and save output to a file.

        Args:
            ssh: Connected SSH client
            command: Command to execute on remote host
            output_file: Filename to save output (relative to collection_dir)

        Raises:
            Exception: If command execution fails
        """
        logger.debug(f"Executing command: {command}")

        try:
            stdin, stdout, stderr = ssh.exec_command(command, timeout=self.command_timeout)
            output = stdout.read().decode('utf-8', errors='replace')
            error = stderr.read().decode('utf-8', errors='replace')

            output_path = os.path.join(self.collection_dir, output_file)
            with open(output_path, 'w') as f:
                f.write(output)
                if error:
                    f.write(f"\n\n--- STDERR ---\n{error}")

            logger.debug(f"Command output saved to {output_file}")

        except socket.timeout:
            logger.error(f"Command timed out after {self.command_timeout}s: {command}")
            raise
        except Exception as e:
            logger.error(f"Command execution failed: {command} - {e}")
            raise

    def _collect_system_info(self, ssh: paramiko.SSHClient) -> None:
        """
        Collect basic system information from ESXi host.

        Args:
            ssh: Connected SSH client
        """
        commands: Dict[str, str] = {
            "version": "vmware -v",
            "system_info": "esxcli system version get",
            "uptime": "uptime",
            "hostname": "hostname",
            "time_info": "esxcli system time get",
            "boot_device": "esxcli system boot device get",
            "licenses": "esxcli software license list"
        }

        for name, cmd in commands.items():
            try:
                self._run_command(ssh, cmd, f"system_{name}.txt")
            except Exception as e:
                logger.warning(f"Failed to collect system info '{name}': {e}")

    def _collect_performance_metrics(self, ssh: paramiko.SSHClient) -> None:
        """
        Collect performance metrics from ESXi host.

        Args:
            ssh: Connected SSH client
        """
        commands: Dict[str, str] = {
            "cpu_info": "esxcli hardware cpu list",
            "cpu_stats": "esxtop -b -n 1 -d 5 -c",
            "memory_info": "esxcli hardware memory get",
            "system_stats": "esxcli system stats system get",
            "disk_latency": "esxcli storage core device stats get",
            "io_stats": "esxtop -b -n 1 -d 5 -d"
        }

        for name, cmd in commands.items():
            try:
                self._run_command(ssh, cmd, f"perf_{name}.txt")
            except Exception as e:
                logger.warning(f"Failed to collect performance metric '{name}': {e}")

    def _collect_hardware_status(self, ssh: paramiko.SSHClient) -> None:
        """
        Collect hardware status information from ESXi host.

        Args:
            ssh: Connected SSH client
        """
        commands: Dict[str, str] = {
            "storage_devices": "esxcli storage core device list",
            "hba_info": "esxcli storage core adapter list",
            "health_status": "esxcli hardware platform get",
            "sensors": "esxcli hardware sensor list",
            "pci_devices": "lspci"
        }

        for name, cmd in commands.items():
            try:
                self._run_command(ssh, cmd, f"hw_{name}.txt")
            except Exception as e:
                logger.warning(f"Failed to collect hardware status '{name}': {e}")

    def _collect_vm_states(self, ssh: paramiko.SSHClient) -> None:
        """
        Collect VM state information from ESXi host.

        Args:
            ssh: Connected SSH client
        """
        commands: Dict[str, str] = {
            "vm_list": "esxcli vm process list",
            "vm_stats": "esxtop -b -n 1 -d 5 -v",
            "datastore_info": "esxcli storage filesystem list"
        }

        for name, cmd in commands.items():
            try:
                self._run_command(ssh, cmd, f"vm_{name}.txt")
            except Exception as e:
                logger.warning(f"Failed to collect VM state '{name}': {e}")

    def _collect_network_config(self, ssh: paramiko.SSHClient) -> None:
        """
        Collect network configuration from ESXi host.

        Args:
            ssh: Connected SSH client
        """
        commands: Dict[str, str] = {
            "interfaces": "esxcli network ip interface list",
            "vswitches": "esxcli network vswitch standard list",
            "portgroups": "esxcli network vswitch standard portgroup list",
            "vmkernel": "esxcli network ip interface ipv4 get",
            "neighbors": "esxcli network ip neighbor list",
            "dns_info": "esxcli network ip dns server list",
            "firewall_status": "esxcli network firewall get"
        }

        for name, cmd in commands.items():
            try:
                self._run_command(ssh, cmd, f"net_{name}.txt")
            except Exception as e:
                logger.warning(f"Failed to collect network config '{name}': {e}")

    def _collect_logs(self, ssh: paramiko.SSHClient) -> None:
        """
        Collect important log files from ESXi host via SFTP.

        Args:
            ssh: Connected SSH client
        """
        # Create logs directory
        logs_dir = os.path.join(self.collection_dir, "logs")
        os.makedirs(logs_dir, exist_ok=True)

        # List of important logs to collect
        log_files: List[str] = [
            "/var/log/vmkernel.log",
            "/var/log/hostd.log",
            "/var/log/auth.log",
            "/var/log/syslog.log",
            "/var/log/vpxa.log",
            "/var/log/fdm.log",
            "/var/log/esxi_install.log"
        ]

        # Use SFTP to copy logs
        sftp = None
        try:
            transport = ssh.get_transport()
            sftp = paramiko.SFTPClient.from_transport(transport)

            for log_file in log_files:
                try:
                    logger.debug(f"Collecting log: {log_file}")

                    # Get the filename part
                    filename = os.path.basename(log_file)
                    local_path = os.path.join(logs_dir, filename)

                    # Download the file
                    sftp.get(log_file, local_path)
                    logger.debug(f"Downloaded {log_file}")

                except FileNotFoundError:
                    logger.debug(f"Log file not found: {log_file}")
                except Exception as e:
                    logger.warning(f"Could not collect {log_file}: {e}")

        except Exception as e:
            logger.error(f"SFTP connection failed: {e}")
        finally:
            if sftp:
                sftp.close()