#!/bin/bash
# Phase 7 Verification Script

echo "=========================================="
echo "PHASE 7: TENANT ISOLATION VERIFICATION"
echo "=========================================="
echo ""

# Run security tests
echo "1. Running security tests..."
echo "----------------------------"
make test ARGS='apps.tenants.verification.test_security'

echo ""
echo "2. Running verification management command..."
echo "--------------------------------------------"
make manage ARGS='verify_tenant_isolation --verbose'

echo ""
echo "3. Scanning for raw SQL queries..."
echo "---------------------------------"
python3 apps/tenants/verification/raw_query_scanner.py

echo ""
echo "=========================================="
echo "VERIFICATION COMPLETE"
echo "=========================================="