# ESXi Issue Analyzer

[![CI](https://github.com/kekzl/esxi-analyzer/actions/workflows/ci.yml/badge.svg)](https://github.com/kekzl/esxi-analyzer/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Code style: ruff-format](https://img.shields.io/badge/code%20style-ruff--format-000000.svg)](https://github.com/astral-sh/ruff)

An automated tool that diagnoses and suggests solutions for common VMware ESXi server problems.

![Example Report](example.png "Example")

## Features

- **Automated Log Collection**: Connects to ESXi hosts via SSH to collect system logs and configuration information
  - Password and SSH key authentication support
  - Automatic retry with exponential backoff
  - Configurable timeouts and connection settings
- **Comprehensive Analysis**: Analyzes performance metrics, hardware status, VM states, and network configurations
- **Issue Detection**: Automatically identifies common issues such as:
  - Storage failures and high latency
  - High CPU/memory utilization
  - Network configuration problems and errors
  - Hardware sensor warnings
  - VM state issues and snapshot problems
  - ESXi version and security concerns
- **Detailed Reporting**: Generates HTML reports with:
  - Issue severity classification (Critical, High, Medium, Low)
  - Evidence and context for each detected issue
  - Specific troubleshooting steps based on VMware best practices
  - Links to relevant VMware Knowledge Base articles
- **Dual Interface**: Supports both command-line and web-based interfaces
- **Advanced Features**:
  - Configurable thresholds via YAML configuration
  - Professional logging with rotation
  - Type-safe code with full type hints
  - Improved error handling and recovery

## Installation

### Using uv (recommended)

```bash
uv pip install git+https://github.com/kekzl/esxi-analyzer.git
```

### Using pip

```bash
pip install git+https://github.com/kekzl/esxi-analyzer.git
```

### From source

```bash
git clone https://github.com/kekzl/esxi-analyzer.git
cd esxi-analyzer

# Using uv (recommended)
uv pip install -e .

# Or using pip
pip install -e .
```

### Development installation

```bash
git clone https://github.com/kekzl/esxi-analyzer.git
cd esxi-analyzer

# Install with development dependencies
uv pip install -e ".[dev]"

# Set up pre-commit hooks
pre-commit install
```

## Configuration

The analyzer can be configured using the `config.yaml` file. Copy and customize it to adjust thresholds, SSH settings, and logging behavior:

```yaml
# Analysis Thresholds
thresholds:
  high_latency_ms: 20.0              # Storage latency threshold
  low_datastore_space_percent: 10    # Datastore free space warning
  high_cpu_percent: 80               # CPU utilization threshold
  high_memory_percent: 90            # Memory usage threshold
  max_uptime_days: 180               # Maximum uptime before warning
  max_snapshot_age_days: 3           # Snapshot age threshold

# SSH Connection Settings
ssh:
  timeout: 30                        # Connection timeout in seconds
  command_timeout: 60                # Command execution timeout
  retry_attempts: 3                  # Number of retry attempts
  retry_delay: 2                     # Initial retry delay in seconds
  verify_host_keys: true             # Enable host key verification
  use_key_auth: false                # Use SSH key authentication
  key_file: "~/.ssh/id_rsa"         # Path to SSH private key

# Logging Settings
logging:
  level: "INFO"                      # DEBUG, INFO, WARNING, ERROR, CRITICAL
  log_file: "esxi_analyzer.log"     # Log file path
  max_bytes: 10485760                # Max log file size (10MB)
  backup_count: 5                    # Number of backup log files
```

### SSH Key Authentication

For improved security, you can use SSH key authentication instead of passwords:

1. Generate an SSH key pair (if you don't have one):
   ```bash
   ssh-keygen -t ed25519
   ```

2. Copy the public key to your ESXi host:
   ```bash
   ssh-copy-id root@esxi-host
   ```

3. Update `config.yaml` to enable key authentication:
   ```yaml
   ssh:
     use_key_auth: true
     key_file: "~/.ssh/id_ed25519"
     verify_host_keys: true
   ```

4. Run the analyzer without specifying a password:
   ```bash
   esxi-analyzer -H <esxi-host> -u root -o report.html
   ```

## Usage

### Command Line Interface

Analyze a remote ESXi host with password:
```bash
esxi-analyzer -H <esxi-host> -u <username> -p <password> -o report.html -v
```

Analyze using SSH key authentication:
```bash
esxi-analyzer -H <esxi-host> -u <username> -k ~/.ssh/id_ed25519 -o report.html -v
```

Analyze previously collected logs:
```bash
esxi-analyzer -d /path/to/logs -o report.html -v
```

Or run directly with Python:
```bash
python esxi_analyzer.py -H <esxi-host> -u <username> -p <password> -o report.html -v
```

Options:
- `-H, --host`: ESXi host IP or hostname
- `-u, --username`: ESXi host username
- `-p, --password`: ESXi host password (not required with SSH key auth)
- `-k, --key-file`: Path to SSH private key file
- `-d, --directory`: Directory containing ESXi logs (if already collected)
- `-o, --output`: Output report file (default: report.html)
- `-v, --verbose`: Enable verbose output
- `-w, --web`: Start web interface

### Web Interface

Start the web interface:
```bash
esxi-analyzer -w
```

This will launch a web browser pointing to http://localhost:8080 where you can:
- Connect to remote ESXi hosts
- Analyze locally stored logs
- Generate interactive reports

## Example Report

The generated HTML report includes:
- Executive summary with issue counts by severity
- Detailed breakdowns of each issue category
- Evidence collected for each issue
- Recommended solutions and VMware KB article references

## Requirements

- Python 3.10+
- Paramiko >= 3.5.0 (SSH library for Python)
- PyYAML >= 6.0.1 (for configuration management)
- Network connectivity to ESXi hosts (for remote analysis)
- SSH enabled on ESXi hosts

## Security Notes

- **SSH Access**: The tool requires SSH access to ESXi hosts which is typically disabled by default
- **Authentication**: SSH key authentication is strongly recommended over password authentication
- **Host Key Verification**: Enable `verify_host_keys` in config.yaml to prevent man-in-the-middle attacks
- **Credentials**: Use temporary credentials or dedicated service accounts with minimal required permissions
- **Logging**: Sensitive information is not logged by default; adjust log level carefully
- **Password Storage**: Password information is never stored persistently or written to disk

## Development

### Running tests

```bash
pytest
```

### Running linters

```bash
# Check code style
ruff check .

# Format code
ruff format .

# Type checking
mypy lib
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests and linters (`pytest && ruff check .`)
4. Commit your changes (`git commit -m 'Add amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

- VMware for their extensive Knowledge Base articles
- The Paramiko project for SSH connectivity
