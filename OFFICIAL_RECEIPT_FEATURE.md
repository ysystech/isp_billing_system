# Acknowledgment Receipt Feature Implementation

## Overview
The ISP Billing System now includes acknowledgment receipt generation for prepaid subscription payments. This feature allows staff to print PDF receipts for customers after processing payments as a simple payment acknowledgment.

## Features Implemented

### 1. Receipt Generation
- **URL Pattern**: `/customer-subscriptions/<subscription_id>/receipt/`
- **View Function**: `generate_receipt` in `apps/customer_subscriptions/views.py`
- **Template**: `apps/customer_subscriptions/templates/customer_subscriptions/receipts/official_receipt.html`

### 2. Receipt Number Format
- Format: `AR-YYYY-MMDD-XXXX` (AR = Acknowledgment Receipt)
- Example: `AR-2025-0628-0001`
- Sequential numbering per day

### 3. Receipt Contents
- Company header with contact info
- Customer information
- Payment details
- Service period
- Days added
- Amount paid
- Signature sections

### 4. Print Receipt Buttons Added To:
1. **Subscription List** (`/customer-subscriptions/`)
   - Button appears for each subscription entry

2. **Payment History** (`/customer-subscriptions/customer/<id>/history/`)
   - Receipt button for each payment record

3. **Active Subscriptions** (`/customer-subscriptions/active/`)
   - Receipt button for the latest subscription

## Technical Implementation

### Dependencies
- **WeasyPrint**: PDF generation library
- Added to `requirements/requirements.in`
- Generates professional PDF receipts

### Receipt Template Features
- A4 size format
- Print-optimized CSS
- Company branding section
- Clear payment details
- Signature areas

## Usage

1. **From Subscription List**:
   - Navigate to Customer Subscriptions
   - Click "Print Receipt" button next to any subscription

2. **From Payment History**:
   - Go to customer's payment history
   - Click receipt icon for specific payment

3. **From Active Subscriptions**:
   - View active subscriptions
   - Click "Receipt" button for latest payment

## Customization

To customize the receipt, edit these values in `views.py`:
```python
'company_name': 'Your ISP Company Name',
'company_address': '123 Main Street, Cagayan de Oro City',
'company_phone': '(088) 123-4567',
'company_email': 'billing@yourisp.com',
```

## Installation Notes

After pulling these changes:
1. Install new dependencies: `pip install -r requirements/requirements.txt`
2. WeasyPrint may require system dependencies:
   - On Ubuntu/Debian: `sudo apt-get install python3-cffi python3-brotli libpango-1.0-0 libpangoft2-1.0-0`
   - On macOS: `brew install pango`

## Future Enhancements
- Email receipt to customer
- Receipt templates for different payment types
- Batch receipt printing
- Receipt reprint logging
