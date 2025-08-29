#!/usr/bin/env python3
"""
Test NetSuite SuiteQL API with TBA Authentication
"""

import json
import os
from datetime import datetime

import requests
from dotenv import load_dotenv
from requests_oauthlib import OAuth1

# Load environment variables
load_dotenv()


def test_suiteql():
    """Test NetSuite SuiteQL queries with TBA authentication"""

    # Get credentials from environment variables
    consumer_key = os.getenv("GYM_PLUS_COFFEE_CONSUMER_ID")
    consumer_secret = os.getenv("GYM_PLUS_COFFEE_CONSUMER_SECRET")
    token_id = os.getenv("GYM_PLUS_COFFEE_TOKEN_ID")
    token_secret = os.getenv("GYM_PLUS_COFFEE_TOKEN_SECRET")

    # Your NetSuite account configuration
    account_id = "7326096_SB1"
    url_account_id = "7326096-sb1"

    print("🔍 NetSuite SuiteQL Test")
    print("=" * 70)
    print(f"Account: {account_id}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 70)

    # SuiteQL endpoint
    suiteql_url = f"https://{url_account_id}.suitetalk.api.netsuite.com/services/rest/query/v1/suiteql"

    # Setup OAuth1 authentication for TBA
    auth = OAuth1(
        client_key=consumer_key,
        client_secret=consumer_secret,
        resource_owner_key=token_id,
        resource_owner_secret=token_secret,
        signature_method="HMAC-SHA256",
        realm=account_id,
    )

    # Headers for SuiteQL
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Prefer": "transient",  # Optional: controls query result behavior
    }

    # Test queries
    queries = [
        {
            "name": "Customer List with Details",
            "query": """
                SELECT 
                    id,
                    entityid,
                    companyname,
                    firstname,
                    lastname,
                    email,
                    phone,
                    datecreated
                FROM customer 
                WHERE ROWNUM <= 10
            """,
        },
        {
            "name": "Inventory Items",
            "query": """
                SELECT 
                    id,
                    itemid,
                    displayname,
                    salesdescription,
                    baseprice,
                    quantityavailable
                FROM item 
                WHERE itemtype = 'InvtPart'
                AND ROWNUM <= 10
            """,
        },
        {
            "name": "Vendor List",
            "query": """
                SELECT 
                    id,
                    entityid,
                    companyname,
                    email,
                    phone,
                    isactive
                FROM vendor 
                WHERE ROWNUM <= 10
            """,
        },
        {
            "name": "Sales Orders (Recent)",
            "query": """
                SELECT 
                    id,
                    tranid,
                    trandate,
                    entity,
                    total,
                    status
                FROM transaction
                WHERE recordtype = 'salesorder'
                AND ROWNUM <= 10
                ORDER BY trandate DESC
            """,
        },
        {
            "name": "Location List",
            "query": """
                SELECT 
                    id,
                    name,
                    fullname,
                    isactive,
                    makeinventoryavailable
                FROM location
                WHERE ROWNUM <= 10
            """,
        },
        {
            "name": "Employee List",
            "query": """
                SELECT 
                    id,
                    entityid,
                    firstname,
                    lastname,
                    email,
                    title,
                    hiredate
                FROM employee
                WHERE ROWNUM <= 10
            """,
        },
        {
            "name": "All Available Tables (Schema Discovery)",
            "query": """
                SELECT DISTINCT 
                    table_name
                FROM information_schema.tables
                WHERE table_schema = 'PUBLIC'
                AND ROWNUM <= 20
                ORDER BY table_name
            """,
        },
        {
            "name": "Customer Count",
            "query": "SELECT COUNT(*) as total_customers FROM customer",
        },
    ]

    # Execute each query
    for query_info in queries:
        print(f"\n📊 {query_info['name']}")
        print("-" * 50)

        # Prepare the query payload
        payload = {"q": query_info["query"].strip()}

        try:
            # Make the SuiteQL request
            response = requests.post(
                suiteql_url, auth=auth, headers=headers, json=payload, timeout=30
            )

            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()

                # Check if we have items/rows
                if "items" in data:
                    items = data["items"]
                    print(f"✅ SUCCESS - Retrieved {len(items)} records")

                    # Display the data
                    if items:
                        print("\nResults:")

                        # For first 3 records, show all fields
                        for i, item in enumerate(items[:3], 1):
                            print(f"\n  Record #{i}:")
                            for key, value in item.items():
                                # Truncate long values
                                if isinstance(value, str) and len(str(value)) > 50:
                                    value = str(value)[:50] + "..."
                                print(f"    {key}: {value}")

                        if len(items) > 3:
                            print(f"\n  ... and {len(items) - 3} more records")
                    else:
                        print("No records found")

                elif "value" in data:
                    # For aggregation queries
                    print(f"✅ Result: {data['value']}")

                else:
                    # Show the raw response structure
                    print("✅ Response received:")
                    print(json.dumps(data, indent=2)[:500])

            elif response.status_code == 400:
                print("❌ Bad Request - Query syntax error or invalid table/field")
                error_data = response.json()
                if "o:errorDetails" in error_data:
                    for error in error_data["o:errorDetails"]:
                        print(f"  Error: {error.get('detail', 'Unknown error')}")
                else:
                    print(f"  Error: {response.text[:200]}")

            elif response.status_code == 401:
                print("❌ Unauthorized - Authentication failed")

            elif response.status_code == 403:
                print("⚠️  Forbidden - Insufficient permissions")

            else:
                print(f"❌ Unexpected status: {response.status_code}")
                print(f"Response: {response.text[:200]}")

        except requests.exceptions.Timeout:
            print("⏱️  Request timed out (30 seconds)")

        except requests.exceptions.ConnectionError as e:
            print(f"🔌 Connection error: {str(e)[:100]}")

        except Exception as e:
            print(f"❌ Error: {type(e).__name__}: {str(e)[:100]}")

    # Test a custom query if needed
    print("\n" + "=" * 70)
    print("📝 Custom Query Test")
    print("-" * 50)

    custom_query = """
        SELECT 
            c.id,
            c.entityid as customer_id,
            c.companyname,
            COUNT(t.id) as order_count
        FROM customer c
        LEFT JOIN transaction t ON t.entity = c.id AND t.recordtype = 'salesorder'
        WHERE c.id IS NOT NULL
        GROUP BY c.id, c.entityid, c.companyname
        HAVING COUNT(t.id) > 0
        AND ROWNUM <= 5
    """

    payload = {"q": custom_query.strip()}

    try:
        response = requests.post(
            suiteql_url, auth=auth, headers=headers, json=payload, timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            if "items" in data:
                print(
                    f"✅ Custom query successful - {len(data['items'])} customers with orders found"
                )
                for item in data["items"]:
                    print(
                        f"  Customer: {item.get('companyname', 'N/A')} - Orders: {item.get('order_count', 0)}"
                    )
        else:
            print(f"Custom query failed with status {response.status_code}")

    except Exception as e:
        print(f"Custom query error: {e}")

    print("\n" + "=" * 70)
    print("✅ SuiteQL testing complete!")
    print("=" * 70)


if __name__ == "__main__":
    test_suiteql()
