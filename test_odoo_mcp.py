#!/usr/bin/env python3
"""
Test script for Odoo MCP connection
"""

import os
import sys
from pathlib import Path

# Add the odoo_mcp directory to the Python path
odoo_mcp_path = Path("/Users/yoangabison/files/source/odoo_mcp")
if odoo_mcp_path.exists():
    sys.path.insert(0, str(odoo_mcp_path))

try:
    # Try importing the odoo_mcp_client
    from odoo_mcp_client import OdooMCPClient
    
    # Initialize the client with instance_id
    client = OdooMCPClient(instance_id="default")
    
    # Test connection
    print("Testing Odoo MCP connection...")
    print(f"Instance ID: default")
    
    # Try to search for users (without limit parameter)
    result = client.search("res.users", [])
    print(f"Search result: {result}")
    
except ImportError as e:
    print(f"Import error: {e}")
    print("Trying alternative approach...")
    
    # Try direct xmlrpc connection
    import xmlrpc.client
    
    # Load configuration from environment
    from dotenv import load_dotenv
    load_dotenv("/Users/yoangabison/files/source/odoo_mcp/.env")
    
    url = os.getenv("ODOO_URL", "https://source4.odoo.com/odoo")
    db = os.getenv("ODOO_DATABASE", "source4")
    username = os.getenv("ODOO_USERNAME", "admin@quickfindai.com")
    password = os.getenv("ODOO_PASSWORD")
    
    print(f"\nDirect XMLRPC connection test:")
    print(f"URL: {url}")
    print(f"Database: {db}")
    print(f"Username: {username}")
    
    # Connect to Odoo
    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
    
    # Authenticate
    uid = common.authenticate(db, username, password, {})
    
    if uid:
        print(f"✅ Authentication successful! UID: {uid}")
        
        # Create object proxy
        models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
        
        # Test search
        partner_ids = models.execute_kw(
            db, uid, password,
            'res.partner', 'search',
            [[]],
            {'limit': 3}
        )
        print(f"Found partner IDs: {partner_ids}")
        
        # Read partner details
        if partner_ids:
            partners = models.execute_kw(
                db, uid, password,
                'res.partner', 'read',
                [partner_ids],
                {'fields': ['name', 'email']}
            )
            print(f"Partner details: {partners[:2]}")
    else:
        print("❌ Authentication failed!")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()