#!/usr/bin/env python3
"""
Verify exact permission status and troubleshoot access issues
"""

import os
from datetime import datetime

import requests
from dotenv import load_dotenv
from requests_oauthlib import OAuth1

# Load environment variables
load_dotenv()


def verify_permissions():
    """Detailed verification of current permissions"""

    # Get credentials
    consumer_key = os.getenv("GYM_PLUS_COFFEE_CONSUMER_ID")
    consumer_secret = os.getenv("GYM_PLUS_COFFEE_CONSUMER_SECRET")
    token_id = os.getenv("GYM_PLUS_COFFEE_TOKEN_ID")
    token_secret = os.getenv("GYM_PLUS_COFFEE_TOKEN_SECRET")

    account_id = "7326096_SB1"
    url_account_id = "7326096-sb1"

    print("🔐 NetSuite Permission Verification")
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

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Prefer": "transient",
    }

    suiteql_url = f"https://{url_account_id}.suitetalk.api.netsuite.com/services/rest/query/v1/suiteql"

    print("\n📋 CURRENT ACCESS STATUS:")
    print("-" * 50)

    # Test queries with detailed error capture
    test_queries = [
        {
            "name": "Customer Table",
            "query": "SELECT COUNT(*) as cnt FROM customer",
            "expected": "Should work - master data",
        },
        {
            "name": "Transaction Table (Direct)",
            "query": "SELECT * FROM transaction WHERE ROWNUM = 1",
            "expected": "Requires transaction permissions",
        },
        {
            "name": "Transaction Table (Count)",
            "query": "SELECT COUNT(*) as cnt FROM transaction",
            "expected": "Requires transaction permissions",
        },
        {
            "name": "TransactionLine Table",
            "query": "SELECT * FROM transactionline WHERE ROWNUM = 1",
            "expected": "Requires transaction permissions",
        },
        {
            "name": "Sales Order via Transaction",
            "query": "SELECT * FROM transaction WHERE recordtype = 'salesorder' AND ROWNUM = 1",
            "expected": "Requires sales order view permission",
        },
        {
            "name": "Employee Table",
            "query": "SELECT * FROM employee WHERE ROWNUM = 1",
            "expected": "Requires employee list permission",
        },
    ]

    for test in test_queries:
        print(f"\n📝 {test['name']}")
        print(f"   Expected: {test['expected']}")

        payload = {"q": test["query"]}

        try:
            response = requests.post(
                suiteql_url, auth=auth, headers=headers, json=payload, timeout=15
            )

            if response.status_code == 200:
                data = response.json()
                if "items" in data:
                    if data["items"]:
                        print("   ✅ ACCESSIBLE")
                        # Show result for count queries
                        if "cnt" in test["query"].lower():
                            cnt = data["items"][0].get("cnt", 0)
                            print(f"   Result: {cnt} records")
                    else:
                        print("   ✅ Accessible but no data")
                else:
                    print("   ⚠️  Unexpected response structure")

            elif response.status_code == 400:
                print("   ❌ NOT ACCESSIBLE (Bad Request)")
                # Parse error message
                try:
                    error_data = response.json()
                    if "o:errorDetails" in error_data:
                        error_msg = error_data["o:errorDetails"][0].get(
                            "detail", "Unknown error"
                        )
                        if "was not found" in error_msg:
                            print("   Reason: Table doesn't exist in SuiteQL")
                        elif "Unknown identifier" in error_msg:
                            print("   Reason: Field doesn't exist")
                        elif "Invalid search query" in error_msg:
                            print("   Reason: Permission denied or syntax error")
                        print(f"   Error: {error_msg[:150]}")
                except:
                    print(f"   Raw error: {response.text[:200]}")

            elif response.status_code == 401:
                print("   ❌ UNAUTHORIZED - Token/authentication issue")

            elif response.status_code == 403:
                print("   ❌ FORBIDDEN - Explicit permission denial")

            else:
                print(f"   ❌ Status {response.status_code}")

        except Exception as e:
            print(f"   ❌ Connection Error: {str(e)[:100]}")

    print("\n" + "=" * 80)
    print("🔍 DIAGNOSIS")
    print("=" * 80)

    print("""
Based on the tests above:

1. If CUSTOMER works but TRANSACTION doesn't:
   → Transaction permissions not yet applied
   → Need "Find Transaction" permission at minimum
   
2. If you get "Record 'transaction' was not found":
   → SuiteAnalytics Connect might not be fully enabled
   → Or permissions haven't propagated yet
   
3. If authentication works (customer query succeeds):
   → Your tokens are valid
   → The issue is purely permissions-based
    """)

    print("\n📋 POSSIBLE ISSUES:")
    print("""
1. **Permission Propagation Delay**
   - Changes can take 5-15 minutes to propagate
   - Try again in a few minutes
   
2. **Token Needs Refresh**
   - If permissions were just added, you might need new tokens
   - Generate new tokens with the updated role
   
3. **Wrong Permission Level**
   - Ensure permissions are set to "View" not just "None"
   - "Find Transaction" must be included
   
4. **Feature Not Fully Enabled**
   - SuiteAnalytics Connect needs to be checked
   - May require NetSuite restart/cache clear
    """)

    print("\n🔧 RECOMMENDED ACTIONS:")
    print("""
1. Wait 10-15 minutes and test again
2. Ask admin to verify:
   - "Find Transaction" permission is set to View
   - At least one transaction type (e.g., Sales Order) is View
   - SuiteAnalytics Connect is enabled
3. If still not working, may need to:
   - Generate new tokens
   - Clear NetSuite cache
   - Contact NetSuite support
    """)

    print("\n" + "=" * 80)


if __name__ == "__main__":
    verify_permissions()
