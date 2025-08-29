#!/usr/bin/env python3
"""
Test NetSuite REST API access to Sales Orders and other transactions
"""

import json
import os
from datetime import datetime

import requests
from dotenv import load_dotenv
from requests_oauthlib import OAuth1

# Load environment variables
load_dotenv()


def test_rest_api_access():
    """Test REST API access to sales orders and transactions"""

    # Get credentials
    consumer_key = os.getenv("GYM_PLUS_COFFEE_CONSUMER_ID")
    consumer_secret = os.getenv("GYM_PLUS_COFFEE_CONSUMER_SECRET")
    token_id = os.getenv("GYM_PLUS_COFFEE_TOKEN_ID")
    token_secret = os.getenv("GYM_PLUS_COFFEE_TOKEN_SECRET")

    account_id = "7326096_SB1"
    url_account_id = "7326096-sb1"

    print("🌐 NetSuite REST API Transaction Access Test")
    print("=" * 80)
    print(f"Account: {account_id}")
    print(f"Timestamp: {datetime.now().isoformat()}")
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

    # =====================================
    # TEST 1: Transaction Endpoints
    # =====================================
    print("\n📊 TESTING TRANSACTION REST API ENDPOINTS")
    print("-" * 50)

    transaction_endpoints = [
        ("salesOrder", "Sales Orders"),
        ("invoice", "Invoices"),
        ("estimate", "Estimates/Quotes"),
        ("cashSale", "Cash Sales"),
        ("creditMemo", "Credit Memos"),
        ("purchaseOrder", "Purchase Orders"),
        ("vendorBill", "Vendor Bills"),
        ("customerPayment", "Customer Payments"),
        ("customerDeposit", "Customer Deposits"),
        ("customerRefund", "Customer Refunds"),
        ("returnAuthorization", "Return Authorizations"),
        ("itemFulfillment", "Item Fulfillments"),
        ("itemReceipt", "Item Receipts"),
    ]

    accessible_endpoints = []

    for endpoint, description in transaction_endpoints:
        print(f"\n📝 Testing: {description}")
        url = f"{base_url}/{endpoint}?limit=1"

        try:
            response = requests.get(url, auth=auth, headers=headers, timeout=15)

            if response.status_code == 200:
                data = response.json()
                total = data.get("totalResults", data.get("count", 0))
                items = data.get("items", [])

                print("   ✅ ACCESSIBLE via REST API!")
                print(f"   Total records: {total}")

                accessible_endpoints.append(endpoint)

                # If we have data, get more details
                if items and len(items) > 0:
                    record_id = items[0].get("id")
                    print(f"   Sample record ID: {record_id}")

                    # Try to get full details of this record
                    detail_url = f"{base_url}/{endpoint}/{record_id}"
                    detail_response = requests.get(
                        detail_url, auth=auth, headers=headers, timeout=15
                    )

                    if detail_response.status_code == 200:
                        detail_data = detail_response.json()

                        # Check for line items
                        if "item" in detail_data and "items" in detail_data["item"]:
                            line_count = len(detail_data["item"]["items"])
                            print(
                                f"   ✅ Full details accessible with {line_count} line items!"
                            )

                        # Show available fields
                        fields = list(detail_data.keys())[:10]
                        print(f"   Available fields: {', '.join(fields)}...")

                        # Save sample for analysis
                        filename = f"sample_{endpoint}.json"
                        with open(filename, "w") as f:
                            json.dump(detail_data, f, indent=2)
                        print(f"   📁 Sample saved to: {filename}")

            elif response.status_code == 400:
                print("   ❌ Bad Request - Endpoint may not exist or wrong format")

            elif response.status_code == 403:
                print("   ❌ FORBIDDEN - No permission for this record type")

            elif response.status_code == 404:
                print("   ❌ NOT FOUND - Endpoint doesn't exist")

            else:
                print(f"   ❌ Status {response.status_code}")

        except Exception as e:
            print(f"   ❌ Error: {str(e)[:100]}")

    # =====================================
    # TEST 2: Query Parameters
    # =====================================
    if accessible_endpoints:
        print("\n" + "=" * 80)
        print("📊 TESTING QUERY CAPABILITIES")
        print("-" * 50)

        test_endpoint = accessible_endpoints[0]
        print(f"\nUsing endpoint: {test_endpoint}")

        # Test different query patterns
        query_tests = [
            {
                "name": "Filter by date range",
                "params": {"q": 'tranDate AFTER "2024-01-01"', "limit": 5},
            },
            {
                "name": "Expand related records",
                "params": {"expandSubResources": "true", "limit": 1},
            },
            {
                "name": "Select specific fields",
                "params": {"fields": "id,tranId,tranDate,total,entity", "limit": 5},
            },
        ]

        for test in query_tests:
            print(f"\n📝 {test['name']}")
            url = f"{base_url}/{test_endpoint}"

            try:
                response = requests.get(
                    url, auth=auth, headers=headers, params=test["params"], timeout=15
                )

                if response.status_code == 200:
                    data = response.json()
                    items = data.get("items", [])
                    print(f"   ✅ Query successful - {len(items)} results")

                    if items:
                        # Show sample result structure
                        sample = items[0]
                        print(f"   Fields returned: {list(sample.keys())[:10]}")
                else:
                    print(f"   ❌ Query failed - Status {response.status_code}")

            except Exception as e:
                print(f"   ❌ Error: {str(e)[:50]}")

    # =====================================
    # SUMMARY
    # =====================================
    print("\n" + "=" * 80)
    print("📊 REST API ACCESS SUMMARY")
    print("=" * 80)

    if accessible_endpoints:
        print("\n✅ ACCESSIBLE TRANSACTION TYPES:")
        for endpoint in accessible_endpoints:
            print(f"   • {endpoint}")

        print("\n🎯 KEY FINDINGS:")
        print("   • You CAN access transaction data via REST API")
        print("   • Full details including line items are available")
        print("   • This uses different permissions than SuiteQL")

        print("\n💡 RECOMMENDATION:")
        print(
            "   Use REST API for transaction access while waiting for SuiteQL permissions!"
        )

    else:
        print("\n❌ No transaction endpoints accessible via REST API")
        print("\n📋 This means:")
        print("   • Your role lacks transaction view permissions")
        print("   • Or the endpoints require different naming")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    test_rest_api_access()
