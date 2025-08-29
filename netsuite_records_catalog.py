#!/usr/bin/env python3
"""
NetSuite Records Catalog API Discovery
Based on Tim Dietrich's technique: https://timdietrich.me/blog/netsuite-records-catalog-api/
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


def discover_records_catalog():
    """Use NetSuite Records Catalog API to discover all tables and fields"""

    # Get credentials
    consumer_key = os.getenv("GYM_PLUS_COFFEE_CONSUMER_ID")
    consumer_secret = os.getenv("GYM_PLUS_COFFEE_CONSUMER_SECRET")
    token_id = os.getenv("GYM_PLUS_COFFEE_TOKEN_ID")
    token_secret = os.getenv("GYM_PLUS_COFFEE_TOKEN_SECRET")

    account_id = "7326096_SB1"
    url_account_id = "7326096-sb1"

    print("🔍 NetSuite Records Catalog Discovery")
    print("=" * 70)
    print(f"Account: {account_id}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 70)

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
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "GYM+Coffee Records Catalog Discovery/1.0",
    }

    # Method 1: Try the Records Catalog endpoint directly
    print("\n📚 Method 1: Records Catalog API Endpoint")
    print("-" * 50)

    # Build the Records Catalog endpoint URL
    rc_endpoint = (
        f"https://{url_account_id}.app.netsuite.com/app/recordscatalog/rcendpoint.nl"
    )

    # First, try to get record types
    params = {"action": "getRecordTypes", "data": json.dumps({"structureType": "FLAT"})}

    try:
        response = requests.get(
            rc_endpoint, params=params, auth=auth, headers=headers, timeout=30
        )

        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            try:
                record_types = response.json()
                if "data" in record_types:
                    print(f"✅ Found {len(record_types['data'])} record types")

                    # Save record types to file
                    with open("netsuite_record_types.json", "w") as f:
                        json.dump(record_types, f, indent=2)
                    print("📁 Saved to netsuite_record_types.json")

                    # Show first 10 record types
                    print("\nSample Record Types:")
                    for rt in record_types["data"][:10]:
                        print(f"  - {rt.get('id', 'N/A')}: {rt.get('name', 'N/A')}")

                    # Now try to get details for a few record types
                    print("\n📋 Getting Record Type Details...")
                    schema = []

                    # Just get details for first 5 types as a demo
                    for rt in record_types["data"][:5]:
                        record_id = rt.get("id")
                        print(f"  Loading {record_id}...", end="")

                        detail_params = {
                            "action": "getRecordTypeDetail",
                            "data": json.dumps(
                                {"scriptId": record_id, "detailType": "SS_ANAL"}
                            ),
                        }

                        try:
                            detail_response = requests.get(
                                rc_endpoint,
                                params=detail_params,
                                auth=auth,
                                headers=headers,
                                timeout=30,
                            )

                            if detail_response.status_code == 200:
                                detail_data = detail_response.json()
                                schema.append(detail_data.get("data"))
                                print(" ✅")
                            else:
                                print(f" ❌ Status {detail_response.status_code}")

                            time.sleep(0.5)  # Be nice to the API

                        except Exception as e:
                            print(f" ❌ Error: {e}")

                    if schema:
                        with open("netsuite_schema_sample.json", "w") as f:
                            json.dump(schema, f, indent=2)
                        print("\n📁 Sample schema saved to netsuite_schema_sample.json")
                else:
                    print(
                        "Response structure:", json.dumps(record_types, indent=2)[:500]
                    )
            except json.JSONDecodeError:
                print("Response is not JSON:", response.text[:500])
        else:
            print("Failed to access Records Catalog API")
            print(f"Response: {response.text[:500]}")

    except Exception as e:
        print(f"Error accessing Records Catalog: {e}")

    # Method 2: Use REST API metadata endpoint
    print("\n📚 Method 2: REST API Metadata Catalog")
    print("-" * 50)

    metadata_url = f"https://{url_account_id}.suitetalk.api.netsuite.com/services/rest/record/v1/metadata-catalog"

    try:
        response = requests.get(metadata_url, auth=auth, headers=headers, timeout=30)

        if response.status_code == 200:
            metadata = response.json()
            items = metadata.get("items", [])

            print(f"✅ Found {len(items)} record types via REST API")

            # Save to file
            with open("netsuite_metadata_catalog.json", "w") as f:
                json.dump(metadata, f, indent=2)
            print("📁 Saved to netsuite_metadata_catalog.json")

            # Group by type and show summary
            record_types = {}
            for item in items:
                name = item.get("name", "unknown")
                # Extract base type (before underscore for custom records)
                if name.startswith("customrecord_"):
                    base_type = "customrecord"
                elif name.startswith("customlist"):
                    base_type = "customlist"
                else:
                    base_type = name

                if base_type not in record_types:
                    record_types[base_type] = []
                record_types[base_type].append(name)

            print("\nRecord Types Summary:")
            for base_type, names in sorted(record_types.items())[:20]:
                print(f"  {base_type}: {len(names)} tables")
                if len(names) <= 3:
                    for name in names:
                        print(f"    - {name}")

    except Exception as e:
        print(f"Error accessing metadata catalog: {e}")

    # Method 3: Use SuiteQL to query analytics tables
    print("\n📚 Method 3: SuiteQL Analytics Tables Discovery")
    print("-" * 50)

    suiteql_url = f"https://{url_account_id}.suitetalk.api.netsuite.com/services/rest/query/v1/suiteql"

    # Try to discover tables using SuiteQL patterns
    discovery_queries = [
        {
            "name": "Transaction Analytics",
            "query": "SELECT * FROM transaction WHERE ROWNUM = 1",
        },
        {
            "name": "Transaction Lines",
            "query": "SELECT * FROM transactionline WHERE ROWNUM = 1",
        },
        {
            "name": "Analytics Tables",
            "query": "SELECT DISTINCT recordtype FROM transaction WHERE ROWNUM <= 10",
        },
        {
            "name": "Item Analytics",
            "query": "SELECT DISTINCT itemtype FROM item WHERE ROWNUM <= 10",
        },
    ]

    for dq in discovery_queries:
        payload = {"q": dq["query"]}

        try:
            response = requests.post(
                suiteql_url,
                auth=auth,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                json=payload,
                timeout=30,
            )

            if response.status_code == 200:
                data = response.json()
                if "items" in data:
                    print(f"✅ {dq['name']}: Found {len(data['items'])} results")
                    if data["items"] and len(data["items"][0]) > 0:
                        # Show fields found
                        fields = list(data["items"][0].keys())
                        print(f"   Fields: {', '.join(fields[:10])}")
                        if len(fields) > 10:
                            print(f"   ... and {len(fields) - 10} more fields")
            else:
                print(
                    f"❌ {dq['name']}: Query failed with status {response.status_code}"
                )

        except Exception as e:
            print(f"❌ {dq['name']}: Error - {str(e)[:50]}")

    # Method 4: Get detailed schema for specific tables
    print("\n📊 Method 4: Detailed Table Schema via SuiteQL")
    print("-" * 50)

    tables_to_detail = ["customer", "vendor", "item", "location"]
    detailed_schema = {}

    for table in tables_to_detail:
        query = f"SELECT * FROM {table} WHERE ROWNUM = 1"
        payload = {"q": query}

        try:
            response = requests.post(
                suiteql_url,
                auth=auth,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                json=payload,
                timeout=30,
            )

            if response.status_code == 200:
                data = response.json()
                if "items" in data and data["items"]:
                    fields = list(data["items"][0].keys())
                    detailed_schema[table] = {
                        "field_count": len(fields),
                        "fields": [f for f in fields if f != "links"],
                    }
                    print(f"✅ {table}: {len(fields)} fields discovered")

        except Exception as e:
            print(f"❌ {table}: Error - {e}")

    # Save detailed schema
    if detailed_schema:
        with open("netsuite_detailed_schema.json", "w") as f:
            json.dump(detailed_schema, f, indent=2)
        print("\n📁 Detailed schema saved to netsuite_detailed_schema.json")

    # Summary
    print("\n" + "=" * 70)
    print("📊 DISCOVERY COMPLETE")
    print("=" * 70)

    print("\n📁 Generated Files:")
    print("  - netsuite_metadata_catalog.json: REST API metadata")
    print("  - netsuite_detailed_schema.json: Table field details")
    print("  - netsuite_record_types.json: Records Catalog types (if accessible)")
    print("  - netsuite_schema_sample.json: Sample schema details (if accessible)")

    print("\n💡 Next Steps:")
    print("  1. Review the generated JSON files for available tables")
    print("  2. Use discovered table and field names in SuiteQL queries")
    print("  3. Check metadata catalog for custom records and fields")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    discover_records_catalog()
