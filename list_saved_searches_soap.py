#!/usr/bin/env python3
"""
List NetSuite saved searches using SOAP API with Token-Based Authentication
"""

import base64
import hashlib
import hmac
import json
import os
import random
import string
import time
import xml.etree.ElementTree as ET
from datetime import datetime

import requests
from dotenv import load_dotenv
from requests_oauthlib import OAuth1

# Load environment variables
load_dotenv()


def list_saved_searches_soap():
    """List saved searches using SOAP API"""

    # Get credentials
    consumer_key = os.getenv("GYM_PLUS_COFFEE_CONSUMER_ID")
    consumer_secret = os.getenv("GYM_PLUS_COFFEE_CONSUMER_SECRET")
    token_id = os.getenv("GYM_PLUS_COFFEE_TOKEN_ID")
    token_secret = os.getenv("GYM_PLUS_COFFEE_TOKEN_SECRET")

    account_id = "7326096_SB1"
    url_account_id = "7326096-sb1"

    print("🔍 NetSuite Saved Search Discovery via SOAP")
    print("=" * 80)
    print(f"Account: {account_id}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 80)

    # Generate nonce and timestamp for SOAP
    def generate_nonce(length=20):
        return "".join(
            random.choice(string.ascii_letters + string.digits) for _ in range(length)
        )

    timestamp = str(int(time.time()))
    nonce = generate_nonce()

    # Build signature for TokenPassport
    def compute_signature(account, consumer_key, token_id, nonce, timestamp):
        """Build and sign the TokenPassport signature for TBA"""
        base_string = "&".join([account, consumer_key, token_id, nonce, timestamp])
        key = f"{consumer_secret}&{token_secret}"
        signature = hmac.new(
            key.encode("utf-8"), base_string.encode("utf-8"), hashlib.sha256
        )
        return base64.b64encode(signature.digest()).decode("utf-8")

    signature = compute_signature(account_id, consumer_key, token_id, nonce, timestamp)

    # NetSuite SOAP endpoints
    soap_endpoints = [
        f"https://{url_account_id}.suitetalk.api.netsuite.com/services/NetSuitePort_2024_1",
        f"https://{url_account_id}.suitetalk.api.netsuite.com/services/NetSuitePort_2023_2",
        f"https://{url_account_id}.suitetalk.api.netsuite.com/services/NetSuitePort_2022_2",
        "https://webservices.netsuite.com/services/NetSuitePort_2024_1",
    ]

    # Try different SOAP versions
    for soap_url in soap_endpoints:
        print(f"\n📊 TESTING SOAP ENDPOINT: {soap_url}")
        print("-" * 50)

        # Build SOAP envelope for getSavedSearch
        soap_envelope = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
               xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
               xmlns:xsd="http://www.w3.org/2001/XMLSchema"
               xmlns:platformMsgs="urn:messages_2024_1.platform.webservices.netsuite.com"
               xmlns:platformCore="urn:core_2024_1.platform.webservices.netsuite.com">
    <soap:Header>
        <platformMsgs:tokenPassport>
            <platformCore:account>{account_id}</platformCore:account>
            <platformCore:consumerKey>{consumer_key}</platformCore:consumerKey>
            <platformCore:token>{token_id}</platformCore:token>
            <platformCore:nonce>{nonce}</platformCore:nonce>
            <platformCore:timestamp>{timestamp}</platformCore:timestamp>
            <platformMsgs:signature algorithm="HMAC-SHA256">{signature}</platformMsgs:signature>
        </platformMsgs:tokenPassport>
    </soap:Header>
    <soap:Body>
        <platformMsgs:getSavedSearch>
            <platformMsgs:record>
                <platformCore:searchType>transaction</platformCore:searchType>
            </platformMsgs:record>
        </platformMsgs:getSavedSearch>
    </soap:Body>
</soap:Envelope>"""

        headers = {
            "Content-Type": "text/xml; charset=utf-8",
            "SOAPAction": "getSavedSearch",
            "Accept": "text/xml",
        }

        try:
            response = requests.post(
                soap_url, data=soap_envelope, headers=headers, timeout=30
            )

            print(f"Status Code: {response.status_code}")

            if response.status_code == 200:
                print("✅ SOAP request successful!")

                # Parse XML response
                try:
                    root = ET.fromstring(response.text)

                    # Find saved searches in response
                    # Look for recordRefList elements
                    namespaces = {
                        "soap": "http://schemas.xmlsoap.org/soap/envelope/",
                        "platformCore": "urn:core_2024_1.platform.webservices.netsuite.com",
                        "platformMsgs": "urn:messages_2024_1.platform.webservices.netsuite.com",
                    }

                    # Try to find saved search results
                    saved_searches = []

                    # Look for recordRef elements
                    for elem in root.iter():
                        if "recordRef" in elem.tag or "savedSearch" in elem.tag:
                            internal_id = elem.get("internalId")
                            script_id = elem.get("scriptId")
                            name = elem.text if elem.text else elem.get("name", "")

                            if internal_id:
                                saved_searches.append(
                                    {
                                        "internalId": internal_id,
                                        "scriptId": script_id,
                                        "name": name,
                                    }
                                )

                    if saved_searches:
                        print(f"\n🎉 Found {len(saved_searches)} saved searches!")
                        for ss in saved_searches[:10]:  # Show first 10
                            print(
                                f"  • ID: {ss['internalId']}, Script: {ss['scriptId']}, Name: {ss['name']}"
                            )
                    else:
                        print("No saved searches found in response")
                        print("\nResponse snippet:")
                        print(response.text[:1000])

                except Exception as e:
                    print(f"Error parsing XML: {e}")
                    print("\nRaw response:")
                    print(response.text[:500])

                break  # Success, don't try other endpoints

            elif response.status_code == 500:
                print("❌ SOAP fault - checking error details")

                # Parse fault message
                try:
                    root = ET.fromstring(response.text)
                    for elem in root.iter():
                        if "faultstring" in elem.tag.lower():
                            print(f"Fault: {elem.text}")
                        if "message" in elem.tag.lower():
                            print(f"Message: {elem.text}")
                except:
                    print(response.text[:500])

            else:
                print(f"❌ Unexpected status: {response.status_code}")
                print(response.text[:300])

        except requests.exceptions.Timeout:
            print("⏰ Request timed out")
        except Exception as e:
            print(f"❌ Error: {str(e)[:200]}")

    # Alternative: Try with simpler REST-style SOAP call
    print("\n" + "=" * 80)
    print("📊 ALTERNATIVE: REST-STYLE WEB SERVICES")
    print("-" * 50)

    # Try NetSuite REST web services (different from REST API)
    rest_ws_url = f"https://{url_account_id}.suitetalk.api.netsuite.com/services/rest/query/v1/suiteql"

    # Check if there's a way to query saved search metadata via undocumented tables
    undocumented_queries = [
        "SELECT * FROM DUAL WHERE ROWNUM = 1",  # Test basic query
        "SHOW TABLES",  # Try MySQL-style
        "SELECT name FROM sys.tables WHERE name LIKE '%search%'",  # Try SQL Server style
        "SELECT tablename FROM pg_tables WHERE tablename LIKE '%search%'",  # Try PostgreSQL style
    ]

    auth = OAuth1(
        client_key=consumer_key,
        client_secret=consumer_secret,
        resource_owner_key=token_id,
        resource_owner_secret=token_secret,
        signature_method="HMAC-SHA256",
        realm=account_id,
    )

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Prefer": "transient",
    }

    for query in undocumented_queries:
        print(f"\nTrying: {query[:50]}...")
        payload = {"q": query}

        try:
            response = requests.post(
                rest_ws_url, auth=auth, headers=headers, json=payload, timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("items"):
                    print("✅ Query worked!")
                    print(f"Result: {json.dumps(data, indent=2)[:300]}")
            else:
                print(f"❌ Status: {response.status_code}")

        except Exception as e:
            print(f"❌ Error: {str(e)[:50]}")

    print("\n" + "=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    print("""
SOAP API Results:
- If successful, saved searches would be listed above
- SOAP is the only documented way to list saved searches
- Requires proper TokenPassport authentication

Alternative Methods:
- REST API: No saved search listing capability
- SuiteQL: No saved search tables available
- Metadata Catalog: Doesn't include saved searches

NEXT STEPS:
1. If SOAP worked, use the IDs to reference searches
2. If SOAP failed, may need to:
   - Install zeep library for better SOAP handling
   - Check if SOAP web services are enabled
   - Verify role has saved search permissions
3. Alternative: Manually list saved searches from UI
   and recreate their logic in SuiteQL
""")


if __name__ == "__main__":
    list_saved_searches_soap()
