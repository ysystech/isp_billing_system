#!/bin/bash
# Cleanup obsolete .md files from ISP Billing System

echo "This script will remove obsolete .md documentation files."
echo "Files to keep: README.md, PROJECT_KNOWLEDGE_UPDATED.md, MULTITENANT_COMPLETE.md, UPDATE_GUIDE.md, TODO.md, CLAUDE.md, LICENSE.md"
echo ""
read -p "Do you want to continue? (y/N) " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cleanup cancelled."
    exit 0
fi

cd /Users/aldesabido/pers/isp_billing_system

# Remove old project knowledge files
echo "Removing old project knowledge files..."
rm -f PROJECT_KNOWLEDGE_JUNE_29_FINAL.md
rm -f PROJECT_KNOWLEDGE_JUNE_30_PHASE5.md
rm -f PROJECT_KNOWLEDGE_MULTITENANT.md
rm -f PROJECT_KNOWLEDGE_PHASE7.md
rm -f PROJECT_KNOWLEDGE_PHASE8.md
rm -f PROJECT_KNOWLEDGE_PHASE9.md
rm -f project_knowledge_update.md

# Remove phase documentation
echo "Removing phase documentation..."
rm -f PHASE1_COMPLETE.md
rm -f PHASE2_COMPLETE.md
rm -f PHASE3_COMPLETE.md
rm -f PHASE3_GUIDE.md
rm -f PHASE3_UPDATE_REPORT.md
rm -f PHASE4_COMPLETE.md
rm -f PHASE4_IN_PROGRESS.md
rm -f PHASE5_COMPLETE.md
rm -f PHASE6_COMPLETE.md
rm -f PHASE6_IMPLEMENTATION.md
rm -f PHASE7_COMPLETE.md
rm -f PHASE8_COMPLETE.md
rm -f PHASE8_IMPLEMENTATION.md
rm -f PHASE8_TESTING_COMMANDS.md
rm -f PHASE8_TESTING_GUIDE.md
rm -f PHASE9_COMPLETE.md
rm -f PHASE10_COMPLETE.md
rm -f PHASE10_PLAN.md

# Remove fix documentation
echo "Removing fix documentation..."
rm -f BARANGAY_FORM_UPDATE.md
rm -f CUSTOMER_URL_FIX.md
rm -f LCP_TENANT_FIX.md
rm -f PERMISSION_CATEGORIES_SETUP.md
rm -f ROLE_FORM_TYPEERROR_FIX.md
rm -f ROLE_PERMISSIONS_EMPTY_FIX.md
rm -f ROLE_VIEW_PERMISSION_FIX.md
rm -f ROUTER_DUPLICATE_VALIDATION.md
rm -f ROUTER_FORM_UPDATE.md
rm -f TENANT_NAME_UNIQUE_REMOVAL.md
rm -f USER_MANAGEMENT_TENANT_FIX.md
rm -f ticket_permission_changes_guide.md
rm -f role_management_guide.md

# Remove other outdated files
echo "Removing other outdated files..."
rm -f GCE_DEPLOYMENT_MANUAL.md
rm -f TEST_VERIFICATION_REPORT.md
rm -f SQUASH_MIGRATIONS_GUIDE.md
rm -f MULTITENANT_CONTEXT.md
rm -f MULTITENANT_FINAL_SUMMARY.md
rm -f MULTITENANT_STATUS.md

echo ""
echo "Cleanup complete! Remaining .md files:"
find . -name "*.md" -type f | grep -v node_modules | grep -v venv | sort

echo ""
echo "Git status:"
git status --short
