#!/usr/bin/env python3
"""
Fixed version: List NetSuite saved searches with correct SOAP versions
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

# Load environment variables
load_dotenv()


def list_saved_searches_fixed():
    """List saved searches using correct SOAP API versions"""

    # Get credentials
    consumer_key = os.getenv("GYM_PLUS_COFFEE_CONSUMER_ID")
    consumer_secret = os.getenv("GYM_PLUS_COFFEE_CONSUMER_SECRET")
    token_id = os.getenv("GYM_PLUS_COFFEE_TOKEN_ID")
    token_secret = os.getenv("GYM_PLUS_COFFEE_TOKEN_SECRET")

    account_id = "7326096_SB1"
    url_account_id = "7326096-sb1"

    print("🔍 NetSuite Saved Search Discovery (Fixed Versions)")
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

    # Test different SOAP versions with correct namespaces
    soap_tests = [
        {
            "version": "2024_1",
            "url": f"https://{url_account_id}.suitetalk.api.netsuite.com/services/NetSuitePort_2024_1",
            "msg_ns": "urn:messages_2024_1.platform.webservices.netsuite.com",
            "core_ns": "urn:core_2024_1.platform.webservices.netsuite.com",
        },
        {
            "version": "2023_2",
            "url": f"https://{url_account_id}.suitetalk.api.netsuite.com/services/NetSuitePort_2023_2",
            "msg_ns": "urn:messages_2023_2.platform.webservices.netsuite.com",
            "core_ns": "urn:core_2023_2.platform.webservices.netsuite.com",
        },
        {
            "version": "2022_2",
            "url": f"https://{url_account_id}.suitetalk.api.netsuite.com/services/NetSuitePort_2022_2",
            "msg_ns": "urn:messages_2022_2.platform.webservices.netsuite.com",
            "core_ns": "urn:core_2022_2.platform.webservices.netsuite.com",
        },
    ]

    saved_searches_found = []

    for test in soap_tests:
        print(f"\n📊 TESTING SOAP VERSION: {test['version']}")
        print("-" * 50)

        # Build SOAP envelope with correct namespaces for this version
        soap_envelope = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
               xmlns:platformMsgs="{test['msg_ns']}"
               xmlns:platformCore="{test['core_ns']}">
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
                <platformCore:searchType>Transaction</platformCore:searchType>
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
                test["url"], data=soap_envelope, headers=headers, timeout=30
            )

            print(f"Status Code: {response.status_code}")

            if response.status_code == 200:
                print("✅ SOAP request successful!")

                # Parse XML response - be more flexible with namespaces
                try:
                    # Remove namespaces for easier parsing
                    xml_str = response.text
                    # Simple namespace removal for parsing
                    xml_str = xml_str.replace("xmlns:", "xmlnamespace:")
                    xml_str = xml_str.replace("xmlns=", "xmlnamespace=")

                    root = ET.fromstring(xml_str)

                    # Look for saved search data in various possible locations
                    for elem in root.iter():
                        # Check for elements that might contain saved search info
                        if any(
                            keyword in elem.tag.lower()
                            for keyword in [
                                "recordref",
                                "savedsearch",
                                "searchid",
                                "searchrecord",
                            ]
                        ):
                            # Extract attributes
                            internal_id = elem.get("internalId", "")
                            script_id = elem.get("scriptId", "")
                            name = elem.text if elem.text else ""

                            # Also check for child elements
                            for child in elem:
                                if not name and child.text:
                                    name = child.text

                            if internal_id or script_id or name:
                                saved_search = {
                                    "internalId": internal_id,
                                    "scriptId": script_id,
                                    "name": name,
                                }
                                saved_searches_found.append(saved_search)
                                print(
                                    f"  Found: ID={internal_id}, Script={script_id}, Name={name}"
                                )

                    if not saved_searches_found:
                        print("\nChecking raw response structure...")
                        # Show first 2000 chars to see what we got
                        print(response.text[:2000])

                except Exception as e:
                    print(f"Error parsing XML: {e}")
                    print("\nRaw response snippet:")
                    print(response.text[:1000])

            elif response.status_code == 500:
                print("❌ SOAP fault")

                # Parse fault message
                try:
                    root = ET.fromstring(response.text)
                    fault_found = False
                    for elem in root.iter():
                        if "faultstring" in elem.tag.lower():
                            print(f"   Fault: {elem.text}")
                            fault_found = True
                        elif "message" in elem.tag.lower() and elem.text:
                            print(f"   Message: {elem.text}")
                            fault_found = True

                    if not fault_found:
                        print("   Response snippet:")
                        print(response.text[:500])

                except Exception as e:
                    print(f"   Could not parse fault: {e}")

        except requests.exceptions.Timeout:
            print("⏰ Request timed out")
        except Exception as e:
            print(f"❌ Error: {str(e)[:200]}")

    # Also try querying for Customer saved searches
    print("\n" + "=" * 80)
    print("📊 TRYING CUSTOMER SAVED SEARCHES")
    print("-" * 50)

    for test in soap_tests[:1]:  # Just try one version
        print(f"\nVersion: {test['version']}")

        # Try Customer record type
        soap_envelope = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
               xmlns:platformMsgs="{test['msg_ns']}"
               xmlns:platformCore="{test['core_ns']}">
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
                <platformCore:searchType>Customer</platformCore:searchType>
            </platformMsgs:record>
        </platformMsgs:getSavedSearch>
    </soap:Body>
</soap:Envelope>"""

        try:
            response = requests.post(
                test["url"],
                data=soap_envelope,
                headers={
                    "Content-Type": "text/xml; charset=utf-8",
                    "SOAPAction": "getSavedSearch",
                    "Accept": "text/xml",
                },
                timeout=30,
            )

            print(f"Status Code: {response.status_code}")

            if response.status_code == 200:
                print("✅ Customer search request successful!")
                print("Response snippet:")
                print(response.text[:1000])
            else:
                print(f"❌ Status: {response.status_code}")

        except Exception as e:
            print(f"❌ Error: {str(e)[:100]}")

    print("\n" + "=" * 80)
    print("📊 FINAL SUMMARY")
    print("=" * 80)

    if saved_searches_found:
        print(f"\n🎉 FOUND {len(saved_searches_found)} SAVED SEARCHES!")
        print("\nSaved Searches List:")
        for i, ss in enumerate(saved_searches_found, 1):
            print(f"{i}. Internal ID: {ss['internalId']}")
            print(f"   Script ID: {ss['scriptId']}")
            print(f"   Name: {ss['name']}")
            print()
    else:
        print("""
❌ Could not retrieve saved searches via SOAP

POSSIBLE REASONS:
1. SOAP Web Services might not be enabled for this account
2. Token-based authentication might not have SOAP permissions
3. The role might not have saved search visibility permissions
4. SOAP is being phased out in favor of REST API/SuiteQL

ALTERNATIVES:
1. Manually document saved search IDs from NetSuite UI:
   - Go to Lists > Search > Saved Searches
   - Note the ID column for each search
   
2. Create RESTlets (requires SuiteScript):
   - Deploy custom scripts to expose saved searches
   - Call them via REST endpoints
   
3. Recreate saved searches in SuiteQL:
   - Since we have full transaction access
   - Build equivalent queries using the 93 fields we discovered
   
4. Use NetSuite's UI export:
   - Export saved search definitions
   - Convert to SuiteQL programmatically
""")

    # Save any results found
    if saved_searches_found:
        with open("saved_searches_list.json", "w") as f:
            json.dump(saved_searches_found, f, indent=2)
        print("\n📁 Saved search list exported to: saved_searches_list.json")


if __name__ == "__main__":
    list_saved_searches_fixed()
