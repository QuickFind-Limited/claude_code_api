#!/usr/bin/env python3
"""
Extensive NetSuite SuiteQL Testing - Testing as many queries as possible
This will take time but will provide comprehensive insight into what's accessible
"""

import json
import os
import time
from datetime import datetime
from typing import Any, Dict

import requests
from dotenv import load_dotenv
from requests_oauthlib import OAuth1

# Load environment variables
load_dotenv()


class NetSuiteExtensiveTester:
    def __init__(self):
        self.consumer_key = os.getenv("GYM_PLUS_COFFEE_CONSUMER_ID")
        self.consumer_secret = os.getenv("GYM_PLUS_COFFEE_CONSUMER_SECRET")
        self.token_id = os.getenv("GYM_PLUS_COFFEE_TOKEN_ID")
        self.token_secret = os.getenv("GYM_PLUS_COFFEE_TOKEN_SECRET")

        self.account_id = "7326096_SB1"
        self.url_account_id = "7326096-sb1"

        self.auth = OAuth1(
            client_key=self.consumer_key,
            client_secret=self.consumer_secret,
            resource_owner_key=self.token_id,
            resource_owner_secret=self.token_secret,
            signature_method="HMAC-SHA256",
            realm=self.account_id,
        )

        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Prefer": "transient",
        }

        self.suiteql_url = f"https://{self.url_account_id}.suitetalk.api.netsuite.com/services/rest/query/v1/suiteql"

        self.results = {
            "timestamp": datetime.now().isoformat(),
            "account_id": self.account_id,
            "successful_queries": [],
            "failed_queries": [],
            "discovered_tables": {},
            "discovered_fields": {},
            "working_patterns": [],
            "statistics": {},
        }

        self.query_count = 0
        self.success_count = 0
        self.failure_count = 0

    def execute_query(self, query: str, description: str = "") -> Dict[str, Any]:
        """Execute a SuiteQL query and return results"""
        self.query_count += 1

        payload = {"q": query.strip()}

        try:
            response = requests.post(
                self.suiteql_url,
                auth=self.auth,
                headers=self.headers,
                json=payload,
                timeout=15,
            )

            if response.status_code == 200:
                self.success_count += 1
                data = response.json()

                result = {
                    "query": query,
                    "description": description,
                    "status": "success",
                    "data": data,
                }

                self.results["successful_queries"].append(
                    {
                        "query": query,
                        "description": description,
                        "record_count": len(data.get("items", [])),
                        "sample_data": data.get("items", [])[:2],  # First 2 records
                    }
                )

                return result
            else:
                self.failure_count += 1
                self.results["failed_queries"].append(
                    {
                        "query": query,
                        "description": description,
                        "status_code": response.status_code,
                        "error": response.text[:200]
                        if response.text
                        else "No error message",
                    }
                )

                return {
                    "query": query,
                    "description": description,
                    "status": "failed",
                    "status_code": response.status_code,
                }

        except Exception as e:
            self.failure_count += 1
            self.results["failed_queries"].append(
                {"query": query, "description": description, "error": str(e)[:100]}
            )

            return {
                "query": query,
                "description": description,
                "status": "error",
                "error": str(e),
            }

    def test_basic_tables(self):
        """Test all basic table access patterns"""
        print("\n" + "=" * 80)
        print("📊 TESTING BASIC TABLES")
        print("=" * 80)

        tables = [
            # Master data
            "customer",
            "vendor",
            "item",
            "location",
            "subsidiary",
            "department",
            "classification",
            "account",
            "currency",
            "employee",
            "contact",
            "partner",
            "lead",
            "prospect",
            "competitor",
            # Inventory
            "inventoryitem",
            "noninventoryitem",
            "serviceitem",
            "assemblyitem",
            "kititem",
            "otherchargeitem",
            "itemgroup",
            "inventorynumber",
            "inventorylocation",
            "inventorybalance",
            # Transactions (different patterns)
            "transaction",
            "transactionline",
            "transactionaccountingline",
            "salesorder",
            "invoice",
            "cashsale",
            "estimate",
            "opportunity",
            "purchaseorder",
            "vendorbill",
            "purchaserequisition",
            "check",
            "deposit",
            "customerrefund",
            "vendorpayment",
            "vendorcredit",
            "creditmemo",
            "returnauthorization",
            "cashrefund",
            "journalentry",
            "intercompanyjournalentry",
            "inventoryadjustment",
            "inventorytransfer",
            "workorder",
            "assemblybuild",
            "itemfulfillment",
            "itemreceipt",
            # Financial
            "accountingperiod",
            "accountingbook",
            "consolidatedexchangerate",
            "taxperiod",
            "taxgroup",
            "taxtype",
            "salestaxitem",
            # CRM
            "campaign",
            "promocode",
            "couponcode",
            "emailtemplate",
            "marketingtemplate",
            "case",
            "issue",
            "topic",
            "solution",
            "supportcase",
            "phone",
            "email",
            "task",
            "event",
            "calendarevent",
            # Project
            "job",
            "project",
            "projecttask",
            "projecttemplate",
            "resourceallocation",
            "charge",
            "timesheet",
            "timeentry",
            # Lists
            "state",
            "country",
            "unitstype",
            "paymentmethod",
            "term",
            "pricelist",
            "pricelevel",
            "customercategory",
            "vendorcategory",
            # System
            "role",
            "savedcsv",
            "savedsearch",
            "customrecord",
            "customlist",
            "customfield",
            "note",
            "message",
            "file",
            "folder",
            "systemnote",
            "usereventlog",
            "loginaudit",
            "recentrecord",
        ]

        for table in tables:
            print(f"\nTesting table: {table}")

            # Test basic SELECT
            result = self.execute_query(
                f"SELECT * FROM {table} WHERE ROWNUM = 1", f"Basic SELECT from {table}"
            )

            if result["status"] == "success":
                print(f"  ✅ {table} exists")

                # Get fields
                if result["data"].get("items"):
                    fields = list(result["data"]["items"][0].keys())
                    fields = [f for f in fields if f != "links"]
                    self.results["discovered_tables"][table] = fields
                    print(f"     Fields: {len(fields)} - {', '.join(fields[:5])}...")

                # Test COUNT
                count_result = self.execute_query(
                    f"SELECT COUNT(*) as total FROM {table}",
                    f"Count records in {table}",
                )

                if count_result["status"] == "success" and count_result["data"].get(
                    "items"
                ):
                    total = count_result["data"]["items"][0].get("total", 0)
                    print(f"     Total records: {total}")
            else:
                print(f"  ❌ {table} not accessible")

            # Rate limiting
            time.sleep(0.3)

    def test_advanced_queries(self):
        """Test advanced query patterns"""
        print("\n" + "=" * 80)
        print("🔬 TESTING ADVANCED QUERY PATTERNS")
        print("=" * 80)

        # Only test on known working tables
        working_tables = ["customer", "vendor", "item", "location", "subsidiary"]

        advanced_queries = [
            {
                "description": "JOIN between customer and subsidiary",
                "query": """
                    SELECT 
                        c.id,
                        c.companyname,
                        s.name as subsidiary_name,
                        s.country
                    FROM customer c
                    LEFT JOIN subsidiary s ON c.subsidiary = s.id
                    WHERE c.companyname IS NOT NULL
                    AND ROWNUM <= 5
                """,
            },
            {
                "description": "Customer aggregation with GROUP BY",
                "query": """
                    SELECT 
                        subsidiary,
                        COUNT(*) as customer_count,
                        MIN(datecreated) as first_customer,
                        MAX(datecreated) as latest_customer
                    FROM customer
                    WHERE subsidiary IS NOT NULL
                    GROUP BY subsidiary
                """,
            },
            {
                "description": "Item pricing analysis",
                "query": """
                    SELECT 
                        itemtype,
                        COUNT(*) as item_count,
                        AVG(cost) as avg_cost,
                        MIN(cost) as min_cost,
                        MAX(cost) as max_cost
                    FROM item
                    WHERE cost IS NOT NULL
                    GROUP BY itemtype
                """,
            },
            {
                "description": "CASE statement test",
                "query": """
                    SELECT 
                        id,
                        companyname,
                        CASE 
                            WHEN companyname LIKE '%Coffee%' THEN 'Coffee Related'
                            WHEN companyname LIKE '%Gym%' THEN 'Gym Related'
                            ELSE 'Other'
                        END as category
                    FROM customer
                    WHERE ROWNUM <= 10
                """,
            },
            {
                "description": "Date filtering",
                "query": """
                    SELECT 
                        id,
                        companyname,
                        datecreated
                    FROM customer
                    WHERE datecreated >= '01/01/2022'
                    AND datecreated <= '31/12/2024'
                    AND ROWNUM <= 10
                """,
            },
            {
                "description": "DISTINCT values",
                "query": """
                    SELECT DISTINCT 
                        entitystatus
                    FROM customer
                    WHERE entitystatus IS NOT NULL
                """,
            },
            {
                "description": "Subquery test",
                "query": """
                    SELECT 
                        id,
                        companyname
                    FROM customer
                    WHERE subsidiary IN (
                        SELECT id 
                        FROM subsidiary 
                        WHERE country = 'IE'
                    )
                    AND ROWNUM <= 5
                """,
            },
            {
                "description": "UNION test",
                "query": """
                    SELECT 'Customer' as type, id, companyname as name FROM customer WHERE ROWNUM <= 3
                    UNION
                    SELECT 'Vendor' as type, id, companyname as name FROM vendor WHERE ROWNUM <= 3
                """,
            },
            {
                "description": "String functions",
                "query": """
                    SELECT 
                        id,
                        companyname,
                        UPPER(companyname) as upper_name,
                        LOWER(companyname) as lower_name,
                        LENGTH(companyname) as name_length
                    FROM customer
                    WHERE ROWNUM <= 5
                """,
            },
            {
                "description": "NULL handling",
                "query": """
                    SELECT 
                        id,
                        companyname,
                        COALESCE(email, 'No Email') as email_display,
                        CASE WHEN email IS NULL THEN 'Missing' ELSE 'Present' END as email_status
                    FROM customer
                    WHERE ROWNUM <= 10
                """,
            },
        ]

        for query_info in advanced_queries:
            print(f"\n📝 {query_info['description']}")
            result = self.execute_query(query_info["query"], query_info["description"])

            if result["status"] == "success":
                print("   ✅ Query successful")
                if result["data"].get("items"):
                    print(f"   Records returned: {len(result['data']['items'])}")
                    # Show sample
                    sample = (
                        result["data"]["items"][0] if result["data"]["items"] else {}
                    )
                    print(f"   Sample: {json.dumps(sample, indent=0)[:150]}...")

                self.results["working_patterns"].append(query_info["description"])
            else:
                print("   ❌ Query failed")

            time.sleep(0.5)

    def test_analytics_tables(self):
        """Test analytics and reporting tables"""
        print("\n" + "=" * 80)
        print("📈 TESTING ANALYTICS & REPORTING TABLES")
        print("=" * 80)

        analytics_tables = [
            # Transaction analytics
            "transaction",
            "transactionline",
            "transactionaccountingline",
            "transaction_alt",
            "transactionlines",
            "transactions",
            # Analytics views
            "analytics_customer",
            "analytics_item",
            "analytics_transaction",
            "customeranalyticsbyperiod",
            "itemanalyticsbyperiod",
            "transactionanalyticsbyperiod",
            "transactionanalyticsbyuser",
            # Financial analytics
            "financialanalysis",
            "budgetanalysis",
            "consolidatedanalysis",
            "accountanalysis",
            "glanalysis",
            "trialbalance",
            # Sales analytics
            "salesanalysis",
            "salesbyitem",
            "salesbycustomer",
            "salesbyperiod",
            "salesbysubsidiary",
            "salesforecast",
            # Inventory analytics
            "inventoryanalysis",
            "inventorybyitem",
            "inventorybylocation",
            "inventoryaging",
            "inventoryturnover",
            # Alternative names
            "tranline",
            "tranlines",
            "tran",
            "trans",
            "accountingline",
            "accountinglines",
            # System analytics
            "auditlog",
            "audittrail",
            "systemlog",
            "activitylog",
            "userlog",
            "loginlog",
            "changehistory",
        ]

        for table in analytics_tables:
            print(f"\nTesting: {table}")

            # Try different query patterns
            queries_to_try = [
                f"SELECT * FROM {table} WHERE ROWNUM = 1",
                f"SELECT * FROM {table}s WHERE ROWNUM = 1",  # Plural
                f"SELECT * FROM {table.upper()} WHERE ROWNUM = 1",  # Uppercase
                f"SELECT * FROM Analytics.{table} WHERE ROWNUM = 1",  # Schema prefix
                f"SELECT * FROM ANALYTICS.{table.upper()} WHERE ROWNUM = 1",
            ]

            found = False
            for query in queries_to_try:
                result = self.execute_query(query, f"Testing {table} variations")
                if result["status"] == "success":
                    print(f"  ✅ Found with query: {query[:50]}...")
                    found = True
                    break

            if not found:
                print("  ❌ Not accessible in any variation")

            time.sleep(0.3)

    def test_custom_records(self):
        """Test custom records and fields"""
        print("\n" + "=" * 80)
        print("🔧 TESTING CUSTOM RECORDS & FIELDS")
        print("=" * 80)

        # Try to discover custom records
        print("\nAttempting to discover custom records...")

        # Test pattern-based discovery
        patterns = [
            "customrecord_%",
            "customlist_%",
            "custentity_%",
            "custitem_%",
            "custbody_%",
            "custcol_%",
        ]

        # Since we know some custom records from metadata, test them
        known_custom = [
            "customrecord_2663_batch",
            "customrecord_nav_shortcut_tooltip",
            "customrecord_ns_ibe_project",
            "customlist596",
            "customlist_2663_week_of_month",
        ]

        for custom in known_custom:
            print(f"\nTesting: {custom}")
            result = self.execute_query(
                f"SELECT * FROM {custom} WHERE ROWNUM = 1", f"Custom record: {custom}"
            )

            if result["status"] == "success":
                print("  ✅ Accessible")
                if result["data"].get("items"):
                    fields = list(result["data"]["items"][0].keys())
                    print(f"  Fields: {', '.join(fields[:5])}...")
            else:
                print("  ❌ Not accessible via SuiteQL")

            time.sleep(0.3)

        # Test custom fields on standard records
        print("\n\nTesting custom fields on standard records...")

        # Get all fields from customer table
        result = self.execute_query(
            "SELECT * FROM customer WHERE ROWNUM = 1",
            "Get all customer fields including custom",
        )

        if result["status"] == "success" and result["data"].get("items"):
            fields = list(result["data"]["items"][0].keys())
            custom_fields = [f for f in fields if f.startswith("cust")]

            if custom_fields:
                print(f"\n✅ Found {len(custom_fields)} custom fields on customer:")
                for cf in custom_fields[:10]:
                    print(f"  - {cf}")

                # Test querying custom fields
                custom_field_query = f"""
                    SELECT 
                        id,
                        companyname,
                        {', '.join(custom_fields[:3])}
                    FROM customer
                    WHERE ROWNUM <= 5
                """

                cf_result = self.execute_query(
                    custom_field_query, "Query custom fields"
                )
                if cf_result["status"] == "success":
                    print("\n✅ Custom fields are queryable")

    def test_system_tables(self):
        """Test system and metadata tables"""
        print("\n" + "=" * 80)
        print("⚙️ TESTING SYSTEM & METADATA TABLES")
        print("=" * 80)

        system_tables = [
            # Metadata
            "record",
            "recordtype",
            "field",
            "fieldtype",
            "sublist",
            "subtab",
            "form",
            "workflow",
            # User and roles
            "user",
            "role",
            "permission",
            "rolepermission",
            "userpermission",
            "useraudit",
            "userrole",
            # Saved searches and reports
            "savedsearch",
            "savedreport",
            "savedcsv",
            "customsearch",
            "customreport",
            "report",
            # Scripts and customizations
            "script",
            "scriptdeployment",
            "customization",
            "bundle",
            "suitebundle",
            "customcode",
            # Files and documents
            "file",
            "folder",
            "document",
            "attachment",
            "mediaitem",
            "image",
            # Communication
            "message",
            "note",
            "email",
            "phonecall",
            "emailtemplate",
            "lettertemplate",
            # Audit and logging
            "systemnote",
            "auditlog",
            "loginaudit",
            "changehistory",
            "deletedrecord",
            "trashedrecord",
        ]

        for table in system_tables:
            result = self.execute_query(
                f"SELECT * FROM {table} WHERE ROWNUM = 1", f"System table: {table}"
            )

            if result["status"] == "success":
                print(f"✅ {table} - accessible")
            else:
                print(f"❌ {table} - not accessible")

            time.sleep(0.3)

    def test_special_queries(self):
        """Test special queries and edge cases"""
        print("\n" + "=" * 80)
        print("🎯 TESTING SPECIAL QUERIES & EDGE CASES")
        print("=" * 80)

        special_queries = [
            {
                "description": "Get database version/info",
                "query": "SELECT VERSION() as version",
            },
            {
                "description": "Current date/time",
                "query": "SELECT CURRENT_DATE as today, CURRENT_TIMESTAMP as now",
            },
            {
                "description": "Test LIKE with wildcards",
                "query": """
                    SELECT id, companyname 
                    FROM customer 
                    WHERE companyname LIKE '%Coffee%' 
                    OR companyname LIKE '%Gym%'
                    AND ROWNUM <= 10
                """,
            },
            {
                "description": "Test IN operator",
                "query": """
                    SELECT id, name 
                    FROM location 
                    WHERE id IN (1, 2, 3, 4, 5)
                """,
            },
            {
                "description": "Test BETWEEN",
                "query": """
                    SELECT id, companyname, datecreated
                    FROM customer
                    WHERE datecreated BETWEEN '01/01/2022' AND '31/12/2023'
                    AND ROWNUM <= 10
                """,
            },
            {
                "description": "Test ORDER BY",
                "query": """
                    SELECT id, companyname, datecreated
                    FROM customer
                    WHERE ROWNUM <= 10
                    ORDER BY datecreated DESC
                """,
            },
            {
                "description": "Test HAVING clause",
                "query": """
                    SELECT 
                        subsidiary,
                        COUNT(*) as cnt
                    FROM customer
                    GROUP BY subsidiary
                    HAVING COUNT(*) > 1
                """,
            },
            {
                "description": "Test nested SELECT",
                "query": """
                    SELECT 
                        (SELECT COUNT(*) FROM customer) as total_customers,
                        (SELECT COUNT(*) FROM vendor) as total_vendors,
                        (SELECT COUNT(*) FROM item) as total_items
                """,
            },
            {
                "description": "Test WITH clause (CTE)",
                "query": """
                    WITH customer_summary AS (
                        SELECT subsidiary, COUNT(*) as customer_count
                        FROM customer
                        GROUP BY subsidiary
                    )
                    SELECT * FROM customer_summary WHERE customer_count > 0
                """,
            },
            {
                "description": "Test EXISTS",
                "query": """
                    SELECT c.id, c.companyname
                    FROM customer c
                    WHERE EXISTS (
                        SELECT 1 FROM customer c2 
                        WHERE c2.subsidiary = c.subsidiary 
                        AND c2.id != c.id
                    )
                    AND ROWNUM <= 5
                """,
            },
        ]

        for query_info in special_queries:
            print(f"\n📝 {query_info['description']}")
            result = self.execute_query(query_info["query"], query_info["description"])

            if result["status"] == "success":
                print("   ✅ Supported")
                if result["data"].get("items"):
                    print(
                        f"   Result: {json.dumps(result['data']['items'][0], indent=0)[:100]}..."
                    )
            else:
                print("   ❌ Not supported or failed")

            time.sleep(0.5)

    def generate_report(self):
        """Generate comprehensive report"""
        print("\n" + "=" * 80)
        print("📊 GENERATING COMPREHENSIVE REPORT")
        print("=" * 80)

        # Calculate statistics
        self.results["statistics"] = {
            "total_queries": self.query_count,
            "successful": self.success_count,
            "failed": self.failure_count,
            "success_rate": f"{(self.success_count/self.query_count*100):.1f}%"
            if self.query_count > 0
            else "0%",
            "tables_discovered": len(self.results["discovered_tables"]),
            "working_patterns": len(self.results["working_patterns"]),
        }

        # Save to file
        with open("netsuite_extensive_test_results.json", "w") as f:
            json.dump(self.results, f, indent=2)

        # Print summary
        print("\n📈 TESTING SUMMARY:")
        print(f"   Total Queries Executed: {self.query_count}")
        print(f"   Successful: {self.success_count}")
        print(f"   Failed: {self.failure_count}")
        print(f"   Success Rate: {self.results['statistics']['success_rate']}")
        print(f"   Tables Discovered: {len(self.results['discovered_tables'])}")

        print("\n✅ WORKING TABLES:")
        for table in self.results["discovered_tables"].keys():
            field_count = len(self.results["discovered_tables"][table])
            print(f"   - {table}: {field_count} fields")

        print("\n✅ WORKING QUERY PATTERNS:")
        for pattern in self.results["working_patterns"]:
            print(f"   - {pattern}")

        print("\n📁 Full results saved to: netsuite_extensive_test_results.json")

        return self.results

    def run_all_tests(self):
        """Run all test suites"""
        print("\n" + "🚀" * 40)
        print("    STARTING EXTENSIVE NETSUITE TESTING")
        print("    This will test hundreds of queries and may take several minutes...")
        print("🚀" * 40)

        # Run test suites
        self.test_basic_tables()
        self.test_advanced_queries()
        self.test_analytics_tables()
        self.test_custom_records()
        self.test_system_tables()
        self.test_special_queries()

        # Generate report
        return self.generate_report()


if __name__ == "__main__":
    tester = NetSuiteExtensiveTester()
    results = tester.run_all_tests()

    print("\n" + "=" * 80)
    print("✅ EXTENSIVE TESTING COMPLETE!")
    print("=" * 80)
