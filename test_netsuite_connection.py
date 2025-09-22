#!/usr/bin/env python3
"""
NetSuite Token-Based Authentication (TBA) Connection Test
Tests the connection to NetSuite using OAuth 1.0 (TBA) with the GYM + Coffee credentials
"""

import os
import sys
from datetime import datetime

import requests
from dotenv import load_dotenv
from requests_oauthlib import OAuth1

# Load environment variables
load_dotenv()


def test_netsuite_tba():
    """Test NetSuite TBA (OAuth 1.0) connection with credentials from .env file"""

    # Get credentials from environment variables
    consumer_key = os.getenv("GYM_PLUS_COFFEE_CONSUMER_ID")
    consumer_secret = os.getenv("GYM_PLUS_COFFEE_CONSUMER_SECRET")
    token_id = os.getenv("GYM_PLUS_COFFEE_TOKEN_ID")
    token_secret = os.getenv("GYM_PLUS_COFFEE_TOKEN_SECRET")

    # Verify all credentials are present
    if not all([consumer_key, consumer_secret, token_id, token_secret]):
        print("❌ Error: Missing NetSuite TBA credentials in .env file")
        print("Required variables:")
        print(f"  GYM_PLUS_COFFEE_CONSUMER_ID: {'✓' if consumer_key else '✗'}")
        print(f"  GYM_PLUS_COFFEE_CONSUMER_SECRET: {'✓' if consumer_secret else '✗'}")
        print(f"  GYM_PLUS_COFFEE_TOKEN_ID: {'✓' if token_id else '✗'}")
        print(f"  GYM_PLUS_COFFEE_TOKEN_SECRET: {'✓' if token_secret else '✗'}")
        return False

    print("🔐 NetSuite TBA (OAuth 1.0) Connection Test")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("\n📋 TBA Credentials Status:")
    print(f"  Consumer Key: {consumer_key[:15]}...{consumer_key[-8:]}")
    print(f"  Consumer Secret: {'*' * 15}...{consumer_secret[-8:]}")
    print(f"  Token ID: {token_id[:15]}...{token_id[-8:]}")
    print(f"  Token Secret: {'*' * 15}...{token_secret[-8:]}")

    # GYM + Coffee NetSuite Account ID
    account_ids = [
        "7326096_SB1",  # GYM + Coffee Sandbox 1 (confirmed)
        "7326096-SB1",  # Alternative format with hyphen
        "7326096",  # Production (if exists)
    ]

    print("\n🔍 Testing NetSuite TBA endpoints...")
    print("Using OAuth 1.0 signature method: HMAC-SHA256")

    successful_connection = False
    working_config = {}

    for account_id in account_ids:
        print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"📡 Testing Account ID: {account_id}")

        # Format the account ID for the URL (replace underscore with hyphen)
        url_account_id = account_id.lower().replace("_", "-")

        # Test both signature methods as some accounts may require SHA1
        signature_methods = ["HMAC-SHA256", "HMAC-SHA1"]

        for sig_method in signature_methods:
            print(f"\n  Signature Method: {sig_method}")

            # Test different API endpoints
            endpoints = [
                {
                    "name": "OpenAPI Specification",
                    "url": f"https://{url_account_id}.suitetalk.api.netsuite.com/services/rest/openapi/v1",
                    "description": "Basic connectivity test",
                },
                {
                    "name": "Metadata Catalog",
                    "url": f"https://{url_account_id}.suitetalk.api.netsuite.com/services/rest/record/v1/metadata-catalog",
                    "description": "List available record types",
                },
                {
                    "name": "Customer Records",
                    "url": f"https://{url_account_id}.suitetalk.api.netsuite.com/services/rest/record/v1/customer?limit=1",
                    "description": "Fetch customer data",
                },
                {
                    "name": "Employee Records",
                    "url": f"https://{url_account_id}.suitetalk.api.netsuite.com/services/rest/record/v1/employee?limit=1",
                    "description": "Fetch employee data",
                },
            ]

            for endpoint in endpoints:
                print(f"\n  📍 {endpoint['name']}")
                print(f"     {endpoint['description']}")
                print(f"     URL: {endpoint['url'][:80]}...")

                # Setup OAuth1 authentication for TBA
                auth = OAuth1(
                    client_key=consumer_key,
                    client_secret=consumer_secret,
                    resource_owner_key=token_id,
                    resource_owner_secret=token_secret,
                    signature_method=sig_method,
                    realm=account_id,  # NetSuite requires realm parameter
                )

                try:
                    # Make the request with TBA authentication
                    response = requests.get(
                        endpoint["url"],
                        auth=auth,
                        headers={
                            "Accept": "application/json",
                            "Content-Type": "application/json",
                            "User-Agent": "GYM+Coffee TBA Test/1.0",
                        },
                        timeout=15,
                    )

                    print(f"     Status: {response.status_code}", end="")

                    if response.status_code == 200:
                        print(" ✅ SUCCESS!")
                        successful_connection = True
                        working_config = {
                            "account_id": account_id,
                            "url_account_id": url_account_id,
                            "signature_method": sig_method,
                            "endpoint": endpoint["name"],
                        }

                        # Parse and display response info
                        try:
                            json_response = response.json()
                            if isinstance(json_response, list):
                                print(
                                    f"     Response: List with {len(json_response)} items"
                                )
                            elif isinstance(json_response, dict):
                                keys = list(json_response.keys())[:3]
                                print(f"     Response Keys: {', '.join(keys)}")
                                # If it's metadata, show some record types
                                if "items" in json_response:
                                    items = json_response.get("items", [])[:3]
                                    if items:
                                        print(
                                            f"     Sample Records: {', '.join([i.get('id', 'unknown') for i in items])}"
                                        )
                        except:
                            print(f"     Response Size: {len(response.text)} bytes")

                        # Found working config, break out of all loops
                        break

                    elif response.status_code == 401:
                        print(" ❌ UNAUTHORIZED")
                        try:
                            error_data = response.json()
                            if "o:errorDetails" in error_data:
                                details = error_data["o:errorDetails"][0]
                                print(
                                    f"     Error: {details.get('detail', 'Authentication failed')}"
                                )
                        except:
                            print(f"     Error: {response.text[:100]}")

                    elif response.status_code == 403:
                        print(" ⚠️  FORBIDDEN - Check permissions")

                    elif response.status_code == 404:
                        print(" ⚠️  NOT FOUND - Wrong account/endpoint")

                    else:
                        print(f" ⚠️  Status {response.status_code}")

                except requests.exceptions.Timeout:
                    print("     ⏱️  TIMEOUT (15s)")

                except requests.exceptions.ConnectionError as e:
                    print("     🔌 CONNECTION ERROR")
                    if "Name or service not known" in str(e):
                        print("        Invalid account ID or domain")

                except Exception as e:
                    print(f"     ❌ ERROR: {type(e).__name__}")
                    print(f"        {str(e)[:80]}")

            if successful_connection:
                break

        if successful_connection:
            break

    # Final Report
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS")
    print("=" * 60)

    if successful_connection:
        print("\n✅ NetSuite TBA Authentication: SUCCESSFUL")
        print("\n🔑 Working Configuration:")
        print(f"  Account ID: {working_config['account_id']}")
        print(
            f"  API Domain: {working_config['url_account_id']}.suitetalk.api.netsuite.com"
        )
        print(f"  Signature Method: {working_config['signature_method']}")
        print(f"  Working Endpoint: {working_config['endpoint']}")

        print("\n📝 Next Steps:")
        print("  1. Save the working Account ID for production use")
        print("  2. Test specific business endpoints (orders, products, etc.)")
        print("  3. Implement error handling for production code")
        print("  4. Set up proper logging for API calls")

        print("\n💡 Example API Call:")
        print(
            f"  GET https://{working_config['url_account_id']}.suitetalk.api.netsuite.com/services/rest/record/v1/{{record_type}}"
        )

    else:
        print("\n❌ NetSuite TBA Authentication: FAILED")
        print("\n🔧 Troubleshooting Checklist:")
        print("  □ Verify Account ID with NetSuite administrator")
        print("  □ Confirm TBA is enabled in Setup > Company > Enable Features")
        print("  □ Check Integration record status in NetSuite")
        print("  □ Verify User/Role has 'Web Services' permission")
        print("  □ Confirm tokens haven't been revoked")
        print("  □ Check if account requires specific signature method")
        print("  □ Ensure no IP restrictions blocking access")

        print("\n📚 Common Issues:")
        print("  • Wrong Account ID → Get from Setup > Company > Company Information")
        print("  • Expired tokens → Generate new tokens in NetSuite")
        print("  • Permission issues → Add 'Lists > Customers' permission to role")
        print("  • Sandbox vs Production → Different account IDs and tokens")

    print("\n" + "=" * 60)
    return successful_connection


if __name__ == "__main__":
    success = test_netsuite_tba()
    sys.exit(0 if success else 1)
