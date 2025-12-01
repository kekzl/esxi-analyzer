"""
Unit tests for issue analyzer
"""

# Add parent directory to path for imports
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.analyzer import Issue, IssueAnalyzer


class TestIssue(unittest.TestCase):
    """Test cases for Issue dataclass"""

    def test_issue_creation(self):
        """Test creating an Issue instance"""
        issue = Issue(
            title="Test Issue",
            description="Test description",
            category=Issue.CATEGORY_STORAGE,
            severity=Issue.SEVERITY_HIGH,
            evidence=["Evidence 1", "Evidence 2"],
            solution="Test solution",
            doc_links=["https://kb.vmware.com/test"],
        )

        self.assertEqual(issue.title, "Test Issue")
        self.assertEqual(issue.category, "storage")
        self.assertEqual(issue.severity, "high")
        self.assertEqual(len(issue.evidence), 2)

    def test_issue_default_fields(self):
        """Test Issue creation with default fields"""
        issue = Issue(title="Test", description="Test", category=Issue.CATEGORY_CPU, severity=Issue.SEVERITY_LOW)

        self.assertEqual(issue.evidence, [])
        self.assertEqual(issue.solution, "")
        self.assertEqual(issue.doc_links, [])


class TestIssueAnalyzer(unittest.TestCase):
    """Test cases for IssueAnalyzer class"""

    def setUp(self):
        """Set up test fixtures"""
        # Create a temporary directory with test files
        self.test_dir = tempfile.mkdtemp()

        # Create some test files
        test_path = Path(self.test_dir)
        (test_path / "system_version.txt").write_text("VMware ESXi 6.0.0 build-12345678")
        (test_path / "system_uptime.txt").write_text("up 200 days")

        self.analyzer = IssueAnalyzer(self.test_dir, verbose=False)

    def tearDown(self):
        """Clean up test fixtures"""
        import shutil

        if Path(self.test_dir).exists():
            shutil.rmtree(self.test_dir)

    def test_analyzer_initialization(self):
        """Test IssueAnalyzer initialization"""
        self.assertEqual(self.analyzer.log_path, self.test_dir)
        self.assertFalse(self.analyzer.verbose)
        self.assertEqual(len(self.analyzer.issues), 0)

    def test_read_existing_file(self):
        """Test reading an existing file"""
        content = self.analyzer._read_file("system_version.txt")
        self.assertIn("VMware ESXi", content)

    def test_read_nonexistent_file(self):
        """Test reading a non-existent file returns empty string"""
        content = self.analyzer._read_file("nonexistent.txt")
        self.assertEqual(content, "")

    def test_analyze_system_info_detects_eol_version(self):
        """Test that analyzer detects EOL ESXi version"""
        self.analyzer._analyze_system_info()

        # Should detect EOL version (6.0 < 6.5)
        eol_issues = [i for i in self.analyzer.issues if "EOL" in i.title]
        self.assertGreater(len(eol_issues), 0)

    def test_analyze_system_info_detects_excessive_uptime(self):
        """Test that analyzer detects excessive uptime"""
        self.analyzer._analyze_system_info()

        # Should detect excessive uptime (200 days > 180 days)
        uptime_issues = [i for i in self.analyzer.issues if "Uptime" in i.title]
        self.assertGreater(len(uptime_issues), 0)

    def test_analyze_returns_issue_list(self):
        """Test that analyze() returns a list of issues"""
        issues = self.analyzer.analyze()
        self.assertIsInstance(issues, list)


if __name__ == "__main__":
    unittest.main()
