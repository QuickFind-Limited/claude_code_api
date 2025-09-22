#!/usr/bin/env python3
"""
Debug REST API access - get detailed error messages
"""

import json
import os

import requests
from dotenv import load_dotenv
from requests_oauthlib import OAuth1

# Load environment variables
load_dotenv()


def debug_rest_api():
    """Debug REST API access with detailed error capture"""

    # Get credentials
    consumer_key = os.getenv("GYM_PLUS_COFFEE_CONSUMER_ID")
    consumer_secret = os.getenv("GYM_PLUS_COFFEE_CONSUMER_SECRET")
    token_id = os.getenv("GYM_PLUS_COFFEE_TOKEN_ID")
    token_secret = os.getenv("GYM_PLUS_COFFEE_TOKEN_SECRET")

    account_id = "7326096_SB1"
    url_account_id = "7326096-sb1"

    print("🔍 NetSuite REST API Debug")
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

    headers = {"Accept": "application/json", "Content-Type": "application/json"}

    base_url = (
        f"https://{url_account_id}.suitetalk.api.netsuite.com/services/rest/record/v1"
    )

    # Test different endpoint formats
    test_cases = [
        {"name": "Sales Order (camelCase)", "url": f"{base_url}/salesOrder?limit=1"},
        {"name": "Sales Order (lowercase)", "url": f"{base_url}/salesorder?limit=1"},
        {"name": "Sales Order (PascalCase)", "url": f"{base_url}/SalesOrder?limit=1"},
        {"name": "Invoice (camelCase)", "url": f"{base_url}/invoice?limit=1"},
        {"name": "Customer (known working)", "url": f"{base_url}/customer?limit=1"},
        {
            "name": "OpenAPI specification",
            "url": f"https://{url_account_id}.suitetalk.api.netsuite.com/services/rest/openapi/v1",
        },
        {
            "name": "Record types listing",
            "url": f"https://{url_account_id}.suitetalk.api.netsuite.com/services/rest/record/v1",
        },
    ]

    for test in test_cases:
        print(f"\n📝 {test['name']}")
        print(f"   URL: {test['url']}")

        try:
            response = requests.get(test["url"], auth=auth, headers=headers, timeout=15)

            print(f"   Status: {response.status_code}")

            if response.status_code == 200:
                print("   ✅ SUCCESS!")
                data = response.json() if response.text else {}

                # Show response structure
                if isinstance(data, dict):
                    keys = list(data.keys())[:10]
                    print(f"   Response keys: {keys}")

                    # For list endpoints, show count
                    if "items" in data:
                        print(f"   Items: {len(data['items'])}")
                    if "totalResults" in data:
                        print(f"   Total: {data['totalResults']}")
                    if "count" in data:
                        print(f"   Count: {data['count']}")

            else:
                # Try to get detailed error
                try:
                    error_data = response.json()
                    print(
                        f"   Error response: {json.dumps(error_data, indent=2)[:500]}"
                    )
                except:
                    print(f"   Raw error: {response.text[:300]}")

        except Exception as e:
            print(f"   ❌ Exception: {str(e)}")

    # Test metadata catalog for available record types
    print("\n" + "=" * 80)
    print("📋 CHECKING AVAILABLE RECORD TYPES")
    print("-" * 50)

    metadata_url = f"https://{url_account_id}.suitetalk.api.netsuite.com/services/rest/record/v1/metadata-catalog"

    try:
        response = requests.get(metadata_url, auth=auth, headers=headers, timeout=15)

        if response.status_code == 200:
            data = response.json()
            items = data.get("items", [])

            # Look for transaction-related records
            transaction_records = [
                item
                for item in items
                if any(
                    keyword in item["name"].lower()
                    for keyword in [
                        "sale",
                        "invoice",
                        "order",
                        "transaction",
                        "bill",
                        "payment",
                    ]
                )
            ]

            if transaction_records:
                print("\n✅ Transaction-related records in metadata:")
                for record in transaction_records[:20]:
                    print(f"   • {record['name']}")

                    # Check if we can access the first one
                    if transaction_records:
                        test_record = transaction_records[0]["name"]
                        test_url = f"{base_url}/{test_record}?limit=1"

                        print(f"\n📝 Testing access to: {test_record}")
                        test_response = requests.get(
                            test_url, auth=auth, headers=headers, timeout=10
                        )

                        if test_response.status_code == 200:
                            print(f"   ✅ Can access {test_record}!")
                        else:
                            print(
                                f"   ❌ Cannot access {test_record} - Status {test_response.status_code}"
                            )
            else:
                print("❌ No transaction records found in metadata")

    except Exception as e:
        print(f"Error checking metadata: {e}")

    print("\n" + "=" * 80)
    print("📊 DIAGNOSIS")
    print("=" * 80)

    print("""
Based on the tests:

1. If customer works but salesOrder doesn't:
   → Transaction permissions are missing
   → REST API requires same permissions as UI
   
2. If you get 400 Bad Request:
   → The endpoint name might be wrong
   → Or the record type isn't exposed via REST API
   
3. Check the metadata catalog:
   → Shows which records are available
   → Not all records are REST-enabled
    """)


if __name__ == "__main__":
    debug_rest_api()
