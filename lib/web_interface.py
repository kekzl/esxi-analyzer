#!/usr/bin/env python3
"""
ESXi Issue Analyzer - Web Interface Module
"""
import os
import tempfile
import threading
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import json
import io
import cgi
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.collector import LogCollector
from lib.analyzer import IssueAnalyzer
from lib.report import ReportGenerator

# Global variable to store the server instance
server_instance = None

class ESXiAnalyzerHandler(BaseHTTPRequestHandler):
    """HTTP Request Handler for ESXi Analyzer Web Interface"""
    
    def do_GET(self):
        """Handle GET requests"""
        # Parse the URL path
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        if path == '/' or path == '/index.html':
            self._serve_index()
        elif path == '/analyze':
            # Handle analyze request with query parameters
            query = parse_qs(parsed_url.query)
            self._handle_analyze(query)
        else:
            self.send_error(404)
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path == '/analyze':
            # Parse form data
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={
                    'REQUEST_METHOD': 'POST',
                    'CONTENT_TYPE': self.headers['Content-Type'],
                }
            )
            
            # Convert form to dict
            form_data = {}
            for field in form.keys():
                form_data[field] = form[field].value
                
            self._handle_analyze(form_data)
        else:
            self.send_error(404)
    
    def _serve_index(self):
        """Serve the index HTML page"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ESXi Issue Analyzer</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
        }
        h1 {
            color: #0066cc;
            border-bottom: 2px solid #0066cc;
            padding-bottom: 10px;
        }
        .container {
            background: #f5f5f5;
            border-radius: 5px;
            padding: 20px;
            margin-bottom: 20px;
        }
        form {
            margin-top: 15px;
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            font-weight: bold;
            margin-bottom: 5px;
        }
        input[type="text"], input[type="password"], input[type="file"] {
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-sizing: border-box;
        }
        .btn {
            background: #0066cc;
            color: white;
            border: none;
            padding: 10px 15px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
        }
        .btn:hover {
            background: #0052a3;
        }
        .tabs {
            display: flex;
            margin-bottom: 20px;
        }
        .tab {
            padding: 10px 15px;
            background: #ddd;
            cursor: pointer;
            border-radius: 5px 5px 0 0;
            margin-right: 5px;
        }
        .tab.active {
            background: #f5f5f5;
            font-weight: bold;
        }
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
        }
        #loading {
            display: none;
            text-align: center;
            margin: 20px 0;
        }
        .spinner {
            border: 6px solid #f3f3f3;
            border-top: 6px solid #0066cc;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <h1>ESXi Issue Analyzer</h1>
    
    <div class="tabs">
        <div class="tab active" onclick="showTab('remote')">Remote ESXi Host</div>
        <div class="tab" onclick="showTab('local')">Local Log Files</div>
    </div>
    
    <div class="container tab-content active" id="remote-tab">
        <h2>Analyze Remote ESXi Host</h2>
        <p>Connect to an ESXi host to collect and analyze logs and system information.</p>
        
        <form id="remote-form" method="post" action="/analyze">
            <input type="hidden" name="type" value="remote">
            
            <div class="form-group">
                <label for="host">ESXi Host IP or Hostname:</label>
                <input type="text" id="host" name="host" required>
            </div>
            
            <div class="form-group">
                <label for="username">Username:</label>
                <input type="text" id="username" name="username" value="root" required>
            </div>
            
            <div class="form-group">
                <label for="password">Password:</label>
                <input type="password" id="password" name="password" required>
            </div>
            
            <button type="submit" class="btn" onclick="showLoading()">Analyze Host</button>
        </form>
    </div>
    
    <div class="container tab-content" id="local-tab">
        <h2>Analyze Local Log Files</h2>
        <p>Select a directory containing ESXi logs that you've already collected.</p>
        
        <form id="local-form" method="post" action="/analyze">
            <input type="hidden" name="type" value="local">
            
            <div class="form-group">
                <label for="directory">Log Directory Path:</label>
                <input type="text" id="directory" name="directory" required>
                <p><small>Enter the full path to the directory containing ESXi logs</small></p>
            </div>
            
            <button type="submit" class="btn" onclick="showLoading()">Analyze Logs</button>
        </form>
    </div>
    
    <div id="loading">
        <div class="spinner"></div>
        <p>Analyzing ESXi host... This may take a few minutes.</p>
    </div>
    
    <script>
        function showTab(tabName) {
            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Show selected tab
            document.getElementById(tabName + '-tab').classList.add('active');
            document.querySelector(`.tab[onclick="showTab('${tabName}')"]`).classList.add('active');
        }
        
        function showLoading() {
            document.getElementById('loading').style.display = 'block';
        }
    </script>
</body>
</html>
"""
        
        self.wfile.write(html.encode())
    
    def _handle_analyze(self, form_data):
        """Handle analyze requests"""
        try:
            analysis_type = form_data.get('type', ['remote'])[0] if isinstance(form_data.get('type'), list) else form_data.get('type')
            
            # Show processing page
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            processing_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ESXi Issue Analyzer - Processing</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
        }
        .container {
            background: #f5f5f5;
            border-radius: 5px;
            padding: 20px;
        }
        .spinner {
            border: 6px solid #f3f3f3;
            border-top: 6px solid #0066cc;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        #status {
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h2>Analyzing ESXi Host</h2>
        <div class="spinner"></div>
        <div id="status">
            <p>Starting analysis. This process may take a few minutes...</p>
        </div>
    </div>
</body>
</html>
"""
            self.wfile.write(processing_html.encode())
            
            # Start analysis in a separate thread
            threading.Thread(target=self._run_analysis, args=(form_data,)).start()
            
        except Exception as e:
            self.send_error(500, str(e))
    
    def _run_analysis(self, form_data):
        """Run the analysis process"""
        try:
            analysis_type = form_data.get('type', ['remote'])[0] if isinstance(form_data.get('type'), list) else form_data.get('type')
            
            # Create a temporary file for the report
            fd, report_path = tempfile.mkstemp(suffix='.html', prefix='esxi_analyzer_report_')
            os.close(fd)
            
            # Collect logs and analyze based on the type
            if analysis_type == 'remote':
                host = form_data.get('host', [''])[0] if isinstance(form_data.get('host'), list) else form_data.get('host')
                username = form_data.get('username', [''])[0] if isinstance(form_data.get('username'), list) else form_data.get('username')
                password = form_data.get('password', [''])[0] if isinstance(form_data.get('password'), list) else form_data.get('password')
                
                collector = LogCollector(host, username, password, verbose=True)
                log_path = collector.collect()
            else:
                log_path = form_data.get('directory', [''])[0] if isinstance(form_data.get('directory'), list) else form_data.get('directory')
            
            # Analyze the logs
            analyzer = IssueAnalyzer(log_path, verbose=True)
            issues = analyzer.analyze()
            
            # Generate report
            host_info = form_data.get('host', ['Unknown Host'])[0] if isinstance(form_data.get('host'), list) else form_data.get('host', 'Unknown Host')
            report_gen = ReportGenerator(issues, host_info)
            report_gen.generate_report(report_path)
            
            # Open the report in the default web browser
            webbrowser.open('file://' + os.path.abspath(report_path))
            
        except Exception as e:
            print(f"Error during analysis: {str(e)}")


def start_web_server(port=8080):
    """Start the web server for the ESXi Analyzer web interface"""
    global server_instance
    
    try:
        server_address = ('localhost', port)
        server_instance = HTTPServer(server_address, ESXiAnalyzerHandler)
        
        # Open web browser with the interface
        webbrowser.open(f'http://localhost:{port}')
        
        print(f"Web interface started at http://localhost:{port}")
        server_instance.serve_forever()
    except Exception as e:
        print(f"Error starting web server: {str(e)}")
    finally:
        if server_instance:
            server_instance.server_close()


if __name__ == "__main__":
    # This allows running the web interface directly
    start_web_server()