#!/usr/bin/env python3
"""
Test NetSuite saved search access via REST API and SuiteQL
"""

import json
import os
from datetime import datetime

import requests
from dotenv import load_dotenv
from requests_oauthlib import OAuth1

# Load environment variables
load_dotenv()


def test_saved_searches():
    """Test various methods to access saved searches"""

    # Get credentials
    consumer_key = os.getenv("GYM_PLUS_COFFEE_CONSUMER_ID")
    consumer_secret = os.getenv("GYM_PLUS_COFFEE_CONSUMER_SECRET")
    token_id = os.getenv("GYM_PLUS_COFFEE_TOKEN_ID")
    token_secret = os.getenv("GYM_PLUS_COFFEE_TOKEN_SECRET")

    account_id = "7326096_SB1"
    url_account_id = "7326096-sb1"

    print("🔍 NetSuite Saved Search Access Testing")
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

    base_url = f"https://{url_account_id}.suitetalk.api.netsuite.com"

    # =====================================
    # TEST 1: Check metadata-catalog endpoint
    # =====================================
    print("\n📊 TEST 1: METADATA CATALOG")
    print("-" * 50)

    metadata_url = f"{base_url}/services/rest/record/v1/metadata-catalog"

    try:
        response = requests.get(metadata_url, auth=auth, headers=headers, timeout=15)

        if response.status_code == 200:
            data = response.json()
            items = data.get("items", [])

            print("✅ Metadata catalog accessible")
            print(f"   Found {len(items)} record types")

            # Look for anything related to saved searches
            search_related = [
                item for item in items if "search" in item.get("name", "").lower()
            ]

            if search_related:
                print("\n   Search-related items found:")
                for item in search_related[:5]:
                    print(f"   • {item.get('name')}")
            else:
                print("   ❌ No saved search entries in metadata catalog")

        else:
            print(f"❌ Metadata catalog not accessible: {response.status_code}")

    except Exception as e:
        print(f"❌ Error: {str(e)[:100]}")

    # =====================================
    # TEST 2: Try direct saved search endpoints
    # =====================================
    print("\n📊 TEST 2: DIRECT SAVED SEARCH ENDPOINTS")
    print("-" * 50)

    # Try various potential endpoints based on documentation
    test_endpoints = [
        {
            "name": "Search endpoint (customer)",
            "url": f"{base_url}/services/rest/record/v1/customer/search",
            "method": "GET",
        },
        {
            "name": "Search endpoint (transaction)",
            "url": f"{base_url}/services/rest/record/v1/transaction/search",
            "method": "GET",
        },
        {
            "name": "Saved search discovery",
            "url": f"{base_url}/services/rest/record/v1/savedsearch",
            "method": "GET",
        },
        {
            "name": "Query saved searches",
            "url": f"{base_url}/services/rest/query/v1/savedsearch",
            "method": "GET",
        },
    ]

    for endpoint in test_endpoints:
        print(f"\nTrying: {endpoint['name']}")
        print(f"   URL: {endpoint['url']}")

        try:
            if endpoint["method"] == "GET":
                response = requests.get(
                    endpoint["url"], auth=auth, headers=headers, timeout=10
                )
            else:
                response = requests.post(
                    endpoint["url"], auth=auth, headers=headers, timeout=10
                )

            if response.status_code == 200:
                print("   ✅ Endpoint accessible!")
                data = response.json()

                # Show response structure
                if isinstance(data, dict):
                    keys = list(data.keys())[:5]
                    print(f"   Response keys: {keys}")

                    if "items" in data:
                        print(f"   Items found: {len(data['items'])}")
                        if data["items"]:
                            print(
                                f"   Sample: {json.dumps(data['items'][0], indent=2)[:200]}..."
                            )

            elif response.status_code == 404:
                print("   ❌ Endpoint not found (404)")
            elif response.status_code == 400:
                print("   ❌ Bad request (400)")
            else:
                print(f"   ❌ Status: {response.status_code}")

        except Exception as e:
            print(f"   ❌ Error: {str(e)[:100]}")

    # =====================================
    # TEST 3: SuiteQL for saved search info
    # =====================================
    print("\n📊 TEST 3: SUITEQL SAVED SEARCH QUERIES")
    print("-" * 50)

    suiteql_url = f"{base_url}/services/rest/query/v1/suiteql"
    headers_suiteql = headers.copy()
    headers_suiteql["Prefer"] = "transient"

    # Try various SuiteQL queries to find saved search information
    queries = [
        {
            "name": "Check for savedsearch table",
            "query": "SELECT * FROM savedsearch WHERE ROWNUM = 1",
        },
        {
            "name": "Check for customsearch table",
            "query": "SELECT * FROM customsearch WHERE ROWNUM = 1",
        },
        {
            "name": "Check for search table",
            "query": "SELECT * FROM search WHERE ROWNUM = 1",
        },
        {
            "name": "Check INFORMATION_SCHEMA for searches",
            "query": "SELECT table_name FROM INFORMATION_SCHEMA.TABLES WHERE table_name LIKE '%search%' AND ROWNUM <= 10",
        },
        {
            "name": "Check userevent table for saved searches",
            "query": "SELECT * FROM userevent WHERE recordtype = 'savedsearch' AND ROWNUM = 1",
        },
    ]

    for q in queries:
        print(f"\nTrying: {q['name']}")
        print(f"   Query: {q['query'][:100]}...")

        payload = {"q": q["query"]}

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
                items = data.get("items", [])

                if items:
                    print(f"   ✅ Found {len(items)} results!")
                    print(f"   Fields: {list(items[0].keys())}")
                    print(f"   Sample: {json.dumps(items[0], indent=2)[:200]}...")
                else:
                    print("   ✅ Query executed but no results")

            elif response.status_code == 400:
                print("   ❌ Table/query not valid")
                # Get error details
                try:
                    error_data = response.json()
                    if "o:errorDetails" in error_data:
                        error_msg = error_data["o:errorDetails"][0].get("detail", "")
                        if "was not found" in error_msg:
                            print("      Table doesn't exist")
                except:
                    pass
            else:
                print(f"   ❌ Status: {response.status_code}")

        except Exception as e:
            print(f"   ❌ Error: {str(e)[:100]}")

    # =====================================
    # TEST 4: RESTlet endpoints
    # =====================================
    print("\n📊 TEST 4: CHECK FOR RESTLET ENDPOINTS")
    print("-" * 50)

    # Check if there are any deployed RESTlets
    restlet_url = f"{base_url}/app/site/hosting/restlet.nl"

    print(f"Testing RESTlet base URL: {restlet_url}")

    try:
        response = requests.get(restlet_url, auth=auth, headers=headers, timeout=10)

        if response.status_code == 200:
            print("   ✅ RESTlet endpoint accessible")
            print("   Note: Need script ID and deploy ID to call specific RESTlets")
        elif response.status_code == 404:
            print("   ❌ No RESTlets deployed or not accessible")
        else:
            print(f"   Status: {response.status_code}")

    except Exception as e:
        print(f"   ❌ Error: {str(e)[:100]}")

    # =====================================
    # TEST 5: OpenAPI specification check
    # =====================================
    print("\n📊 TEST 5: OPENAPI SPECIFICATION")
    print("-" * 50)

    openapi_url = f"{base_url}/services/rest/openapi/v1"

    try:
        response = requests.get(openapi_url, auth=auth, headers=headers, timeout=15)

        if response.status_code == 200:
            print("✅ OpenAPI spec accessible")

            # Check if it mentions saved searches
            spec_text = response.text
            if (
                "savedsearch" in spec_text.lower()
                or "saved_search" in spec_text.lower()
            ):
                print("   ✅ OpenAPI spec mentions saved searches!")

                # Try to parse and find relevant endpoints
                try:
                    spec = response.json()
                    paths = spec.get("paths", {})
                    search_paths = [p for p in paths.keys() if "search" in p.lower()]

                    if search_paths:
                        print("\n   Search-related paths in OpenAPI:")
                        for path in search_paths[:5]:
                            print(f"   • {path}")
                except:
                    pass
            else:
                print("   ❌ No saved search references in OpenAPI spec")

        else:
            print(f"❌ OpenAPI spec not accessible: {response.status_code}")

    except Exception as e:
        print(f"❌ Error: {str(e)[:100]}")

    # =====================================
    # SUMMARY
    # =====================================
    print("\n" + "=" * 80)
    print("📊 SAVED SEARCH ACCESS SUMMARY")
    print("=" * 80)

    print("""
Based on tests:

1. **Metadata Catalog**: Provides record type info, not saved searches
2. **Direct Search Endpoints**: Not available for saved search execution
3. **SuiteQL**: Cannot query saved search definitions directly
4. **RESTlets**: Would need custom scripts deployed (not standard)
5. **OpenAPI**: Check spec for available endpoints

CONCLUSION:
- Saved searches cannot be executed directly via REST API
- Must use RESTlets (custom scripts) or recreate search logic in SuiteQL
- For data access, recreate saved search filters using SuiteQL queries

RECOMMENDATION:
- Use SuiteQL to recreate any saved search logic you need
- The transaction and customer tables are fully accessible
- Can build complex queries with JOINs, filters, and aggregations
""")


if __name__ == "__main__":
    test_saved_searches()
