#!/usr/bin/env python3
"""
Simple verification script to check code structure and imports.

This script verifies that all modules are properly structured without
requiring external dependencies.
"""

import os
import sys
from pathlib import Path


def check_file_exists(filepath, description):
    """Check if a file exists."""
    if os.path.exists(filepath):
        print(f"✓ {description}: {filepath}")
        return True
    else:
        print(f"✗ {description} missing: {filepath}")
        return False


def check_module_structure():
    """Verify the module structure is correct."""
    print("=== Checking Module Structure ===\n")
    
    base_dir = Path(__file__).parent
    
    checks = [
        # Core package files
        (base_dir / "emo_options_bot" / "__init__.py", "Main package init"),
        (base_dir / "emo_options_bot" / "core" / "__init__.py", "Core module init"),
        (base_dir / "emo_options_bot" / "core" / "bot.py", "Main bot class"),
        (base_dir / "emo_options_bot" / "core" / "config.py", "Configuration"),
        (base_dir / "emo_options_bot" / "core" / "models.py", "Data models"),
        
        # AI module
        (base_dir / "emo_options_bot" / "ai" / "__init__.py", "AI module init"),
        (base_dir / "emo_options_bot" / "ai" / "nlp_processor.py", "NLP Processor"),
        
        # Trading module
        (base_dir / "emo_options_bot" / "trading" / "__init__.py", "Trading module init"),
        (base_dir / "emo_options_bot" / "trading" / "strategy_engine.py", "Strategy Engine"),
        
        # Risk module
        (base_dir / "emo_options_bot" / "risk" / "__init__.py", "Risk module init"),
        (base_dir / "emo_options_bot" / "risk" / "risk_manager.py", "Risk Manager"),
        
        # Orders module
        (base_dir / "emo_options_bot" / "orders" / "__init__.py", "Orders module init"),
        (base_dir / "emo_options_bot" / "orders" / "order_stager.py", "Order Stager"),
        
        # Market data module
        (base_dir / "emo_options_bot" / "market_data" / "__init__.py", "Market data init"),
        (base_dir / "emo_options_bot" / "market_data" / "provider.py", "Market Data Provider"),
        
        # Utils module
        (base_dir / "emo_options_bot" / "utils" / "__init__.py", "Utils module init"),
        (base_dir / "emo_options_bot" / "utils" / "helpers.py", "Helper functions"),
        
        # CLI
        (base_dir / "emo_options_bot" / "cli.py", "CLI interface"),
        
        # Tests
        (base_dir / "tests" / "__init__.py", "Tests init"),
        (base_dir / "tests" / "unit" / "test_nlp_processor.py", "NLP tests"),
        (base_dir / "tests" / "unit" / "test_strategy_engine.py", "Strategy tests"),
        (base_dir / "tests" / "unit" / "test_risk_manager.py", "Risk tests"),
        (base_dir / "tests" / "unit" / "test_order_stager.py", "Order tests"),
        (base_dir / "tests" / "integration" / "test_bot_integration.py", "Integration tests"),
        
        # Examples
        (base_dir / "examples" / "example_basic.py", "Basic example"),
        (base_dir / "examples" / "example_advanced.py", "Advanced example"),
        (base_dir / "examples" / "example_risk_management.py", "Risk management example"),
        
        # Configuration files
        (base_dir / "requirements.txt", "Requirements file"),
        (base_dir / "setup.py", "Setup file"),
        (base_dir / "pyproject.toml", "PyProject config"),
        (base_dir / ".gitignore", "Git ignore"),
        (base_dir / ".env.example", "Environment example"),
        (base_dir / "README.md", "README"),
    ]
    
    all_passed = True
    for filepath, description in checks:
        if not check_file_exists(filepath, description):
            all_passed = False
    
    print()
    if all_passed:
        print("✓ All files present!")
        return True
    else:
        print("✗ Some files are missing")
        return False


def check_python_syntax():
    """Check Python files for syntax errors."""
    print("\n=== Checking Python Syntax ===\n")
    
    base_dir = Path(__file__).parent
    python_files = list(base_dir.rglob("*.py"))
    
    errors = []
    for filepath in python_files:
        # Skip __pycache__
        if "__pycache__" in str(filepath):
            continue
        
        try:
            with open(filepath, 'r') as f:
                compile(f.read(), str(filepath), 'exec')
            print(f"✓ {filepath.relative_to(base_dir)}")
        except SyntaxError as e:
            errors.append((filepath, e))
            print(f"✗ {filepath.relative_to(base_dir)}: {e}")
    
    print()
    if not errors:
        print(f"✓ All {len(python_files)} Python files have valid syntax!")
        return True
    else:
        print(f"✗ {len(errors)} files have syntax errors")
        return False


def count_lines_of_code():
    """Count total lines of code."""
    print("\n=== Code Statistics ===\n")
    
    base_dir = Path(__file__).parent
    
    # Count by category
    categories = {
        "Core": base_dir / "emo_options_bot",
        "Tests": base_dir / "tests",
        "Examples": base_dir / "examples",
    }
    
    total_lines = 0
    total_files = 0
    
    for category, path in categories.items():
        if not path.exists():
            continue
        
        python_files = list(path.rglob("*.py"))
        lines = 0
        
        for filepath in python_files:
            if "__pycache__" in str(filepath):
                continue
            
            with open(filepath, 'r') as f:
                file_lines = len(f.readlines())
                lines += file_lines
        
        print(f"{category}:")
        print(f"  Files: {len(python_files)}")
        print(f"  Lines: {lines}")
        
        total_lines += lines
        total_files += len(python_files)
    
    print(f"\nTotal:")
    print(f"  Files: {total_files}")
    print(f"  Lines: {total_lines}")


def main():
    """Main verification function."""
    print("\n" + "=" * 60)
    print("EMO Options Bot - Structure Verification")
    print("=" * 60 + "\n")
    
    structure_ok = check_module_structure()
    syntax_ok = check_python_syntax()
    count_lines_of_code()
    
    print("\n" + "=" * 60)
    if structure_ok and syntax_ok:
        print("✓ All verifications passed!")
        print("=" * 60 + "\n")
        
        print("Next steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Run tests: pytest")
        print("3. Try examples: python examples/example_basic.py")
        print("4. Use CLI: emo-bot interactive")
        
        return 0
    else:
        print("✗ Some verifications failed")
        print("=" * 60 + "\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
