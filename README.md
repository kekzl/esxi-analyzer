# ESXi Issue Analyzer

An automated tool that diagnoses and suggests solutions for common VMware ESXi server problems.

## Features

- **Automated Log Collection**: Connects to ESXi hosts via SSH to collect system logs and configuration information
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

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/esxi-analyzer.git
   cd esxi-analyzer
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Make the main script executable (Linux/Mac):
   ```
   chmod +x esxi_analyzer.py
   ```

## Usage

### Command Line Interface

Analyze a remote ESXi host:
```
python esxi_analyzer.py -H <esxi-host> -u <username> -p <password> -o report.html -v
```

Analyze previously collected logs:
```
python esxi_analyzer.py -d /path/to/logs -o report.html -v
```

Options:
- `-H, --host`: ESXi host IP or hostname
- `-u, --username`: ESXi host username
- `-p, --password`: ESXi host password
- `-d, --directory`: Directory containing ESXi logs (if already collected)
- `-o, --output`: Output report file (default: report.html)
- `-v, --verbose`: Enable verbose output
- `-w, --web`: Start web interface

### Web Interface

Start the web interface:
```
python esxi_analyzer.py -w
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

- Python 3.6+
- Paramiko (SSH library for Python)
- Network connectivity to ESXi hosts (for remote analysis)
- SSH enabled on ESXi hosts

## Security Notes

- The tool requires SSH access to ESXi hosts which is typically disabled by default
- It's recommended to use temporary credentials or dedicated service accounts
- Password information is not stored persistently

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the terms included in the LICENSE file.

## Acknowledgements

- VMware for their extensive Knowledge Base articles
- The Paramiko project for SSH connectivity