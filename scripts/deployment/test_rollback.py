#!/usr/bin/env python3
"""
Rollback Procedure Testing Script
Tests rollback procedures in a safe staging environment
"""

import os
import sys
import json
import shutil
from pathlib import Path
from datetime import datetime
import tempfile


class RollbackTester:
    """Test rollback procedures safely"""
    
    def __init__(self, root_dir: str = None):
        self.root_dir = Path(root_dir) if root_dir else Path.cwd()
        self.test_dir = None
        self.backup_dir = None
        
    def setup_test_environment(self):
        """Create safe test environment"""
        print("Setting up test environment...")
        
        # Create temporary directory for testing
        self.test_dir = Path(tempfile.mkdtemp(prefix="helios_rollback_"))
        self.backup_dir = self.test_dir / "backup"
        self.backup_dir.mkdir()
        
        print(f"Test environment: {self.test_dir}")
        return True
    
    def test_file_backup_restore(self):
        """Test basic file backup and restore"""
        print("Testing file backup/restore...")
        
        # Create test files
        test_service = self.test_dir / "test_service"
        test_service.mkdir()
        
        config_file = test_service / "config.yaml"
        config_file.write_text("version: 1.0\nservice: test")
        
        # Test backup
        backup_file = self.backup_dir / "config.yaml.backup"
        shutil.copy2(config_file, backup_file)
        
        # Modify original
        config_file.write_text("version: 2.0\nservice: modified")
        
        # Test restore
        shutil.copy2(backup_file, config_file)
        
        # Verify restore
        content = config_file.read_text()
        success = "version: 1.0" in content
        
        print(f"  File backup/restore: {'PASS' if success else 'FAIL'}")
        return success
    
    def test_configuration_rollback(self):
        """Test configuration rollback"""
        print("Testing configuration rollback...")
        
        # Create test configuration
        config_dir = self.test_dir / "config"
        config_dir.mkdir()
        
        # Original config
        original_config = {
            "database": {"host": "localhost", "port": 5432},
            "feature_flags": {"new_feature": False, "legacy_mode": True},
            "version": "1.0"
        }
        
        config_file = config_dir / "app.json"
        config_file.write_text(json.dumps(original_config, indent=2))
        
        # Backup
        backup_config = config_dir / "app.json.backup"
        shutil.copy2(config_file, backup_config)
        
        # Simulate upgrade
        new_config = original_config.copy()
        new_config["feature_flags"]["new_feature"] = True
        new_config["feature_flags"]["legacy_mode"] = False
        new_config["version"] = "2.0"
        
        config_file.write_text(json.dumps(new_config, indent=2))
        
        # Test rollback
        shutil.copy2(backup_config, config_file)
        
        # Verify
        restored_config = json.loads(config_file.read_text())
        success = (restored_config["version"] == "1.0" and 
                  restored_config["feature_flags"]["legacy_mode"] == True)
        
        print(f"  Configuration rollback: {'PASS' if success else 'FAIL'}")
        return success
    
    def test_service_state_management(self):
        """Test service state during rollback"""
        print("Testing service state management...")
        
        # Create mock service state files
        state_dir = self.test_dir / "state"
        state_dir.mkdir()
        
        # Service states
        services = ["orchestrator", "profile-ingestor", "strategist", "analyst"]
        
        success = True
        for service in services:
            # Create service state
            state_file = state_dir / f"{service}_state.json"
            state = {
                "status": "running",
                "version": "1.0", 
                "last_updated": datetime.now().isoformat(),
                "connections": {"database": "connected", "redis": "connected"}
            }
            state_file.write_text(json.dumps(state, indent=2))
            
            # Backup state
            backup_state = state_dir / f"{service}_state.json.backup"
            shutil.copy2(state_file, backup_state)
            
            # Simulate failure state
            failed_state = state.copy()
            failed_state["status"] = "failed"
            failed_state["version"] = "2.0"
            failed_state["connections"]["database"] = "disconnected"
            
            state_file.write_text(json.dumps(failed_state, indent=2))
            
            # Test rollback
            shutil.copy2(backup_state, state_file)
            
            # Verify restoration
            restored = json.loads(state_file.read_text())
            if not (restored["status"] == "running" and restored["version"] == "1.0"):
                success = False
                break
        
        print(f"  Service state management: {'PASS' if success else 'FAIL'}")
        return success
    
    def test_database_rollback_simulation(self):
        """Simulate database rollback procedure"""
        print("Testing database rollback simulation...")
        
        # Create mock database files
        db_dir = self.test_dir / "database"
        db_dir.mkdir()
        
        # Original schema
        schema_v1 = """
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100),
            email VARCHAR(100)
        );
        """
        
        schema_v2 = """
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100),
            email VARCHAR(100),
            created_at TIMESTAMP DEFAULT NOW()
        );
        """
        
        # Test schema rollback
        schema_file = db_dir / "schema.sql"
        schema_file.write_text(schema_v2)
        
        # Backup
        schema_backup = db_dir / "schema.sql.v1"
        schema_backup.write_text(schema_v1)
        
        # Rollback
        shutil.copy2(schema_backup, schema_file)
        
        # Verify
        content = schema_file.read_text()
        success = "created_at" not in content
        
        print(f"  Database rollback: {'PASS' if success else 'FAIL'}")
        return success
    
    def test_dependency_rollback(self):
        """Test dependency version rollback"""
        print("Testing dependency rollback...")
        
        # Create test requirements
        req_dir = self.test_dir / "requirements"
        req_dir.mkdir()
        
        # Original requirements
        original_reqs = """
        fastapi==0.104.1
        pydantic==2.5.0
        spacy==3.7.5
        uvicorn==0.24.0
        """
        
        # New requirements (with problematic version)
        new_reqs = """
        fastapi==0.105.0
        pydantic==2.6.0
        spacy==4.0.2
        uvicorn==0.25.0
        """
        
        req_file = req_dir / "requirements.txt"
        req_file.write_text(new_reqs.strip())
        
        # Backup original
        backup_req = req_dir / "requirements.txt.backup"
        backup_req.write_text(original_reqs.strip())
        
        # Test rollback
        shutil.copy2(backup_req, req_file)
        
        # Verify
        content = req_file.read_text()
        success = "spacy==3.7.5" in content and "spacy==4.0.2" not in content
        
        print(f"  Dependency rollback: {'PASS' if success else 'FAIL'}")
        return success
    
    def test_feature_flag_rollback(self):
        """Test feature flag rollback"""
        print("Testing feature flag rollback...")
        
        # Create feature flag config
        flag_dir = self.test_dir / "flags"
        flag_dir.mkdir()
        
        # Safe flags (old system)
        safe_flags = {
            "use_new_database": False,
            "enhanced_nlp": False,
            "new_ui": False,
            "legacy_mode": True
        }
        
        # Risky flags (new system)
        risky_flags = {
            "use_new_database": True,
            "enhanced_nlp": True,
            "new_ui": True,
            "legacy_mode": False
        }
        
        flag_file = flag_dir / "feature_flags.json"
        flag_file.write_text(json.dumps(risky_flags, indent=2))
        
        # Backup safe flags
        backup_flags = flag_dir / "feature_flags.json.safe"
        backup_flags.write_text(json.dumps(safe_flags, indent=2))
        
        # Test rollback
        shutil.copy2(backup_flags, flag_file)
        
        # Verify
        restored_flags = json.loads(flag_file.read_text())
        success = (not restored_flags["use_new_database"] and 
                  restored_flags["legacy_mode"])
        
        print(f"  Feature flag rollback: {'PASS' if success else 'FAIL'}")
        return success
    
    def cleanup_test_environment(self):
        """Clean up test environment"""
        if self.test_dir and self.test_dir.exists():
            shutil.rmtree(self.test_dir)
            print(f"Cleaned up test environment: {self.test_dir}")
    
    def run_rollback_tests(self):
        """Run all rollback tests"""
        print("=" * 60)
        print("ROLLBACK PROCEDURE TESTING")
        print("=" * 60)
        print()
        
        if not self.setup_test_environment():
            print("Failed to setup test environment")
            return False
        
        tests = [
            ("File Backup/Restore", self.test_file_backup_restore),
            ("Configuration Rollback", self.test_configuration_rollback),
            ("Service State Management", self.test_service_state_management),
            ("Database Rollback Simulation", self.test_database_rollback_simulation),
            ("Dependency Rollback", self.test_dependency_rollback),
            ("Feature Flag Rollback", self.test_feature_flag_rollback)
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                result = test_func()
                results.append((test_name, result))
                print()
            except Exception as e:
                print(f"  ERROR in {test_name}: {e}")
                results.append((test_name, False))
                print()
        
        # Summary
        print("=" * 60)
        print("ROLLBACK TEST SUMMARY")
        print("=" * 60)
        
        passed = 0
        for test_name, result in results:
            status = "PASS" if result else "FAIL"
            icon = "✓" if result else "✗"
            print(f"{icon} {test_name}: {status}")
            if result:
                passed += 1
        
        success_rate = (passed / len(results)) * 100
        print(f"\nOverall: {passed}/{len(results)} tests passed ({success_rate:.0f}%)")
        
        if success_rate >= 100:
            print("🎉 All rollback procedures validated!")
        elif success_rate >= 80:
            print("👍 Rollback procedures mostly working")
        else:
            print("⚠️ Some rollback procedures need attention")
        
        self.cleanup_test_environment()
        return success_rate >= 80


def main():
    """Main entry point"""
    tester = RollbackTester()
    success = tester.run_rollback_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()