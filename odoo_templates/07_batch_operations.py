#!/usr/bin/env python3
"""
Batch Operations Template for Odoo
Efficient bulk operations, performance optimization, and error handling
"""

import asyncio
from datetime import datetime, timedelta
import sys
import os
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from odoo_connection import OdooConnection


class OdooBatchOperations:
    """Batch operations for Odoo with performance optimization."""
    
    def __init__(self, connection: OdooConnection):
        self.odoo = connection
        
    async def batch_create_example(self):
        """Demonstrate efficient batch creation."""
        print("\n" + "="*60)
        print("BATCH CREATE OPERATIONS")
        print("="*60)
        
        # Create multiple partners efficiently
        print("\n📝 Creating 20 test partners in batch...")
        
        start_time = time.time()
        created_ids = []
        
        # Method 1: Individual creates (slower)
        print("\n1️⃣ Method 1: Individual Creates")
        individual_start = time.time()
        
        for i in range(5):
            partner_data = {
                'name': f'Individual Partner {i+1} - {datetime.now().strftime("%Y%m%d_%H%M%S")}',
                'email': f'individual{i+1}@test.com',
                'is_company': True,
            }
            partner_id = await self.odoo.create('res.partner', partner_data)
            created_ids.append(partner_id)
            
        individual_time = time.time() - individual_start
        print(f"   Created 5 partners individually in {individual_time:.2f} seconds")
        
        # Method 2: Prepare data and create in sequence (more efficient)
        print("\n2️⃣ Method 2: Sequential Batch Creation")
        batch_start = time.time()
        
        # Prepare all data first
        partners_data = []
        for i in range(15):
            partners_data.append({
                'name': f'Batch Partner {i+1} - {datetime.now().strftime("%Y%m%d_%H%M%S")}',
                'email': f'batch{i+1}@test.com',
                'is_company': i % 2 == 0,
                'customer_rank': 1,
            })
            
        # Create all at once
        for partner_data in partners_data:
            partner_id = await self.odoo.create('res.partner', partner_data)
            created_ids.append(partner_id)
            
        batch_time = time.time() - batch_start
        print(f"   Created 15 partners in batch in {batch_time:.2f} seconds")
        
        total_time = time.time() - start_time
        print(f"\n✅ Total: Created {len(created_ids)} partners in {total_time:.2f} seconds")
        
        # Clean up
        await self.odoo.unlink('res.partner', created_ids)
        print("   Cleaned up test data")
        
    async def batch_update_example(self):
        """Demonstrate efficient batch updates."""
        print("\n" + "="*60)
        print("BATCH UPDATE OPERATIONS")
        print("="*60)
        
        # Find partners to update
        print("\n🔍 Finding partners to update...")
        partner_ids = await self.odoo.search('res.partner', [
            ['customer_rank', '=', 1]
        ], limit=50)
        
        if not partner_ids:
            print("   No partners found to update")
            return
            
        print(f"   Found {len(partner_ids)} partners to update")
        
        # Batch update all at once
        print("\n✏️ Updating all partners with timestamp...")
        start_time = time.time()
        
        update_data = {
            'comment': f'Batch updated at {datetime.now().isoformat()}',
        }
        
        # Update all IDs at once
        success = await self.odoo.write('res.partner', partner_ids, update_data)
        
        update_time = time.time() - start_time
        print(f"   ✅ Updated {len(partner_ids)} partners in {update_time:.2f} seconds")
        print(f"   Success: {success}")
        
    async def batch_read_optimization(self):
        """Demonstrate optimized batch reading."""
        print("\n" + "="*60)
        print("BATCH READ OPTIMIZATION")
        print("="*60)
        
        # Find products
        print("\n🔍 Finding products...")
        product_ids = await self.odoo.search('product.template', [], limit=100)
        
        if not product_ids:
            print("   No products found")
            return
            
        print(f"   Found {len(product_ids)} products")
        
        # Method 1: Read all fields (slower, more data)
        print("\n1️⃣ Reading ALL fields (slower)...")
        start_time = time.time()
        
        # Read only first 10 with all fields to avoid timeout
        all_fields_data = await self.odoo.read('product.template', product_ids[:10])
        
        all_fields_time = time.time() - start_time
        print(f"   Read 10 products with ALL fields in {all_fields_time:.2f} seconds")
        print(f"   Data size per record: ~{len(str(all_fields_data[0])) if all_fields_data else 0} characters")
        
        # Method 2: Read specific fields only (faster, less data)
        print("\n2️⃣ Reading SPECIFIC fields only (faster)...")
        start_time = time.time()
        
        specific_fields = ['name', 'list_price', 'type', 'sale_ok']
        specific_data = await self.odoo.read('product.template', product_ids, specific_fields)
        
        specific_time = time.time() - start_time
        print(f"   Read {len(product_ids)} products with specific fields in {specific_time:.2f} seconds")
        print(f"   Data size per record: ~{len(str(specific_data[0])) if specific_data else 0} characters")
        
        # Method 3: Use search_read (most efficient)
        print("\n3️⃣ Using search_read (most efficient)...")
        start_time = time.time()
        
        search_read_data = await self.odoo.search_read(
            'product.template',
            [],
            specific_fields,
            limit=100
        )
        
        search_read_time = time.time() - start_time
        print(f"   Search and read 100 products in {search_read_time:.2f} seconds")
        
        print("\n📊 Performance Comparison:")
        print(f"   All fields (10 records): {all_fields_time:.2f}s")
        print(f"   Specific fields (100 records): {specific_time:.2f}s")
        print(f"   Search_read (100 records): {search_read_time:.2f}s")
        
    async def batch_delete_with_safety(self):
        """Demonstrate safe batch deletion."""
        print("\n" + "="*60)
        print("SAFE BATCH DELETE OPERATIONS")
        print("="*60)
        
        # Create test records
        print("\n📝 Creating test records for deletion...")
        test_ids = []
        
        for i in range(10):
            partner_id = await self.odoo.create('res.partner', {
                'name': f'Delete Test {i+1} - {datetime.now().strftime("%Y%m%d_%H%M%S")}',
                'email': f'delete{i+1}@test.com',
            })
            test_ids.append(partner_id)
            
        print(f"   Created {len(test_ids)} test records")
        
        # Verify before deletion
        print("\n🔍 Verifying records before deletion...")
        existing = await self.odoo.search('res.partner', [
            ['id', 'in', test_ids]
        ])
        print(f"   Found {len(existing)} records to delete")
        
        # Batch delete with chunks (safer for large datasets)
        print("\n🗑️ Deleting in chunks...")
        chunk_size = 5
        deleted_count = 0
        
        for i in range(0, len(test_ids), chunk_size):
            chunk = test_ids[i:i+chunk_size]
            success = await self.odoo.unlink('res.partner', chunk)
            if success:
                deleted_count += len(chunk)
                print(f"   Deleted chunk {i//chunk_size + 1}: {len(chunk)} records")
                
        print(f"\n✅ Total deleted: {deleted_count} records")
        
        # Verify deletion
        remaining = await self.odoo.search('res.partner', [
            ['id', 'in', test_ids]
        ])
        print(f"   Remaining records: {len(remaining)} (should be 0)")
        
    async def error_handling_patterns(self):
        """Demonstrate error handling in batch operations."""
        print("\n" + "="*60)
        print("ERROR HANDLING IN BATCH OPERATIONS")
        print("="*60)
        
        # Pattern 1: Try-except for individual operations
        print("\n1️⃣ Individual Error Handling")
        
        test_data = [
            {'name': 'Valid Partner 1', 'email': 'valid1@test.com'},
            {'name': 'Valid Partner 2', 'email': 'invalid-email'},  # Might fail validation
            {'name': 'Valid Partner 3', 'email': 'valid3@test.com'},
        ]
        
        created_ids = []
        failed_records = []
        
        for i, data in enumerate(test_data):
            try:
                partner_id = await self.odoo.create('res.partner', data)
                created_ids.append(partner_id)
                print(f"   ✅ Created: {data['name']}")
            except Exception as e:
                failed_records.append((i, data, str(e)))
                print(f"   ❌ Failed: {data['name']} - {str(e)[:50]}...")
                
        print(f"\n   Summary: {len(created_ids)} succeeded, {len(failed_records)} failed")
        
        # Clean up
        if created_ids:
            await self.odoo.unlink('res.partner', created_ids)
            
        # Pattern 2: Validation before batch operation
        print("\n2️⃣ Pre-validation Pattern")
        
        # Check for duplicates before creating
        emails_to_check = ['test1@example.com', 'test2@example.com']
        
        print("   Checking for existing emails...")
        existing = await self.odoo.search_read(
            'res.partner',
            [['email', 'in', emails_to_check]],
            ['email']
        )
        
        existing_emails = [p['email'] for p in existing]
        new_emails = [e for e in emails_to_check if e not in existing_emails]
        
        print(f"   Existing: {len(existing_emails)}, New: {len(new_emails)}")
        
        # Pattern 3: Rollback pattern
        print("\n3️⃣ Transaction Rollback Pattern")
        
        print("   Note: Odoo handles transactions server-side")
        print("   For client-side rollback, track created IDs and delete on error")
        
        transaction_ids = []
        try:
            # Simulate a transaction
            id1 = await self.odoo.create('res.partner', {'name': 'Transaction Test 1'})
            transaction_ids.append(id1)
            
            id2 = await self.odoo.create('res.partner', {'name': 'Transaction Test 2'})
            transaction_ids.append(id2)
            
            # Simulate an error condition
            # raise Exception("Simulated error - rolling back")
            
            print(f"   ✅ Transaction completed: {len(transaction_ids)} records created")
            
        except Exception as e:
            # Rollback by deleting created records
            if transaction_ids:
                await self.odoo.unlink('res.partner', transaction_ids)
                print(f"   ⚠️ Rolled back {len(transaction_ids)} records due to error")
                
        finally:
            # Clean up
            if transaction_ids:
                await self.odoo.unlink('res.partner', transaction_ids)
                
    async def pagination_for_large_datasets(self):
        """Handle large datasets with pagination."""
        print("\n" + "="*60)
        print("PAGINATION FOR LARGE DATASETS")
        print("="*60)
        
        # Get total count
        total_partners = await self.odoo.search_count('res.partner', [])
        print(f"\n📊 Total partners in database: {total_partners}")
        
        # Process in pages
        page_size = 100
        pages_to_process = min(5, (total_partners + page_size - 1) // page_size)  # Limit to 5 pages for demo
        
        print(f"   Processing {pages_to_process} pages of {page_size} records each")
        
        processed_count = 0
        companies_count = 0
        
        for page in range(pages_to_process):
            offset = page * page_size
            
            # Fetch page
            page_ids = await self.odoo.search(
                'res.partner',
                [],
                limit=page_size,
                offset=offset,
                order='id asc'
            )
            
            if not page_ids:
                break
                
            # Process page
            page_data = await self.odoo.read(
                'res.partner',
                page_ids,
                ['name', 'is_company']
            )
            
            # Count companies in this page
            page_companies = sum(1 for p in page_data if p['is_company'])
            companies_count += page_companies
            processed_count += len(page_data)
            
            print(f"   Page {page + 1}: Processed {len(page_data)} records, {page_companies} companies")
            
        print(f"\n✅ Summary:")
        print(f"   Total processed: {processed_count}")
        print(f"   Companies found: {companies_count}")
        print(f"   Contacts found: {processed_count - companies_count}")
        
    async def parallel_operations_example(self):
        """Demonstrate parallel operations for better performance."""
        print("\n" + "="*60)
        print("PARALLEL OPERATIONS (SIMULATED)")
        print("="*60)
        
        print("\n⚡ Simulating parallel operations...")
        print("   Note: True parallelism requires multiple connections")
        
        # Simulate parallel searches
        start_time = time.time()
        
        # Define multiple search operations
        searches = [
            ('Companies', [['is_company', '=', True]]),
            ('Customers', [['customer_rank', '>', 0]]),
            ('Suppliers', [['supplier_rank', '>', 0]]),
            ('With Email', [['email', '!=', False]]),
        ]
        
        # Execute searches (would be parallel with asyncio.gather in production)
        results = {}
        for name, domain in searches:
            count = await self.odoo.search_count('res.partner', domain)
            results[name] = count
            print(f"   {name}: {count}")
            
        total_time = time.time() - start_time
        print(f"\n   Completed {len(searches)} searches in {total_time:.2f} seconds")


async def main():
    """Main function to run batch operation demonstrations."""
    
    async with OdooConnection() as odoo:
        batch_ops = OdooBatchOperations(odoo)
        
        try:
            # Run demonstrations
            await batch_ops.batch_create_example()
            await batch_ops.batch_update_example()
            await batch_ops.batch_read_optimization()
            await batch_ops.batch_delete_with_safety()
            await batch_ops.error_handling_patterns()
            await batch_ops.pagination_for_large_datasets()
            await batch_ops.parallel_operations_example()
            
            print("\n" + "="*60)
            print("✅ BATCH OPERATIONS COMPLETED!")
            print("="*60)
            
        except Exception as e:
            print(f"\n❌ Error during batch operations: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())