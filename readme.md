# LinkedIn Profile Scraper

A Python-based automation tool that scrapes LinkedIn profiles for professional data including name, bio, experience, education, and certifications.

## Overview

This tool allows you to extract structured data from multiple LinkedIn profiles by providing a CSV file with profile URLs. It uses Selenium WebDriver to navigate through LinkedIn pages and extract relevant information, saving the results in both CSV and JSON formats.

## Features

- Extracts key profile information:
  - Full name
  - Professional bio/headline
  - Work experience history (company and role)
  - Education background (institution and degree)
  - Certifications and licenses
- Handles LinkedIn's dynamic content loading
- Supports bulk processing of multiple profiles
- Saves data in both CSV and JSON formats for easy analysis and integration
- Uses environment variables for secure credential management

## Requirements

- Python 3.6+
- Required packages:
  - selenium>=4.10.0
  - pandas>=1.5.3
  - python-dotenv>=0.21.0
- Microsoft Edge WebDriver or Google Chrome WebDriver (Selenium compatible)

## Installation

1. Clone this repository or download the script files.

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up your LinkedIn credentials in the `.env` file:
   ```
   LINKEDIN_USER="your-email@example.com"
   LINKEDIN_PASS="your-password"
   ```

## Usage

Prepare a CSV file containing LinkedIn profile URLs. The file should have a column with header "url" (or a custom header that you can specify).

Run the script with the following command:

```bash
python script.py --input profiles.csv --output results --url-header url
```

### Command Line Arguments

- `--input`: (Required) Path to the CSV file containing LinkedIn profile URLs
- `--output`: (Optional) Prefix for output files (default: "results")
- `--url-header`: (Optional) Header name for the URL column in the CSV file (default: "url")

## How It Works

1. The script logs into LinkedIn using your credentials
2. It loads each profile URL from the input CSV
3. For each profile:
   - Extracts the person's name and bio
   - Navigates to and extracts work experience information
   - Navigates to and extracts education information
   - Navigates to and extracts certification information
4. The script handles "Show all" buttons to expand sections with more information
5. All data is saved in both CSV and JSON formats for further analysis

## Output

The script generates two output files:
- `{output_prefix}.csv`: CSV file with all the extracted information
- `{output_prefix}.json`: JSON file with the same information in a structured format

Each entry in the output contains:
- URL: The LinkedIn profile URL
- Name: The person's full name
- Bio: The person's professional headline or bio
- Experience: Dictionary of companies and roles
- Education: Dictionary of educational institutions and degrees
- Certification: Dictionary of certifications and issuers

## Important Notes

- This tool is for educational and research purposes only
- Use responsibly and in compliance with LinkedIn's Terms of Service
- Consider rate limiting your requests to avoid IP blocking
- The script includes waiting times to handle page loading - these may need adjustment based on your internet connection
- LinkedIn's website structure may change, requiring script updates

## Troubleshooting

- If profiles aren't loading, check your internet connection
- If login fails, verify your credentials in the `.env` file
- If elements aren't being found, LinkedIn may have updated their page structure
- Try increasing the sleep times if the script is running too fast for page loading

