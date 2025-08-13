# Odoo Integration Guide

This project includes Python scripts for integrating with Odoo ERP systems using JSON-RPC API.

## Quick Start

### 1. Install Dependencies

```bash
pip install aiohttp python-dotenv
```

### 2. Configure Environment

Copy the example environment file and update with your Odoo credentials:

```bash
cp .env.example .env
# Edit .env with your Odoo instance details
```

### 3. Count Products

Run the product counter script:

```bash
python3 count_products.py
```

Or for a simple count only:

```bash
python3 count_products.py --simple
```

## Available Scripts

### `count_products.py`
Counts all products in your Odoo instance with detailed statistics:
- Total product templates and variants
- Products by type (consumable, service, storable)
- Active vs inactive products
- Sellable vs purchasable products

**Usage:**
```bash
# Detailed count (recommended)
python3 count_products.py

# Simple count only
python3 count_products.py --simple

# Help
python3 count_products.py --help
```

## Odoo Templates

The `odoo_templates/` directory contains comprehensive examples:

- `odoo_connection.py` - Base connection class with async/await
- `02_crud_operations.py` - Create, Read, Update, Delete operations
- `03_search_and_filter.py` - Search patterns and filtering
- `04_product_management.py` - Product operations (like the count script uses)
- `05_sales_orders.py` - Sales order management
- `06_invoicing.py` - Invoice handling
- `07_batch_operations.py` - Bulk operations
- `ODOO_API_GUIDE.md` - Complete API reference

## Key Odoo Models

- `res.partner` - Contacts (customers/suppliers)
- `product.template` - Product templates (main products)
- `product.product` - Product variants (specific SKUs)
- `sale.order` - Sales orders
- `account.move` - Invoices

## Configuration

Required environment variables in `.env`:

```bash
ODOO_URL=https://your-instance.odoo.com
ODOO_DATABASE=your_database_name
ODOO_USERNAME=your.email@company.com
ODOO_PASSWORD=your_password
```

## Features

- **Async/await support** - Efficient concurrent operations
- **Error handling** - Comprehensive error management
- **Connection pooling** - Optimized HTTP connections
- **Environment configuration** - Secure credential management
- **Type safety** - Full type hints for better IDE support

## Security Notes

- Never commit your `.env` file with real credentials
- Use API keys or OAuth when available instead of passwords
- Consider using read-only users for reporting scripts
- Always validate and sanitize input data

## Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Check your credentials in `.env`
   - Ensure the user has API access enabled
   - Verify database name is correct

2. **Connection Timeout**
   - Check your Odoo URL
   - Ensure network connectivity
   - Try increasing timeout in connection settings

3. **Permission Denied**
   - User needs read access to the models you're querying
   - Some fields may require specific access rights

### Getting Help

1. Check the `ODOO_API_GUIDE.md` for detailed API documentation
2. Review the template examples in `odoo_templates/`
3. Enable debug logging to see detailed error messages

## Development

To create new Odoo integration scripts:

1. Import the `OdooConnection` class
2. Use async context manager pattern
3. Follow the examples in the templates
4. Add proper error handling

Example:
```python
from odoo_templates.odoo_connection import OdooConnection

async def my_odoo_operation():
    async with OdooConnection() as odoo:
        # Your operations here
        count = await odoo.search_count('product.template')
        return count
```