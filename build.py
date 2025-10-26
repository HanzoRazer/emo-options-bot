#!/usr/bin/env python3
"""EMO Options Bot Build & Validation Script"""

import os
import sys
import subprocess
import argparse
import logging
from pathlib import Path

project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def validate_environment():
    logger.info("🔍 Validating environment...")
    
    if sys.version_info < (3, 8):
        logger.error("❌ Python 3.8+ required")
        return False
    
    logger.info(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    return True

def validate_dependencies():
    logger.info("📦 Checking dependencies...")
    
    requirements_file = project_root / "requirements.txt"
    if not requirements_file.exists():
        logger.error("❌ requirements.txt not found")
        return False
    
    logger.info("✅ Dependencies file found")
    return True

def validate_structure():
    logger.info("🏗️ Validating structure...")
    
    required = [
        project_root / "src",
        project_root / "ops" / "db" / "session.py", 
        project_root / "ops" / "staging" / "models.py",
        project_root / "tools" / "stage_order_cli.py",
        project_root / "tools" / "emit_health.py",
        project_root / "tools" / "db_manage.py"
    ]
    
    missing = [p for p in required if not p.exists()]
    if missing:
        logger.error(f"❌ Missing: {missing}")
        return False
    
    logger.info("✅ Structure validated")
    return True

def test_database():
    logger.info("🗄️ Testing database...")
    
    try:
        from ops.db.session import init_db, test_connection
        init_db()
        
        if test_connection():
            logger.info("✅ Database working")
            return True
        else:
            logger.error("❌ Database failed")
            return False
    except Exception as e:
        logger.error(f"❌ Database error: {e}")
        return False

def test_tools():
    logger.info("🔧 Testing tools...")
    
    try:
        result = subprocess.run([
            sys.executable, str(project_root / "tools" / "stage_order_cli.py"), "--help"
        ], capture_output=True, timeout=10)
        
        if result.returncode == 0:
            logger.info("✅ Tools working")
            return True
        else:
            logger.error("❌ Tools failed")
            return False
    except Exception as e:
        logger.error(f"❌ Tools error: {e}")
        return False

def run_validation():
    logger.info("🚀 EMO Options Bot v2.0 Validation")
    
    checks = [
        ("Environment", validate_environment),
        ("Dependencies", validate_dependencies), 
        ("Structure", validate_structure),
        ("Database", test_database),
        ("Tools", test_tools),
    ]
    
    for name, func in checks:
        logger.info(f"📋 {name}...")
        if not func():
            logger.error(f"❌ FAILED: {name}")
            return False
        logger.info(f"✅ PASSED: {name}")
    
    logger.info("🎉 ALL VALIDATIONS PASSED!")
    logger.info("🚀 EMO Options Bot v2.0 is ready!")
    return True

def main():
    parser = argparse.ArgumentParser(description="EMO Options Bot Build System")
    parser.add_argument("--validate", action="store_true", help="Run validation")
    parser.add_argument("--test", action="store_true", help="Run tests")
    
    args = parser.parse_args()
    
    try:
        success = run_validation()
        if success:
            logger.info("✅ SUCCESS: System ready for use!")
            logger.info("📖 Run: python tools/emit_health.py (health dashboard)")
            logger.info("📖 Run: python tools/stage_order_cli.py --help (CLI tools)")
            logger.info("📖 Run: python tools/db_manage.py health (database)")
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        logger.info("\n🛑 Cancelled")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
