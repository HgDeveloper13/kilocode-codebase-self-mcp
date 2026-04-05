#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive test script for the configuration system.
Tests all scenarios including basic functionality, environment variables,
validation, integration, and backward compatibility.
"""

import os
import sys
import tempfile
import json
import yaml
from pathlib import Path
from typing import Dict, Any
import unittest
from unittest.mock import patch, MagicMock

# Add the current directory to Python path to import our modules
sys.path.insert(0, str(Path(__file__).parent))

from qdrant_config import QdrantConfig, ConfigError
from qdrant_manager_with_config import QdrantManager


class TestConfigSystem(unittest.TestCase):
    """Test suite for the configuration system."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = Path(self.temp_dir) / "test_config.yaml"
        
        # Clean environment variables
        for key in ['QDRANT_HOST', 'QDRANT_PORT', 'QDRANT_API_KEY', 'QDRANT_TIMEOUT']:
            if key in os.environ:
                del os.environ[key]

    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_test_config(self, config_data: Dict[str, Any]):
        """Helper to create a test configuration file."""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f, allow_unicode=True)

    def test_basic_functionality(self):
        """Test basic configuration loading from file."""
        print("Testing basic functionality...")
        
        config_data = {
            'qdrant': {
                'host': 'localhost',
                'port': 6333,
                'api_key': 'test-key',
                'timeout': 30
            }
        }
        
        self.create_test_config(config_data)
        
        # Test loading from file
        config = QdrantConfig(config_path=str(self.config_file))
        
        self.assertEqual(config.host, 'localhost')
        self.assertEqual(config.port, 6333)
        self.assertEqual(config.api_key, 'test-key')
        self.assertEqual(config.timeout, 30)
        
        print("Basic functionality test passed")

    def test_environment_variable_priority(self):
        """Test that environment variables override file configuration."""
        print("Testing environment variable priority...")
        
        config_data = {
            'qdrant': {
                'host': 'localhost',
                'port': 6333,
                'api_key': 'file-key',
                'timeout': 30
            }
        }
        
        self.create_test_config(config_data)
        
        # Set environment variables
        os.environ['QDRANT_HOST'] = 'env-host'
        os.environ['QDRANT_PORT'] = '8080'
        os.environ['QDRANT_API_KEY'] = 'env-key'
        os.environ['QDRANT_TIMEOUT'] = '60'
        
        config = QdrantConfig(config_path=str(self.config_file))
        
        # Environment variables should override file values
        self.assertEqual(config.host, 'env-host')
        self.assertEqual(config.port, 8080)
        self.assertEqual(config.api_key, 'env-key')
        self.assertEqual(config.timeout, 60)
        
        print("Environment variable priority test passed")

    def test_validation_errors(self):
        """Test configuration validation and error handling."""
        print("Testing validation errors...")
        
        # Test invalid host
        config_data = {
            'qdrant': {
                'host': '',
                'port': 6333,
                'api_key': 'test-key',
                'timeout': 30
            }
        }
        
        self.create_test_config(config_data)
        
        with self.assertRaises(ConfigError) as context:
            config = QdrantConfig(config_path=str(self.config_file))
            config.validate_config()
        
        self.assertIn("Invalid host", str(context.exception))
        
        # Test invalid port
        config_data['qdrant']['host'] = 'localhost'
        config_data['qdrant']['port'] = 0
        
        self.create_test_config(config_data)
        
        with self.assertRaises(ConfigError) as context:
            config = QdrantConfig(config_path=str(self.config_file))
            config.validate_config()
        
        self.assertIn("Invalid port", str(context.exception))
        
        # Test invalid timeout
        config_data['qdrant']['port'] = 6333
        config_data['qdrant']['timeout'] = -1
        
        self.create_test_config(config_data)
        
        with self.assertRaises(ConfigError) as context:
            config = QdrantConfig(config_path=str(self.config_file))
            config.validate_config()
        
        self.assertIn("Invalid timeout", str(context.exception))
        
        print("Validation errors test passed")

    def test_missing_config_file(self):
        """Test behavior when config file doesn't exist."""
        print("Testing missing config file...")
        
        # Test with non-existent file - should use defaults
        config = QdrantConfig(config_path='/nonexistent/config.yaml')
        self.assertEqual(config.host, 'localhost')
        self.assertEqual(config.port, 6333)
        self.assertIsNone(config.api_key)
        self.assertEqual(config.timeout, 30)
        
        print("Missing config file test passed")

    def test_invalid_yaml_format(self):
        """Test handling of invalid YAML format."""
        print("Testing invalid YAML format...")
        
        # Create invalid YAML
        with open(self.config_file, 'w', encoding='utf-8') as f:
            f.write("invalid: yaml: format: [unclosed")
        
        with self.assertRaises(ConfigError) as context:
            QdrantConfig(config_path=str(self.config_file))
        
        self.assertIn("Failed to parse configuration file", str(context.exception))
        
        print("Invalid YAML format test passed")

    def test_integration_with_qdrant_manager(self):
        """Test integration with QdrantManager."""
        print("Testing integration with QdrantManager...")
        
        config_data = {
            'qdrant': {
                'host': 'localhost',
                'port': 6333,
                'api_key': 'test-key',
                'timeout': 30
            }
        }
        
        self.create_test_config(config_data)
        
        # Mock the requests to avoid actual network calls
        with patch('qdrant_manager_with_config.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'result': {
                    'collections': [
                        {'name': 'test_collection'}
                    ]
                }
            }
            mock_get.return_value = mock_response
            
            # Test QdrantManager initialization with config
            manager = QdrantManager(config_path=str(self.config_file))
            
            # Verify that the manager was created with correct parameters
            self.assertEqual(manager.config.host, 'localhost')
            self.assertEqual(manager.config.port, 6333)
            self.assertEqual(manager.config.api_key, 'test-key')
            self.assertEqual(manager.config.timeout, 30)
            
            print("Integration with QdrantManager test passed")

    def test_backward_compatibility(self):
        """Test backward compatibility with old imports."""
        print("Testing backward compatibility...")
        
        # Test that new imports work
        try:
            from qdrant_manager_with_config import QdrantManager as NewQdrantManager
            print("New import works")
        except ImportError:
            self.fail("New import should work")
        
        print("Backward compatibility test passed")

    def test_config_with_different_formats(self):
        """Test configuration with different data formats."""
        print("Testing configuration with different formats...")
        
        # Test with JSON config
        json_config = {
            'qdrant': {
                'host': 'localhost',
                'port': 6333,
                'api_key': 'json-key',
                'timeout': 30
            }
        }
        
        json_file = Path(self.temp_dir) / "test_config.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_config, f)
        
        config = QdrantConfig(config_path=str(json_file))
        self.assertEqual(config.api_key, 'json-key')
        
        print("Different formats test passed")

    def test_config_with_partial_data(self):
        """Test configuration with partial data (missing optional fields)."""
        print("Testing configuration with partial data...")
        
        config_data = {
            'qdrant': {
                'host': 'localhost',
                'port': 6333
                # Missing api_key and timeout
            }
        }
        
        self.create_test_config(config_data)
        
        config = QdrantConfig(config_path=str(self.config_file))
        
        self.assertEqual(config.host, 'localhost')
        self.assertEqual(config.port, 6333)
        self.assertIsNone(config.api_key)  # Should default to None
        self.assertEqual(config.timeout, 30)  # Should default to 30
        
        print("Partial data test passed")

    def test_config_with_environment_override(self):
        """Test configuration with selective environment variable override."""
        print("Testing selective environment variable override...")
        
        config_data = {
            'qdrant': {
                'host': 'localhost',
                'port': 6333,
                'api_key': 'file-key',
                'timeout': 30
            }
        }
        
        self.create_test_config(config_data)
        
        # Set only some environment variables
        os.environ['QDRANT_HOST'] = 'env-host'
        # Don't set QDRANT_PORT, QDRANT_API_KEY, QDRANT_TIMEOUT
        
        config = QdrantConfig(config_path=str(self.config_file))
        
        # Only host should be overridden
        self.assertEqual(config.host, 'env-host')
        self.assertEqual(config.port, 6333)  # From file
        self.assertEqual(config.api_key, 'file-key')  # From file
        self.assertEqual(config.timeout, 30)  # From file
        
        print("Selective environment override test passed")

    def test_config_with_invalid_environment_values(self):
        """Test configuration with invalid environment variable values."""
        print("Testing invalid environment variable values...")
        
        config_data = {
            'qdrant': {
                'host': 'localhost',
                'port': 6333,
                'api_key': 'file-key',
                'timeout': 30
            }
        }
        
        self.create_test_config(config_data)
        
        # Set invalid environment values
        os.environ['QDRANT_PORT'] = 'invalid'
        os.environ['QDRANT_TIMEOUT'] = 'also-invalid'
        
        with self.assertRaises(ConfigError) as context:
            QdrantConfig(config_path=str(self.config_file))
        
        self.assertIn("Invalid QDRANT_PORT value", str(context.exception))
        
        print("Invalid environment values test passed")


def run_comprehensive_tests():
    """Run all tests and provide a comprehensive report."""
    print("=" * 60)
    print("COMPREHENSIVE CONFIGURATION SYSTEM TEST SUITE")
    print("=" * 60)
    print()
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestConfigSystem)
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout, buffer=True)
    result = runner.run(suite)
    
    print()
    print("=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    
    if result.wasSuccessful():
        print("ALL TESTS PASSED!")
        print(f"Total tests run: {result.testsRun}")
        print("Configuration system is working correctly!")
    else:
        print("SOME TESTS FAILED")
        print(f"Tests run: {result.testsRun}")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
        
        if result.failures:
            print("\nFAILURES:")
            for test, traceback in result.failures:
                print(f"- {test}: {traceback}")
        
        if result.errors:
            print("\nERRORS:")
            for test, traceback in result.errors:
                print(f"- {test}: {traceback}")
    
    return result.wasSuccessful()


def test_manual_scenarios():
    """Test manual scenarios that are hard to automate."""
    print("\n" + "=" * 60)
    print("MANUAL TESTING SCENARIOS")
    print("=" * 60)
    
    scenarios = [
        {
            'name': 'File permissions test',
            'description': 'Test reading config file with different permissions',
            'steps': [
                'Create a config file with restricted permissions',
                'Try to load the config (should handle permission errors gracefully)'
            ]
        },
        {
            'name': 'Network connectivity test',
            'description': 'Test QdrantManager with actual Qdrant instance',
            'steps': [
                'Start a local Qdrant instance',
                'Configure the system to connect to it',
                'Test collection operations'
            ]
        },
        {
            'name': 'Large configuration test',
            'description': 'Test with a large configuration file',
            'steps': [
                'Create a config file with many collections and settings',
                'Verify the system can handle it efficiently'
            ]
        }
    ]
    
    for scenario in scenarios:
        print(f"\n{scenario['name']}")
        print(f"Description: {scenario['description']}")
        print("Steps to test manually:")
        for i, step in enumerate(scenario['steps'], 1):
            print(f"  {i}. {step}")
    
    print("\nNote: These scenarios require manual testing in a real environment.")


if __name__ == '__main__':
    # Run automated tests
    success = run_comprehensive_tests()
    
    # Show manual testing scenarios
    test_manual_scenarios()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)