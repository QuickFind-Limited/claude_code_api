#!/usr/bin/env python3
"""
Odoo Connection Template - Base connection and authentication module
This template provides the foundation for all Odoo operations.

IMPORTANT: The instance_id is always "default" unless you have multiple Odoo instances.
"""

import asyncio
import os
import aiohttp
from dotenv import load_dotenv
from typing import Any, Dict, List, Optional
import json

# Load environment variables
load_dotenv()


class OdooConnection:
    """Base class for Odoo connections using JSON-RPC."""
    
    def __init__(self, url: str = None, database: str = None, 
                 username: str = None, password: str = None):
        """
        Initialize Odoo connection.
        
        Args:
            url: Odoo URL (defaults to ODOO_URL env var)
            database: Database name (defaults to ODOO_DATABASE env var)
            username: Username (defaults to ODOO_USERNAME env var)
            password: Password (defaults to ODOO_PASSWORD env var)
        """
        self.url = url or os.getenv("ODOO_URL", "https://source2.odoo.com")
        self.database = database or os.getenv("ODOO_DATABASE", "source2")
        self.username = username or os.getenv("ODOO_USERNAME")
        self.password = password or os.getenv("ODOO_PASSWORD")
        self.uid = None
        self.session = None
        self.connector = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
        
    async def connect(self):
        """Create session and authenticate with Odoo."""
        # Create HTTP session with connection pooling
        self.connector = aiohttp.TCPConnector(
            limit=10,  # Maximum number of connections
            force_close=True,
            enable_cleanup_closed=True
        )
        self.session = aiohttp.ClientSession(
            connector=self.connector,
            timeout=aiohttp.ClientTimeout(total=30)
        )
        
        # Authenticate
        await self.authenticate()
        
    async def disconnect(self):
        """Close the session and cleanup."""
        if self.session:
            await self.session.close()
        if self.connector:
            await self.connector.close()
            
    async def authenticate(self) -> int:
        """
        Authenticate with Odoo and get user ID.
        
        Returns:
            User ID (uid)
            
        Raises:
            Exception: If authentication fails
        """
        auth_url = f"{self.url}/jsonrpc"
        auth_payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "service": "common",
                "method": "authenticate",
                "args": [self.database, self.username, self.password, {}],
            },
            "id": 1,
        }
        
        print(f"🔐 Authenticating to {self.url} (database: {self.database})...")
        
        async with self.session.post(auth_url, json=auth_payload) as resp:
            result = await resp.json()
            
            if "error" in result:
                error = result["error"]
                raise Exception(f"Authentication failed: {error.get('message', 'Unknown error')}")
                
            self.uid = result.get("result")
            
            if not self.uid:
                raise Exception("Authentication failed: Invalid credentials")
                
            print(f"✅ Authenticated successfully! UID: {self.uid}")
            return self.uid
            
    async def execute_kw(self, model: str, method: str, args: List = None, 
                        kwargs: Dict = None) -> Any:
        """
        Execute a method on an Odoo model using execute_kw.
        
        Args:
            model: Odoo model name (e.g., 'res.partner', 'product.product')
            method: Method to execute (e.g., 'search', 'read', 'create', 'write', 'unlink')
            args: Positional arguments for the method
            kwargs: Keyword arguments for the method
            
        Returns:
            Result from Odoo
            
        Examples:
            # Search for partners
            partner_ids = await odoo.execute_kw('res.partner', 'search', [[['is_company', '=', True]]])
            
            # Read partner data
            partners = await odoo.execute_kw('res.partner', 'read', [partner_ids, ['name', 'email']])
            
            # Create a partner
            partner_id = await odoo.execute_kw('res.partner', 'create', [{'name': 'Test Company'}])
        """
        if not self.uid:
            raise Exception("Not authenticated. Call authenticate() first.")
            
        args = args or []
        kwargs = kwargs or {}
        
        url = f"{self.url}/jsonrpc"
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "service": "object",
                "method": "execute_kw",
                "args": [self.database, self.uid, self.password, model, method, args, kwargs],
            },
            "id": 2,
        }
        
        async with self.session.post(url, json=payload) as resp:
            result = await resp.json()
            
            if "error" in result:
                error = result["error"]
                error_msg = error.get("message", "Unknown error")
                error_data = error.get("data", {})
                
                # Try to extract more detailed error information
                if isinstance(error_data, dict):
                    debug_info = error_data.get("debug", "")
                    if debug_info:
                        error_msg = f"{error_msg}\nDebug: {debug_info}"
                        
                raise Exception(f"Odoo error: {error_msg}")
                
            return result.get("result")
            
    async def search(self, model: str, domain: List = None, 
                    limit: int = None, offset: int = 0, 
                    order: str = None) -> List[int]:
        """
        Search for records in Odoo.
        
        Args:
            model: Odoo model name
            domain: Search domain (Odoo domain syntax)
            limit: Maximum number of records to return
            offset: Number of records to skip
            order: Sort order (e.g., 'name asc', 'id desc')
            
        Returns:
            List of record IDs
            
        Examples:
            # Find all companies
            company_ids = await odoo.search('res.partner', [['is_company', '=', True]])
            
            # Find customers with email
            customer_ids = await odoo.search('res.partner', 
                                            [['customer_rank', '>', 0], 
                                             ['email', '!=', False]])
            
            # Complex domain with AND/OR logic
            ids = await odoo.search('res.partner',
                                   ['|', ['is_company', '=', True],
                                         ['parent_id', '=', False]])
        """
        domain = domain or []
        kwargs = {}
        
        if limit is not None:
            kwargs['limit'] = limit
        if offset:
            kwargs['offset'] = offset
        if order:
            kwargs['order'] = order
            
        return await self.execute_kw(model, 'search', [domain], kwargs)
        
    async def search_count(self, model: str, domain: List = None) -> int:
        """
        Count records matching the domain.
        
        Args:
            model: Odoo model name
            domain: Search domain
            
        Returns:
            Number of matching records
            
        Example:
            count = await odoo.search_count('product.template', [['sale_ok', '=', True]])
        """
        domain = domain or []
        return await self.execute_kw(model, 'search_count', [domain])
        
    async def search_read(self, model: str, domain: List = None,
                         fields: List[str] = None, limit: int = None,
                         offset: int = 0, order: str = None) -> List[Dict]:
        """
        Search and read records in one operation.
        
        Args:
            model: Odoo model name
            domain: Search domain
            fields: Fields to read (None for all fields - be careful with large models!)
            limit: Maximum number of records
            offset: Number of records to skip
            order: Sort order
            
        Returns:
            List of dictionaries with record data
            
        Example:
            products = await odoo.search_read('product.product',
                                             [['sale_ok', '=', True]],
                                             ['name', 'list_price', 'qty_available'],
                                             limit=10)
        """
        domain = domain or []
        kwargs = {}
        
        if fields:
            kwargs['fields'] = fields
        if limit is not None:
            kwargs['limit'] = limit
        if offset:
            kwargs['offset'] = offset
        if order:
            kwargs['order'] = order
            
        return await self.execute_kw(model, 'search_read', [domain], kwargs)
        
    async def read(self, model: str, ids: List[int], 
                  fields: List[str] = None) -> List[Dict]:
        """
        Read records by IDs.
        
        Args:
            model: Odoo model name
            ids: List of record IDs
            fields: Fields to read (None for all)
            
        Returns:
            List of dictionaries with record data
            
        Example:
            partners = await odoo.read('res.partner', [1, 2, 3], ['name', 'email', 'phone'])
        """
        if fields:
            return await self.execute_kw(model, 'read', [ids, fields])
        else:
            return await self.execute_kw(model, 'read', [ids])
            
    async def create(self, model: str, values: Dict) -> int:
        """
        Create a new record.
        
        Args:
            model: Odoo model name
            values: Dictionary of field values
            
        Returns:
            ID of created record
            
        Example:
            partner_id = await odoo.create('res.partner', {
                'name': 'New Company',
                'is_company': True,
                'email': 'info@company.com'
            })
        """
        return await self.execute_kw(model, 'create', [values])
        
    async def write(self, model: str, ids: List[int], values: Dict) -> bool:
        """
        Update existing records.
        
        Args:
            model: Odoo model name
            ids: List of record IDs to update
            values: Dictionary of field values to update
            
        Returns:
            True if successful
            
        Example:
            success = await odoo.write('res.partner', [partner_id], {
                'phone': '+1234567890',
                'website': 'https://company.com'
            })
        """
        return await self.execute_kw(model, 'write', [ids, values])
        
    async def unlink(self, model: str, ids: List[int]) -> bool:
        """
        Delete records.
        
        Args:
            model: Odoo model name
            ids: List of record IDs to delete
            
        Returns:
            True if successful
            
        Example:
            success = await odoo.unlink('res.partner', [partner_id])
        """
        return await self.execute_kw(model, 'unlink', [ids])
        
    async def fields_get(self, model: str, attributes: List[str] = None) -> Dict:
        """
        Get field definitions for a model.
        
        Args:
            model: Odoo model name
            attributes: List of field attributes to return
                       (e.g., ['string', 'type', 'required', 'readonly'])
            
        Returns:
            Dictionary of field definitions
            
        Example:
            fields = await odoo.fields_get('res.partner', ['string', 'type', 'required'])
        """
        kwargs = {}
        if attributes:
            kwargs['attributes'] = attributes
            
        return await self.execute_kw(model, 'fields_get', [], kwargs)


# Example usage function
async def main():
    """Example usage of OdooConnection class."""
    
    # Method 1: Using context manager (recommended)
    async with OdooConnection() as odoo:
        # Count products
        product_count = await odoo.search_count('product.template')
        print(f"📦 Total products: {product_count}")
        
        # Search for companies
        company_ids = await odoo.search('res.partner', 
                                       [['is_company', '=', True]], 
                                       limit=5)
        print(f"🏢 Found {len(company_ids)} companies")
        
        # Read company details
        if company_ids:
            companies = await odoo.read('res.partner', company_ids, 
                                       ['name', 'email', 'phone'])
            for company in companies:
                print(f"  - {company['name']}: {company.get('email', 'No email')}")
                
    # Method 2: Manual connection management
    odoo = OdooConnection()
    try:
        await odoo.connect()
        
        # Your operations here
        count = await odoo.search_count('sale.order', [['state', '=', 'sale']])
        print(f"📊 Confirmed sales orders: {count}")
        
    finally:
        await odoo.disconnect()


if __name__ == "__main__":
    asyncio.run(main())