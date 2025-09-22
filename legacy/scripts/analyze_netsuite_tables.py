#!/usr/bin/env python3
"""
Analyze and test all discovered NetSuite tables via SuiteQL
"""

import json
import os
import time
from datetime import datetime

import requests
from dotenv import load_dotenv
from requests_oauthlib import OAuth1

# Load environment variables
load_dotenv()


def analyze_all_tables():
    """Analyze all tables from metadata catalog"""

    # Get credentials
    consumer_key = os.getenv("GYM_PLUS_COFFEE_CONSUMER_ID")
    consumer_secret = os.getenv("GYM_PLUS_COFFEE_CONSUMER_SECRET")
    token_id = os.getenv("GYM_PLUS_COFFEE_TOKEN_ID")
    token_secret = os.getenv("GYM_PLUS_COFFEE_TOKEN_SECRET")

    account_id = "7326096_SB1"
    url_account_id = "7326096-sb1"

    print("📊 NetSuite Complete Table Analysis")
    print("=" * 70)
    print(f"Account: {account_id}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 70)

    # Load metadata catalog
    try:
        with open("netsuite_metadata_catalog.json", "r") as f:
            metadata = json.load(f)
    except FileNotFoundError:
        print("❌ Error: netsuite_metadata_catalog.json not found")
        print("Please run netsuite_records_catalog.py first")
        return

    # Setup OAuth1 authentication
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

    suiteql_url = f"https://{url_account_id}.suitetalk.api.netsuite.com/services/rest/query/v1/suiteql"

    # Extract all table names
    all_tables = [item["name"] for item in metadata.get("items", [])]

    print(f"\n📋 Total tables found: {len(all_tables)}")

    # Categorize tables
    standard_tables = []
    custom_records = []
    custom_lists = []

    for table in all_tables:
        if table.startswith("customrecord_"):
            custom_records.append(table)
        elif table.startswith("customlist"):
            custom_lists.append(table)
        else:
            standard_tables.append(table)

    print("\n📂 Table Categories:")
    print(f"  Standard Tables: {len(standard_tables)}")
    print(f"  Custom Records: {len(custom_records)}")
    print(f"  Custom Lists: {len(custom_lists)}")

    # Test access to different table types
    print("\n" + "=" * 70)
    print("🔍 TESTING TABLE ACCESS VIA SUITEQL")
    print("=" * 70)

    working_tables = {}
    failed_tables = []

    # Test a sample of each type
    tables_to_test = []

    # Add first 20 standard tables
    tables_to_test.extend(standard_tables[:20])

    # Add first 5 custom records
    tables_to_test.extend(custom_records[:5])

    # Add first 5 custom lists
    tables_to_test.extend(custom_lists[:5])

    print(f"\nTesting {len(tables_to_test)} sample tables...")
    print("-" * 50)

    for i, table in enumerate(tables_to_test, 1):
        print(f"{i:3}. Testing '{table}'...", end=" ")

        # Try simple query
        query = f"SELECT * FROM {table} WHERE ROWNUM = 1"
        payload = {"q": query}

        try:
            response = requests.post(
                suiteql_url, auth=auth, headers=headers, json=payload, timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if "items" in data:
                    if data["items"]:
                        fields = list(data["items"][0].keys())
                        working_tables[table] = {
                            "fields": [f for f in fields if f != "links"],
                            "field_count": len(fields) - 1
                            if "links" in fields
                            else len(fields),
                        }
                        print(f"✅ ({len(fields)} fields)")
                    else:
                        # Table exists but is empty
                        working_tables[table] = {
                            "fields": [],
                            "field_count": 0,
                            "note": "empty",
                        }
                        print("✅ (empty table)")
                else:
                    print("⚠️  (unexpected response)")
                    failed_tables.append(table)
            else:
                print(f"❌ (status {response.status_code})")
                failed_tables.append(table)

        except requests.exceptions.Timeout:
            print("⏱️  (timeout)")
            failed_tables.append(table)
        except Exception as e:
            print(f"❌ ({str(e)[:20]})")
            failed_tables.append(table)

        # Be nice to the API
        if i % 10 == 0:
            time.sleep(1)

    # Show working standard tables
    print("\n" + "=" * 70)
    print("✅ WORKING STANDARD TABLES")
    print("=" * 70)

    standard_working = {
        k: v for k, v in working_tables.items() if not k.startswith("custom")
    }

    for table_name in sorted(standard_working.keys()):
        info = standard_working[table_name]
        print(f"\n📊 {table_name}")
        print(f"   Fields: {info['field_count']}")
        if info.get("fields"):
            # Show first 10 fields
            sample_fields = info["fields"][:10]
            for field in sample_fields:
                print(f"   - {field}")
            if len(info["fields"]) > 10:
                print(f"   ... and {len(info['fields']) - 10} more fields")

    # Show some custom records
    print("\n" + "=" * 70)
    print("🔧 SAMPLE CUSTOM RECORDS")
    print("=" * 70)

    custom_working = {
        k: v for k, v in working_tables.items() if k.startswith("customrecord_")
    }

    for table_name in list(custom_working.keys())[:5]:
        info = custom_working[table_name]
        print(f"\n📊 {table_name}")
        print(f"   Fields: {info['field_count']}")

    # Save detailed results
    results = {
        "timestamp": datetime.now().isoformat(),
        "account_id": account_id,
        "summary": {
            "total_tables": len(all_tables),
            "standard_tables": len(standard_tables),
            "custom_records": len(custom_records),
            "custom_lists": len(custom_lists),
            "tested": len(tables_to_test),
            "working": len(working_tables),
            "failed": len(failed_tables),
        },
        "working_tables": working_tables,
        "failed_tables": failed_tables,
        "all_standard_tables": standard_tables,
        "sample_custom_records": custom_records[:20],
        "sample_custom_lists": custom_lists[:20],
    }

    with open("netsuite_table_analysis.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 70)
    print("📊 ANALYSIS SUMMARY")
    print("=" * 70)

    print(f"\n✅ Successfully accessed: {len(working_tables)} tables")
    print(f"❌ Failed to access: {len(failed_tables)} tables")
    print("📁 Full results saved to: netsuite_table_analysis.json")

    # Test some specific queries on working tables
    print("\n" + "=" * 70)
    print("🔍 SAMPLE DATA QUERIES")
    print("=" * 70)

    sample_queries = [
        {
            "name": "Customers with email",
            "query": "SELECT id, entityid, companyname, email FROM customer WHERE email IS NOT NULL AND ROWNUM <= 3",
        },
        {
            "name": "Active items",
            "query": "SELECT id, itemid, displayname FROM item WHERE isinactive = 'F' AND ROWNUM <= 3",
        },
        {
            "name": "Locations",
            "query": "SELECT id, name, fullname FROM location WHERE ROWNUM <= 3",
        },
        {
            "name": "Vendors",
            "query": "SELECT id, entityid, companyname FROM vendor WHERE ROWNUM <= 3",
        },
    ]

    for sq in sample_queries:
        print(f"\n📝 {sq['name']}")
        print("-" * 40)

        payload = {"q": sq["query"]}

        try:
            response = requests.post(
                suiteql_url, auth=auth, headers=headers, json=payload, timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if "items" in data and data["items"]:
                    for item in data["items"]:
                        print(f"  • {json.dumps(item, indent=0)[:100]}")
                else:
                    print("  No results found")
            else:
                print(f"  Query failed: Status {response.status_code}")

        except Exception as e:
            print(f"  Error: {e}")

    print("\n" + "=" * 70)
    print("✅ Analysis complete!")
    print("=" * 70)


if __name__ == "__main__":
    analyze_all_tables()
