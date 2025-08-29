#!/usr/bin/env python3
"""
Discover available tables and fields in NetSuite using SuiteQL
"""

import json
import os
from datetime import datetime

import requests
from dotenv import load_dotenv
from requests_oauthlib import OAuth1

# Load environment variables
load_dotenv()


def discover_schema():
    """Discover available tables and fields in NetSuite"""

    # Get credentials
    consumer_key = os.getenv("GYM_PLUS_COFFEE_CONSUMER_ID")
    consumer_secret = os.getenv("GYM_PLUS_COFFEE_CONSUMER_SECRET")
    token_id = os.getenv("GYM_PLUS_COFFEE_TOKEN_ID")
    token_secret = os.getenv("GYM_PLUS_COFFEE_TOKEN_SECRET")

    account_id = "7326096_SB1"
    url_account_id = "7326096-sb1"

    print("🔍 NetSuite Schema Discovery")
    print("=" * 70)
    print(f"Account: {account_id}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 70)

    suiteql_url = f"https://{url_account_id}.suitetalk.api.netsuite.com/services/rest/query/v1/suiteql"

    auth = OAuth1(
        client_key=consumer_key,
        client_secret=consumer_secret,
        resource_owner_key=token_id,
        resource_owner_secret=token_secret,
        signature_method="HMAC-SHA256",
        realm=account_id,
    )

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Prefer": "transient",
    }

    def run_query(query_name, query):
        """Helper function to run a query"""
        payload = {"q": query.strip()}
        try:
            response = requests.post(
                suiteql_url, auth=auth, headers=headers, json=payload, timeout=30
            )
            if response.status_code == 200:
                return response.json()
            else:
                print(f"  ❌ {query_name} failed: {response.status_code}")
                return None
        except Exception as e:
            print(f"  ❌ {query_name} error: {e}")
            return None

    # 1. Test common NetSuite tables
    print("\n📊 Testing Common Tables")
    print("-" * 50)

    tables_to_test = [
        "customer",
        "vendor",
        "item",
        "inventoryitem",
        "location",
        "subsidiary",
        "department",
        "class",
        "account",
        "currency",
        "contact",
        "salesorder",
        "invoice",
        "purchaseorder",
        "transaction",
        "employee",
        "partner",
        "lead",
        "opportunity",
        "customrecord",
    ]

    working_tables = []

    for table in tables_to_test:
        query = f"SELECT * FROM {table} WHERE ROWNUM = 1"
        result = run_query(table, query)
        if result:
            print(f"  ✅ {table}: EXISTS")
            working_tables.append(table)
            # Show available fields
            if "items" in result and result["items"]:
                fields = list(result["items"][0].keys())
                print(f"     Fields: {', '.join(fields[:10])}")
                if len(fields) > 10:
                    print(f"     ... and {len(fields) - 10} more fields")
        else:
            # Try alternative names
            alt_query = f"SELECT * FROM {table}s WHERE ROWNUM = 1"  # Try plural
            alt_result = run_query(f"{table}s", alt_query)
            if alt_result:
                print(f"  ✅ {table}s: EXISTS (plural form)")
                working_tables.append(f"{table}s")

    # 2. Get detailed customer fields
    print("\n📋 Customer Table Schema")
    print("-" * 50)

    query = "SELECT * FROM customer WHERE ROWNUM = 1"
    result = run_query("customer_schema", query)
    if result and "items" in result and result["items"]:
        fields = list(result["items"][0].keys())
        print(f"Total fields: {len(fields)}")
        print("\nAvailable fields:")
        for field in sorted(fields):
            if field != "links":
                print(f"  - {field}")

    # 3. Test different query patterns
    print("\n🔬 Testing Query Patterns")
    print("-" * 50)

    test_queries = [
        {
            "name": "Customer with filters",
            "query": "SELECT id, entityid, companyname FROM customer WHERE companyname IS NOT NULL AND ROWNUM <= 5",
        },
        {
            "name": "Customer emails",
            "query": "SELECT id, entityid, email FROM customer WHERE email IS NOT NULL AND ROWNUM <= 5",
        },
        {
            "name": "Items basic",
            "query": "SELECT id, itemid, displayname FROM item WHERE ROWNUM <= 5",
        },
        {
            "name": "Vendor basic",
            "query": "SELECT id, entityid, companyname FROM vendor WHERE ROWNUM <= 5",
        },
        {
            "name": "Location basic",
            "query": "SELECT id, name FROM location WHERE ROWNUM <= 5",
        },
    ]

    for test in test_queries:
        result = run_query(test["name"], test["query"])
        if result and "items" in result:
            print(f"  ✅ {test['name']}: {len(result['items'])} records")
            if result["items"]:
                # Show first record
                print(
                    f"     Sample: {json.dumps(result['items'][0], indent=0)[:100]}..."
                )

    # 4. Test transactions with different approaches
    print("\n💰 Testing Transaction Tables")
    print("-" * 50)

    transaction_types = [
        "salesorder",
        "invoice",
        "cashsale",
        "creditmemo",
        "purchaseorder",
        "vendorbill",
        "itemfulfillment",
        "itemreceipt",
    ]

    for trans_type in transaction_types:
        # Try as direct table
        query = f"SELECT * FROM {trans_type} WHERE ROWNUM = 1"
        result = run_query(trans_type, query)
        if result:
            print(f"  ✅ {trans_type}: EXISTS as table")
            if "items" in result and result["items"]:
                fields = list(result["items"][0].keys())[:5]
                print(f"     Sample fields: {', '.join(fields)}")

    # 5. Summary
    print("\n" + "=" * 70)
    print("📊 DISCOVERY SUMMARY")
    print("=" * 70)

    print(f"\n✅ Working tables found: {len(working_tables)}")
    for table in working_tables:
        print(f"  - {table}")

    print("\n💡 Next Steps:")
    print("  1. Use discovered table names in your queries")
    print("  2. Check field names using SELECT * with ROWNUM = 1")
    print("  3. Build queries using available fields only")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    discover_schema()
