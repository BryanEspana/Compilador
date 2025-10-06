"""
Main script to run all TAC (Three-Address Code) tests
"""

import sys
import os
# Add the program directory to the path to import TAC modules
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

from test_tac_basic import run_all_tests as run_basic_tests
from test_tac_parser import run_all_parser_tests
from test_extended_symbol_table import run_all_extended_symbol_table_tests
from test_integration import run_all_integration_tests

def main():
    """Run all TAC tests"""
    print("🚀 Running All Three-Address Code (TAC) Tests")
    print("=" * 60)
    print()
    
    # Run basic TAC generation tests
    print("1️⃣ TAC Generation Tests")
    print("-" * 30)
    run_basic_tests()
    print()
    
    # Run TAC parser tests
    print("2️⃣ TAC Parser Tests")
    print("-" * 30)
    run_all_parser_tests()
    print()
    
    # Run Extended Symbol Table tests
    print("3️⃣ Extended Symbol Table Tests")
    print("-" * 30)
    run_all_extended_symbol_table_tests()
    print()
    
    # Run Integration tests
    print("4️⃣ Integration Tests")
    print("-" * 30)
    run_all_integration_tests()
    print()
    
    print("🎉 All TAC tests completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    main()
