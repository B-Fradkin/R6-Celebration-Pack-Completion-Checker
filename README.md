# R6 Siege Celebration Pack Checker

A Python script that scrapes celebration pack items from r6.skin and compares them with your Ubisoft marketplace inventory to identify which items you're missing. Uses Ubisoft's official GraphQL API for accurate ownership checking.

## Features

- Scrapes all celebration pack items from r6.skin
- Automatically authenticates with Ubisoft services via GraphQL API
- Checks ownership status for each item
- Generates a list of missing items

## Requirements

- Python 3.8 or higher
- Ubisoft account with Rainbow Six Siege access

## Installation

1. **Clone the repository:**

```bash
git clone https://github.com/B-Fradkin/R6-Celebration-Pack-Completion-Checker.git
cd R6-Celebration-Pack-Completion-Checker
```

2. **Install Python dependencies:**

```bash
pip install -r requirements.txt
```

This will install:
- `requests` - For HTTP requests and API calls
- `beautifulsoup4` - For HTML parsing from r6.skin

## How It Works

### Overview

The script performs three main operations:

1. **Scraping Celebration Pack Items**
   - Fetches the HTML from [r6.skin/packs/celebration](https://r6.skin/packs/celebration/)
   - Parses all item names organized by category (Headgear, Uniforms, Weapon Skins, etc.)
   - Extracts ~1400+ unique items from the celebration pack

2. **Authentication with Ubisoft**
   - Uses Ubisoft's official GraphQL API endpoint
   - Authenticates using Basic Auth with your credentials (base64 encoded)
   - Receives a session ticket and profile ID for subsequent API calls
   - API endpoint: `https://public-ubiservices.ubi.com/v3/profiles/sessions`

3. **Checking Ownership Status**
   - For each item, queries Ubisoft's marketplace GraphQL API
   - Uses `withOwnership: true` parameter to get ownership data
   - API returns `isOwned: true/false` for each item
   - Handles special characters in item names by generating multiple search variations
   - Uses fuzzy matching to handle items like "S.I. 2019", "R&D Director", etc.

### Technical Details

**Authentication Flow:**
```
1. User provides email/password
2. Script creates Basic Auth header: base64(email:password)
3. POST to Ubisoft auth API with headers:
   - Authorization: Basic [credentials]
   - Ubi-AppId: 80a4a0e8-8797-440f-8f4c-eaba87d0fdda
4. Receive ticket + sessionId for authenticated requests
```

**Ownership Check Flow:**
```
1. For each celebration pack item:
   a. Generate search terms (handle special characters)
   b. Query GraphQL API with item name
   c. API returns marketplace results with isOwned field
   d. Check exact match first, then partial match
   e. Mark as owned/missing based on API response
2. Group items by base name and count variants
3. Generate summary report
```

**Smart Name Matching:**
- Handles special characters (periods, ampersands, etc.)
- Searches with multiple variations:
  - Original name: "S.I. 2019"
  - No special chars: "SI 2019"
  - Last word: "2019"
  - Last 2 words: "SI 2019"
- Uses word-based validation to avoid false positives
- Groups variants (e.g., "BLACK ICE" for different weapons)

## Usage

Run the script:

```bash
python script_api.py
or
py script_api.py
```

The script will:
1. Ask for your Ubisoft email and password
2. Authenticate with Ubisoft's GraphQL API
3. Scrape celebration pack items from r6.skin
4. Check ownership status for each item via API
5. Generate a report of missing items

**Output:** Results saved to `celebration_pack_results_api.json`

### Important Notes

#### Authentication
- Keep your 2FA device/email ready for verification if required
- Your credentials are only used for Ubisoft API authentication

#### Performance
- Processing time: ~0.3s per item
- Full completion pack (~1400+ items) takes 10-30 minutes
- You can press Ctrl+C to stop at any time

## Output

The script generates:

1. **Console Output**: Real-time progress and missing items summary
2. **JSON Report**: `celebration_pack_results_api.json`

### Sample Output

```
============================================================
R6 SIEGE CELEBRATION PACK CHECKER (API VERSION)
============================================================

This version uses Ubisoft's GraphQL API

Ubisoft Email: user@example.com
Password: ********
Authenticating with Ubisoft...
✓ Successfully authenticated!

Fetching celebration pack data from r6.skin...
Found 1429 total item name elements
Found 9 categories with 1429 total items

============================================================
CHECKING OWNERSHIP
============================================================

This will check 1429 items...
This may take a while. Press Ctrl+C to stop.

[1/1429] Checking: BLACK ICE - AUG A2... ✓ OWNED
[2/1429] Checking: BLACK ICE - R4-C... ✗ Missing
[3/1429] Checking: PLASMA PINK - UNIVERSAL... ✓ OWNED
...

============================================================
RESULTS SUMMARY
============================================================

Total celebration pack items: 1429
Owned: 582
Missing: 847
Completion: 40.73%

============================================================
MISSING ITEMS
============================================================

- AERATED BODY ARMOR
- ALL EARS
- BLACK ICE (12 variants)
- ORANGE PEEL
- REDHAMMER STANDARD (2 variants)
- SAFARI MESH
... and 841 more items

============================================================
Results saved to celebration_pack_results_api.json
============================================================
```

## Troubleshooting

### Import Errors
If you see import errors for `bs4`, `requests`, etc., make sure you installed the requirements:
```bash
pip install -r requirements.txt
```

### Authentication Failed
- Verify your email and password are correct
- If using 2FA, you may need to generate an app-specific password
- Check that your account has access to Rainbow Six Siege

### API Errors
- The API may be temporarily unavailable
- Try again later

### Rate Limiting
- The script includes delays to avoid rate limiting (0.3s per item)
- If you encounter errors, you can increase the sleep time in [script_api.py](script_api.py:389)

## Privacy & Security

- Your credentials are only used to authenticate with Ubisoft's official API
- No credentials are stored or transmitted to third parties
- The script runs entirely on your local machine
- All API requests go directly to Ubisoft's servers

## Limitations

- Processing all celebration pack items (~1400+) takes 10-30 minutes
- May require handling 2FA challenges during authentication
- Some items may have false positives/negatives if names don't match exactly in the API

## Credits

- Celebration pack data from [r6.skin](https://r6.skin) by [@kran27_](https://x.com/kran27_/)
- API implementation based on [liljaba1337/r6-marketplace](https://github.com/liljaba1337/r6-marketplace)
- Ubisoft R6 Marketplace: [rainbow6.com/marketplace](https://rainbow6.com/marketplace)

## Disclaimer

This tool is for personal use only. It automates publicly available web interfaces and does not violate Ubisoft's terms of service. However, use at your own risk. The author is not responsible for any account issues that may arise from using this tool.

## License

MIT License - Feel free to modify and use as needed.
