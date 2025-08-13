#!/usr/bin/env python3
"""
Search and Filter Operations Template for Odoo
Comprehensive examples of searching, filtering, and querying data
"""

import asyncio
from datetime import datetime, timedelta
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from odoo_connection import OdooConnection


class OdooSearch:
    """Search and filter operations for Odoo."""
    
    def __init__(self, connection: OdooConnection):
        self.odoo = connection
        
    async def basic_search_examples(self):
        """Basic search operations."""
        print("\n" + "="*60)
        print("BASIC SEARCH OPERATIONS")
        print("="*60)
        
        # Simple equality search
        print("\n1️⃣ Simple Equality Search")
        company_ids = await self.odoo.search('res.partner', [['is_company', '=', True]])
        print(f"   Found {len(company_ids)} companies")
        
        # Multiple conditions (AND)
        print("\n2️⃣ Multiple Conditions (AND)")
        customer_companies = await self.odoo.search('res.partner', [
            ['is_company', '=', True],
            ['customer_rank', '>', 0]
        ])
        print(f"   Found {len(customer_companies)} customer companies")
        
        # OR conditions
        print("\n3️⃣ OR Conditions")
        customers_or_suppliers = await self.odoo.search('res.partner', [
            '|',
            ['customer_rank', '>', 0],
            ['supplier_rank', '>', 0]
        ])
        print(f"   Found {len(customers_or_suppliers)} customers or suppliers")
        
        # Complex nested conditions
        print("\n4️⃣ Complex Nested Conditions")
        complex_search = await self.odoo.search('res.partner', [
            '&',
            ['is_company', '=', True],
            '|',
            ['customer_rank', '>', 5],
            ['supplier_rank', '>', 5]
        ])
        print(f"   Found {len(complex_search)} companies with high ranking")
        
        # NOT conditions
        print("\n5️⃣ NOT Conditions")
        no_email = await self.odoo.search('res.partner', [
            ['email', '=', False],
            ['is_company', '=', True]
        ])
        print(f"   Found {len(no_email)} companies without email")
        
    async def search_operators_demo(self):
        """Demonstrate different search operators."""
        print("\n" + "="*60)
        print("SEARCH OPERATORS")
        print("="*60)
        
        # LIKE operator (case-sensitive pattern matching)
        print("\n1️⃣ LIKE Operator (case-sensitive)")
        like_search = await self.odoo.search('res.partner', [
            ['name', 'like', '%Coffee%']
        ])
        print(f"   Found {len(like_search)} partners with 'Coffee' in name")
        
        # ILIKE operator (case-insensitive pattern matching)
        print("\n2️⃣ ILIKE Operator (case-insensitive)")
        ilike_search = await self.odoo.search('res.partner', [
            ['email', 'ilike', '%@gmail.com']
        ])
        print(f"   Found {len(ilike_search)} partners with Gmail addresses")
        
        # IN operator
        print("\n3️⃣ IN Operator")
        specific_ids = [1, 2, 3, 4, 5]
        in_search = await self.odoo.search('res.partner', [
            ['id', 'in', specific_ids]
        ])
        print(f"   Found {len(in_search)} partners with IDs in {specific_ids}")
        
        # NOT IN operator
        print("\n4️⃣ NOT IN Operator")
        not_in_search = await self.odoo.search('res.partner', [
            ['id', 'not in', specific_ids]
        ], limit=10)
        print(f"   Found partners with IDs not in {specific_ids} (limited to 10)")
        
        # Comparison operators
        print("\n5️⃣ Comparison Operators")
        greater_than = await self.odoo.search('res.partner', [
            ['customer_rank', '>', 10]
        ])
        print(f"   Found {len(greater_than)} partners with customer_rank > 10")
        
        less_than = await self.odoo.search('res.partner', [
            ['customer_rank', '<', 5],
            ['customer_rank', '>', 0]
        ])
        print(f"   Found {len(less_than)} partners with 0 < customer_rank < 5")
        
    async def search_with_pagination(self):
        """Demonstrate pagination in search results."""
        print("\n" + "="*60)
        print("PAGINATION IN SEARCH")
        print("="*60)
        
        # Get total count first
        total_count = await self.odoo.search_count('res.partner', [])
        print(f"\n📊 Total partners in database: {total_count}")
        
        # Page 1: First 10 records
        print("\n📄 Page 1 (First 10 records)")
        page1_ids = await self.odoo.search('res.partner', [], limit=10, offset=0, order='id asc')
        page1_data = await self.odoo.read('res.partner', page1_ids, ['name', 'email'])
        for partner in page1_data[:3]:  # Show first 3
            print(f"   - {partner['name']}: {partner.get('email', 'No email')}")
        print(f"   ... and {len(page1_data)-3} more")
        
        # Page 2: Next 10 records
        print("\n📄 Page 2 (Records 11-20)")
        page2_ids = await self.odoo.search('res.partner', [], limit=10, offset=10, order='id asc')
        page2_data = await self.odoo.read('res.partner', page2_ids, ['name', 'email'])
        for partner in page2_data[:3]:  # Show first 3
            print(f"   - {partner['name']}: {partner.get('email', 'No email')}")
        print(f"   ... and {len(page2_data)-3} more")
        
    async def search_and_read_combined(self):
        """Demonstrate search_read for efficiency."""
        print("\n" + "="*60)
        print("SEARCH AND READ COMBINED")
        print("="*60)
        
        # Search and read in one operation
        print("\n🔍 Search and Read Companies")
        companies = await self.odoo.search_read(
            'res.partner',
            [['is_company', '=', True]],
            ['name', 'email', 'phone', 'website', 'customer_rank'],
            limit=5,
            order='customer_rank desc'
        )
        
        print(f"\nTop 5 companies by customer rank:")
        for company in companies:
            print(f"\n   Company: {company['name']}")
            print(f"   - ID: {company['id']}")
            print(f"   - Customer Rank: {company['customer_rank']}")
            print(f"   - Email: {company.get('email', 'N/A')}")
            print(f"   - Website: {company.get('website', 'N/A')}")
            
    async def product_search_examples(self):
        """Product-specific search examples."""
        print("\n" + "="*60)
        print("PRODUCT SEARCH EXAMPLES")
        print("="*60)
        
        # Count all products
        total_products = await self.odoo.search_count('product.template', [])
        print(f"\n📦 Total product templates: {total_products}")
        
        # Search saleable products
        print("\n1️⃣ Saleable Products")
        saleable = await self.odoo.search('product.template', [
            ['sale_ok', '=', True]
        ])
        print(f"   Found {len(saleable)} saleable products")
        
        # Search purchasable products
        print("\n2️⃣ Purchasable Products")
        purchasable = await self.odoo.search('product.template', [
            ['purchase_ok', '=', True]
        ])
        print(f"   Found {len(purchasable)} purchasable products")
        
        # Search products by type
        print("\n3️⃣ Products by Type")
        
        # Service products
        services = await self.odoo.search_count('product.template', [
            ['type', '=', 'service']
        ])
        print(f"   Services: {services}")
        
        # Consumable products
        consumables = await self.odoo.search_count('product.template', [
            ['type', '=', 'consu']
        ])
        print(f"   Consumables: {consumables}")
        
        # Storable products
        storable = await self.odoo.search_count('product.template', [
            ['type', '=', 'product']
        ])
        print(f"   Storable Products: {storable}")
        
        # Search products with specific criteria
        print("\n4️⃣ Products with Price Range")
        mid_range_products = await self.odoo.search_read(
            'product.template',
            [
                ['list_price', '>', 10],
                ['list_price', '<', 100],
                ['sale_ok', '=', True]
            ],
            ['name', 'list_price', 'type'],
            limit=5,
            order='list_price desc'
        )
        
        print(f"   Found products between $10 and $100:")
        for product in mid_range_products:
            print(f"   - {product['name']}: ${product['list_price']:.2f} ({product['type']})")
            
    async def sales_order_search(self):
        """Sales order search examples."""
        print("\n" + "="*60)
        print("SALES ORDER SEARCH")
        print("="*60)
        
        # Count orders by state
        print("\n📊 Orders by State:")
        
        states = [
            ('draft', 'Quotation'),
            ('sent', 'Quotation Sent'),
            ('sale', 'Sales Order'),
            ('done', 'Locked'),
            ('cancel', 'Cancelled')
        ]
        
        for state_code, state_name in states:
            count = await self.odoo.search_count('sale.order', [
                ['state', '=', state_code]
            ])
            print(f"   {state_name}: {count}")
            
        # Recent orders
        print("\n🕐 Recent Orders (Last 30 days)")
        thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        recent_orders = await self.odoo.search_count('sale.order', [
            ['date_order', '>=', thirty_days_ago]
        ])
        print(f"   Orders in last 30 days: {recent_orders}")
        
        # High-value orders
        print("\n💰 High-Value Orders")
        high_value = await self.odoo.search_read(
            'sale.order',
            [['amount_total', '>', 1000]],
            ['name', 'partner_id', 'amount_total', 'date_order', 'state'],
            limit=5,
            order='amount_total desc'
        )
        
        if high_value:
            print(f"   Top {len(high_value)} high-value orders:")
            for order in high_value:
                partner_name = order['partner_id'][1] if order['partner_id'] else 'N/A'
                print(f"   - {order['name']}: ${order['amount_total']:.2f} - {partner_name} ({order['state']})")
                
    async def advanced_domain_examples(self):
        """Advanced domain construction examples."""
        print("\n" + "="*60)
        print("ADVANCED DOMAIN EXAMPLES")
        print("="*60)
        
        # Example 1: Complex nested conditions
        print("\n1️⃣ Complex Nested Domain")
        # Find: Companies that are either (customers with rank > 5) OR (suppliers with email)
        complex_domain = [
            ['is_company', '=', True],
            '|',
            '&',
            ['customer_rank', '>', 5],
            ['customer_rank', '!=', False],
            '&',
            ['supplier_rank', '>', 0],
            ['email', '!=', False]
        ]
        
        result = await self.odoo.search_count('res.partner', complex_domain)
        print(f"   Found {result} companies matching complex criteria")
        
        # Example 2: Date range queries
        print("\n2️⃣ Date Range Queries")
        # Partners created in the last 7 days
        seven_days_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
        new_partners = await self.odoo.search_count('res.partner', [
            ['create_date', '>=', seven_days_ago]
        ])
        print(f"   Partners created in last 7 days: {new_partners}")
        
        # Example 3: Child of queries
        print("\n3️⃣ Child Of Queries")
        # Find all partners that are children of companies
        child_contacts = await self.odoo.search_count('res.partner', [
            ['is_company', '=', False],
            ['parent_id', '!=', False]
        ])
        print(f"   Contact persons linked to companies: {child_contacts}")
        
        # Example 4: Many2many field searches
        print("\n4️⃣ Many2many Field Search")
        # Find partners with specific tags (if tags are configured)
        try:
            # First, let's see if there are any tags
            tag_count = await self.odoo.search_count('res.partner.category', [])
            print(f"   Partner tags available: {tag_count}")
            
            if tag_count > 0:
                # Get first tag
                tag_ids = await self.odoo.search('res.partner.category', [], limit=1)
                if tag_ids:
                    partners_with_tag = await self.odoo.search_count('res.partner', [
                        ['category_id', 'in', tag_ids]
                    ])
                    print(f"   Partners with specific tag: {partners_with_tag}")
        except:
            print(f"   Partner tags not available or accessible")


async def main():
    """Main function to run search demonstrations."""
    
    async with OdooConnection() as odoo:
        search = OdooSearch(odoo)
        
        try:
            # Run all search demonstrations
            await search.basic_search_examples()
            await search.search_operators_demo()
            await search.search_with_pagination()
            await search.search_and_read_combined()
            await search.product_search_examples()
            await search.sales_order_search()
            await search.advanced_domain_examples()
            
            print("\n" + "="*60)
            print("✅ ALL SEARCH OPERATIONS COMPLETED SUCCESSFULLY!")
            print("="*60)
            
        except Exception as e:
            print(f"\n❌ Error during search operations: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())