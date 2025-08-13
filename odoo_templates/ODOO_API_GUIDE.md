# Comprehensive Odoo API Guide for Claude Code

## Overview

This guide provides complete instructions for interacting with Odoo ERP systems using Python. All operations use JSON-RPC protocol over HTTPS.

## Quick Reference

### Essential Information
- **Instance ID**: Always use `"default"` unless specified otherwise
- **Database**: Usually matches the subdomain (e.g., `source-gym-plus-coffee` for `source-gym-plus-coffee.odoo.com`)
- **Authentication**: Required before any operation - stores UID for session
- **Connection Pooling**: Use aiohttp with TCPConnector for efficiency

## Core Concepts

### 1. Models
Odoo uses models to represent business objects:
- `res.partner` - Contacts (customers, suppliers, companies, individuals)
- `product.template` - Product templates (master products)
- `product.product` - Product variants (actual sellable items)
- `sale.order` - Sales orders and quotations
- `sale.order.line` - Sales order lines
- `account.move` - Invoices, bills, journal entries
- `res.users` - System users
- `product.category` - Product categories

### 2. Field Types
- `Char` - Text fields (name, email)
- `Text` - Long text (description, notes)
- `Integer` - Whole numbers (quantity)
- `Float` - Decimal numbers (price, weight)
- `Boolean` - True/False (active, is_company)
- `Date` / `Datetime` - Date values
- `Many2one` - Reference to single record (returns [id, name])
- `One2many` / `Many2many` - List of record IDs

### 3. Domain Syntax
Odoo uses Polish notation for search domains:
```python
# Simple conditions
[['field', 'operator', value]]

# AND (implicit)
[['field1', '=', value1], ['field2', '=', value2]]

# OR
['|', ['field1', '=', value1], ['field2', '=', value2]]

# Complex
['&', ['active', '=', True], '|', ['customer_rank', '>', 0], ['supplier_rank', '>', 0]]
```

### Common Operators
- `=`, `!=` - Equality
- `>`, `>=`, `<`, `<=` - Comparison
- `like`, `ilike` - Pattern matching (% as wildcard)
- `in`, `not in` - List membership
- `=?` - Equals or unset

## Connection Setup

```python
import asyncio
import aiohttp
import os
from dotenv import load_dotenv

load_dotenv()

class OdooConnection:
    def __init__(self):
        self.url = os.getenv("ODOO_URL")
        self.database = os.getenv("ODOO_DATABASE")
        self.username = os.getenv("ODOO_USERNAME")
        self.password = os.getenv("ODOO_PASSWORD")
        self.uid = None
        self.session = None
        
    async def connect(self):
        self.connector = aiohttp.TCPConnector(limit=10, force_close=True)
        self.session = aiohttp.ClientSession(
            connector=self.connector,
            timeout=aiohttp.ClientTimeout(total=30)
        )
        await self.authenticate()
        
    async def authenticate(self):
        auth_url = f"{self.url}/jsonrpc"
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "service": "common",
                "method": "authenticate",
                "args": [self.database, self.username, self.password, {}],
            },
            "id": 1,
        }
        async with self.session.post(auth_url, json=payload) as resp:
            result = await resp.json()
            self.uid = result.get("result")
            return self.uid
```

## CRUD Operations

### CREATE
```python
# Create single record
partner_id = await odoo.execute_kw('res.partner', 'create', [{
    'name': 'ACME Corporation',
    'is_company': True,
    'email': 'info@acme.com',
    'phone': '+1234567890',
    'street': '123 Main St',
    'city': 'New York',
    'customer_rank': 1,  # Mark as customer
}])

# Create with One2many relations (e.g., order with lines)
order_id = await odoo.execute_kw('sale.order', 'create', [{
    'partner_id': customer_id,
    'order_line': [
        (0, 0, {  # (0, 0, values) creates new record
            'product_id': product_id,
            'product_uom_qty': 5,
            'price_unit': 100.00,
        })
    ]
}])
```

### READ
```python
# Read specific fields
partners = await odoo.execute_kw('res.partner', 'read', 
    [[1, 2, 3], ['name', 'email', 'phone']])

# Read all fields (be careful with large models)
partners = await odoo.execute_kw('res.partner', 'read', [[1, 2, 3]])
```

### UPDATE
```python
# Update records
success = await odoo.execute_kw('res.partner', 'write', 
    [[partner_id], {'phone': '+9876543210', 'website': 'https://acme.com'}])

# Update One2many field
await odoo.execute_kw('sale.order', 'write', [[order_id], {
    'order_line': [
        (1, line_id, {'price_unit': 110.00}),  # (1, id, values) updates
        (2, line_id, 0),  # (2, id, 0) deletes
        (0, 0, {'product_id': new_product_id})  # (0, 0, values) creates
    ]
}])
```

### DELETE
```python
# Delete records
success = await odoo.execute_kw('res.partner', 'unlink', [[partner_id]])

# Delete multiple
success = await odoo.execute_kw('res.partner', 'unlink', [partner_ids])
```

## Search Operations

### Basic Search
```python
# Search returns IDs only
partner_ids = await odoo.execute_kw('res.partner', 'search', 
    [[['is_company', '=', True]]])

# With pagination
partner_ids = await odoo.execute_kw('res.partner', 'search',
    [[['customer_rank', '>', 0]]], 
    {'limit': 10, 'offset': 20, 'order': 'name asc'})
```

### Search and Read
```python
# Most efficient for getting data
partners = await odoo.execute_kw('res.partner', 'search_read',
    [[['is_company', '=', True]]],
    {'fields': ['name', 'email', 'phone'], 'limit': 10})
```

### Count
```python
count = await odoo.execute_kw('product.template', 'search_count',
    [[['sale_ok', '=', True]]])
```

## Common Patterns

### Product Management
```python
# Products have two models:
# - product.template: Master product (T-shirt)
# - product.product: Variants (T-shirt Size M Blue)

# Create product
product_id = await odoo.execute_kw('product.template', 'create', [{
    'name': 'Premium Widget',
    'type': 'consu',  # consu/service (inventory module adds 'product')
    'list_price': 99.99,
    'standard_price': 45.00,
    'sale_ok': True,
    'purchase_ok': True,
}])

# Get product with stock info
products = await odoo.execute_kw('product.product', 'search_read',
    [[['type', '=', 'consu']]],
    {'fields': ['name', 'qty_available', 'virtual_available']})
```

### Sales Orders
```python
# Create quotation
order_id = await odoo.execute_kw('sale.order', 'create', [{
    'partner_id': customer_id,
    'order_line': [(0, 0, {
        'product_id': product_id,
        'product_uom_qty': 2,
        'price_unit': product_price,
    })]
}])

# Confirm order (changes state from 'draft' to 'sale')
await odoo.execute_kw('sale.order', 'action_confirm', [[order_id]])

# Order states: draft -> sent -> sale -> done -> cancel
```

### Invoicing
```python
# Create customer invoice
invoice_id = await odoo.execute_kw('account.move', 'create', [{
    'move_type': 'out_invoice',  # out_invoice/out_refund/in_invoice/in_refund
    'partner_id': customer_id,
    'invoice_date': '2025-01-15',
    'invoice_line_ids': [(0, 0, {
        'product_id': product_id,
        'quantity': 3,
        'price_unit': 100.00,
        'name': 'Product description',
    })]
}])

# Post invoice (draft -> posted)
await odoo.execute_kw('account.move', 'action_post', [[invoice_id]])
```

### Batch Operations
```python
# Efficient batch processing
page_size = 100
offset = 0

while True:
    batch_ids = await odoo.execute_kw('res.partner', 'search',
        [domain], {'limit': page_size, 'offset': offset})
    
    if not batch_ids:
        break
        
    # Process batch
    await odoo.execute_kw('res.partner', 'write',
        [batch_ids, {'active': True}])
    
    offset += page_size
```

## Error Handling

```python
try:
    result = await odoo.execute_kw(model, method, args)
except Exception as e:
    if "does not exist" in str(e):
        # Record not found
    elif "Access Denied" in str(e):
        # Permission issue
    elif "ValidationError" in str(e):
        # Data validation failed
    else:
        # Other error
```

## Performance Tips

1. **Always specify fields** when reading - never read all fields unless necessary
2. **Use search_read** instead of search + read
3. **Batch operations** - process records in chunks of 50-100
4. **Connection pooling** - reuse connections with aiohttp
5. **Pagination** - use limit/offset for large datasets
6. **Avoid computed fields** in search domains when possible

## Module Dependencies

Some features require specific Odoo modules:
- **Inventory**: Adds 'product' type, stock levels
- **Sales**: sale.order model
- **Accounting**: account.move for invoices
- **Purchase**: Purchase orders, supplier management

## Common Issues and Solutions

### Issue: "Invalid field" error
**Solution**: Field doesn't exist in model or module not installed

### Issue: "Access Denied"
**Solution**: User lacks permissions for operation

### Issue: "Singleton expected"
**Solution**: Method expects single ID, not list

### Issue: Timeout on large operations
**Solution**: Reduce batch size, increase timeout, paginate

### Issue: "does not exist"
**Solution**: Record deleted or wrong ID

## Template Files

1. `odoo_connection.py` - Base connection class
2. `02_crud_operations.py` - CRUD examples
3. `03_search_and_filter.py` - Search patterns
4. `04_product_management.py` - Product operations
5. `05_sales_orders.py` - Sales management
6. `06_invoicing.py` - Invoice handling
7. `07_batch_operations.py` - Bulk operations

## Quick Start Example

```python
import asyncio
from odoo_connection import OdooConnection

async def main():
    async with OdooConnection() as odoo:
        # Count products
        count = await odoo.search_count('product.template')
        print(f"Total products: {count}")
        
        # Find customers
        customers = await odoo.search_read(
            'res.partner',
            [['customer_rank', '>', 0]],
            ['name', 'email'],
            limit=5
        )
        
        for customer in customers:
            print(f"{customer['name']}: {customer.get('email', 'No email')}")

if __name__ == "__main__":
    asyncio.run(main())
```