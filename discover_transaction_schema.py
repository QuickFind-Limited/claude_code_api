#!/usr/bin/env python3
"""
Discover NetSuite transaction table schema and available fields
Now that we have access to the transaction table, let's explore what's available
"""

import json
import os
from datetime import datetime

import requests
from dotenv import load_dotenv
from requests_oauthlib import OAuth1

# Load environment variables
load_dotenv()


def discover_transaction_schema():
    """Discover transaction table schema and capabilities"""

    # Get credentials
    consumer_key = os.getenv("GYM_PLUS_COFFEE_CONSUMER_ID")
    consumer_secret = os.getenv("GYM_PLUS_COFFEE_CONSUMER_SECRET")
    token_id = os.getenv("GYM_PLUS_COFFEE_TOKEN_ID")
    token_secret = os.getenv("GYM_PLUS_COFFEE_TOKEN_SECRET")

    account_id = "7326096_SB1"
    url_account_id = "7326096-sb1"

    print("🎉 NetSuite Transaction Schema Discovery")
    print("=" * 80)
    print(f"Account: {account_id}")
    print("Total Transactions Available: 2,162,333+")
    print("=" * 80)

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
        "Prefer": "transient",
    }

    suiteql_url = f"https://{url_account_id}.suitetalk.api.netsuite.com/services/rest/query/v1/suiteql"

    schema_info = {
        "discovered_at": datetime.now().isoformat(),
        "transaction_table": {},
        "transactionline_table": {},
        "transaction_types": [],
        "sample_data": {},
    }

    # =====================================
    # STEP 1: Get Transaction Table Fields
    # =====================================
    print("\n📊 DISCOVERING TRANSACTION TABLE SCHEMA")
    print("-" * 50)

    # Get a sample transaction to see all fields
    query = "SELECT * FROM transaction WHERE ROWNUM = 1"
    payload = {"q": query}

    try:
        response = requests.post(
            suiteql_url, auth=auth, headers=headers, json=payload, timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("items") and len(data["items"]) > 0:
                fields = list(data["items"][0].keys())
                fields = [f for f in fields if f != "links"]

                print(f"✅ Transaction table has {len(fields)} fields")
                print("\nAvailable fields:")
                for i, field in enumerate(fields, 1):
                    print(f"  {i:3}. {field}")
                    if i % 5 == 0 and i < len(fields):
                        print()  # Add spacing for readability

                schema_info["transaction_table"]["fields"] = fields
                schema_info["transaction_table"]["field_count"] = len(fields)

                # Save sample record
                schema_info["sample_data"]["transaction"] = data["items"][0]
        else:
            print(f"❌ Error accessing transaction table: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {str(e)[:100]}")

    # =====================================
    # STEP 2: Get TransactionLine Fields
    # =====================================
    print("\n📊 DISCOVERING TRANSACTIONLINE TABLE SCHEMA")
    print("-" * 50)

    query = "SELECT * FROM transactionline WHERE ROWNUM = 1"
    payload = {"q": query}

    try:
        response = requests.post(
            suiteql_url, auth=auth, headers=headers, json=payload, timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("items") and len(data["items"]) > 0:
                fields = list(data["items"][0].keys())
                fields = [f for f in fields if f != "links"]

                print(f"✅ TransactionLine table has {len(fields)} fields")
                print("\nAvailable fields:")
                for i, field in enumerate(fields, 1):
                    print(f"  {i:3}. {field}")
                    if i % 5 == 0 and i < len(fields):
                        print()

                schema_info["transactionline_table"]["fields"] = fields
                schema_info["transactionline_table"]["field_count"] = len(fields)

                # Save sample record
                schema_info["sample_data"]["transactionline"] = data["items"][0]
        else:
            print(f"❌ Error accessing transactionline table: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {str(e)[:100]}")

    # =====================================
    # STEP 3: Get Transaction Types
    # =====================================
    print("\n📊 DISCOVERING TRANSACTION TYPES")
    print("-" * 50)

    query = """
        SELECT 
            recordtype,
            COUNT(*) as count
        FROM transaction
        GROUP BY recordtype
        ORDER BY count DESC
    """
    payload = {"q": query.strip()}

    try:
        response = requests.post(
            suiteql_url, auth=auth, headers=headers, json=payload, timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            items = data.get("items", [])

            print(f"✅ Found {len(items)} transaction types")
            print("\nTransaction Types by Volume:")

            total = 0
            for item in items[:30]:  # Show top 30
                recordtype = item.get("recordtype", "Unknown")
                count = item.get("count", 0)
                total += count
                print(f"  • {recordtype:30} {count:>10,} records")

                schema_info["transaction_types"].append(
                    {"type": recordtype, "count": count}
                )

            if len(items) > 30:
                print(f"  ... and {len(items) - 30} more types")

            print(f"\n  Total: {total:,} records")
        else:
            print(f"❌ Error getting transaction types: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {str(e)[:100]}")

    # =====================================
    # STEP 4: Test Sample Queries
    # =====================================
    print("\n📊 TESTING SAMPLE QUERIES")
    print("-" * 50)

    sample_queries = [
        {
            "name": "Recent Sales Orders",
            "query": """
                SELECT 
                    id,
                    tranid,
                    trandate,
                    entity,
                    recordtype
                FROM transaction
                WHERE recordtype = 'salesorder'
                AND ROWNUM <= 5
                ORDER BY id DESC
            """,
        },
        {
            "name": "Transaction with Line Items",
            "query": """
                SELECT 
                    t.id,
                    t.tranid,
                    t.recordtype,
                    tl.item,
                    tl.quantity,
                    tl.rate
                FROM transaction t
                JOIN transactionline tl ON t.id = tl.transaction
                WHERE t.recordtype = 'salesorder'
                AND ROWNUM <= 5
            """,
        },
        {
            "name": "Customer Transactions",
            "query": """
                SELECT 
                    t.id,
                    t.tranid,
                    t.recordtype,
                    c.companyname
                FROM transaction t
                LEFT JOIN customer c ON t.entity = c.id
                WHERE c.companyname IS NOT NULL
                AND ROWNUM <= 5
            """,
        },
    ]

    for sq in sample_queries:
        print(f"\n📝 {sq['name']}")
        payload = {"q": sq["query"].strip()}

        try:
            response = requests.post(
                suiteql_url, auth=auth, headers=headers, json=payload, timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                print(f"   ✅ Query successful - {len(items)} results")

                if items:
                    # Show first result
                    print(f"   Sample: {json.dumps(items[0], indent=2)[:300]}...")
                    schema_info["sample_data"][sq["name"]] = items
            else:
                print(f"   ❌ Query failed: {response.status_code}")
                # Try to get error details
                try:
                    error_data = response.json()
                    if "o:errorDetails" in error_data:
                        error_msg = error_data["o:errorDetails"][0].get("detail", "")
                        print(f"   Error: {error_msg[:200]}")
                except:
                    pass
        except Exception as e:
            print(f"   ❌ Error: {str(e)[:100]}")

    # =====================================
    # SAVE SCHEMA
    # =====================================
    print("\n" + "=" * 80)
    print("💾 SAVING SCHEMA INFORMATION")
    print("-" * 50)

    # Save to JSON file
    with open("netsuite_transaction_schema.json", "w") as f:
        json.dump(schema_info, f, indent=2)

    print("✅ Schema saved to: netsuite_transaction_schema.json")

    # Create a readable markdown report
    with open("TRANSACTION_SCHEMA.md", "w") as f:
        f.write("# NetSuite Transaction Schema\n\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n\n")
        f.write(f"Account: {account_id}\n\n")

        f.write("## Transaction Table\n\n")
        f.write(
            f"- **Total Fields**: {schema_info['transaction_table'].get('field_count', 0)}\n"
        )
        f.write("- **Total Records**: 2,162,333+\n\n")

        f.write("### Available Fields:\n\n")
        fields = schema_info["transaction_table"].get("fields", [])
        for field in fields:
            f.write(f"- `{field}`\n")

        f.write("\n## TransactionLine Table\n\n")
        f.write(
            f"- **Total Fields**: {schema_info['transactionline_table'].get('field_count', 0)}\n\n"
        )

        f.write("### Available Fields:\n\n")
        fields = schema_info["transactionline_table"].get("fields", [])
        for field in fields:
            f.write(f"- `{field}`\n")

        f.write("\n## Transaction Types\n\n")
        f.write("| Type | Record Count |\n")
        f.write("|------|-------------:|\n")
        for tt in schema_info["transaction_types"][:30]:
            f.write(f"| {tt['type']} | {tt['count']:,} |\n")

    print("✅ Markdown report saved to: TRANSACTION_SCHEMA.md")

    print("\n" + "=" * 80)
    print("🎉 SCHEMA DISCOVERY COMPLETE!")
    print("=" * 80)

    return schema_info


if __name__ == "__main__":
    discover_transaction_schema()
