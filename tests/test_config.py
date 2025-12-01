"""
Unit tests for configuration management
"""

# Add parent directory to path for imports
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.config import Config


class TestConfig(unittest.TestCase):
    """Test cases for Config class"""

    def setUp(self):
        """Set up test fixtures"""
        self.config = Config()

    def test_get_threshold(self):
        """Test getting threshold values"""
        high_latency = self.config.get_threshold("high_latency_ms")
        self.assertIsNotNone(high_latency)
        self.assertIsInstance(high_latency, (int, float))

    def test_get_ssh_config(self):
        """Test getting SSH configuration"""
        timeout = self.config.get_ssh("timeout")
        self.assertIsNotNone(timeout)
        self.assertIsInstance(timeout, int)

    def test_get_logging_config(self):
        """Test getting logging configuration"""
        level = self.config.get_logging("level")
        self.assertIsNotNone(level)
        self.assertIn(level, ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])

    def test_get_with_dot_notation(self):
        """Test getting values using dot notation"""
        value = self.config.get("thresholds.high_latency_ms")
        self.assertIsNotNone(value)

    def test_get_with_default(self):
        """Test getting non-existent key returns default"""
        value = self.config.get("nonexistent.key", "default_value")
        self.assertEqual(value, "default_value")

    def test_singleton_pattern(self):
        """Test that Config follows singleton pattern"""
        config1 = Config()
        config2 = Config()
        self.assertIs(config1, config2)


class TestConfigDefaults(unittest.TestCase):
    """Test default configuration values"""

    def setUp(self):
        """Set up test fixtures"""
        self.config = Config()

    def test_default_thresholds(self):
        """Test that default threshold values are reasonable"""
        self.assertEqual(self.config.get_threshold("high_latency_ms"), 20.0)
        self.assertEqual(self.config.get_threshold("low_datastore_space_percent"), 10)
        self.assertEqual(self.config.get_threshold("high_cpu_percent"), 80)
        self.assertEqual(self.config.get_threshold("high_memory_percent"), 90)
        self.assertEqual(self.config.get_threshold("max_uptime_days"), 180)

    def test_default_ssh_settings(self):
        """Test that default SSH settings are reasonable"""
        self.assertEqual(self.config.get_ssh("timeout"), 30)
        self.assertEqual(self.config.get_ssh("retry_attempts"), 3)
        self.assertEqual(self.config.get_ssh("retry_delay"), 2)


if __name__ == "__main__":
    unittest.main()
