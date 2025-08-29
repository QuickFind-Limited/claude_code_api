# Email to NetSuite Administrator - Permission Request

**Subject: NetSuite Integration - Read-Only Transaction Access Request**

---

Hi [Admin Name],

Our integration with NetSuite (Account: 7326096_SB1) is currently working well for master data (customers, vendors, items), but we need read-only access to transaction data for reporting and analytics purposes.

Currently, our integration role is missing permissions to query transaction tables via SuiteQL, which is preventing us from accessing sales orders, invoices, and other transactional data.

## What We Need:

**Read-only (View) access to transactions for our integration role.** We don't need Create, Edit, or Delete permissions - only View.

## Specific Steps to Grant Access:

### 1. Navigate to the Role:
- Go to **Setup > Users/Roles > Manage Roles**
- Find and click **Edit** next to our integration role

### 2. In the Permissions Tab > Transactions Section, Please Enable:

**Required Permissions (Set all to "View" level only):**
- ✅ **Find Transaction** - View
- ✅ **Sales Order** - View  
- ✅ **Invoice** - View
- ✅ **Cash Sale** - View
- ✅ **Credit Memo** - View
- ✅ **Customer Payment** - View
- ✅ **Customer Deposit** - View
- ✅ **Customer Refund** - View
- ✅ **Return Authorization** - View
- ✅ **Purchase Order** - View
- ✅ **Vendor Bill** - View
- ✅ **Vendor Payment** - View
- ✅ **Item Fulfillment** - View
- ✅ **Item Receipt** - View

### 3. Enable Features (if not already enabled):
- Go to **Setup > Company > Enable Features**
- Under **SuiteCloud** tab, ensure these are checked:
  - ✅ **SuiteAnalytics Connect**
  - ✅ **REST Web Services** (already enabled)
  - ✅ **Token-Based Authentication** (already enabled)

### 4. Save the Role

## Why We Need This:

- **Reporting**: Generate sales reports and analytics
- **Data Integration**: Sync transaction data with our systems
- **Business Intelligence**: Analyze order patterns and trends
- **Compliance**: Track and audit transaction history

## Security Note:

- We're only requesting **View** permissions (read-only)
- No ability to create, modify, or delete any transactions
- Access via API only (not UI access)
- All queries are logged and auditable

## Testing:

Once permissions are granted, we'll test by running this simple SuiteQL query:
```sql
SELECT id, tranid, trandate FROM transaction WHERE ROWNUM = 1
```

If this returns data instead of an error, we'll know the permissions are working.

## Current Status:

✅ **Working:** Customer, Vendor, Item, Location tables (master data)
❌ **Not Working:** Transaction, TransactionLine tables (transactional data)

Please let me know if you need any additional information or have concerns about granting these permissions. We can also schedule a quick call to discuss if needed.

The integration is using Token-Based Authentication with the following credentials:
- Consumer Key: 7d09ea1cb48f158...f22d5bb1
- Token ID: 38413d945d5d098...02ae04ec

Thank you for your help in enabling this critical functionality for our integration.

Best regards,
[Your Name]

---

**P.S.** If you'd prefer to create a new read-only role specifically for this integration instead of modifying the existing one, that would work perfectly as well. We just need a role with the transaction view permissions listed above.