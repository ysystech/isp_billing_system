# ISP Billing System - Phase 3 User Guide

## Overview
Phase 3 introduces the prepaid subscription management system with customer installations and payment tracking.

## Key Features

### 1. Customer Installations
- **Purpose**: Track router installations for customers
- **Access**: http://localhost:8000/installations/
- **Features**:
  - Create new installations for customers
  - Assign routers and technicians
  - Track installation status (Active/Suspended/Terminated)
  - View subscription history per installation

### 2. Customer Subscriptions (Prepaid Payments)
- **Purpose**: Process and track prepaid subscription payments
- **Access**: http://localhost:8000/customer-subscriptions/
- **Features**:
  - Process new payments for existing installations
  - Track payment methods (Cash, GCash, Bank Transfer)
  - Monitor active and expiring subscriptions
  - View payment history

## Workflow

### Setting Up a New Customer:
1. **Create Customer** → Customers menu
2. **Create Installation** → Installations menu → "New Installation"
3. **Add Subscription** → From installation detail page → "Add New Payment"

### Processing a Renewal:
1. Go to **Installations** or **Subscriptions**
2. Find the customer
3. Click **"Add Payment"** or **"Renew"**
4. Select plan and enter payment details
5. Submit to activate subscription

### Monitoring Expiring Subscriptions:
1. Go to **Subscriptions** → **"Expiring Soon"**
2. View customers with subscriptions expiring in next 3-30 days
3. Contact customers for renewal
4. Process payment when customer arrives

## Key Concepts

### Subscription Plans
- Plans now have `day_count` (1, 3, 7, 15, 30 days)
- Price is for the entire period, not monthly
- Examples:
  - Daily Basic: 1 day for ₱50
  - Weekly Standard: 7 days for ₱300
  - Monthly Premium: 30 days for ₱1,800

### Prepaid Model
- Customers pay upfront for a time period
- Subscription starts immediately or at specified time
- Automatically expires after the period ends
- No auto-renewal - customer must pay again

### Installation Status
- **Active**: Normal operations
- **Suspended**: Temporary hold (e.g., technical issues)
- **Terminated**: Permanent disconnection

## Dashboard Updates
The dashboard now shows:
- Total and active installations
- Active subscriptions count
- Subscriptions expiring soon
- Today's revenue collection

## Reports Available
- Subscription list with filters
- Expiring subscriptions report
- Installation status overview
- Payment history per customer

## Tips
1. Check "Expiring Soon" daily to prepare renewal reminders
2. Use reference numbers for GCash/Bank payments
3. Add notes for special cases or discounts
4. Monitor dashboard for daily collection totals
