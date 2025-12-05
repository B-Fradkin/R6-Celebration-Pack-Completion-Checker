"""
R6 Siege Celebration Pack Checker - API Version
Uses Ubisoft's GraphQL API to check ownership status
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import getpass
from typing import Dict, List, Tuple
import base64


class UbisoftAuth:
    """Handles Ubisoft authentication using their API"""

    AUTH_URL = "https://public-ubiservices.ubi.com/v3/profiles/sessions"
    DATA_URL = "https://public-ubiservices.ubi.com/v1/profiles/me/uplay/graphql"
    SPACE_ID = "0d2ae42d-4c27-4cb7-af6c-2099062302bb"  # R6 Siege space ID
    APP_ID = "80a4a0e8-8797-440f-8f4c-eaba87d0fdda"  # Ubisoft Connect App ID
    STATIC_SESSION_ID = "1e08944e-f5da-4ebf-afb3-664091601c4b"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Content-Type': 'application/json',
            'Ubi-AppId': self.APP_ID,
            'Ubi-SessionId': self.STATIC_SESSION_ID
        })
        self.ticket = None
        self.session_id = None

    def authenticate(self, email: str, password: str) -> bool:
        """Authenticate with Ubisoft and get session ticket"""
        print("Authenticating with Ubisoft...")

        # Create Basic Auth header
        credentials = f"{email}:{password}"
        credentials_b64 = base64.b64encode(credentials.encode()).decode()

        headers = {
            'Authorization': f'Basic {credentials_b64}',
            'Content-Type': 'application/json'
        }

        data = json.dumps({"rememberMe": False})

        try:
            response = self.session.post(self.AUTH_URL, data=data, headers=headers)

            if response.status_code == 401:
                print("Error: Invalid email or password")
                return False
            elif response.status_code != 200:
                print(f"Error: Unexpected status code {response.status_code}")
                print(response.text)
                return False

            auth_data = response.json()
            self.ticket = auth_data.get('ticket')
            self.session_id = auth_data.get('sessionId')

            if not self.ticket:
                print("Error: Failed to get authentication ticket")
                return False

            # Update session headers with ticket
            self.session.headers.update({
                'Authorization': f'Ubi_v1 t={self.ticket}',
                'Ubi-SessionId': self.session_id
            })

            print("✓ Successfully authenticated!")
            return True

        except Exception as e:
            print(f"Authentication error: {e}")
            return False

    def graphql_query(self, query: str, variables: dict) -> dict:
        """Execute a GraphQL query against Ubisoft's API"""
        payload = [{
            "operationName": variables.get("operationName", ""),
            "variables": variables,
            "query": query
        }]

        try:
            response = self.session.post(self.DATA_URL, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"GraphQL query error: {e}")
            return None


class R6MarketplaceAPI:
    """Interacts with R6 Marketplace API to check item ownership"""

    # GraphQL query for searching items with ownership info
    SEARCH_QUERY = """query GetMarketableItems($spaceId: String!, $limit: Int!, $offset: Int, $filterBy: MarketableItemFilter, $withOwnership: Boolean = true, $sortBy: MarketableItemSort) {
  game(spaceId: $spaceId) {
    id
    marketableItems(
      limit: $limit
      offset: $offset
      filterBy: $filterBy
      sortBy: $sortBy
      withMarketData: true
    ) {
      nodes {
        id
        item {
          id
          assetUrl
          itemId
          name
          tags
          type
          __typename
          viewer @include(if: $withOwnership) {
            meta {
              id
              isOwned
              quantity
              __typename
            }
            __typename
          }
        }
        __typename
      }
      totalCount
      __typename
    }
    __typename
  }
}"""

    def __init__(self, auth: UbisoftAuth):
        self.auth = auth

    def search_item(self, name: str, limit: int = 50, offset: int = 0) -> List[Dict]:
        """Search for items by name and return results with ownership status"""
        variables = {
            "operationName": "GetMarketableItems",
            "spaceId": UbisoftAuth.SPACE_ID,
            "limit": limit,
            "offset": offset,
            "withOwnership": True,
            "filterBy": {
                "types": [],
                "tags": [],
                "text": name
            },
            "sortBy": {
                "field": "ACTIVE_COUNT",
                "direction": "DESC",
                "orderType": "Sell",
                "paymentItemId": "9ef71262-515b-46e8-b9a8-b6b6ad456c67"
            }
        }

        result = self.auth.graphql_query(self.SEARCH_QUERY, variables)

        if not result or len(result) == 0:
            return []

        try:
            nodes = result[0]['data']['game']['marketableItems']['nodes']
            items = []

            for node in nodes:
                item_data = node['item']
                is_owned = False

                # Check if ownership data exists
                if 'viewer' in item_data and item_data['viewer']:
                    meta = item_data['viewer'].get('meta', {})
                    is_owned = meta.get('isOwned', False)

                items.append({
                    'id': item_data['itemId'],
                    'name': item_data['name'],
                    'type': item_data['type'],
                    'tags': item_data.get('tags', []),
                    'is_owned': is_owned
                })

            return items

        except (KeyError, IndexError, TypeError) as e:
            print(f"Error parsing search results: {e}")
            return []


class R6SkinScraper:
    """Scrapes celebration pack items from r6.skin"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def scrape_celebration_pack(self) -> Dict[str, List[str]]:
        """Scrape celebration pack items from r6.skin"""
        print("Fetching celebration pack data from r6.skin...")

        try:
            response = self.session.get("https://r6.skin/packs/celebration/")
            soup = BeautifulSoup(response.content, 'html.parser')

            # Find all item name spans
            all_item_spans = soup.find_all('span', class_='name')
            print(f"Found {len(all_item_spans)} total item name elements")

            # Define categories
            items_by_category = {
                'HEADGEAR': [],
                'UNIFORMS': [],
                'UNIVERSAL WEAPON SKINS': [],
                'SEASONAL WEAPON SKINS': [],
                'WEAPON SKINS': [],
                'ATTACHMENT SKINS': [],
                'UNIQUE ABILITY SKINS': [],
                'DRONE SKINS': [],
                'OPERATOR PORTRAITS': []
            }

            category_keywords = {
                'HEADGEAR': 'HEADGEAR',
                'UNIFORMS': 'UNIFORMS',
                'UNIVERSAL WEAPON SKINS': 'UNIVERSAL WEAPON SKINS',
                'SEASONAL WEAPON SKINS': 'SEASONAL WEAPON SKINS',
                'WEAPON SKINS': 'WEAPON SKINS',
                'ATTACHMENT SKINS': 'ATTACHMENT SKINS',
                'UNIQUE ABILITY SKINS': 'UNIQUE ABILITY SKINS',
                'DRONE SKINS': 'DRONE SKINS',
                'OPERATOR PORTRAITS': 'OPERATOR PORTRAITS'
            }

            # Parse items by category
            all_elements = soup.find_all()
            current_category = None

            for element in all_elements:
                element_text = element.get_text(strip=True).upper()

                # Check if this is a category header
                for keyword in category_keywords.keys():
                    if keyword in element_text and '(' in element_text and ')' in element_text:
                        current_category = category_keywords[keyword]
                        break

                # If we're in a category and this is an item name
                if current_category and element.name == 'span' and 'name' in element.get('class', []):
                    item_name = element.get_text(strip=True)
                    if item_name and item_name not in items_by_category[current_category]:
                        items_by_category[current_category].append(item_name)

            total_items = sum(len(items) for items in items_by_category.values())
            print(f"Found {len(items_by_category)} categories with {total_items} total items\n")

            return items_by_category

        except Exception as e:
            print(f"Error scraping r6.skin: {e}")
            return {}


class CelebrationPackChecker:
    """Compares celebration pack items with owned items"""

    def __init__(self, marketplace_api: R6MarketplaceAPI):
        self.marketplace_api = marketplace_api
        self.celebration_items = {}
        self.owned_items = {}
        self.missing_items = {}

    def normalize_name(self, name: str) -> str:
        """Normalize item name for comparison"""
        import re
        # Remove special characters but keep spaces and dashes
        normalized = re.sub(r'[^\w\s-]', '', name)
        return normalized.upper().strip()

    def get_search_terms(self, item_name: str) -> List[str]:
        """Generate multiple search terms for an item to handle special cases"""
        import re
        terms = [item_name]  # Original name

        # Remove special characters version
        no_special = re.sub(r'[^\w\s-]', '', item_name)
        if no_special != item_name:
            terms.append(no_special)

        # For items with ANY non-alphanumeric characters (except spaces and dashes),
        # try searching with just the last word
        if re.search(r'[^\w\s-]', item_name):
            # Remove all special characters and split into words
            cleaned = re.sub(r'[^\w\s-]', '', item_name)
            words = cleaned.split()

            if len(words) > 0:
                # Try last word only
                terms.append(words[-1])
                # Try last 2 words if available
                if len(words) >= 2:
                    terms.append(' '.join(words[-2:]))

        return terms

    def check_ownership(self, item_name: str) -> bool:
        """Check if an item is owned via API search"""
        # Try multiple search terms
        search_terms = self.get_search_terms(item_name)

        for search_term in search_terms:
            results = self.marketplace_api.search_item(search_term, limit=30)

            if not results:
                continue

            # Look for matches
            normalized_search = self.normalize_name(item_name)

            for item in results:
                normalized_result = self.normalize_name(item['name'])

                # Exact match - highest priority
                if normalized_result == normalized_search:
                    return item['is_owned']

            # If no exact match found, check for partial matches
            # This handles weapon variants (e.g., "BLACK ICE" matches "BLACK ICE - R4-C")
            for item in results:
                normalized_result = self.normalize_name(item['name'])

                # Only consider partial match if:
                # 1. The search term is contained in the result (not vice versa to avoid false positives)
                # 2. The item is owned
                if normalized_search in normalized_result and item['is_owned']:
                    # Make sure it's not just a substring match
                    # e.g., "RED" shouldn't match "INFRARED"
                    words_search = set(normalized_search.split())
                    words_result = set(normalized_result.split())

                    # Check if all words from search are in result
                    if words_search.issubset(words_result):
                        return True

        return False

    def find_missing_items(self, celebration_items: Dict[str, List[str]]):
        """Find which celebration pack items are missing from inventory"""
        self.celebration_items = celebration_items

        total_items = sum(len(items) for items in celebration_items.values())
        checked = 0

        print("\n" + "="*60)
        print("CHECKING OWNERSHIP")
        print("="*60)
        print(f"\nThis will check {total_items} items...")
        print("This may take a while. Press Ctrl+C to stop.\n")

        for category, items in celebration_items.items():
            self.owned_items[category] = []
            self.missing_items[category] = []

            for item in items:
                checked += 1
                print(f"[{checked}/{total_items}] Checking: {item[:60]}...", end=' ')

                try:
                    is_owned = self.check_ownership(item)

                    if is_owned:
                        self.owned_items[category].append(item)
                        print("✓ OWNED")
                    else:
                        self.missing_items[category].append(item)
                        print("✗ Missing")

                    # Small delay to avoid rate limiting
                    time.sleep(0.3)

                except KeyboardInterrupt:
                    print("\n\nStopped by user.")
                    return
                except Exception as e:
                    print(f"Error: {e}")
                    self.missing_items[category].append(item)

    def generate_report(self) -> dict:
        """Generate a summary report"""
        total_celebration = sum(len(items) for items in self.celebration_items.values())
        total_owned = sum(len(items) for items in self.owned_items.values())
        total_missing = sum(len(items) for items in self.missing_items.values())

        return {
            "summary": {
                "total_celebration_items": total_celebration,
                "total_owned": total_owned,
                "total_missing": total_missing,
                "completion_percentage": round((total_owned / total_celebration) * 100, 2) if total_celebration > 0 else 0
            },
            "owned_by_category": self.owned_items,
            "missing_by_category": self.missing_items,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

    def group_items_by_base_name(self, items: List[str]) -> Dict[str, List[str]]:
        """Group items that share the same base name (e.g., 'REDHAMMER STANDARD - HEADGEAR')"""
        from collections import defaultdict
        grouped = defaultdict(list)

        for item in items:
            # Extract base name (everything before the last ' - ' if it exists)
            if ' - ' in item:
                parts = item.rsplit(' - ', 1)
                base_name = parts[0]
            else:
                base_name = item

            grouped[base_name].append(item)

        return dict(grouped)

    def print_summary(self):
        """Print a summary of missing items with grouping"""
        report = self.generate_report()

        print("\n" + "="*60)
        print("RESULTS SUMMARY")
        print("="*60)
        print(f"\nTotal celebration pack items: {report['summary']['total_celebration_items']}")
        print(f"Owned: {report['summary']['total_owned']}")
        print(f"Missing: {report['summary']['total_missing']}")
        print(f"Completion: {report['summary']['completion_percentage']}%")

        print("\n" + "="*60)
        print("MISSING ITEMS")
        print("="*60)

        # Collect all missing items across all categories
        all_missing = []
        for category, items in self.missing_items.items():
            all_missing.extend(items)

        if all_missing:
            # Group items by base name
            grouped = self.group_items_by_base_name(all_missing)

            # Show grouped items in simple unordered list
            print()
            displayed = 0
            for base_name, variants in sorted(grouped.items()):
                if displayed >= 50:  # Show first 50 items/groups
                    remaining = len(all_missing) - displayed
                    print(f"... and {remaining} more items")
                    break

                if len(variants) > 1:
                    # Multiple variants with same base name
                    print(f"- {base_name} ({len(variants)} variants)")
                    displayed += len(variants)
                else:
                    # Single item
                    print(f"- {variants[0]}")
                    displayed += 1
        else:
            print("\n🎉 You own all celebration pack items!")


def main():
    print("="*60)
    print("R6 SIEGE CELEBRATION PACK CHECKER (API VERSION)")
    print("="*60)
    print("\nThis version uses Ubisoft's GraphQL API\n")

    # Get credentials
    email = input("Ubisoft Email: ").strip()
    password = getpass.getpass("Password: ")

    # Authenticate
    auth = UbisoftAuth()
    if not auth.authenticate(email, password):
        print("\nAuthentication failed. Exiting.")
        return

    # Initialize API client
    marketplace_api = R6MarketplaceAPI(auth)

    # Scrape celebration pack
    scraper = R6SkinScraper()
    celebration_items = scraper.scrape_celebration_pack()

    if not celebration_items:
        print("Failed to scrape celebration pack items. Exiting.")
        return

    # Check ownership
    checker = CelebrationPackChecker(marketplace_api)
    checker.find_missing_items(celebration_items)

    # Print summary
    checker.print_summary()

    # Save results
    report = checker.generate_report()
    with open('celebration_pack_results_api.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print("\n" + "="*60)
    print("Results saved to celebration_pack_results_api.json")
    print("="*60)


if __name__ == "__main__":
    main()
