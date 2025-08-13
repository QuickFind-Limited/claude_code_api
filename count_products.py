#!/usr/bin/env python3
"""
Count Products in Odoo

A simple script to count all products in an Odoo instance.
Uses the Odoo JSON-RPC API with async/await for efficient operations.

Requirements:
- Python 3.7+
- aiohttp
- python-dotenv

Environment variables (create .env file):
- ODOO_URL=https://your-odoo-instance.com
- ODOO_DATABASE=your_database_name
- ODOO_USERNAME=your_username
- ODOO_PASSWORD=your_password
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from odoo_templates.odoo_connection import OdooConnection


async def count_all_products():
    """Count all products in Odoo and display detailed statistics."""
    
    print("🔍 Connecting to Odoo and counting products...")
    print("=" * 60)
    
    async with OdooConnection() as odoo:
        try:
            # Count product templates (main products)
            print("\n📦 Product Templates:")
            total_templates = await odoo.search_count('product.template', [])
            print(f"   Total Product Templates: {total_templates}")
            
            # Count active templates
            active_templates = await odoo.search_count('product.template', [
                ['active', '=', True]
            ])
            print(f"   Active Product Templates: {active_templates}")
            
            # Count inactive templates
            inactive_templates = total_templates - active_templates
            print(f"   Inactive Product Templates: {inactive_templates}")
            
            # Count product variants (specific SKUs)
            print("\n🔢 Product Variants:")
            total_variants = await odoo.search_count('product.product', [])
            print(f"   Total Product Variants: {total_variants}")
            
            # Count active variants
            active_variants = await odoo.search_count('product.product', [
                ['active', '=', True]
            ])
            print(f"   Active Product Variants: {active_variants}")
            
            # Count by product type
            print("\n📊 Products by Type:")
            product_types = [
                ('consu', 'Consumable'),
                ('service', 'Service'), 
                ('product', 'Storable Product')
            ]
            
            for type_code, type_name in product_types:
                count = await odoo.search_count('product.template', [
                    ['type', '=', type_code]
                ])
                print(f"   {type_name}: {count}")
            
            # Count by sales configuration
            print("\n💰 Sales Configuration:")
            can_be_sold = await odoo.search_count('product.template', [
                ['sale_ok', '=', True]
            ])
            can_be_purchased = await odoo.search_count('product.template', [
                ['purchase_ok', '=', True]
            ])
            print(f"   Can be Sold: {can_be_sold}")
            print(f"   Can be Purchased: {can_be_purchased}")
            
            # Summary
            print("\n" + "=" * 60)
            print("📋 SUMMARY:")
            print(f"   🏷️  Product Templates: {total_templates}")
            print(f"   🔢  Product Variants: {total_variants}")
            print(f"   ✅  Active Products: {active_templates}")
            print(f"   💰  Sellable Products: {can_be_sold}")
            print("=" * 60)
            
            return {
                'total_templates': total_templates,
                'active_templates': active_templates,
                'total_variants': total_variants,
                'active_variants': active_variants,
                'sellable_products': can_be_sold,
                'purchasable_products': can_be_purchased
            }
            
        except Exception as e:
            print(f"❌ Error counting products: {e}")
            import traceback
            traceback.print_exc()
            return None


async def count_products_simple():
    """Simple product count - just the total number."""
    
    async with OdooConnection() as odoo:
        try:
            count = await odoo.search_count('product.template')
            print(f"Total products in Odoo: {count}")
            return count
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return None


async def main():
    """Main function - choose between detailed or simple count."""
    
    print("🚀 Odoo Product Counter")
    print("Choose operation:")
    print("1. Detailed product count (recommended)")
    print("2. Simple count only")
    
    if len(sys.argv) > 1 and sys.argv[1] == "--simple":
        choice = "2"
    else:
        choice = input("\nEnter choice (1 or 2, default=1): ").strip() or "1"
    
    if choice == "2":
        await count_products_simple()
    else:
        await count_all_products()


if __name__ == "__main__":
    # Handle command line arguments
    if len(sys.argv) > 1 and sys.argv[1] in ["--help", "-h"]:
        print(__doc__)
        sys.exit(0)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Operation cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)