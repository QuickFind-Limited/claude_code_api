#!/usr/bin/env python3
"""
CRUD Operations Template for Odoo
Complete examples of Create, Read, Update, Delete operations
"""

import asyncio
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from odoo_connection import OdooConnection


class OdooCRUD:
    """CRUD operations for Odoo."""
    
    def __init__(self, connection: OdooConnection):
        self.odoo = connection
        
    async def demo_partner_crud(self):
        """Demonstrate CRUD operations on res.partner (Contacts)."""
        print("\n" + "="*60)
        print("PARTNER (CONTACT) CRUD OPERATIONS")
        print("="*60)
        
        # CREATE - Create a new partner
        print("\n📝 CREATE: Creating new partners...")
        
        # Create a company
        company_data = {
            'name': f'Test Company {datetime.now().strftime("%Y%m%d_%H%M%S")}',
            'is_company': True,
            'email': 'test@example.com',
            'phone': '+1234567890',
            'street': '123 Main Street',
            'city': 'New York',
            'zip': '10001',
            'website': 'https://testcompany.com',
            'comment': 'Created via Python API',
            'customer_rank': 1,  # Mark as customer
            'supplier_rank': 0,  # Not a supplier
        }
        
        company_id = await self.odoo.create('res.partner', company_data)
        print(f"✅ Created company with ID: {company_id}")
        
        # Create a contact person for the company
        contact_data = {
            'name': 'John Doe',
            'is_company': False,
            'parent_id': company_id,  # Link to parent company
            'email': 'john.doe@example.com',
            'phone': '+1234567891',
            'function': 'CEO',
        }
        
        contact_id = await self.odoo.create('res.partner', contact_data)
        print(f"✅ Created contact with ID: {contact_id}")
        
        # READ - Read the created records
        print("\n🔍 READ: Reading created partners...")
        
        # Read specific fields
        partners = await self.odoo.read(
            'res.partner', 
            [company_id, contact_id],
            ['name', 'email', 'phone', 'is_company', 'parent_id', 'function']
        )
        
        for partner in partners:
            print(f"\n  Partner: {partner['name']}")
            print(f"    - ID: {partner['id']}")
            print(f"    - Email: {partner.get('email', 'N/A')}")
            print(f"    - Phone: {partner.get('phone', 'N/A')}")
            print(f"    - Is Company: {partner['is_company']}")
            if partner.get('parent_id'):
                print(f"    - Parent: {partner['parent_id'][1]}")  # [id, name] tuple
            if partner.get('function'):
                print(f"    - Function: {partner['function']}")
                
        # UPDATE - Update the records
        print("\n✏️ UPDATE: Updating partner information...")
        
        # Update company
        update_success = await self.odoo.write(
            'res.partner',
            [company_id],
            {
                'website': 'https://updated-website.com',
                'comment': 'Updated via Python API at ' + datetime.now().isoformat(),
                'customer_rank': 2,  # Increase customer ranking
            }
        )
        print(f"✅ Company update successful: {update_success}")
        
        # Update contact
        contact_update = await self.odoo.write(
            'res.partner',
            [contact_id],
            {
                'function': 'Chief Executive Officer',
            }
        )
        print(f"✅ Contact update successful: {contact_update}")
        
        # Read again to verify updates
        updated_company = await self.odoo.read(
            'res.partner',
            [company_id],
            ['name', 'website', 'comment', 'customer_rank']
        )
        print(f"\n  Updated company data:")
        print(f"    - Website: {updated_company[0]['website']}")
        print(f"    - Comment: {updated_company[0]['comment']}")
        print(f"    - Customer Rank: {updated_company[0]['customer_rank']}")
        
        # DELETE - Delete the records
        print("\n🗑️ DELETE: Deleting test partners...")
        
        # Delete contact first (child record)
        contact_deleted = await self.odoo.unlink('res.partner', [contact_id])
        print(f"✅ Contact deleted: {contact_deleted}")
        
        # Delete company
        company_deleted = await self.odoo.unlink('res.partner', [company_id])
        print(f"✅ Company deleted: {company_deleted}")
        
        # Verify deletion
        try:
            deleted_check = await self.odoo.read('res.partner', [company_id], ['name'])
            print("❌ Record still exists!")
        except Exception as e:
            if "does not exist" in str(e) or "not found" in str(e).lower():
                print("✅ Deletion verified - records no longer exist")
            else:
                print(f"⚠️ Verification error: {e}")
                
        return company_id, contact_id
        
    async def demo_product_crud(self):
        """Demonstrate CRUD operations on products."""
        print("\n" + "="*60)
        print("PRODUCT CRUD OPERATIONS")
        print("="*60)
        
        # CREATE - Create a new product
        print("\n📝 CREATE: Creating new product...")
        
        product_data = {
            'name': f'Test Product {datetime.now().strftime("%Y%m%d_%H%M%S")}',
            'type': 'consu',  # Consumable product
            'list_price': 99.99,  # Sale price
            'standard_price': 50.00,  # Cost
            'categ_id': 1,  # Product category (usually 1 is 'All')
            'sale_ok': True,  # Can be sold
            'purchase_ok': True,  # Can be purchased
            'description': 'This is a test product created via Python API',
            'description_sale': 'Premium quality test product',
            'weight': 1.5,
            'volume': 0.01,
        }
        
        # Note: Use product.product for variants, product.template for templates
        product_id = await self.odoo.create('product.product', product_data)
        print(f"✅ Created product with ID: {product_id}")
        
        # READ - Read the product
        print("\n🔍 READ: Reading product details...")
        
        products = await self.odoo.read(
            'product.product',
            [product_id],
            ['name', 'list_price', 'standard_price', 'type', 'qty_available', 
             'virtual_available', 'description_sale']
        )
        
        product = products[0]
        print(f"\n  Product: {product['name']}")
        print(f"    - ID: {product['id']}")
        print(f"    - Sale Price: ${product['list_price']}")
        print(f"    - Cost: ${product['standard_price']}")
        print(f"    - Type: {product['type']}")
        print(f"    - Qty Available: {product['qty_available']}")
        print(f"    - Description: {product.get('description_sale', 'N/A')}")
        
        # UPDATE - Update the product
        print("\n✏️ UPDATE: Updating product information...")
        
        update_success = await self.odoo.write(
            'product.product',
            [product_id],
            {
                'list_price': 129.99,
                'description_sale': 'Updated: Premium quality test product with new features',
                'weight': 2.0,
            }
        )
        print(f"✅ Product update successful: {update_success}")
        
        # Read updated product
        updated_product = await self.odoo.read(
            'product.product',
            [product_id],
            ['name', 'list_price', 'description_sale', 'weight']
        )
        print(f"\n  Updated product data:")
        print(f"    - New Price: ${updated_product[0]['list_price']}")
        print(f"    - New Weight: {updated_product[0]['weight']} kg")
        
        # DELETE - Delete the product
        print("\n🗑️ DELETE: Deleting test product...")
        
        product_deleted = await self.odoo.unlink('product.product', [product_id])
        print(f"✅ Product deleted: {product_deleted}")
        
        return product_id
        
    async def demo_user_crud(self):
        """Demonstrate CRUD operations on users (res.users)."""
        print("\n" + "="*60)
        print("USER CRUD OPERATIONS")
        print("="*60)
        
        # CREATE - Create a new user
        print("\n📝 CREATE: Creating new user...")
        
        # First create a partner for the user
        partner_data = {
            'name': f'Test User {datetime.now().strftime("%Y%m%d_%H%M%S")}',
            'email': f'testuser_{datetime.now().strftime("%Y%m%d_%H%M%S")}@example.com',
        }
        partner_id = await self.odoo.create('res.partner', partner_data)
        
        # Create user linked to partner
        user_data = {
            'partner_id': partner_id,
            'login': f'testuser_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
            'password': 'TestPassword123!',  # Note: In production, use secure passwords
            'groups_id': [(6, 0, [])],  # Empty groups (will get default groups)
        }
        
        try:
            user_id = await self.odoo.create('res.users', user_data)
            print(f"✅ Created user with ID: {user_id}")
            
            # READ - Read user details
            print("\n🔍 READ: Reading user details...")
            
            users = await self.odoo.read(
                'res.users',
                [user_id],
                ['name', 'login', 'email', 'create_date', 'lang']
            )
            
            user = users[0]
            print(f"\n  User: {user['name']}")
            print(f"    - ID: {user['id']}")
            print(f"    - Login: {user['login']}")
            print(f"    - Email: {user.get('email', 'N/A')}")
            print(f"    - Language: {user.get('lang', 'N/A')}")
            
            # UPDATE - Update user
            print("\n✏️ UPDATE: Updating user information...")
            
            update_success = await self.odoo.write(
                'res.users',
                [user_id],
                {
                    'lang': 'en_US',
                    'tz': 'America/New_York',
                }
            )
            print(f"✅ User update successful: {update_success}")
            
            # DELETE - Delete the user
            print("\n🗑️ DELETE: Deleting test user...")
            
            user_deleted = await self.odoo.unlink('res.users', [user_id])
            print(f"✅ User deleted: {user_deleted}")
            
        except Exception as e:
            print(f"⚠️ User operations may require special permissions: {e}")
            
        # Clean up partner
        await self.odoo.unlink('res.partner', [partner_id])
        
    async def demo_batch_operations(self):
        """Demonstrate batch CRUD operations."""
        print("\n" + "="*60)
        print("BATCH CRUD OPERATIONS")
        print("="*60)
        
        # BATCH CREATE - Create multiple records at once
        print("\n📝 BATCH CREATE: Creating multiple partners...")
        
        created_ids = []
        for i in range(5):
            partner_data = {
                'name': f'Batch Partner {i+1} - {datetime.now().strftime("%Y%m%d_%H%M%S")}',
                'email': f'batch{i+1}@example.com',
                'is_company': i % 2 == 0,  # Alternate between company and contact
            }
            partner_id = await self.odoo.create('res.partner', partner_data)
            created_ids.append(partner_id)
            print(f"  Created partner {i+1} with ID: {partner_id}")
            
        # BATCH READ - Read all at once
        print("\n🔍 BATCH READ: Reading all created partners...")
        
        partners = await self.odoo.read(
            'res.partner',
            created_ids,
            ['name', 'email', 'is_company']
        )
        
        for partner in partners:
            print(f"  - {partner['name']}: {partner['email']} (Company: {partner['is_company']})")
            
        # BATCH UPDATE - Update all at once
        print("\n✏️ BATCH UPDATE: Updating all partners...")
        
        batch_update = await self.odoo.write(
            'res.partner',
            created_ids,
            {
                'comment': f'Batch updated at {datetime.now().isoformat()}',
                'customer_rank': 1,
            }
        )
        print(f"✅ Batch update successful: {batch_update}")
        
        # Verify batch update
        updated_partners = await self.odoo.read(
            'res.partner',
            created_ids[:2],  # Check first two
            ['name', 'comment', 'customer_rank']
        )
        
        for partner in updated_partners:
            print(f"  - {partner['name']}: {partner['comment']}")
            
        # BATCH DELETE - Delete all at once
        print("\n🗑️ BATCH DELETE: Deleting all test partners...")
        
        batch_delete = await self.odoo.unlink('res.partner', created_ids)
        print(f"✅ Batch delete successful: {batch_delete}")
        print(f"   Deleted {len(created_ids)} records")


async def main():
    """Main function to run all CRUD demonstrations."""
    
    async with OdooConnection() as odoo:
        crud = OdooCRUD(odoo)
        
        # Run demonstrations
        try:
            # Partner CRUD
            await crud.demo_partner_crud()
            
            # Product CRUD
            await crud.demo_product_crud()
            
            # User CRUD (may require admin permissions)
            await crud.demo_user_crud()
            
            # Batch operations
            await crud.demo_batch_operations()
            
            print("\n" + "="*60)
            print("✅ ALL CRUD OPERATIONS COMPLETED SUCCESSFULLY!")
            print("="*60)
            
        except Exception as e:
            print(f"\n❌ Error during CRUD operations: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())