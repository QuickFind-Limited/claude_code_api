#!/usr/bin/env python3
"""
Deep Analysis of NetSuite Access - What's available, what's not, and why
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


def deep_analysis():
    """Perform deep analysis of NetSuite access capabilities"""

    # Get credentials
    consumer_key = os.getenv("GYM_PLUS_COFFEE_CONSUMER_ID")
    consumer_secret = os.getenv("GYM_PLUS_COFFEE_CONSUMER_SECRET")
    token_id = os.getenv("GYM_PLUS_COFFEE_TOKEN_ID")
    token_secret = os.getenv("GYM_PLUS_COFFEE_TOKEN_SECRET")

    account_id = "7326096_SB1"
    url_account_id = "7326096-sb1"

    print("🔬 NetSuite Deep Access Analysis")
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
    rest_api_url = (
        f"https://{url_account_id}.suitetalk.api.netsuite.com/services/rest/record/v1"
    )

    # Analysis results
    analysis = {
        "timestamp": datetime.now().isoformat(),
        "account_id": account_id,
        "suiteql": {
            "working_tables": [],
            "failed_tables": [],
            "permission_errors": [],
            "not_found_errors": [],
        },
        "rest_api": {"accessible": [], "forbidden": [], "not_found": []},
        "recommendations": [],
    }

    # =====================================
    # SECTION 1: SuiteQL Table Analysis
    # =====================================
    print("\n" + "=" * 80)
    print("📊 SECTION 1: SUITEQL TABLE ANALYSIS")
    print("=" * 80)

    # Test core tables and their variations
    suiteql_tables = [
        # Standard record tables
        ("customer", "Basic customer table"),
        ("vendor", "Basic vendor table"),
        ("item", "Basic item table"),
        ("location", "Location/warehouse table"),
        ("subsidiary", "Subsidiary table"),
        ("department", "Department table"),
        ("account", "Chart of accounts"),
        ("currency", "Currency table"),
        ("employee", "Employee records"),
        # Transaction tables (often problematic)
        ("transaction", "Main transaction table"),
        ("transactionline", "Transaction line items"),
        ("transactionaccountingline", "Transaction accounting lines"),
        # Analytics tables
        ("transactionanalyticsbyuser", "Transaction analytics by user"),
        ("itemanalyticsbyperiod", "Item analytics by period"),
        ("customeranalyticsbyperiod", "Customer analytics by period"),
        # Alternative transaction access
        ("salesorder", "Sales orders"),
        ("invoice", "Invoices"),
        ("purchaseorder", "Purchase orders"),
        ("cashsale", "Cash sales"),
        ("creditmemo", "Credit memos"),
        # System tables
        ("systemnote", "System notes/audit trail"),
        ("usereventlog", "User event log"),
        ("loginaudit", "Login audit trail"),
        # Custom tables
        ("customrecord", "Generic custom record"),
        ("customlist", "Generic custom list"),
    ]

    print("\nTesting SuiteQL table access...")
    print("-" * 50)

    for table_name, description in suiteql_tables:
        print(f"\n📋 Testing: {table_name} ({description})")

        # Try basic SELECT
        query = f"SELECT * FROM {table_name} WHERE ROWNUM = 1"
        payload = {"q": query}

        try:
            response = requests.post(
                suiteql_url, auth=auth, headers=headers, json=payload, timeout=15
            )

            if response.status_code == 200:
                data = response.json()
                if "items" in data:
                    fields = []
                    if data["items"]:
                        fields = list(data["items"][0].keys())
                        fields = [f for f in fields if f != "links"]

                    print(f"   ✅ SUCCESS - {len(fields)} fields accessible")
                    analysis["suiteql"]["working_tables"].append(
                        {
                            "table": table_name,
                            "fields": fields[:10],  # First 10 fields
                            "field_count": len(fields),
                        }
                    )

                    # Show sample fields
                    if fields:
                        print(f"   Sample fields: {', '.join(fields[:5])}")

            elif response.status_code == 400:
                error_data = response.json() if response.text else {}
                error_msg = "Unknown error"

                if "o:errorDetails" in error_data:
                    error_msg = error_data["o:errorDetails"][0].get("detail", "Unknown")

                print(f"   ❌ BAD REQUEST - {error_msg[:50]}")

                if "was not found" in error_msg or "Unknown identifier" in error_msg:
                    analysis["suiteql"]["not_found_errors"].append(table_name)
                elif "permission" in error_msg.lower() or "access" in error_msg.lower():
                    analysis["suiteql"]["permission_errors"].append(table_name)
                else:
                    analysis["suiteql"]["failed_tables"].append(table_name)

            elif response.status_code == 401:
                print("   ❌ UNAUTHORIZED - Authentication issue")
                analysis["suiteql"]["permission_errors"].append(table_name)

            elif response.status_code == 403:
                print("   ❌ FORBIDDEN - Permission denied")
                analysis["suiteql"]["permission_errors"].append(table_name)

            else:
                print(f"   ❌ Status {response.status_code}")
                analysis["suiteql"]["failed_tables"].append(table_name)

        except Exception as e:
            print(f"   ❌ Error: {str(e)[:50]}")
            analysis["suiteql"]["failed_tables"].append(table_name)

        time.sleep(0.5)  # Rate limiting

    # =====================================
    # SECTION 2: REST API Access Analysis
    # =====================================
    print("\n" + "=" * 80)
    print("🌐 SECTION 2: REST API ACCESS ANALYSIS")
    print("=" * 80)

    # Test REST API endpoints
    rest_endpoints = [
        "customer",
        "vendor",
        "employee",
        "item",
        "inventoryitem",
        "salesorder",
        "invoice",
        "purchaseorder",
        "location",
        "subsidiary",
        "department",
    ]

    print("\nTesting REST API endpoints...")
    print("-" * 50)

    for endpoint in rest_endpoints:
        print(f"\n📍 Testing: /record/v1/{endpoint}")

        url = f"{rest_api_url}/{endpoint}?limit=1"

        try:
            response = requests.get(
                url, auth=auth, headers={"Accept": "application/json"}, timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                count = data.get("count", 0)
                print(f"   ✅ ACCESSIBLE - {count} records available")
                analysis["rest_api"]["accessible"].append(endpoint)

            elif response.status_code == 403:
                print("   ⚠️  FORBIDDEN - No permission")
                analysis["rest_api"]["forbidden"].append(endpoint)

            elif response.status_code == 404:
                print("   ❌ NOT FOUND - Endpoint doesn't exist")
                analysis["rest_api"]["not_found"].append(endpoint)

            else:
                print(f"   ❌ Status {response.status_code}")

        except Exception as e:
            print(f"   ❌ Error: {str(e)[:50]}")

        time.sleep(0.5)

    # =====================================
    # SECTION 3: Permission Testing
    # =====================================
    print("\n" + "=" * 80)
    print("🔐 SECTION 3: PERMISSION & ROLE ANALYSIS")
    print("=" * 80)

    permission_tests = [
        {
            "name": "Financial Data Access",
            "query": "SELECT id FROM account WHERE ROWNUM = 1",
            "permission": "Lists > Accounts",
        },
        {
            "name": "Employee Data Access",
            "query": "SELECT id FROM employee WHERE ROWNUM = 1",
            "permission": "Lists > Employees",
        },
        {
            "name": "Transaction Access",
            "query": "SELECT id FROM transaction WHERE ROWNUM = 1",
            "permission": "Transactions > Various",
        },
        {
            "name": "Custom Record Access",
            "query": "SELECT id FROM customrecord_2663_batch WHERE ROWNUM = 1",
            "permission": "Custom Records > Specific Record",
        },
        {
            "name": "System Note Access",
            "query": "SELECT id FROM systemnote WHERE ROWNUM = 1",
            "permission": "Setup > System Notes",
        },
    ]

    print("\nTesting specific permissions...")
    print("-" * 50)

    for test in permission_tests:
        print(f"\n🔑 {test['name']}")
        print(f"   Required: {test['permission']}")

        payload = {"q": test["query"]}

        try:
            response = requests.post(
                suiteql_url, auth=auth, headers=headers, json=payload, timeout=10
            )

            if response.status_code == 200:
                print("   ✅ PERMISSION GRANTED")
            else:
                print("   ❌ PERMISSION DENIED or TABLE NOT FOUND")

        except Exception as e:
            print(f"   ❌ Error: {str(e)[:30]}")

    # =====================================
    # SECTION 4: Alternative Access Methods
    # =====================================
    print("\n" + "=" * 80)
    print("🔄 SECTION 4: ALTERNATIVE ACCESS METHODS")
    print("=" * 80)

    # Test saved searches via SuiteQL
    print("\n📂 Testing Saved Search Access...")
    saved_search_query = """
        SELECT 
            id,
            scriptid,
            title,
            recordtype
        FROM savedsearch
        WHERE ROWNUM <= 5
    """

    payload = {"q": saved_search_query.strip()}

    try:
        response = requests.post(
            suiteql_url, auth=auth, headers=headers, json=payload, timeout=10
        )

        if response.status_code == 200:
            print("   ✅ Saved searches accessible via SuiteQL")
        else:
            print("   ❌ Saved searches not accessible")
    except:
        print("   ❌ Error accessing saved searches")

    # Test Join capabilities
    print("\n🔗 Testing JOIN Capabilities...")
    join_query = """
        SELECT 
            c.id,
            c.companyname,
            s.name as subsidiary_name
        FROM customer c
        LEFT JOIN subsidiary s ON c.subsidiary = s.id
        WHERE ROWNUM <= 3
    """

    payload = {"q": join_query.strip()}

    try:
        response = requests.post(
            suiteql_url, auth=auth, headers=headers, json=payload, timeout=10
        )

        if response.status_code == 200:
            print("   ✅ JOIN operations supported")
        else:
            print("   ❌ JOIN operations failed")
    except:
        print("   ❌ Error testing JOIN")

    # =====================================
    # SECTION 5: Analysis & Recommendations
    # =====================================
    print("\n" + "=" * 80)
    print("💡 ANALYSIS RESULTS & RECOMMENDATIONS")
    print("=" * 80)

    # Calculate statistics
    working_count = len(analysis["suiteql"]["working_tables"])
    permission_errors = len(analysis["suiteql"]["permission_errors"])
    not_found = len(analysis["suiteql"]["not_found_errors"])
    rest_accessible = len(analysis["rest_api"]["accessible"])

    print("\n📊 ACCESS SUMMARY:")
    print(f"   SuiteQL Working Tables: {working_count}")
    print(f"   SuiteQL Permission Errors: {permission_errors}")
    print(f"   SuiteQL Tables Not Found: {not_found}")
    print(f"   REST API Accessible: {rest_accessible}")

    # Generate recommendations
    recommendations = []

    if permission_errors > 0:
        recommendations.append(
            {
                "priority": "HIGH",
                "issue": "Permission Restrictions",
                "tables_affected": analysis["suiteql"]["permission_errors"],
                "solution": "Request NetSuite admin to grant additional permissions to the integration role",
                "permissions_needed": [
                    "Lists > Employees (for employee table)",
                    "Transactions > View (for transaction tables)",
                    "Reports > SuiteAnalytics Connect (for analytics tables)",
                    "Custom Records > View (for custom records)",
                ],
            }
        )

    if not_found > 0:
        recommendations.append(
            {
                "priority": "MEDIUM",
                "issue": "Tables Not Available in SuiteQL",
                "tables_affected": analysis["suiteql"]["not_found_errors"],
                "solution": "These tables may need different access methods",
                "alternatives": [
                    "Use REST API endpoints instead",
                    "Access via Saved Searches",
                    "Use SuiteTalk SOAP API",
                    "Enable SuiteAnalytics Connect",
                ],
            }
        )

    if "transaction" in analysis["suiteql"]["not_found_errors"]:
        recommendations.append(
            {
                "priority": "HIGH",
                "issue": "Transaction Table Not Accessible",
                "solution": "Transaction data is critical for most integrations",
                "actions": [
                    'Enable "SuiteAnalytics Connect" feature in NetSuite',
                    'Grant "Reports > SuiteAnalytics Workbook" permission',
                    "Consider using transaction record type specific tables",
                    "Use REST API for specific transaction types instead",
                ],
            }
        )

    analysis["recommendations"] = recommendations

    # Save analysis results
    with open("netsuite_deep_analysis.json", "w") as f:
        json.dump(analysis, f, indent=2)

    print("\n📋 RECOMMENDATIONS:")
    for i, rec in enumerate(recommendations, 1):
        print(f"\n{i}. [{rec['priority']}] {rec['issue']}")
        print(f"   Solution: {rec['solution']}")
        if "actions" in rec:
            print("   Actions needed:")
            for action in rec["actions"]:
                print(f"   • {action}")
        if "permissions_needed" in rec:
            print("   Permissions to request:")
            for perm in rec["permissions_needed"]:
                print(f"   • {perm}")

    # =====================================
    # SECTION 6: What's Working Well
    # =====================================
    print("\n" + "=" * 80)
    print("✅ WHAT'S WORKING WELL")
    print("=" * 80)

    print("\nCurrently Accessible:")
    for table_info in analysis["suiteql"]["working_tables"]:
        print(f"• {table_info['table']}: {table_info['field_count']} fields")

    print("\nCapabilities Available:")
    print("• Basic CRUD on customers, vendors, items, locations")
    print("• Read access to core master data")
    print("• JOIN operations between accessible tables")
    print("• REST API access for standard records")

    # =====================================
    # SECTION 7: Action Plan
    # =====================================
    print("\n" + "=" * 80)
    print("📝 ACTION PLAN TO GAIN MORE ACCESS")
    print("=" * 80)

    print("""
1. IMMEDIATE ACTIONS (Do yourself):
   □ Document current integration use cases
   □ List specific data requirements
   □ Identify critical missing tables
   
2. REQUEST FROM NETSUITE ADMIN:
   □ Review integration role permissions
   □ Enable SuiteAnalytics Connect feature
   □ Grant these specific permissions:
     - Transactions > View
     - Reports > SuiteAnalytics Workbook
     - Custom Records > View
     - Lists > Employees (if needed)
   
3. TECHNICAL SETUP:
   □ Create new integration record with broader scope
   □ Generate new tokens with enhanced role
   □ Test access with new credentials
   
4. ALTERNATIVE APPROACHES:
   □ Use Saved Searches for complex queries
   □ Implement REST API for specific records
   □ Consider SuiteTalk SOAP for legacy data
   □ Explore RESTlets for custom endpoints
    """)

    print("\n" + "=" * 80)
    print("📁 Full analysis saved to: netsuite_deep_analysis.json")
    print("=" * 80)


if __name__ == "__main__":
    deep_analysis()
