#!/usr/bin/env python3
"""
Sales Order Management Template for Odoo
Complete examples for managing sales orders, quotations, and order lines
"""

import asyncio
from datetime import datetime, timedelta
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from odoo_connection import OdooConnection


class OdooSalesManager:
    """Sales order management operations for Odoo."""
    
    def __init__(self, connection: OdooConnection):
        self.odoo = connection
        
    async def sales_overview(self):
        """Get overview of sales in the system."""
        print("\n" + "="*60)
        print("SALES OVERVIEW")
        print("="*60)
        
        # Count orders by state
        print("\n📊 Sales Orders by State:")
        
        states = [
            ('draft', 'Draft Quotation'),
            ('sent', 'Quotation Sent'),
            ('sale', 'Sales Order'),
            ('done', 'Locked'),
            ('cancel', 'Cancelled')
        ]
        
        total_orders = 0
        for state_code, state_name in states:
            count = await self.odoo.search_count('sale.order', [
                ['state', '=', state_code]
            ])
            total_orders += count
            print(f"   {state_name}: {count}")
            
        print(f"\n   Total Orders: {total_orders}")
        
        # Recent sales statistics
        print("\n📈 Recent Sales Statistics:")
        
        # Last 30 days
        thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        recent_orders = await self.odoo.search_count('sale.order', [
            ['date_order', '>=', thirty_days_ago],
            ['state', 'in', ['sale', 'done']]
        ])
        print(f"   Confirmed orders (last 30 days): {recent_orders}")
        
        # Today's orders
        today = datetime.now().strftime('%Y-%m-%d')
        today_orders = await self.odoo.search_count('sale.order', [
            ['date_order', '>=', today],
        ])
        print(f"   Orders created today: {today_orders}")
        
        # Get top customers (can't search by computed fields like sale_order_count)
        print("\n👥 Top Customers:")
        top_customers = await self.odoo.search_read(
            'res.partner',
            [['customer_rank', '>', 0]],
            ['name', 'customer_rank'],
            limit=5,
            order='customer_rank desc'
        )
        
        for customer in top_customers:
            print(f"   - {customer['name']}: Customer rank {customer['customer_rank']}")
            
    async def create_simple_order(self):
        """Create a simple sales order."""
        print("\n" + "="*60)
        print("CREATE SIMPLE SALES ORDER")
        print("="*60)
        
        # First, find a customer
        print("\n1️⃣ Finding customer...")
        customer_ids = await self.odoo.search('res.partner', [
            ['is_company', '=', True],
            ['customer_rank', '>', 0]
        ], limit=1)
        
        if not customer_ids:
            # Create a test customer
            print("   No customer found, creating test customer...")
            customer_id = await self.odoo.create('res.partner', {
                'name': f'Test Customer {datetime.now().strftime("%Y%m%d_%H%M%S")}',
                'is_company': True,
                'customer_rank': 1,
            })
        else:
            customer_id = customer_ids[0]
            
        customer = await self.odoo.read('res.partner', [customer_id], ['name'])
        print(f"   Using customer: {customer[0]['name']}")
        
        # Find products to sell
        print("\n2️⃣ Finding products...")
        product_ids = await self.odoo.search('product.product', [
            ['sale_ok', '=', True],
            ['list_price', '>', 0]
        ], limit=2)
        
        if len(product_ids) < 2:
            print("   Not enough products, creating test products...")
            # Create test products
            product1_id = await self.odoo.create('product.product', {
                'name': 'Test Product 1',
                'list_price': 100.00,
                'type': 'consu',
                'sale_ok': True,
            })
            product2_id = await self.odoo.create('product.product', {
                'name': 'Test Product 2',
                'list_price': 50.00,
                'type': 'consu',
                'sale_ok': True,
            })
            product_ids = [product1_id, product2_id]
            
        products = await self.odoo.read('product.product', product_ids, 
                                       ['name', 'list_price'])
        
        print("   Products to add:")
        for product in products:
            print(f"   - {product['name']}: ${product['list_price']:.2f}")
            
        # Create sales order
        print("\n3️⃣ Creating sales order...")
        
        order_data = {
            'partner_id': customer_id,
            'date_order': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'validity_date': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
            'order_line': [
                (0, 0, {
                    'product_id': products[0]['id'],
                    'product_uom_qty': 2,
                    'price_unit': products[0]['list_price'],
                }),
                (0, 0, {
                    'product_id': products[1]['id'],
                    'product_uom_qty': 5,
                    'price_unit': products[1]['list_price'],
                })
            ]
        }
        
        order_id = await self.odoo.create('sale.order', order_data)
        print(f"   ✅ Created sales order ID: {order_id}")
        
        # Read the created order
        order = await self.odoo.read('sale.order', [order_id], 
                                    ['name', 'state', 'amount_total', 'amount_tax', 
                                     'amount_untaxed', 'date_order'])
        
        order_info = order[0]
        print(f"\n📋 Order Details:")
        print(f"   - Order Number: {order_info['name']}")
        print(f"   - State: {order_info['state']}")
        print(f"   - Untaxed Amount: ${order_info['amount_untaxed']:.2f}")
        print(f"   - Tax: ${order_info['amount_tax']:.2f}")
        print(f"   - Total: ${order_info['amount_total']:.2f}")
        
        return order_id
        
    async def manage_order_lifecycle(self, order_id=None):
        """Demonstrate order lifecycle management."""
        print("\n" + "="*60)
        print("ORDER LIFECYCLE MANAGEMENT")
        print("="*60)
        
        # Create an order if not provided
        if not order_id:
            order_id = await self.create_simple_order()
            
        # Get order details
        order = await self.odoo.read('sale.order', [order_id], 
                                    ['name', 'state', 'partner_id'])
        order_info = order[0]
        
        print(f"\n📋 Managing Order: {order_info['name']}")
        print(f"   Current State: {order_info['state']}")
        
        # If order is in draft, confirm it
        if order_info['state'] == 'draft':
            print("\n✅ Confirming order...")
            try:
                # Confirm the order (action_confirm method)
                await self.odoo.execute_kw('sale.order', 'action_confirm', [[order_id]])
                
                # Check new state
                order = await self.odoo.read('sale.order', [order_id], ['state'])
                print(f"   New State: {order[0]['state']}")
            except Exception as e:
                print(f"   Could not confirm order: {e}")
                
    async def search_orders_examples(self):
        """Search orders using various criteria."""
        print("\n" + "="*60)
        print("SEARCH ORDERS EXAMPLES")
        print("="*60)
        
        # Search confirmed orders
        print("\n1️⃣ Confirmed Orders")
        confirmed = await self.odoo.search_read(
            'sale.order',
            [['state', '=', 'sale']],
            ['name', 'partner_id', 'amount_total', 'date_order'],
            limit=5,
            order='date_order desc'
        )
        
        if confirmed:
            print(f"   Found {len(confirmed)} confirmed orders:")
            for order in confirmed:
                partner_name = order['partner_id'][1] if order['partner_id'] else 'N/A'
                print(f"   - {order['name']}: {partner_name} - ${order['amount_total']:.2f}")
        else:
            print("   No confirmed orders found")
            
        # Search high-value orders
        print("\n2️⃣ High-Value Orders (> $1000)")
        high_value = await self.odoo.search_read(
            'sale.order',
            [['amount_total', '>', 1000]],
            ['name', 'partner_id', 'amount_total', 'state'],
            limit=5,
            order='amount_total desc'
        )
        
        if high_value:
            print(f"   Found {len(high_value)} high-value orders:")
            for order in high_value:
                partner_name = order['partner_id'][1] if order['partner_id'] else 'N/A'
                print(f"   - {order['name']}: ${order['amount_total']:.2f} ({order['state']})")
        else:
            print("   No high-value orders found")
            
        # Search orders by date range
        print("\n3️⃣ Recent Orders (Last 7 Days)")
        week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        recent = await self.odoo.search_read(
            'sale.order',
            [['date_order', '>=', week_ago]],
            ['name', 'partner_id', 'amount_total', 'date_order', 'state'],
            limit=5,
            order='date_order desc'
        )
        
        if recent:
            print(f"   Found {len(recent)} recent orders:")
            for order in recent:
                partner_name = order['partner_id'][1] if order['partner_id'] else 'N/A'
                date_str = order['date_order'].split(' ')[0] if order['date_order'] else 'N/A'
                print(f"   - {order['name']}: {date_str} - ${order['amount_total']:.2f}")
        else:
            print("   No recent orders found")
            
    async def order_line_management(self):
        """Demonstrate order line management."""
        print("\n" + "="*60)
        print("ORDER LINE MANAGEMENT")
        print("="*60)
        
        # Find an existing draft order or create one
        draft_orders = await self.odoo.search('sale.order', [
            ['state', '=', 'draft']
        ], limit=1)
        
        if draft_orders:
            order_id = draft_orders[0]
            print(f"Using existing draft order ID: {order_id}")
        else:
            print("Creating new order for demonstration...")
            order_id = await self.create_simple_order()
            
        # Read order with lines
        order = await self.odoo.read('sale.order', [order_id], 
                                    ['name', 'order_line', 'amount_total'])
        order_info = order[0]
        
        print(f"\n📋 Order: {order_info['name']}")
        print(f"   Current Total: ${order_info['amount_total']:.2f}")
        print(f"   Number of Lines: {len(order_info['order_line'])}")
        
        # Read order lines
        if order_info['order_line']:
            lines = await self.odoo.read('sale.order.line', 
                                        order_info['order_line'],
                                        ['product_id', 'product_uom_qty', 
                                         'price_unit', 'price_subtotal'])
            
            print("\n   Current Order Lines:")
            for line in lines:
                product_name = line['product_id'][1] if line['product_id'] else 'N/A'
                print(f"   - {product_name}: {line['product_uom_qty']} × ${line['price_unit']:.2f} = ${line['price_subtotal']:.2f}")
                
    async def sales_reporting(self):
        """Generate sales reports and analytics."""
        print("\n" + "="*60)
        print("SALES REPORTING & ANALYTICS")
        print("="*60)
        
        # Sales by month (last 3 months)
        print("\n📊 Sales by Month:")
        
        for i in range(3):
            month_start = (datetime.now().replace(day=1) - timedelta(days=30*i))
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
            month_orders = await self.odoo.search_read(
                'sale.order',
                [
                    ['date_order', '>=', month_start.strftime('%Y-%m-%d')],
                    ['date_order', '<=', month_end.strftime('%Y-%m-%d')],
                    ['state', 'in', ['sale', 'done']]
                ],
                ['amount_total']
            )
            
            total_sales = sum(order['amount_total'] for order in month_orders)
            print(f"   {month_start.strftime('%B %Y')}: ${total_sales:.2f} ({len(month_orders)} orders)")
            
        # Top selling products (if we can access order lines)
        print("\n🏆 Top Selling Products:")
        try:
            # Get all order lines from confirmed orders
            confirmed_orders = await self.odoo.search('sale.order', [
                ['state', 'in', ['sale', 'done']]
            ], limit=100)
            
            if confirmed_orders:
                # Get order lines
                order_lines = []
                for order_id in confirmed_orders[:10]:  # Limit to avoid timeout
                    order = await self.odoo.read('sale.order', [order_id], ['order_line'])
                    if order[0]['order_line']:
                        order_lines.extend(order[0]['order_line'])
                        
                if order_lines:
                    # Read line details
                    lines = await self.odoo.read('sale.order.line', 
                                                order_lines[:50],  # Limit lines
                                                ['product_id', 'product_uom_qty'])
                    
                    # Aggregate by product
                    product_sales = {}
                    for line in lines:
                        if line['product_id']:
                            product_name = line['product_id'][1]
                            product_sales[product_name] = product_sales.get(product_name, 0) + line['product_uom_qty']
                            
                    # Sort and display top 5
                    top_products = sorted(product_sales.items(), key=lambda x: x[1], reverse=True)[:5]
                    for product, qty in top_products:
                        print(f"   - {product}: {qty:.0f} units sold")
                        
        except Exception as e:
            print(f"   Could not generate product report: {e}")


async def main():
    """Main function to run sales order demonstrations."""
    
    async with OdooConnection() as odoo:
        manager = OdooSalesManager(odoo)
        
        try:
            # Run demonstrations
            await manager.sales_overview()
            order_id = await manager.create_simple_order()
            await manager.manage_order_lifecycle(order_id)
            await manager.search_orders_examples()
            await manager.order_line_management()
            await manager.sales_reporting()
            
            print("\n" + "="*60)
            print("✅ SALES ORDER OPERATIONS COMPLETED!")
            print("="*60)
            
        except Exception as e:
            print(f"\n❌ Error during sales operations: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())