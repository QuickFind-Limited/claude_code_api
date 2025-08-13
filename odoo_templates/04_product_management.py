#!/usr/bin/env python3
"""
Product Management Template for Odoo
Complete examples for managing products, inventory, and pricing
"""

import asyncio
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from odoo_connection import OdooConnection


class OdooProductManager:
    """Product management operations for Odoo."""
    
    def __init__(self, connection: OdooConnection):
        self.odoo = connection
        
    async def product_overview(self):
        """Get overview of products in the system."""
        print("\n" + "="*60)
        print("PRODUCT OVERVIEW")
        print("="*60)
        
        # Count products by type
        print("\n📊 Product Statistics:")
        
        # Total product templates
        total_templates = await self.odoo.search_count('product.template', [])
        print(f"   Total Product Templates: {total_templates}")
        
        # Total product variants
        total_variants = await self.odoo.search_count('product.product', [])
        print(f"   Total Product Variants: {total_variants}")
        
        # Active products
        active_products = await self.odoo.search_count('product.template', [
            ['active', '=', True]
        ])
        print(f"   Active Products: {active_products}")
        
        # Products by type
        print("\n📦 Products by Type:")
        product_types = [
            ('consu', 'Consumable'),
            ('service', 'Service'),
            ('product', 'Storable Product')
        ]
        
        for type_code, type_name in product_types:
            count = await self.odoo.search_count('product.template', [
                ['type', '=', type_code]
            ])
            print(f"   {type_name}: {count}")
            
        # Sales configuration
        print("\n💰 Sales Configuration:")
        can_be_sold = await self.odoo.search_count('product.template', [
            ['sale_ok', '=', True]
        ])
        can_be_purchased = await self.odoo.search_count('product.template', [
            ['purchase_ok', '=', True]
        ])
        print(f"   Can be Sold: {can_be_sold}")
        print(f"   Can be Purchased: {can_be_purchased}")
        
    async def create_product_examples(self):
        """Create different types of products."""
        print("\n" + "="*60)
        print("CREATE PRODUCT EXAMPLES")
        print("="*60)
        
        created_products = []
        
        # Create a consumable product
        print("\n1️⃣ Creating Consumable Product...")
        consumable = {
            'name': f'Test Consumable {datetime.now().strftime("%Y%m%d_%H%M%S")}',
            'type': 'consu',
            'list_price': 25.00,
            'standard_price': 10.00,
            'categ_id': 1,  # Default category
            'sale_ok': True,
            'purchase_ok': True,
            'description': 'A consumable product that does not require inventory tracking',
            'description_sale': 'High-quality consumable item',
            'weight': 0.5,
            'volume': 0.001,
            'barcode': f'CONS{datetime.now().strftime("%Y%m%d%H%M%S")}',
        }
        
        consumable_id = await self.odoo.create('product.template', consumable)
        created_products.append(('product.template', consumable_id))
        print(f"   ✅ Created consumable product (ID: {consumable_id})")
        
        # Create a service product
        print("\n2️⃣ Creating Service Product...")
        service = {
            'name': f'Test Service {datetime.now().strftime("%Y%m%d_%H%M%S")}',
            'type': 'service',
            'list_price': 150.00,
            'standard_price': 0.00,  # Services typically don't have cost
            'categ_id': 1,
            'sale_ok': True,
            'purchase_ok': False,  # Services usually not purchased
            'description': 'Professional consulting service',
            'description_sale': 'Expert consultation and support services',
        }
        
        service_id = await self.odoo.create('product.template', service)
        created_products.append(('product.template', service_id))
        print(f"   ✅ Created service product (ID: {service_id})")
        
        # Create a storable product (Note: 'product' type requires stock module)
        print("\n3️⃣ Creating Storable Product...")
        storable = {
            'name': f'Test Storable {datetime.now().strftime("%Y%m%d_%H%M%S")}',
            'type': 'consu',  # Using consumable as fallback if stock module not installed
            'list_price': 99.99,
            'standard_price': 45.00,
            'categ_id': 1,
            'sale_ok': True,
            'purchase_ok': True,
            'description': 'A physical product with inventory tracking',
            'description_sale': 'Premium quality physical product',
            'weight': 2.5,
            'volume': 0.01,
            'barcode': f'STOR{datetime.now().strftime("%Y%m%d%H%M%S")}',
        }
        
        storable_id = await self.odoo.create('product.template', storable)
        created_products.append(('product.template', storable_id))
        print(f"   ✅ Created storable product (ID: {storable_id})")
        
        return created_products
        
    async def product_variants_example(self):
        """Demonstrate product variants (product.product vs product.template)."""
        print("\n" + "="*60)
        print("PRODUCT VARIANTS")
        print("="*60)
        
        # Create a product template with variants
        print("\n📦 Creating Product Template with Variants...")
        
        # Note: Creating actual variants requires attribute configuration
        # This example shows the relationship between template and product
        
        # Create template
        template_data = {
            'name': f'T-Shirt {datetime.now().strftime("%Y%m%d_%H%M%S")}',
            'type': 'product',
            'list_price': 29.99,
            'standard_price': 12.00,
            'categ_id': 1,
            'sale_ok': True,
        }
        
        template_id = await self.odoo.create('product.template', template_data)
        print(f"   Created template (ID: {template_id})")
        
        # Get the automatically created product variant
        variant_ids = await self.odoo.search('product.product', [
            ['product_tmpl_id', '=', template_id]
        ])
        
        if variant_ids:
            print(f"   Found {len(variant_ids)} variant(s) for this template")
            
            # Read variant details
            variants = await self.odoo.read('product.product', variant_ids, 
                                           ['name', 'default_code', 'barcode', 'list_price'])
            
            for variant in variants:
                print(f"\n   Variant: {variant['name']}")
                print(f"   - ID: {variant['id']}")
                print(f"   - Price: ${variant['list_price']}")
                print(f"   - SKU: {variant.get('default_code', 'N/A')}")
                
        # Clean up
        await self.odoo.unlink('product.template', [template_id])
        
    async def update_product_prices(self):
        """Demonstrate bulk price updates."""
        print("\n" + "="*60)
        print("BULK PRICE UPDATE")
        print("="*60)
        
        # Create test products
        print("\n📦 Creating test products for price update...")
        product_ids = []
        
        for i in range(3):
            product = {
                'name': f'Price Test Product {i+1}',
                'type': 'consu',
                'list_price': 50.00 * (i + 1),
                'standard_price': 25.00 * (i + 1),
                'sale_ok': True,
            }
            pid = await self.odoo.create('product.template', product)
            product_ids.append(pid)
            print(f"   Created product {i+1} with price ${50.00 * (i + 1)}")
            
        # Apply bulk discount
        print("\n💰 Applying 20% discount to all products...")
        
        for pid in product_ids:
            # Read current price
            product = await self.odoo.read('product.template', [pid], ['list_price'])
            current_price = product[0]['list_price']
            new_price = current_price * 0.8  # 20% discount
            
            # Update price
            await self.odoo.write('product.template', [pid], {
                'list_price': new_price
            })
            print(f"   Updated product {pid}: ${current_price:.2f} → ${new_price:.2f}")
            
        # Clean up
        await self.odoo.unlink('product.template', product_ids)
        print("\n✅ Test products cleaned up")
        
    async def search_products_by_criteria(self):
        """Search products using various criteria."""
        print("\n" + "="*60)
        print("PRODUCT SEARCH EXAMPLES")
        print("="*60)
        
        # Search by name pattern
        print("\n1️⃣ Search by Name Pattern")
        coffee_products = await self.odoo.search_read(
            'product.template',
            [['name', 'ilike', '%coffee%']],
            ['name', 'list_price', 'type'],
            limit=5
        )
        
        if coffee_products:
            print(f"   Found {len(coffee_products)} coffee-related products:")
            for product in coffee_products:
                print(f"   - {product['name']}: ${product['list_price']:.2f}")
        else:
            print("   No coffee products found")
            
        # Search by price range
        print("\n2️⃣ Search by Price Range ($10-$50)")
        mid_range = await self.odoo.search_read(
            'product.template',
            [
                ['list_price', '>=', 10],
                ['list_price', '<=', 50],
                ['sale_ok', '=', True]
            ],
            ['name', 'list_price'],
            limit=5,
            order='list_price asc'
        )
        
        if mid_range:
            print(f"   Found {len(mid_range)} products in range:")
            for product in mid_range:
                print(f"   - {product['name']}: ${product['list_price']:.2f}")
        else:
            print("   No products in this price range")
            
        # Search products with low stock (if inventory module is installed)
        print("\n3️⃣ Products by Availability")
        try:
            # This requires inventory module
            low_stock = await self.odoo.search_read(
                'product.product',
                [
                    ['type', '=', 'product'],  # Only storable products
                ],
                ['name', 'qty_available', 'virtual_available'],
                limit=5,
                order='qty_available asc'
            )
            
            if low_stock:
                print(f"   Products with lowest stock:")
                for product in low_stock:
                    print(f"   - {product['name']}: {product['qty_available']} available")
        except Exception as e:
            print(f"   Stock information not available: {e}")
            
    async def product_categories(self):
        """Work with product categories."""
        print("\n" + "="*60)
        print("PRODUCT CATEGORIES")
        print("="*60)
        
        # Get all categories
        print("\n📂 Product Categories:")
        categories = await self.odoo.search_read(
            'product.category',
            [],
            ['name', 'parent_id', 'product_count'],
            limit=10
        )
        
        for category in categories:
            parent = category['parent_id'][1] if category['parent_id'] else 'Root'
            print(f"   - {category['name']} (Parent: {parent})")
            
        # Count products per category
        print("\n📊 Products per Category:")
        for category in categories[:5]:  # First 5 categories
            product_count = await self.odoo.search_count('product.template', [
                ['categ_id', '=', category['id']]
            ])
            print(f"   - {category['name']}: {product_count} products")
            
    async def product_fields_info(self):
        """Get information about product fields."""
        print("\n" + "="*60)
        print("PRODUCT FIELD INFORMATION")
        print("="*60)
        
        # Get field definitions
        print("\n📋 Key Product Fields:")
        
        # Get fields but limit the output
        fields = await self.odoo.fields_get('product.template', 
                                           ['string', 'type', 'required', 'readonly'])
        
        # Show only important fields
        important_fields = [
            'name', 'type', 'list_price', 'standard_price', 
            'categ_id', 'sale_ok', 'purchase_ok', 'active',
            'qty_available', 'barcode', 'default_code'
        ]
        
        for field_name in important_fields:
            if field_name in fields:
                field = fields[field_name]
                print(f"\n   {field_name}:")
                print(f"   - Label: {field.get('string', 'N/A')}")
                print(f"   - Type: {field.get('type', 'N/A')}")
                print(f"   - Required: {field.get('required', False)}")
                print(f"   - Readonly: {field.get('readonly', False)}")


async def main():
    """Main function to run product management demonstrations."""
    
    async with OdooConnection() as odoo:
        manager = OdooProductManager(odoo)
        
        try:
            # Run demonstrations
            await manager.product_overview()
            created = await manager.create_product_examples()
            await manager.product_variants_example()
            await manager.update_product_prices()
            await manager.search_products_by_criteria()
            await manager.product_categories()
            await manager.product_fields_info()
            
            # Clean up created products
            print("\n🧹 Cleaning up test products...")
            for model, record_id in created:
                try:
                    await odoo.unlink(model, [record_id])
                    print(f"   Deleted {model} ID {record_id}")
                except:
                    pass  # Already deleted or doesn't exist
                    
            print("\n" + "="*60)
            print("✅ PRODUCT MANAGEMENT OPERATIONS COMPLETED!")
            print("="*60)
            
        except Exception as e:
            print(f"\n❌ Error during product operations: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())