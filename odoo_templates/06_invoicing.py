#!/usr/bin/env python3
"""
Invoice Management Template for Odoo
Complete examples for managing invoices, bills, and payments
"""

import asyncio
from datetime import datetime, timedelta
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from odoo_connection import OdooConnection


class OdooInvoiceManager:
    """Invoice management operations for Odoo."""
    
    def __init__(self, connection: OdooConnection):
        self.odoo = connection
        
    async def invoice_overview(self):
        """Get overview of invoices in the system."""
        print("\n" + "="*60)
        print("INVOICE OVERVIEW")
        print("="*60)
        
        # Count invoices by type and state
        print("\n📊 Invoices by Type:")
        
        invoice_types = [
            ('out_invoice', 'Customer Invoice'),
            ('out_refund', 'Customer Credit Note'),
            ('in_invoice', 'Vendor Bill'),
            ('in_refund', 'Vendor Credit Note')
        ]
        
        for move_type, type_name in invoice_types:
            count = await self.odoo.search_count('account.move', [
                ['move_type', '=', move_type]
            ])
            print(f"   {type_name}: {count}")
            
        # Invoice states
        print("\n📈 Invoice States:")
        
        states = [
            ('draft', 'Draft'),
            ('posted', 'Posted'),
            ('cancel', 'Cancelled')
        ]
        
        for state_code, state_name in states:
            count = await self.odoo.search_count('account.move', [
                ['state', '=', state_code],
                ['move_type', 'in', ['out_invoice', 'out_refund', 'in_invoice', 'in_refund']]
            ])
            print(f"   {state_name}: {count}")
            
        # Payment status
        print("\n💰 Payment Status (Customer Invoices):")
        
        payment_states = [
            ('not_paid', 'Not Paid'),
            ('in_payment', 'In Payment'),
            ('paid', 'Paid'),
            ('partial', 'Partially Paid'),
            ('reversed', 'Reversed')
        ]
        
        for payment_state, state_name in payment_states:
            try:
                count = await self.odoo.search_count('account.move', [
                    ['payment_state', '=', payment_state],
                    ['move_type', '=', 'out_invoice']
                ])
                print(f"   {state_name}: {count}")
            except:
                # payment_state field might not be available in all versions
                pass
                
    async def create_simple_invoice(self):
        """Create a simple customer invoice."""
        print("\n" + "="*60)
        print("CREATE SIMPLE CUSTOMER INVOICE")
        print("="*60)
        
        # Find a customer
        print("\n1️⃣ Finding customer...")
        customer_ids = await self.odoo.search('res.partner', [
            ['is_company', '=', True],
            ['customer_rank', '>', 0]
        ], limit=1)
        
        if not customer_ids:
            # Create test customer
            print("   Creating test customer...")
            customer_id = await self.odoo.create('res.partner', {
                'name': f'Invoice Test Customer {datetime.now().strftime("%Y%m%d_%H%M%S")}',
                'is_company': True,
                'customer_rank': 1,
            })
        else:
            customer_id = customer_ids[0]
            
        customer = await self.odoo.read('res.partner', [customer_id], ['name'])
        print(f"   Using customer: {customer[0]['name']}")
        
        # Find products
        print("\n2️⃣ Finding products...")
        product_ids = await self.odoo.search('product.product', [
            ['sale_ok', '=', True],
            ['list_price', '>', 0]
        ], limit=2)
        
        if not product_ids:
            print("   No products found, creating test product...")
            product_id = await self.odoo.create('product.product', {
                'name': 'Invoice Test Product',
                'list_price': 100.00,
                'type': 'consu',
            })
            product_ids = [product_id]
            
        products = await self.odoo.read('product.product', product_ids[:1], 
                                       ['name', 'list_price'])
        
        # Create invoice
        print("\n3️⃣ Creating customer invoice...")
        
        try:
            invoice_data = {
                'move_type': 'out_invoice',
                'partner_id': customer_id,
                'invoice_date': datetime.now().strftime('%Y-%m-%d'),
                'invoice_date_due': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
                'invoice_line_ids': [
                    (0, 0, {
                        'product_id': products[0]['id'],
                        'quantity': 3,
                        'price_unit': products[0]['list_price'],
                        'name': products[0]['name'],
                    })
                ]
            }
            
            invoice_id = await self.odoo.create('account.move', invoice_data)
            print(f"   ✅ Created invoice ID: {invoice_id}")
            
            # Read invoice details
            invoice = await self.odoo.read('account.move', [invoice_id],
                                          ['name', 'state', 'amount_total', 'amount_tax',
                                           'amount_untaxed', 'invoice_date'])
            
            inv = invoice[0]
            print(f"\n📋 Invoice Details:")
            print(f"   - Invoice Number: {inv['name']}")
            print(f"   - State: {inv['state']}")
            print(f"   - Untaxed: ${inv['amount_untaxed']:.2f}")
            print(f"   - Tax: ${inv['amount_tax']:.2f}")
            print(f"   - Total: ${inv['amount_total']:.2f}")
            
            return invoice_id
            
        except Exception as e:
            print(f"   ⚠️ Could not create invoice: {e}")
            return None
            
    async def search_invoices(self):
        """Search invoices using various criteria."""
        print("\n" + "="*60)
        print("SEARCH INVOICES")
        print("="*60)
        
        # Recent customer invoices
        print("\n1️⃣ Recent Customer Invoices (Last 30 days)")
        thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        recent_invoices = await self.odoo.search_read(
            'account.move',
            [
                ['move_type', '=', 'out_invoice'],
                ['invoice_date', '>=', thirty_days_ago]
            ],
            ['name', 'partner_id', 'amount_total', 'state', 'invoice_date'],
            limit=5,
            order='invoice_date desc'
        )
        
        if recent_invoices:
            print(f"   Found {len(recent_invoices)} recent invoices:")
            for inv in recent_invoices:
                partner_name = inv['partner_id'][1] if inv['partner_id'] else 'N/A'
                date_str = inv['invoice_date'] if inv['invoice_date'] else 'N/A'
                print(f"   - {inv['name']}: {partner_name} - ${inv['amount_total']:.2f} ({date_str})")
        else:
            print("   No recent invoices found")
            
        # Unpaid invoices
        print("\n2️⃣ Draft Invoices")
        draft_invoices = await self.odoo.search_read(
            'account.move',
            [
                ['move_type', '=', 'out_invoice'],
                ['state', '=', 'draft']
            ],
            ['name', 'partner_id', 'amount_total'],
            limit=5
        )
        
        if draft_invoices:
            print(f"   Found {len(draft_invoices)} draft invoices:")
            for inv in draft_invoices:
                partner_name = inv['partner_id'][1] if inv['partner_id'] else 'N/A'
                print(f"   - {inv['name']}: {partner_name} - ${inv['amount_total']:.2f}")
        else:
            print("   No draft invoices found")
            
        # High-value invoices
        print("\n3️⃣ High-Value Invoices (> $1000)")
        high_value = await self.odoo.search_read(
            'account.move',
            [
                ['move_type', '=', 'out_invoice'],
                ['amount_total', '>', 1000]
            ],
            ['name', 'partner_id', 'amount_total', 'state'],
            limit=5,
            order='amount_total desc'
        )
        
        if high_value:
            print(f"   Top {len(high_value)} high-value invoices:")
            for inv in high_value:
                partner_name = inv['partner_id'][1] if inv['partner_id'] else 'N/A'
                print(f"   - {inv['name']}: ${inv['amount_total']:.2f} - {partner_name}")
        else:
            print("   No high-value invoices found")
            
    async def vendor_bills_example(self):
        """Demonstrate vendor bill management."""
        print("\n" + "="*60)
        print("VENDOR BILLS")
        print("="*60)
        
        # Count vendor bills
        vendor_bill_count = await self.odoo.search_count('account.move', [
            ['move_type', '=', 'in_invoice']
        ])
        print(f"\n📊 Total Vendor Bills: {vendor_bill_count}")
        
        # Recent vendor bills
        print("\n📋 Recent Vendor Bills:")
        recent_bills = await self.odoo.search_read(
            'account.move',
            [['move_type', '=', 'in_invoice']],
            ['name', 'partner_id', 'amount_total', 'state', 'invoice_date'],
            limit=5,
            order='create_date desc'
        )
        
        if recent_bills:
            for bill in recent_bills:
                vendor_name = bill['partner_id'][1] if bill['partner_id'] else 'N/A'
                date_str = bill['invoice_date'] if bill['invoice_date'] else 'N/A'
                print(f"   - {bill['name']}: {vendor_name} - ${bill['amount_total']:.2f} ({bill['state']})")
        else:
            print("   No vendor bills found")
            
    async def credit_notes_example(self):
        """Demonstrate credit note management."""
        print("\n" + "="*60)
        print("CREDIT NOTES")
        print("="*60)
        
        # Count credit notes
        print("\n📊 Credit Notes Count:")
        
        customer_credit = await self.odoo.search_count('account.move', [
            ['move_type', '=', 'out_refund']
        ])
        vendor_credit = await self.odoo.search_count('account.move', [
            ['move_type', '=', 'in_refund']
        ])
        
        print(f"   Customer Credit Notes: {customer_credit}")
        print(f"   Vendor Credit Notes: {vendor_credit}")
        
        # Recent credit notes
        print("\n📋 Recent Customer Credit Notes:")
        credit_notes = await self.odoo.search_read(
            'account.move',
            [['move_type', '=', 'out_refund']],
            ['name', 'partner_id', 'amount_total', 'state'],
            limit=5,
            order='create_date desc'
        )
        
        if credit_notes:
            for note in credit_notes:
                partner_name = note['partner_id'][1] if note['partner_id'] else 'N/A'
                print(f"   - {note['name']}: {partner_name} - ${note['amount_total']:.2f} ({note['state']})")
        else:
            print("   No credit notes found")
            
    async def invoice_reporting(self):
        """Generate invoice reports and analytics."""
        print("\n" + "="*60)
        print("INVOICE REPORTING & ANALYTICS")
        print("="*60)
        
        # Revenue by month
        print("\n📊 Revenue by Month (Customer Invoices):")
        
        for i in range(3):
            month_start = (datetime.now().replace(day=1) - timedelta(days=30*i))
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
            month_invoices = await self.odoo.search_read(
                'account.move',
                [
                    ['move_type', '=', 'out_invoice'],
                    ['invoice_date', '>=', month_start.strftime('%Y-%m-%d')],
                    ['invoice_date', '<=', month_end.strftime('%Y-%m-%d')],
                    ['state', '=', 'posted']
                ],
                ['amount_total']
            )
            
            total_revenue = sum(inv['amount_total'] for inv in month_invoices)
            print(f"   {month_start.strftime('%B %Y')}: ${total_revenue:.2f} ({len(month_invoices)} invoices)")
            
        # Top customers by invoice amount
        print("\n👥 Top Customers by Invoice Total:")
        
        # Get all posted customer invoices
        customer_invoices = await self.odoo.search_read(
            'account.move',
            [
                ['move_type', '=', 'out_invoice'],
                ['state', '=', 'posted']
            ],
            ['partner_id', 'amount_total'],
            limit=100
        )
        
        if customer_invoices:
            # Aggregate by customer
            customer_totals = {}
            for inv in customer_invoices:
                if inv['partner_id']:
                    partner_name = inv['partner_id'][1]
                    customer_totals[partner_name] = customer_totals.get(partner_name, 0) + inv['amount_total']
                    
            # Sort and display top 5
            top_customers = sorted(customer_totals.items(), key=lambda x: x[1], reverse=True)[:5]
            for customer, total in top_customers:
                print(f"   - {customer}: ${total:.2f}")
                
        # Average invoice value
        print("\n📈 Invoice Statistics:")
        
        if customer_invoices:
            amounts = [inv['amount_total'] for inv in customer_invoices]
            avg_amount = sum(amounts) / len(amounts)
            max_amount = max(amounts)
            min_amount = min(amounts)
            
            print(f"   Average Invoice: ${avg_amount:.2f}")
            print(f"   Largest Invoice: ${max_amount:.2f}")
            print(f"   Smallest Invoice: ${min_amount:.2f}")


async def main():
    """Main function to run invoice demonstrations."""
    
    async with OdooConnection() as odoo:
        manager = OdooInvoiceManager(odoo)
        
        try:
            # Run demonstrations
            await manager.invoice_overview()
            invoice_id = await manager.create_simple_invoice()
            await manager.search_invoices()
            await manager.vendor_bills_example()
            await manager.credit_notes_example()
            await manager.invoice_reporting()
            
            print("\n" + "="*60)
            print("✅ INVOICE OPERATIONS COMPLETED!")
            print("="*60)
            
        except Exception as e:
            print(f"\n❌ Error during invoice operations: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())