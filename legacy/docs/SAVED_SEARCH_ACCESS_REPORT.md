# NetSuite Saved Search Access Report

## ❌ Saved Searches NOT Directly Accessible via REST API

### Test Results Summary

After comprehensive testing, we've confirmed that **NetSuite saved searches cannot be executed directly via the REST API or SuiteQL**. This is a known limitation of NetSuite's current API architecture.

## 📊 What We Tested

### 1. Direct Saved Search Endpoints
- ❌ `/services/rest/record/v1/savedsearch` - Not found (404)
- ❌ `/services/rest/record/v1/customer/search` - Bad request (400)
- ❌ `/services/rest/record/v1/transaction/search` - Not found (404)
- ❌ `/services/rest/query/v1/savedsearch` - Bad request (400)

### 2. SuiteQL Table Queries
- ❌ `SELECT * FROM savedsearch` - Table doesn't exist
- ❌ `SELECT * FROM customsearch` - Table doesn't exist
- ❌ `SELECT * FROM search` - Table doesn't exist
- ❌ `INFORMATION_SCHEMA` - Not available in SuiteQL

### 3. RESTlet Access
- ❌ `/app/site/hosting/restlet.nl` - Forbidden (403)
- Would require custom SuiteScript deployment

### 4. Metadata Catalog
- ⏱️ Timed out (but wouldn't contain saved searches anyway)
- Only provides record type metadata, not saved searches

### 5. OpenAPI Specification
- ❌ Not accessible (400)
- Would only document available endpoints, not provide saved search access

## 🎯 What This Means

### Cannot Do:
- ❌ Execute existing saved searches by their ID
- ❌ List available saved searches programmatically
- ❌ Access saved search definitions or metadata
- ❌ Use saved search results directly

### Can Do:
- ✅ **Recreate saved search logic using SuiteQL**
- ✅ Access all underlying data (transactions, customers, items)
- ✅ Build complex queries with JOINs and filters
- ✅ Export and analyze data programmatically

## 💡 Recommended Approach

Since you have **full access to the transaction data** (2.1M+ records), you can recreate any saved search using SuiteQL queries. Here's how:

### 1. Identify Saved Search Requirements
Get the saved search criteria from NetSuite UI:
- Record type (e.g., Transaction)
- Filters (e.g., date range, status, type)
- Columns/fields to display
- Sort order

### 2. Convert to SuiteQL
Transform the saved search logic into SQL:

#### Example: Sales Orders This Month
**Saved Search Criteria:**
- Type: Transaction
- Filter: Type = Sales Order, Date = This Month
- Columns: Order#, Date, Customer, Total

**SuiteQL Equivalent:**
```sql
SELECT 
    t.tranid as order_number,
    t.trandate as order_date,
    c.companyname as customer_name,
    t.foreigntotal as total_amount,
    t.status
FROM transaction t
LEFT JOIN customer c ON t.entity = c.id
WHERE t.recordtype = 'salesorder'
AND t.trandate >= '01/08/2025'
AND t.trandate <= '31/08/2025'
ORDER BY t.trandate DESC
```

### 3. Common Saved Search Patterns in SuiteQL

#### Customer Activity Report
```sql
SELECT 
    c.companyname,
    c.email,
    COUNT(t.id) as transaction_count,
    SUM(t.foreigntotal) as total_sales,
    MAX(t.trandate) as last_order_date
FROM customer c
LEFT JOIN transaction t ON c.id = t.entity
WHERE t.recordtype IN ('salesorder', 'invoice')
GROUP BY c.id, c.companyname, c.email
HAVING COUNT(t.id) > 0
ORDER BY total_sales DESC
```

#### Inventory Movement
```sql
SELECT 
    i.itemid,
    i.displayname,
    tl.transaction,
    tl.quantity,
    t.trandate,
    t.recordtype
FROM item i
JOIN transactionline tl ON i.id = tl.item
JOIN transaction t ON tl.transaction = t.id
WHERE t.recordtype IN ('salesorder', 'purchaseorder', 'itemfulfillment')
AND t.trandate >= '01/01/2025'
ORDER BY t.trandate DESC
```

#### Open Sales Orders
```sql
SELECT 
    t.tranid,
    t.trandate,
    c.companyname,
    t.foreigntotal,
    t.status,
    t.shipdate
FROM transaction t
LEFT JOIN customer c ON t.entity = c.id
WHERE t.recordtype = 'salesorder'
AND t.status IN ('A', 'B', 'D', 'E', 'F') -- Pending statuses
ORDER BY t.trandate
```

## 🔧 Alternative Solutions

### Option 1: RESTlet Development
If you absolutely need to run existing saved searches:
1. Create a SuiteScript RESTlet
2. Deploy it to NetSuite
3. Call the RESTlet with saved search ID

**Pros:** Can run exact saved searches
**Cons:** Requires NetSuite admin access and SuiteScript knowledge

### Option 2: Export and Import
1. Export saved search results from NetSuite UI
2. Process the exported CSV/Excel files
3. Automate using scheduled exports

**Pros:** Simple, no coding in NetSuite
**Cons:** Not real-time, manual process

### Option 3: SuiteQL Recreation (Recommended)
1. Use our discovered schema (93 transaction fields)
2. Build equivalent queries in SuiteQL
3. Full programmatic access via REST API

**Pros:** Real-time, flexible, no NetSuite changes needed
**Cons:** Need to recreate search logic

## 📝 Next Steps

1. **List Your Critical Saved Searches**
   - Get their names and IDs from NetSuite UI
   - Document their filters and columns

2. **Convert to SuiteQL**
   - Use the transaction table schema we discovered
   - Test queries with the scripts we created

3. **Automate Data Extraction**
   - Schedule regular data pulls
   - Build dashboards with the extracted data

## 🎯 Summary

While NetSuite doesn't provide direct REST API access to saved searches, you have **complete access to the underlying data** through SuiteQL. With 2.1M+ transaction records and 93 fields available, you can recreate any saved search logic and even build more complex queries than the UI allows.

The key is to think of saved searches as "pre-built queries" that you can rebuild using the powerful SuiteQL interface with your existing TBA credentials.

---

*Report generated: 2025-08-25*
*Based on actual API testing with GYM + Coffee NetSuite instance*