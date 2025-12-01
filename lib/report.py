#!/usr/bin/env python3
"""
ESXi Issue Analyzer - Report Generator Module
"""

import builtins
import contextlib
import datetime
import webbrowser
from pathlib import Path


class ReportGenerator:
    """Generates HTML reports with analysis results"""

    def __init__(self, issues, host_info):
        """
        Initialize the report generator

        Args:
            issues (list): List of detected issues
            host_info (str): ESXi host information
        """
        self.issues = issues
        self.host_info = host_info
        self.timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def generate_report(self, output_file):
        """
        Generate an HTML report with analysis results

        Args:
            output_file (str): Path to save the HTML report
        """
        html_content = self._generate_html()

        output_path = Path(output_file)
        output_path.write_text(html_content)

        # Try to open the report in a web browser
        with contextlib.suppress(builtins.BaseException):
            webbrowser.open("file://" + str(output_path.resolve()))

    def _generate_html(self):
        """Generate HTML content for the report"""
        # Count issues by severity
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}

        for issue in self.issues:
            if issue.severity in severity_counts:
                severity_counts[issue.severity] += 1

        # Sort issues by severity (critical first)
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}

        sorted_issues = sorted(self.issues, key=lambda x: severity_order.get(x.severity, 4))

        # Group issues by category
        issues_by_category = {}
        for issue in sorted_issues:
            if issue.category not in issues_by_category:
                issues_by_category[issue.category] = []
            issues_by_category[issue.category].append(issue)

        # Generate HTML
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ESXi Issue Analyzer Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        header {{
            background: #0066CC;
            color: white;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 5px;
        }}
        h1, h2, h3 {{
            margin-top: 0;
        }}
        .summary {{
            display: flex;
            justify-content: space-between;
            flex-wrap: wrap;
            margin-bottom: 30px;
        }}
        .summary-box {{
            background: #f5f5f5;
            border-radius: 5px;
            padding: 15px;
            width: calc(25% - 20px);
            box-sizing: border-box;
            text-align: center;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .critical {{
            background: #ffebee;
            border-left: 5px solid #d32f2f;
        }}
        .high {{
            background: #fff8e1;
            border-left: 5px solid #ff8f00;
        }}
        .medium {{
            background: #e8f5e9;
            border-left: 5px solid #43a047;
        }}
        .low {{
            background: #e3f2fd;
            border-left: 5px solid #1976d2;
        }}
        .issue {{
            background: white;
            margin-bottom: 15px;
            padding: 15px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .issue-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .issue-title {{
            margin: 0;
            font-size: 18px;
        }}
        .severity-badge {{
            padding: 5px 10px;
            border-radius: 3px;
            font-size: 14px;
            font-weight: bold;
            color: white;
        }}
        .badge-critical {{ background: #d32f2f; }}
        .badge-high {{ background: #ff8f00; }}
        .badge-medium {{ background: #43a047; }}
        .badge-low {{ background: #1976d2; }}
        .evidence {{
            background: #f5f5f5;
            padding: 10px;
            margin: 10px 0;
            border-radius: 5px;
            font-family: monospace;
            white-space: pre-wrap;
            max-height: 200px;
            overflow-y: auto;
        }}
        .solution {{
            background: #e8f5e9;
            padding: 10px;
            margin: 10px 0;
            border-radius: 5px;
        }}
        .links {{
            margin-top: 10px;
        }}
        .category-section {{
            margin-bottom: 30px;
        }}
        @media (max-width: 768px) {{
            .summary-box {{
                width: calc(50% - 20px);
                margin-bottom: 20px;
            }}
        }}
    </style>
</head>
<body>
    <header>
        <h1>ESXi Issue Analyzer Report</h1>
        <p>Host: {self.host_info}</p>
        <p>Analysis Date: {self.timestamp}</p>
    </header>

    <div class="summary">
        <div class="summary-box critical">
            <h3>Critical Issues</h3>
            <p>{severity_counts["critical"]}</p>
        </div>
        <div class="summary-box high">
            <h3>High Severity</h3>
            <p>{severity_counts["high"]}</p>
        </div>
        <div class="summary-box medium">
            <h3>Medium Severity</h3>
            <p>{severity_counts["medium"]}</p>
        </div>
        <div class="summary-box low">
            <h3>Low Severity</h3>
            <p>{severity_counts["low"]}</p>
        </div>
    </div>
"""

        # If no issues found
        if not self.issues:
            html += """
    <div class="category-section">
        <h2>No Issues Found</h2>
        <p>No issues were detected in this ESXi host. This could mean either:</p>
        <ul>
            <li>The system is operating normally</li>
            <li>The collected data was insufficient for analysis</li>
            <li>There are issues present that the analyzer doesn't currently detect</li>
        </ul>
        <p>It's always a good practice to regularly monitor your ESXi hosts
        and apply updates as recommended by VMware.</p>
    </div>
"""
        else:
            # Add a table of contents
            html += """
    <div class="category-section">
        <h2>Table of Contents</h2>
        <ul>
"""
            for category, issues_list in issues_by_category.items():
                # Format the category name for display
                display_category = category.capitalize()
                html += (
                    f'            <li><a href="#{category}">{display_category} Issues ({len(issues_list)})</a></li>\n'
                )

            html += """
        </ul>
    </div>
"""

            # Generate content for each category
            for category, category_issues in issues_by_category.items():
                # Format the category name for display
                display_category = category.capitalize()

                html += f"""
    <div class="category-section" id="{category}">
        <h2>{display_category} Issues</h2>
"""

                for issue in category_issues:
                    # Create severity badge
                    severity_class = f"badge-{issue.severity}"

                    html += f"""
        <div class="issue {issue.severity}">
            <div class="issue-header">
                <h3 class="issue-title">{issue.title}</h3>
                <span class="severity-badge {severity_class}">{issue.severity.upper()}</span>
            </div>
            <p>{issue.description}</p>

            <h4>Evidence:</h4>
            <div class="evidence">"""

                    for evidence in issue.evidence:
                        html += f"{evidence}\n"

                    html += f"""</div>

            <h4>Recommended Solution:</h4>
            <div class="solution">
                <p>{issue.solution}</p>
            </div>
"""

                    if issue.doc_links:
                        html += """
            <div class="links">
                <h4>VMware Documentation:</h4>
                <ul>
"""
                        for link in issue.doc_links:
                            html += f'                    <li><a href="{link}" target="_blank">{link}</a></li>\n'

                        html += """
                </ul>
            </div>
"""

                    html += """
        </div>
"""

                html += """
    </div>
"""

        # Close the HTML
        html += """
    <footer>
        <p>Generated by ESXi Issue Analyzer</p>
    </footer>
</body>
</html>
"""

        return html
