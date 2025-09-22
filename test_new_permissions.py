#!/usr/bin/env python3
"""
Test NetSuite permissions after update - comprehensive analysis
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


def test_new_permissions():
    """Test what's now accessible after permission updates"""

    # Get credentials
    consumer_key = os.getenv("GYM_PLUS_COFFEE_CONSUMER_ID")
    consumer_secret = os.getenv("GYM_PLUS_COFFEE_CONSUMER_SECRET")
    token_id = os.getenv("GYM_PLUS_COFFEE_TOKEN_ID")
    token_secret = os.getenv("GYM_PLUS_COFFEE_TOKEN_SECRET")

    account_id = "7326096_SB1"
    url_account_id = "7326096-sb1"

    print("🔍 NetSuite Permission Analysis - After Update")
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

    results = {
        "timestamp": datetime.now().isoformat(),
        "working_tables": [],
        "failed_tables": [],
        "transaction_access": {},
        "new_capabilities": [],
    }

    # =====================================
    # TEST 1: Basic Transaction Table Access
    # =====================================
    print("\n" + "=" * 80)
    print("📊 TEST 1: TRANSACTION TABLE ACCESS")
    print("=" * 80)

    # Test main transaction table
    print("\n🔍 Testing main transaction table...")
    query = "SELECT * FROM transaction WHERE ROWNUM = 1"
    payload = {"q": query}

    try:
        response = requests.post(
            suiteql_url, auth=auth, headers=headers, json=payload, timeout=15
        )

        if response.status_code == 200:
            data = response.json()
            if "items" in data and data["items"]:
                fields = list(data["items"][0].keys())
                fields = [f for f in fields if f != "links"]
                print("✅ SUCCESS! Transaction table is now accessible!")
                print(f"   Fields available: {len(fields)}")
                print(f"   Sample fields: {', '.join(fields[:10])}...")
                results["working_tables"].append("transaction")
                results["transaction_access"]["main_table"] = True

                # Get transaction count
                count_query = "SELECT COUNT(*) as total FROM transaction"
                count_response = requests.post(
                    suiteql_url,
                    auth=auth,
                    headers=headers,
                    json={"q": count_query},
                    timeout=15,
                )
                if count_response.status_code == 200:
                    count_data = count_response.json()
                    if count_data.get("items"):
                        total = count_data["items"][0].get("total", 0)
                        print(f"   Total transactions: {total:,}")
            else:
                print("✅ Transaction table accessible but empty")
        else:
            print(
                f"❌ Transaction table still not accessible (Status: {response.status_code})"
            )
            results["transaction_access"]["main_table"] = False
    except Exception as e:
        print(f"❌ Error: {str(e)[:100]}")
        results["transaction_access"]["main_table"] = False

    time.sleep(0.5)

    # =====================================
    # TEST 2: TransactionLine Table
    # =====================================
    print("\n" + "=" * 80)
    print("📊 TEST 2: TRANSACTIONLINE TABLE ACCESS")
    print("=" * 80)

    print("\n🔍 Testing transactionline table...")
    query = "SELECT * FROM transactionline WHERE ROWNUM = 1"
    payload = {"q": query}

    try:
        response = requests.post(
            suiteql_url, auth=auth, headers=headers, json=payload, timeout=15
        )

        if response.status_code == 200:
            data = response.json()
            if "items" in data:
                print("✅ SUCCESS! TransactionLine table is now accessible!")
                if data["items"]:
                    fields = list(data["items"][0].keys())
                    fields = [f for f in fields if f != "links"]
                    print(f"   Fields available: {len(fields)}")
                    print(f"   Sample fields: {', '.join(fields[:10])}...")
                results["working_tables"].append("transactionline")
                results["transaction_access"]["line_table"] = True
        else:
            print("❌ TransactionLine table still not accessible")
            results["transaction_access"]["line_table"] = False
    except Exception as e:
        print(f"❌ Error: {str(e)[:100]}")
        results["transaction_access"]["line_table"] = False

    time.sleep(0.5)

    # =====================================
    # TEST 3: Specific Transaction Types
    # =====================================
    print("\n" + "=" * 80)
    print("📊 TEST 3: SPECIFIC TRANSACTION TYPES")
    print("=" * 80)

    transaction_types = [
        ("salesorder", "Sales Orders"),
        ("invoice", "Invoices"),
        ("cashsale", "Cash Sales"),
        ("creditmemo", "Credit Memos"),
        ("customerpayment", "Customer Payments"),
        ("customerdeposit", "Customer Deposits"),
        ("customerrefund", "Customer Refunds"),
        ("estimate", "Estimates/Quotes"),
        ("opportunity", "Opportunities"),
        ("purchaseorder", "Purchase Orders"),
        ("vendorbill", "Vendor Bills"),
        ("vendorpayment", "Vendor Payments"),
        ("vendorcredit", "Vendor Credits"),
        ("itemfulfillment", "Item Fulfillments"),
        ("itemreceipt", "Item Receipts"),
        ("inventoryadjustment", "Inventory Adjustments"),
        ("inventorytransfer", "Inventory Transfers"),
        ("transferorder", "Transfer Orders"),
        ("returnauthorization", "Return Authorizations"),
        ("journalentry", "Journal Entries"),
    ]

    for record_type, description in transaction_types:
        # Try via transaction table with recordtype filter
        query = f"SELECT * FROM transaction WHERE recordtype = '{record_type}' AND ROWNUM = 1"
        payload = {"q": query}

        try:
            response = requests.post(
                suiteql_url, auth=auth, headers=headers, json=payload, timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if "items" in data and data["items"]:
                    print(f"✅ {description}: ACCESSIBLE")
                    results["transaction_access"][record_type] = True

                    # Get count
                    count_query = f"SELECT COUNT(*) as cnt FROM transaction WHERE recordtype = '{record_type}'"
                    count_resp = requests.post(
                        suiteql_url,
                        auth=auth,
                        headers=headers,
                        json={"q": count_query},
                        timeout=10,
                    )
                    if count_resp.status_code == 200:
                        count_data = count_resp.json()
                        if count_data.get("items"):
                            cnt = count_data["items"][0].get("cnt", 0)
                            print(f"   Count: {cnt:,} records")
                else:
                    print(f"⚠️  {description}: No records found")
                    results["transaction_access"][record_type] = "empty"
            else:
                print(f"❌ {description}: Not accessible")
                results["transaction_access"][record_type] = False
        except Exception:
            print(f"❌ {description}: Error")
            results["transaction_access"][record_type] = False

        time.sleep(0.3)

    # =====================================
    # TEST 4: Complex Transaction Queries
    # =====================================
    print("\n" + "=" * 80)
    print("📊 TEST 4: COMPLEX TRANSACTION QUERIES")
    print("=" * 80)

    complex_queries = [
        {
            "name": "Recent Sales Orders",
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
                AND trandate >= '01/01/2024'
                AND ROWNUM <= 5
                ORDER BY trandate DESC
            """,
        },
        {
            "name": "Transaction Summary by Type",
            "query": """
                SELECT 
                    recordtype,
                    COUNT(*) as count,
                    SUM(total) as total_amount
                FROM transaction
                WHERE trandate >= '01/01/2023'
                GROUP BY recordtype
                HAVING COUNT(*) > 0
            """,
        },
        {
            "name": "Customer Transaction History",
            "query": """
                SELECT 
                    t.id,
                    t.tranid,
                    t.recordtype,
                    t.trandate,
                    c.companyname
                FROM transaction t
                JOIN customer c ON t.entity = c.id
                WHERE t.recordtype IN ('salesorder', 'invoice')
                AND ROWNUM <= 10
            """,
        },
        {
            "name": "Transaction Lines with Items",
            "query": """
                SELECT 
                    tl.id,
                    tl.transaction,
                    tl.item,
                    tl.quantity,
                    tl.rate,
                    tl.amount
                FROM transactionline tl
                WHERE tl.item IS NOT NULL
                AND ROWNUM <= 10
            """,
        },
    ]

    for query_info in complex_queries:
        print(f"\n📝 Testing: {query_info['name']}")
        payload = {"q": query_info["query"].strip()}

        try:
            response = requests.post(
                suiteql_url, auth=auth, headers=headers, json=payload, timeout=15
            )

            if response.status_code == 200:
                data = response.json()
                if "items" in data and data["items"]:
                    print(f"   ✅ Query successful - {len(data['items'])} results")
                    # Show sample result
                    sample = data["items"][0]
                    print(f"   Sample: {json.dumps(sample, default=str)[:150]}...")
                    results["new_capabilities"].append(query_info["name"])
                else:
                    print("   ⚠️  Query returned no results")
            else:
                print(f"   ❌ Query failed (Status: {response.status_code})")
        except Exception as e:
            print(f"   ❌ Error: {str(e)[:100]}")

        time.sleep(0.5)

    # =====================================
    # TEST 5: Analytics Tables
    # =====================================
    print("\n" + "=" * 80)
    print("📊 TEST 5: ANALYTICS TABLES")
    print("=" * 80)

    analytics_tables = [
        "transactionaccountingline",
        "transactionanalyticsbyuser",
        "itemanalyticsbyperiod",
        "customeranalyticsbyperiod",
    ]

    for table in analytics_tables:
        query = f"SELECT * FROM {table} WHERE ROWNUM = 1"
        payload = {"q": query}

        try:
            response = requests.post(
                suiteql_url, auth=auth, headers=headers, json=payload, timeout=10
            )

            if response.status_code == 200:
                print(f"✅ {table}: NOW ACCESSIBLE!")
                results["working_tables"].append(table)
            else:
                print(f"❌ {table}: Still not accessible")
                results["failed_tables"].append(table)
        except:
            print(f"❌ {table}: Error")
            results["failed_tables"].append(table)

        time.sleep(0.3)

    # =====================================
    # SUMMARY
    # =====================================
    print("\n" + "=" * 80)
    print("📊 PERMISSION UPDATE SUMMARY")
    print("=" * 80)

    # Calculate what's new
    previously_working = [
        "customer",
        "vendor",
        "item",
        "location",
        "subsidiary",
        "department",
        "classification",
        "account",
        "currency",
    ]

    newly_accessible = [
        t for t in results["working_tables"] if t not in previously_working
    ]

    print("\n🎉 NEWLY ACCESSIBLE:")
    if newly_accessible:
        for table in newly_accessible:
            print(f"   ✅ {table}")
    else:
        print("   No new tables accessible")

    print("\n📊 TRANSACTION ACCESS:")
    working_trans = [k for k, v in results["transaction_access"].items() if v == True]
    if working_trans:
        print(f"   ✅ Can access: {', '.join(working_trans)}")

    not_working = [k for k, v in results["transaction_access"].items() if v == False]
    if not_working:
        print(f"   ❌ Cannot access: {', '.join(not_working)}")

    print("\n🚀 NEW CAPABILITIES:")
    if results["new_capabilities"]:
        for cap in results["new_capabilities"]:
            print(f"   • {cap}")

    # Save results
    with open("new_permissions_analysis.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\n📁 Full results saved to: new_permissions_analysis.json")
    print("=" * 80)

    return results


if __name__ == "__main__":
    test_new_permissions()
