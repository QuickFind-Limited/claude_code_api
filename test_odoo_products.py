#!/usr/bin/env python3
"""
Test script to count products in Odoo using MCP
Tests both with and without Docker
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_with_mcp_tools():
    """Test using MCP Odoo tools directly"""
    print("\n" + "="*60)
    print("Testing with MCP Odoo Tools")
    print("="*60)
    
    try:
        # We'll simulate the MCP tool calls here
        # In actual usage, these would be called through the MCP server
        
        print("\nSearching for products in Odoo...")
        print("Using MCP tools: mcp__odoo_mcp__odoo_search_count")
        
        # This would be the actual MCP call format:
        mcp_request = {
            "tool": "mcp__odoo_mcp__odoo_search_count",
            "parameters": {
                "instance_id": "default",
                "model": "product.product",
                "domain": []  # Empty domain means all products
            }
        }
        
        print(f"\nMCP Request: {json.dumps(mcp_request, indent=2)}")
        
        # The actual implementation would use the MCP client
        # For now, we'll use direct XMLRPC to demonstrate
        
    except Exception as e:
        print(f"MCP test error: {e}")
        return None

def test_with_xmlrpc():
    """Test using direct XMLRPC connection"""
    print("\n" + "="*60)
    print("Testing with Direct XMLRPC Connection (No Docker)")
    print("="*60)
    
    try:
        import xmlrpc.client
        
        # Get credentials from environment
        url = os.getenv("ODOO_URL", "https://source4.odoo.com")
        db = os.getenv("ODOO_DATABASE", "source4")
        username = os.getenv("ODOO_USERNAME", "admin@quickfindai.com")
        password = os.getenv("ODOO_PASSWORD")
        
        print(f"\nConnection details:")
        print(f"  URL: {url}")
        print(f"  Database: {db}")
        print(f"  Username: {username}")
        
        # Connect to Odoo
        common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
        
        # Authenticate
        print("\nAuthenticating...")
        uid = common.authenticate(db, username, password, {})
        
        if uid:
            print(f"✅ Authentication successful! UID: {uid}")
            
            # Create object proxy
            models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
            
            # Count all products
            print("\nCounting products...")
            product_count = models.execute_kw(
                db, uid, password,
                'product.product', 'search_count',
                [[]]  # Empty domain means all products
            )
            print(f"\n📦 Total number of products: {product_count}")
            
            # Get sample of products
            print("\nFetching sample products...")
            product_ids = models.execute_kw(
                db, uid, password,
                'product.product', 'search',
                [[]],
                {'limit': 5}
            )
            
            if product_ids:
                products = models.execute_kw(
                    db, uid, password,
                    'product.product', 'read',
                    [product_ids],
                    {'fields': ['name', 'default_code', 'list_price', 'qty_available']}
                )
                
                print("\nSample products:")
                for product in products:
                    print(f"  - {product.get('name', 'N/A')} "
                          f"[{product.get('default_code', 'No code')}] "
                          f"Price: ${product.get('list_price', 0):.2f} "
                          f"Qty: {product.get('qty_available', 0)}")
            
            # Count products by category
            print("\nAnalyzing products by category...")
            
            # Get product categories
            category_ids = models.execute_kw(
                db, uid, password,
                'product.category', 'search',
                [[]],
                {'limit': 10}
            )
            
            if category_ids:
                categories = models.execute_kw(
                    db, uid, password,
                    'product.category', 'read',
                    [category_ids],
                    {'fields': ['name', 'complete_name']}
                )
                
                print("\nProduct counts by category:")
                for category in categories[:5]:
                    cat_product_count = models.execute_kw(
                        db, uid, password,
                        'product.product', 'search_count',
                        [[['categ_id', '=', category['id']]]]
                    )
                    if cat_product_count > 0:
                        print(f"  - {category['complete_name']}: {cat_product_count} products")
            
            return product_count
        else:
            print("❌ Authentication failed!")
            return None
            
    except Exception as e:
        print(f"XMLRPC test error: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_with_docker():
    """Test using Docker setup with MCP server"""
    print("\n" + "="*60)
    print("Testing with Docker Setup")
    print("="*60)
    
    try:
        import requests
        
        # Check if Docker container is running
        print("\nChecking Docker container status...")
        docker_url = "http://localhost:8000"
        
        try:
            response = requests.get(f"{docker_url}/api/v1/health", timeout=5)
            if response.status_code == 200:
                print("✅ Docker container is running!")
                
                # Make API call through the Docker service
                print("\nCalling API through Docker service...")
                
                # This would be the actual API call to the Claude SDK server
                api_request = {
                    "action": "odoo_count_products",
                    "parameters": {
                        "model": "product.product",
                        "domain": []
                    }
                }
                
                print(f"\nAPI Request: {json.dumps(api_request, indent=2)}")
                
                # Note: The actual implementation would require the API endpoint
                # to be properly configured in the Docker container
                
            else:
                print(f"⚠️ Docker container returned status: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Docker container not accessible: {e}")
            print("\nTo start Docker container, run:")
            print("  docker-compose up -d")
            
    except ImportError:
        print("❌ requests library not installed")
        print("Install with: pip install requests")
    except Exception as e:
        print(f"Docker test error: {e}")

def main():
    """Main test function"""
    print("\n" + "🔍 ODOO PRODUCT COUNT TEST 🔍".center(60, "="))
    print("\nThis script tests counting products in Odoo")
    print("using different connection methods.\n")
    
    # Test 1: Direct XMLRPC (without Docker)
    xmlrpc_count = test_with_xmlrpc()
    
    # Test 2: MCP Tools
    mcp_count = test_with_mcp_tools()
    
    # Test 3: Docker setup
    test_with_docker()
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    if xmlrpc_count is not None:
        print(f"\n✅ Direct XMLRPC connection successful!")
        print(f"   Total products found: {xmlrpc_count}")
    else:
        print("\n❌ Direct XMLRPC connection failed")
    
    print("\n📝 Notes:")
    print("  - Direct XMLRPC works without Docker")
    print("  - Docker setup provides API wrapper for Claude SDK")
    print("  - MCP tools provide standardized interface")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()