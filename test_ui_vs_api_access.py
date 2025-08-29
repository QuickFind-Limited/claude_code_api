#!/usr/bin/env python3
"""
Test the difference between UI permissions and API/SuiteQL access
"""

import os

import requests
from dotenv import load_dotenv
from requests_oauthlib import OAuth1

# Load environment variables
load_dotenv()


def test_access_methods():
    """Test different access methods to understand permission layers"""

    # Get credentials
    consumer_key = os.getenv("GYM_PLUS_COFFEE_CONSUMER_ID")
    consumer_secret = os.getenv("GYM_PLUS_COFFEE_CONSUMER_SECRET")
    token_id = os.getenv("GYM_PLUS_COFFEE_TOKEN_ID")
    token_secret = os.getenv("GYM_PLUS_COFFEE_TOKEN_SECRET")

    account_id = "7326096_SB1"
    url_account_id = "7326096-sb1"

    print("🔍 NetSuite Access Method Comparison")
    print("=" * 80)
    print("Testing why UI access ≠ API access")
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

    # =====================================
    # TEST 1: REST API Direct Access
    # =====================================
    print("\n📊 TEST 1: REST API RECORD ACCESS")
    print("-" * 50)
    print("This uses the same permissions as the UI")
    print()

    rest_endpoints = [
        ("salesOrder", "Sales Orders"),
        ("invoice", "Invoices"),
        ("customer", "Customers"),
        ("item", "Items"),
        ("employee", "Employees"),
    ]

    for endpoint, name in rest_endpoints:
        url = f"https://{url_account_id}.suitetalk.api.netsuite.com/services/rest/record/v1/{endpoint}?limit=1"

        try:
            response = requests.get(url, auth=auth, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                count = data.get("count", 0)
                print(f"✅ {name}: Accessible via REST API (Count: {count})")

                # If we can access via REST, show that we have UI-equivalent permissions
                if endpoint == "salesOrder":
                    print("   → This means you HAVE Sales Order VIEW permission")
                    print("   → You can see these in the UI")

            elif response.status_code == 400:
                # Try to parse the error
                try:
                    error_data = response.json()
                    if "o:errorDetails" in error_data:
                        error_msg = error_data["o:errorDetails"][0].get("detail", "")
                        if "Invalid record type" in error_msg:
                            print(f"⚠️  {name}: Invalid endpoint name")
                        else:
                            print(f"❌ {name}: Bad request")
                    else:
                        print(f"❌ {name}: Not accessible (400)")
                except:
                    print(f"❌ {name}: Not accessible")

            elif response.status_code == 403:
                print(f"❌ {name}: Forbidden - No permission")
            elif response.status_code == 404:
                print(f"⚠️  {name}: Endpoint not found")
            else:
                print(f"❌ {name}: Status {response.status_code}")

        except Exception as e:
            print(f"❌ {name}: Error - {str(e)[:50]}")

    # =====================================
    # TEST 2: SuiteQL Analytics Access
    # =====================================
    print("\n📊 TEST 2: SUITEQL ANALYTICS ACCESS")
    print("-" * 50)
    print("This requires additional analytics permissions")
    print()

    suiteql_url = f"https://{url_account_id}.suitetalk.api.netsuite.com/services/rest/query/v1/suiteql"
    headers["Prefer"] = "transient"

    suiteql_tests = [
        {
            "name": "Transaction table (Analytics)",
            "query": "SELECT * FROM transaction WHERE ROWNUM = 1",
            "note": 'Requires "Find Transaction" + SuiteAnalytics Connect',
        },
        {
            "name": "Customer table (Master Data)",
            "query": "SELECT COUNT(*) as cnt FROM customer",
            "note": "Works with basic customer permission",
        },
        {
            "name": "Sales Order search",
            "query": "SELECT * FROM salesorder WHERE ROWNUM = 1",
            "note": "Alternative table name (might not exist)",
        },
    ]

    for test in suiteql_tests:
        print(f"\n📝 {test['name']}")
        print(f"   Note: {test['note']}")

        payload = {"q": test["query"]}

        try:
            response = requests.post(
                suiteql_url, auth=auth, headers=headers, json=payload, timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if "items" in data:
                    if data["items"]:
                        if "cnt" in test["query"]:
                            cnt = data["items"][0].get("cnt", 0)
                            print(f"   ✅ Accessible - {cnt} records")
                        else:
                            print("   ✅ Accessible")
                    else:
                        print("   ✅ Accessible but no data")
            else:
                error_msg = ""
                try:
                    error_data = response.json()
                    if "o:errorDetails" in error_data:
                        error_msg = error_data["o:errorDetails"][0].get("detail", "")[
                            :100
                        ]
                except:
                    pass

                if "was not found" in error_msg:
                    print("   ❌ Table doesn't exist in SuiteQL")
                else:
                    print("   ❌ Not accessible")

        except Exception as e:
            print(f"   ❌ Error: {str(e)[:50]}")

    # =====================================
    # EXPLANATION
    # =====================================
    print("\n" + "=" * 80)
    print("📚 EXPLANATION: Why You Can See Sales Orders in UI but Not Query Them")
    print("=" * 80)

    print("""
The NetSuite UI and SuiteQL use DIFFERENT permission systems:

1. **UI/Dashboard Access** (What you see when logged in):
   - Uses "Transactions > Sales Order > View" permission
   - Allows viewing records through the web interface
   - Same permissions work for REST API individual record access

2. **SuiteQL Analytics Tables** (transaction, transactionline):
   - Requires "Transactions > Find Transaction" permission
   - Needs "SuiteAnalytics Connect" feature enabled
   - These are special analytics tables, not the same as UI records

3. **Why the Disconnect?**
   - The 'transaction' table is an analytics view, not the raw records
   - It's designed for reporting and requires analytics permissions
   - Even with full UI access, you need specific analytics permissions

4. **Solution**:
   Your admin needs to add:
   ✅ "Find Transaction" permission (under Transactions tab)
   ✅ Ensure SuiteAnalytics Connect is fully activated
   
   These are DIFFERENT from the Sales Order View permission you already have.
    """)

    print("\n🔑 KEY INSIGHT:")
    print("-" * 50)
    print("""
If REST API to /salesOrder works but SuiteQL 'transaction' doesn't:
→ You have UI permissions but lack analytics permissions
→ This is normal - they're separate permission sets
→ Many users can view records but can't run analytics
    """)


if __name__ == "__main__":
    test_access_methods()
