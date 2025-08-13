# Odoo Python Templates for Claude Code API

## Overview

This directory contains comprehensive Python templates for interacting with Odoo ERP systems. These templates allow Claude Code API to generate working Python code for any Odoo operation without requiring MCP tools.

## Files

### Core Connection
- **`odoo_connection.py`** - Base connection class with authentication and all CRUD methods

### Operation Templates (Tested & Working)
- **`02_crud_operations.py`** - Complete CRUD examples for partners, products, users
- **`03_search_and_filter.py`** - Search operators, pagination, complex domains
- **`04_product_management.py`** - Product creation, variants, categories, pricing
- **`05_sales_orders.py`** - Sales order creation, lifecycle, reporting
- **`06_invoicing.py`** - Invoice creation, vendor bills, credit notes
- **`07_batch_operations.py`** - Bulk operations, performance optimization, error handling

### Documentation
- **`ODOO_API_GUIDE.md`** - Complete reference guide with all patterns and examples
- **`CLAUDE_ODOO_SYSTEM_PROMPT.md`** - System prompt for Claude Code API

## Quick Start

1. **Set up environment variables** in `.env`:
```env
ODOO_URL=https://your-instance.odoo.com/
ODOO_DATABASE=your-database
ODOO_USERNAME=your-email@example.com
ODOO_PASSWORD=your-password
```

2. **Install dependencies**:
```bash
pip install aiohttp python-dotenv
```

3. **Run any template**:
```bash
python3 odoo_connection.py  # Test connection
python3 02_crud_operations.py  # Test CRUD
python3 03_search_and_filter.py  # Test search
```

## Key Learnings from Testing

### What Works
✅ All basic CRUD operations
✅ Search with domains and operators
✅ Pagination and batch processing
✅ Product management (using 'consu' type)
✅ Sales order creation and management
✅ Invoice creation (with proper fields)
✅ Batch operations with error handling

### Known Limitations
⚠️ Computed fields (like `sale_order_count`) cannot be used in search domains
⚠️ Some fields don't exist (e.g., `mobile` in res.partner)
⚠️ Product type 'product' requires inventory module (use 'consu' instead)
⚠️ User creation requires email-format login on trial instances
⚠️ Some methods like `action_confirm` may require specific permissions

## Common Patterns

### Connection Pattern
```python
async with OdooConnection() as odoo:
    # Your operations here
```

### Search Pattern
```python
# Most efficient - search and read combined
records = await odoo.search_read(
    'model.name',
    [['field', 'operator', value]],
    ['field1', 'field2'],
    limit=10
)
```

### Error Handling Pattern
```python
try:
    result = await odoo.create('model', data)
except Exception as e:
    if "does not exist" in str(e):
        # Handle missing record
    elif "Invalid field" in str(e):
        # Handle field error
```

## Performance Best Practices

1. **Always specify fields** when reading data
2. **Use search_read** instead of search + read
3. **Batch operations** in chunks of 50-100 records
4. **Use pagination** for large datasets
5. **Handle errors** gracefully with try-except

## Module Dependencies

- **Basic Operations**: Work with default Odoo installation
- **Inventory Module**: Required for 'product' type and stock levels
- **Sales Module**: Required for sale.order operations
- **Accounting Module**: Required for invoices (account.move)

## Testing Results

All templates have been tested against a live Odoo instance:
- ✅ Connection and authentication
- ✅ CRUD operations on partners and products
- ✅ Search with various operators and domains
- ✅ Batch operations with 20+ records
- ✅ Performance optimization patterns
- ✅ Error handling and recovery

## Usage with Claude Code API

When users request Odoo operations, Claude Code API should:
1. Import the `odoo_connection.py` module
2. Use async/await patterns
3. Include proper error handling
4. Reference appropriate template for examples
5. Generate complete, runnable Python scripts

## Support

For issues or improvements, refer to:
- The comprehensive `ODOO_API_GUIDE.md`
- The system prompt in `CLAUDE_ODOO_SYSTEM_PROMPT.md`
- The tested examples in each template file