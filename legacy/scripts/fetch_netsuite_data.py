#!/usr/bin/env python3
"""
Fetch and display actual data from NetSuite using TBA
"""

import os
from datetime import datetime

import requests
from dotenv import load_dotenv
from requests_oauthlib import OAuth1

# Load environment variables
load_dotenv()


def fetch_netsuite_data():
    """Fetch and display actual data from NetSuite"""

    # Get credentials from environment variables
    consumer_key = os.getenv("GYM_PLUS_COFFEE_CONSUMER_ID")
    consumer_secret = os.getenv("GYM_PLUS_COFFEE_CONSUMER_SECRET")
    token_id = os.getenv("GYM_PLUS_COFFEE_TOKEN_ID")
    token_secret = os.getenv("GYM_PLUS_COFFEE_TOKEN_SECRET")

    # Working configuration from our test
    account_id = "7326096_SB1"
    url_account_id = "7326096-sb1"

    print("🔐 NetSuite Data Retrieval")
    print("=" * 60)
    print(f"Account: {account_id}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 60)

    # Setup OAuth1 authentication
    auth = OAuth1(
        client_key=consumer_key,
        client_secret=consumer_secret,
        resource_owner_key=token_id,
        resource_owner_secret=token_secret,
        signature_method="HMAC-SHA256",
        realm=account_id,
    )

    # Headers for API calls
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "GYM+Coffee Data Fetch/1.0",
    }

    # 1. Fetch Customer Data
    print("\n📋 CUSTOMER DATA")
    print("-" * 40)

    customer_url = f"https://{url_account_id}.suitetalk.api.netsuite.com/services/rest/record/v1/customer?limit=5"

    try:
        response = requests.get(customer_url, auth=auth, headers=headers, timeout=30)

        if response.status_code == 200:
            data = response.json()

            print(f"Total Customers: {data.get('count', 'N/A')}")
            print(f"Has More: {data.get('hasMore', False)}")

            customers = data.get("items", [])
            print(f"\nShowing {len(customers)} customers:\n")

            for i, customer in enumerate(customers, 1):
                print(f"Customer #{i}:")
                print(f"  ID: {customer.get('id', 'N/A')}")

                # Check different possible field names for customer info
                print(f"  Entity ID: {customer.get('entityId', 'N/A')}")
                print(
                    f"  Company Name: {customer.get('companyName', customer.get('altName', 'N/A'))}"
                )

                # Try to get name from different fields
                first_name = customer.get("firstName", "")
                last_name = customer.get("lastName", "")
                if first_name or last_name:
                    print(f"  Name: {first_name} {last_name}".strip())

                print(f"  Email: {customer.get('email', 'N/A')}")
                print(f"  Phone: {customer.get('phone', 'N/A')}")
                print(
                    f"  Status: {customer.get('entityStatus', {}).get('name', 'N/A') if isinstance(customer.get('entityStatus'), dict) else 'N/A'}"
                )
                print(f"  Date Created: {customer.get('dateCreated', 'N/A')}")

                # Show available fields for first customer
                if i == 1:
                    print("\n  Available fields for this customer:")
                    fields = list(customer.keys())[:15]  # Show first 15 fields
                    for field in fields:
                        value = customer[field]
                        if isinstance(value, (str, int, float, bool)):
                            print(f"    - {field}: {value}")
                        elif isinstance(value, dict):
                            print(
                                f"    - {field}: [object with {len(value)} properties]"
                            )
                        elif isinstance(value, list):
                            print(f"    - {field}: [array with {len(value)} items]")
                        else:
                            print(f"    - {field}: {type(value).__name__}")

                print()
        else:
            print(f"Failed to fetch customers: Status {response.status_code}")
            print(f"Error: {response.text[:200]}")

    except Exception as e:
        print(f"Error fetching customers: {e}")

    # 2. Fetch Metadata to see what record types are available
    print("\n📊 AVAILABLE RECORD TYPES")
    print("-" * 40)

    metadata_url = f"https://{url_account_id}.suitetalk.api.netsuite.com/services/rest/record/v1/metadata-catalog"

    try:
        response = requests.get(metadata_url, auth=auth, headers=headers, timeout=30)

        if response.status_code == 200:
            data = response.json()
            items = data.get("items", [])

            print(f"Total Record Types Available: {len(items)}")
            print("\nSample Record Types:")

            # Show first 20 record types
            for item in items[:20]:
                print(f"  - {item.get('name', 'N/A')}")

            if len(items) > 20:
                print(f"  ... and {len(items) - 20} more")
        else:
            print(f"Failed to fetch metadata: Status {response.status_code}")

    except Exception as e:
        print(f"Error fetching metadata: {e}")

    # 3. Try to fetch some other common record types
    print("\n📦 TESTING OTHER RECORD TYPES")
    print("-" * 40)

    record_types = [
        "item",
        "inventoryitem",
        "employee",
        "vendor",
        "salesorder",
        "invoice",
        "location",
    ]

    for record_type in record_types:
        url = f"https://{url_account_id}.suitetalk.api.netsuite.com/services/rest/record/v1/{record_type}?limit=1"

        try:
            response = requests.get(url, auth=auth, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                count = data.get("count", 0)
                print(f"  ✅ {record_type.upper()}: {count} records found")

                # Show first record details if available
                items = data.get("items", [])
                if items:
                    item = items[0]
                    print(f"     Sample ID: {item.get('id', 'N/A')}")
                    # Show a few key fields
                    for field in ["name", "displayName", "itemId", "entityId"]:
                        if field in item:
                            print(f"     {field}: {item[field]}")
                            break
            elif response.status_code == 403:
                print(f"  ⚠️  {record_type.upper()}: Access denied (no permission)")
            elif response.status_code == 404:
                print(f"  ❌ {record_type.upper()}: Record type not found")
            else:
                print(f"  ❌ {record_type.upper()}: Status {response.status_code}")

        except requests.exceptions.Timeout:
            print(f"  ⏱️  {record_type.upper()}: Request timed out")
        except Exception as e:
            print(f"  ❌ {record_type.upper()}: Error - {str(e)[:50]}")

    print("\n" + "=" * 60)
    print("Data retrieval complete!")
    print("=" * 60)


if __name__ == "__main__":
    fetch_netsuite_data()
