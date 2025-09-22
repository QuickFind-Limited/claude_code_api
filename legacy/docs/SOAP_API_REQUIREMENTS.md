# NetSuite SOAP API Requirements for Saved Search Access

## 🔴 Why SOAP Failed: Detailed Analysis

### Current Errors We Encountered:

1. **"Invalid login attempt"** - Token authentication not working for SOAP
2. **"Transaction is not a legal value for SearchRecordType"** - Wrong enum value
3. **403 Forbidden on RESTlet endpoints** - No SuiteScript access

## 📋 What Would Be Needed to Make SOAP Work

### 1. Features to Enable in NetSuite

```
Setup > Company > Enable Features
```

- ✅ **SuiteAnalytics Connect** (Already enabled - we can query data)
- ❓ **Web Services** (Might not be enabled for SOAP)
- ❓ **SOAP Web Services** (Separate from REST API)
- ✅ **Token-Based Authentication** (Enabled for REST, but maybe not SOAP)

### 2. Role Permissions Required

The role assigned to your tokens needs these permissions:

```
Setup > Users/Roles > Manage Roles > [Your Role]
```

#### Current Permissions (What We Have):
- ✅ **Lists > Customers** - View
- ✅ **Lists > Items** - View  
- ✅ **Lists > Transactions** - View (recently added)
- ✅ **SuiteAnalytics Connect** - Enabled

#### Missing Permissions (What We Need for SOAP):
- ❌ **Setup > Web Services** - Full
- ❌ **Lists > Perform Search** - View/Full
- ❌ **Lists > Publish Search** - Create (to see saved searches)
- ❌ **Reports > SuiteAnalytics Workbook** - View
- ❌ **Custom Records > Saved Searches** - View

### 3. Integration Record Configuration

Your current integration needs to be updated:

```
Setup > Integration > Manage Integrations
```

Current Setup:
- ✅ Token-Based Authentication enabled
- ✅ REST Web Services enabled
- ❌ SOAP Web Services - Might not be checked

Required Changes:
- Enable "SOAP Web Services" checkbox
- Ensure "State" is "Enabled"
- Verify correct "User" is assigned

### 4. Token Configuration

The issue might be that your tokens were generated for REST only:

```
Setup > Users/Roles > Access Tokens
```

You might need to:
1. Generate NEW tokens after enabling SOAP
2. Ensure tokens are for a user with SOAP permissions
3. Verify tokens haven't expired

### 5. Correct SOAP Request Format

The error "Transaction is not a legal value" means we need the correct enum values:

**Wrong:**
```xml
<platformCore:searchType>Transaction</platformCore:searchType>
```

**Correct Options:**
```xml
<platformCore:searchType>transaction</platformCore:searchType>  <!-- lowercase -->
<platformCore:searchType>TransactionSearchBasic</platformCore:searchType>
<platformCore:searchType>salesOrder</platformCore:searchType>  <!-- specific type -->
```

## 🔧 Steps to Fix SOAP Access

### For Your NetSuite Admin:

1. **Enable Web Services Features**
   ```
   Setup > Company > Enable Features > SuiteCloud Tab
   - ☑ Web Services
   - ☑ SOAP Web Services  
   - ☑ REST Web Services (already enabled)
   ```

2. **Update Role Permissions**
   ```
   Setup > Users/Roles > Manage Roles > [GYM_PLUS_COFFEE_API_ROLE]
   
   Permissions Tab:
   - Setup > Web Services: Full
   - Lists > Perform Search: View
   - Lists > Publish Search: Create
   - Reports > SuiteAnalytics Workbook: View
   ```

3. **Update Integration Record**
   ```
   Setup > Integration > Manage Integrations > [Your Integration]
   
   - ☑ Token-Based Authentication
   - ☑ TBA: Authorization Flow  
   - ☑ REST Web Services
   - ☑ SOAP Web Services (ADD THIS)
   ```

4. **Generate New Tokens**
   ```
   Setup > Users/Roles > Access Tokens > New
   
   - Application: [Your Integration]
   - User: [API User]
   - Role: [Updated Role with SOAP permissions]
   ```

## 📧 Email Template for NetSuite Admin

```
Subject: Enable SOAP API Access for Saved Search Discovery

Hi [Admin],

We need to enable SOAP Web Services to programmatically list saved searches. Currently, we can access transaction data via REST/SuiteQL but cannot discover saved searches.

Please make these changes:

1. ENABLE FEATURES:
   - Setup > Company > Enable Features > SuiteCloud
   - Check: "SOAP Web Services"

2. UPDATE ROLE PERMISSIONS:
   For the role used by our API tokens:
   - Add: Setup > Web Services (Full)
   - Add: Lists > Perform Search (View)
   - Add: Lists > Publish Search (Create)

3. UPDATE INTEGRATION:
   - Setup > Integration > Manage Integrations
   - Find our integration (used for API access)
   - Check: "SOAP Web Services"

4. GENERATE NEW TOKENS:
   - After the above changes
   - Generate new Access Token and Token Secret
   - Send them securely

This will allow us to:
- List all saved searches programmatically
- Get saved search IDs and names
- Eventually run saved searches via API

No changes needed to existing REST API access.

Thanks,
[Your Name]
```

## 🤔 Do You Really Need This?

### Consider the Trade-offs:

**Pros of Enabling SOAP:**
- Can list saved searches by ID and name
- Can potentially run saved searches directly
- Maintains consistency with UI searches

**Cons of Enabling SOAP:**
- SOAP is being deprecated by NetSuite
- Requires admin changes and new tokens
- More complex authentication setup
- Another API to maintain

**Alternative: Stick with SuiteQL**
- ✅ Already working
- ✅ More powerful than saved searches
- ✅ No admin changes needed
- ✅ Future-proof (SOAP is legacy)

## 🎯 Recommendation

Unless you have a specific requirement to run existing saved searches by their ID, **stick with SuiteQL**. You can:

1. **Document important saved searches manually** (one-time effort)
2. **Recreate their logic in SuiteQL** (more flexible)
3. **Build better queries** than saved searches allow

If you DO need saved search access:
1. Send the email template above to your admin
2. Wait for changes and new tokens
3. Test with the corrected SOAP format
4. Consider long-term migration away from SOAP

## 📝 Summary

The SOAP API failed because:
- **Missing "SOAP Web Services" feature** in NetSuite
- **Role lacks Web Services permissions**
- **Integration not configured for SOAP**
- **Tokens generated without SOAP access**

To fix it, you need NetSuite admin to enable features, update permissions, and generate new tokens. However, since you already have full data access via SuiteQL, this may not be worth the effort unless you specifically need to run existing saved searches by their ID.

---
*Analysis completed: 2025-08-25*