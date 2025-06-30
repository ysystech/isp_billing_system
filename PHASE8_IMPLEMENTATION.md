# Phase 8: Background Tasks & Signals - Implementation Plan

## Overview
Phase 8 focuses on making all Celery tasks and Django signals tenant-aware to ensure background processes respect tenant boundaries.

## Current State Analysis

### Existing Background Tasks
1. **customer_subscriptions/tasks.py**
   - `update_expired_subscriptions()` - Updates expired subscriptions
   - `send_expiration_reminders()` - Sends subscription expiration reminders
   - Both tasks currently operate across ALL tenants (security issue)

### Existing Signals
1. **audit_logs/signals.py**
   - Tracks changes to models for audit logging
   - Already partially tenant-aware (checks for tenant in request)
   - Needs enhancement for background task context

2. **users/signals.py**
   - User signup and email confirmation
   - Profile picture management
   - Not tenant-specific (mostly OK as-is)

### Scheduled Tasks
- Tasks are scheduled via Celery Beat
- Configuration in settings.py SCHEDULED_TASKS

## Implementation Steps

### Step 1: Create Tenant-Aware Task Base Class
Create a base class for all tenant-aware Celery tasks that ensures proper tenant context.

### Step 2: Update Customer Subscription Tasks
1. Modify `update_expired_subscriptions` to process each tenant separately
2. Modify `send_expiration_reminders` to respect tenant boundaries
3. Add tenant context to task execution

### Step 3: Create Tenant Context Manager
Build a context manager to set tenant context for background tasks.

### Step 4: Update Audit Log Signals
1. Handle audit logging when no request context exists (background tasks)
2. Ensure tenant is properly set for all audit entries
3. Add support for system-generated changes

### Step 5: Create Tenant-Aware Scheduled Tasks
1. Update task scheduling to run per-tenant
2. Add tenant monitoring tasks
3. Ensure task isolation

### Step 6: Add Signal Handlers for Tenant Events
1. Tenant creation signal handlers
2. Tenant deletion/deactivation handlers
3. User tenant change handlers

### Step 7: Testing
1. Create tests for tenant-aware tasks
2. Test signal handlers with multiple tenants
3. Verify background task isolation

## Files to Create/Modify

### New Files
- `apps/tenants/tasks.py` - Base task classes and utilities
- `apps/tenants/context.py` - Tenant context managers
- `apps/tenants/signals.py` - Tenant-specific signals
- `apps/tenants/tests/test_tasks.py` - Task tests
- `apps/tenants/tests/test_signals.py` - Signal tests

### Files to Modify
- `apps/customer_subscriptions/tasks.py` - Make tasks tenant-aware
- `apps/audit_logs/signals.py` - Handle background context
- `isp_billing_system/settings.py` - Update task configuration

## Security Considerations
1. Tasks must NEVER process data across tenants
2. Each tenant's tasks run in isolation
3. Task results must be tenant-scoped
4. Failed tasks should not leak tenant information
5. Monitoring must respect tenant boundaries

## Let's Begin Implementation...