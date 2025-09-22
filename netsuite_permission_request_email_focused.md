# Email to NetSuite Administrator - Transaction Permission Request

**Subject: NetSuite Integration - Add Transaction View Permissions to Existing Role**

---

Hi [Admin Name],

Our NetSuite integration (Account: 7326096_SB1) is working well, but we discovered we're missing one critical permission set. We can successfully query master data (customers, vendors, items) but cannot access any transaction data.

## Current Status:

✅ **Already Enabled (per our request):**
- REST Web Services (Full)
- SuiteAnalytics Workbook (Edit)
- SuiteAnalytics Connect
- Reports: SuiteAnalytics Workbook (Edit)
- Lists: Items, Units, Locations, Departments, Classes, Subsidiaries, Currencies, Exchange Rates, Accounts, Customers, Vendors
- Perform Search (Full)

❌ **Missing:** Transaction view permissions

## What We Need:

Please add **View-only** permissions for Transactions to our existing integration role.

## Steps to Add:

1. **Navigate to:** Setup > Users/Roles > Manage Roles
2. **Edit** our integration role
3. Go to **Permissions** tab > **Transactions** section
4. Add these permissions with **"View"** level only:

   - ✅ **Find Transaction** - View (CRITICAL - enables base transaction access)
   - ✅ **Sales Order** - View
   - ✅ **Invoice** - View
   - ✅ **Cash Sale** - View
   - ✅ **Credit Memo** - View
   - ✅ **Customer Payment** - View
   - ✅ **Customer Deposit** - View
   - ✅ **Customer Refund** - View
   - ✅ **Return Authorization** - View
   - ✅ **Purchase Order** - View
   - ✅ **Vendor Bill** - View (we have Vendor Bill Approval, but need View)
   - ✅ **Vendor Payment** - View (we have Vendor Payment Approval, but need View)
   - ✅ **Item Receipt** - View
   - ✅ **Item Fulfillment** - View
   - ✅ **Transfer Order** - View
   - ✅ **Inventory Transfer** - View
   - ✅ **Inventory Adjustment** - View

5. Click **Save**

## Why This Will Work:

Since you've already enabled **SuiteAnalytics Connect** and we have **REST Web Services (Full)**, adding these transaction view permissions will immediately allow us to query the `transaction` and `transactionline` tables via SuiteQL.

## Test Query:

Once saved, we'll verify access with:
```sql
SELECT id, tranid, trandate, recordtype 
FROM transaction 
WHERE ROWNUM = 1
```

## Security Note:

- Only requesting **View** level (read-only)
- Cannot create, edit, or delete any transactions
- All existing security controls remain in place

Currently, when we try to query transactions, we get "Invalid search query" errors because the role lacks transaction view permissions, even though SuiteAnalytics Connect is enabled.

Integration Details:
- Token ID: 38413d945d5d098...02ae04ec
- Using Token-Based Authentication (TBA)

Thank you for adding these final permissions to complete our integration setup!

Best regards,
[Your Name]

---

**Note:** The "Vendor Bill Approval" and "Vendor Payment Approval" permissions we currently have don't provide view access to the records themselves, which is why we need the standard View permissions added.