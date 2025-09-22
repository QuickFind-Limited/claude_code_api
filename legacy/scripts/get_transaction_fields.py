#!/usr/bin/env python3
"""
Get transaction table fields with retry logic and shorter queries
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


def get_transaction_fields():
    """Get transaction table fields reliably"""

    # Get credentials
    consumer_key = os.getenv("GYM_PLUS_COFFEE_CONSUMER_ID")
    consumer_secret = os.getenv("GYM_PLUS_COFFEE_CONSUMER_SECRET")
    token_id = os.getenv("GYM_PLUS_COFFEE_TOKEN_ID")
    token_secret = os.getenv("GYM_PLUS_COFFEE_TOKEN_SECRET")

    account_id = "7326096_SB1"
    url_account_id = "7326096-sb1"

    print("🔍 NetSuite Transaction Field Discovery")
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

    results = {}

    # =====================================
    # STEP 1: Get Transaction Fields (Simplified)
    # =====================================
    print("\n📊 GETTING TRANSACTION TABLE FIELDS")
    print("-" * 50)

    # Try different approaches to get fields
    queries = [
        {
            "name": "Sales Order Fields",
            "query": "SELECT * FROM transaction WHERE recordtype = 'salesorder' AND ROWNUM = 1",
        },
        {
            "name": "Any Transaction Fields",
            "query": "SELECT * FROM transaction WHERE id = 5708061",  # Using known ID from previous result
        },
        {
            "name": "Limited Fields Query",
            "query": "SELECT id, tranid, trandate, recordtype, entity FROM transaction WHERE ROWNUM = 1",
        },
    ]

    for q in queries:
        print(f"\nTrying: {q['name']}")
        payload = {"q": q["query"]}

        try:
            response = requests.post(
                suiteql_url,
                auth=auth,
                headers=headers,
                json=payload,
                timeout=10,  # Shorter timeout
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("items") and len(data["items"]) > 0:
                    fields = list(data["items"][0].keys())
                    fields = [f for f in fields if f != "links"]

                    print(f"✅ SUCCESS! Found {len(fields)} fields")
                    print("\nTransaction table fields:")
                    for i, field in enumerate(fields, 1):
                        print(f"  {i:3}. {field}")
                        if i % 5 == 0 and i < len(fields):
                            print()

                    results["transaction_fields"] = fields

                    # Save sample
                    with open("transaction_sample.json", "w") as f:
                        json.dump(data["items"][0], f, indent=2)
                    print("\n📁 Sample saved to: transaction_sample.json")

                    break  # Success, stop trying
                else:
                    print("   ⚠️  No data returned")
            else:
                print(f"   ❌ Status {response.status_code}")

        except requests.exceptions.Timeout:
            print("   ⏰ Timeout - query too slow")
        except Exception as e:
            print(f"   ❌ Error: {str(e)[:100]}")

        time.sleep(0.5)  # Short delay between attempts

    # =====================================
    # STEP 2: Get Transaction Types (Optimized)
    # =====================================
    print("\n" + "=" * 80)
    print("📊 GETTING TRANSACTION TYPES")
    print("-" * 50)

    # Simpler query without GROUP BY
    type_queries = [
        {
            "name": "Common Transaction Types",
            "query": """
                SELECT DISTINCT recordtype 
                FROM transaction 
                WHERE recordtype IN ('salesorder', 'invoice', 'cashsale', 'customerdeposit', 'estimate')
            """,
        },
        {
            "name": "Sample Types from Recent",
            "query": """
                SELECT recordtype, tranid, trandate
                FROM transaction
                WHERE ROWNUM <= 20
                ORDER BY id DESC
            """,
        },
    ]

    for q in type_queries:
        print(f"\nTrying: {q['name']}")
        payload = {"q": q["query"].strip()}

        try:
            response = requests.post(
                suiteql_url, auth=auth, headers=headers, json=payload, timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])

                if items:
                    print(f"✅ Found {len(items)} results")

                    # Extract unique types
                    types = set()
                    for item in items:
                        if "recordtype" in item:
                            types.add(item["recordtype"])

                    if types:
                        print("\nTransaction types found:")
                        for t in sorted(types):
                            print(f"  • {t}")

                        results["transaction_types"] = list(types)

                    # Show sample records
                    if "tranid" in items[0]:
                        print("\nSample transactions:")
                        for item in items[:5]:
                            print(
                                f"  • {item.get('recordtype', 'Unknown'):20} {item.get('tranid', 'N/A'):15} {item.get('trandate', 'N/A')}"
                            )

                    break
            else:
                print(f"   ❌ Status {response.status_code}")

        except requests.exceptions.Timeout:
            print("   ⏰ Timeout")
        except Exception as e:
            print(f"   ❌ Error: {str(e)[:100]}")

        time.sleep(0.5)

    # =====================================
    # STEP 3: Test Specific Transaction Access
    # =====================================
    print("\n" + "=" * 80)
    print("📊 TESTING SPECIFIC TRANSACTION ACCESS")
    print("-" * 50)

    specific_tests = [
        (
            "Sales Orders",
            "SELECT COUNT(*) as cnt FROM transaction WHERE recordtype = 'salesorder'",
        ),
        (
            "Invoices",
            "SELECT COUNT(*) as cnt FROM transaction WHERE recordtype = 'invoice'",
        ),
        (
            "Cash Sales",
            "SELECT COUNT(*) as cnt FROM transaction WHERE recordtype = 'cashsale'",
        ),
        (
            "Customer Deposits",
            "SELECT COUNT(*) as cnt FROM transaction WHERE recordtype = 'customerdeposit'",
        ),
        (
            "Estimates",
            "SELECT COUNT(*) as cnt FROM transaction WHERE recordtype = 'estimate'",
        ),
    ]

    for name, query in specific_tests:
        print(f"\n{name}:")
        payload = {"q": query}

        try:
            response = requests.post(
                suiteql_url, auth=auth, headers=headers, json=payload, timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("items"):
                    count = data["items"][0].get("cnt", 0)
                    print(f"  ✅ {count:,} records")

                    if name not in results:
                        results[name] = count
            else:
                print("  ❌ Cannot access")

        except:
            print("  ⏰ Timeout/Error")

        time.sleep(0.3)

    # =====================================
    # SAVE RESULTS
    # =====================================
    print("\n" + "=" * 80)
    print("💾 SAVING RESULTS")
    print("-" * 50)

    # Save to JSON
    with open("transaction_fields_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print("✅ Results saved to: transaction_fields_results.json")

    # Create markdown report
    with open("TRANSACTION_FIELDS.md", "w") as f:
        f.write("# NetSuite Transaction Fields Report\n\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n\n")

        if "transaction_fields" in results:
            f.write("## Transaction Table Fields\n\n")
            f.write(f"Total fields: {len(results['transaction_fields'])}\n\n")
            for field in results["transaction_fields"]:
                f.write(f"- `{field}`\n")

        if "transaction_types" in results:
            f.write("\n## Transaction Types Available\n\n")
            for t in sorted(results["transaction_types"]):
                f.write(f"- {t}\n")

        f.write("\n## Record Counts by Type\n\n")
        for key, value in results.items():
            if key not in ["transaction_fields", "transaction_types"]:
                f.write(f"- **{key}**: {value:,} records\n")

    print("✅ Report saved to: TRANSACTION_FIELDS.md")

    print("\n" + "=" * 80)
    print("🎉 FIELD DISCOVERY COMPLETE!")
    print("=" * 80)

    return results


if __name__ == "__main__":
    get_transaction_fields()
