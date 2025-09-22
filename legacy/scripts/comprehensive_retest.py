#!/usr/bin/env python3
"""
Comprehensive retest of all NetSuite access methods
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


def comprehensive_retest():
    """Complete retest of all access methods"""

    # Get credentials
    consumer_key = os.getenv("GYM_PLUS_COFFEE_CONSUMER_ID")
    consumer_secret = os.getenv("GYM_PLUS_COFFEE_CONSUMER_SECRET")
    token_id = os.getenv("GYM_PLUS_COFFEE_TOKEN_ID")
    token_secret = os.getenv("GYM_PLUS_COFFEE_TOKEN_SECRET")

    account_id = "7326096_SB1"
    url_account_id = "7326096-sb1"

    print("🔄 NetSuite Comprehensive Access Retest")
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

    results = {
        "timestamp": datetime.now().isoformat(),
        "suiteql": {"working": [], "failed": []},
        "rest_api": {"working": [], "failed": []},
        "changes": [],
    }

    # =====================================
    # SECTION 1: SuiteQL Testing
    # =====================================
    print("\n📊 SECTION 1: SUITEQL ACCESS TEST")
    print("-" * 50)

    suiteql_url = f"https://{url_account_id}.suitetalk.api.netsuite.com/services/rest/query/v1/suiteql"
    headers_suiteql = headers.copy()
    headers_suiteql["Prefer"] = "transient"

    suiteql_tests = [
        (
            "Basic Tables",
            [
                ("customer", "SELECT COUNT(*) as cnt FROM customer"),
                ("vendor", "SELECT COUNT(*) as cnt FROM vendor"),
                ("item", "SELECT COUNT(*) as cnt FROM item"),
                ("location", "SELECT COUNT(*) as cnt FROM location"),
                ("subsidiary", "SELECT COUNT(*) as cnt FROM subsidiary"),
                ("department", "SELECT COUNT(*) as cnt FROM department"),
                ("account", "SELECT COUNT(*) as cnt FROM account"),
            ],
        ),
        (
            "Transaction Tables",
            [
                ("transaction", "SELECT * FROM transaction WHERE ROWNUM = 1"),
                ("transactionline", "SELECT * FROM transactionline WHERE ROWNUM = 1"),
                (
                    "transactionaccountingline",
                    "SELECT * FROM transactionaccountingline WHERE ROWNUM = 1",
                ),
            ],
        ),
        (
            "Specific Transactions",
            [
                (
                    "salesorder",
                    "SELECT * FROM transaction WHERE recordtype = 'salesorder' AND ROWNUM = 1",
                ),
                (
                    "invoice",
                    "SELECT * FROM transaction WHERE recordtype = 'invoice' AND ROWNUM = 1",
                ),
                (
                    "cashsale",
                    "SELECT * FROM transaction WHERE recordtype = 'cashsale' AND ROWNUM = 1",
                ),
                (
                    "purchaseorder",
                    "SELECT * FROM transaction WHERE recordtype = 'purchaseorder' AND ROWNUM = 1",
                ),
            ],
        ),
        (
            "Alternative Approaches",
            [
                ("sales_order_table", "SELECT * FROM salesorder WHERE ROWNUM = 1"),
                ("invoice_table", "SELECT * FROM invoice WHERE ROWNUM = 1"),
                ("tranline", "SELECT * FROM tranline WHERE ROWNUM = 1"),
                ("trans", "SELECT * FROM trans WHERE ROWNUM = 1"),
            ],
        ),
    ]

    for section_name, tests in suiteql_tests:
        print(f"\n{section_name}:")
        for table_name, query in tests:
            payload = {"q": query}
            try:
                response = requests.post(
                    suiteql_url,
                    auth=auth,
                    headers=headers_suiteql,
                    json=payload,
                    timeout=10,
                )

                if response.status_code == 200:
                    data = response.json()
                    if "items" in data:
                        if data["items"]:
                            # Get count or record info
                            if "cnt" in query:
                                count = data["items"][0].get("cnt", 0)
                                print(f"  ✅ {table_name}: {count} records")
                            else:
                                fields = list(data["items"][0].keys())
                                print(
                                    f"  ✅ {table_name}: Accessible ({len(fields)} fields)"
                                )
                        else:
                            print(f"  ✅ {table_name}: Accessible (no data)")
                        results["suiteql"]["working"].append(table_name)
                else:
                    print(f"  ❌ {table_name}: Not accessible")
                    results["suiteql"]["failed"].append(table_name)

            except Exception:
                print(f"  ❌ {table_name}: Error")
                results["suiteql"]["failed"].append(table_name)

            time.sleep(0.2)

    # =====================================
    # SECTION 2: REST API Testing
    # =====================================
    print("\n" + "=" * 80)
    print("📊 SECTION 2: REST API ACCESS TEST")
    print("-" * 50)

    base_url = (
        f"https://{url_account_id}.suitetalk.api.netsuite.com/services/rest/record/v1"
    )

    rest_endpoints = [
        (
            "Master Data",
            [
                "customer",
                "vendor",
                "item",
                "inventoryitem",
                "location",
                "subsidiary",
                "department",
                "account",
            ],
        ),
        (
            "Transaction Endpoints",
            [
                "salesOrder",
                "salesorder",
                "invoice",
                "cashSale",
                "cashsale",
                "creditMemo",
                "creditmemo",
                "purchaseOrder",
                "purchaseorder",
                "vendorBill",
                "vendorbill",
            ],
        ),
    ]

    for section_name, endpoints in rest_endpoints:
        print(f"\n{section_name}:")
        for endpoint in endpoints:
            url = f"{base_url}/{endpoint}?limit=1"

            try:
                response = requests.get(url, auth=auth, headers=headers, timeout=10)

                if response.status_code == 200:
                    data = response.json()
                    count = data.get("totalResults", data.get("count", 0))
                    print(f"  ✅ {endpoint}: {count} records")
                    results["rest_api"]["working"].append(endpoint)

                    # If transaction endpoint works, get details
                    if "sales" in endpoint.lower() or "invoice" in endpoint.lower():
                        items = data.get("items", [])
                        if items:
                            record_id = items[0].get("id")
                            detail_url = f"{base_url}/{endpoint}/{record_id}"
                            detail_resp = requests.get(
                                detail_url, auth=auth, headers=headers, timeout=10
                            )
                            if detail_resp.status_code == 200:
                                print("     → Full details accessible!")
                                detail_data = detail_resp.json()
                                # Save sample
                                with open(f"sample_{endpoint}.json", "w") as f:
                                    json.dump(detail_data, f, indent=2)
                else:
                    print(f"  ❌ {endpoint}: Status {response.status_code}")
                    results["rest_api"]["failed"].append(endpoint)

            except Exception:
                print(f"  ❌ {endpoint}: Error")
                results["rest_api"]["failed"].append(endpoint)

            time.sleep(0.2)

    # =====================================
    # SECTION 3: Analysis
    # =====================================
    print("\n" + "=" * 80)
    print("📊 ANALYSIS")
    print("=" * 80)

    # Check what's changed
    previously_working_suiteql = [
        "customer",
        "vendor",
        "item",
        "location",
        "subsidiary",
        "department",
        "account",
    ]
    newly_working_suiteql = [
        t for t in results["suiteql"]["working"] if t not in previously_working_suiteql
    ]

    previously_working_rest = [
        "customer",
        "vendor",
        "inventoryitem",
        "location",
        "subsidiary",
        "department",
    ]
    newly_working_rest = [
        t for t in results["rest_api"]["working"] if t not in previously_working_rest
    ]

    print("\n🔍 CURRENT STATUS:")
    print(f"  SuiteQL: {len(results['suiteql']['working'])} tables working")
    print(f"  REST API: {len(results['rest_api']['working'])} endpoints working")

    if newly_working_suiteql:
        print("\n🎉 NEW SUITEQL ACCESS:")
        for table in newly_working_suiteql:
            print(f"  ✅ {table}")
            results["changes"].append(f"New SuiteQL access: {table}")

    if newly_working_rest:
        print("\n🎉 NEW REST API ACCESS:")
        for endpoint in newly_working_rest:
            print(f"  ✅ {endpoint}")
            results["changes"].append(f"New REST API access: {endpoint}")

    # Check transaction access specifically
    transaction_access = False
    if "transaction" in results["suiteql"]["working"]:
        print("\n✅ TRANSACTION TABLE NOW ACCESSIBLE!")
        transaction_access = True

    if any(
        "sales" in e.lower() or "invoice" in e.lower()
        for e in results["rest_api"]["working"]
    ):
        print("\n✅ SALES/INVOICE REST API NOW ACCESSIBLE!")
        transaction_access = True

    if not transaction_access:
        print("\n❌ Still no transaction access via any method")
        print("\n📋 Next steps:")
        print("  1. Confirm with admin that permissions were added")
        print("  2. Check if new tokens need to be generated")
        print("  3. Wait for permission propagation (can take up to 30 minutes)")

    # Save results
    with open("retest_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\n📁 Results saved to: retest_results.json")
    print("=" * 80)

    return results


if __name__ == "__main__":
    comprehensive_retest()
