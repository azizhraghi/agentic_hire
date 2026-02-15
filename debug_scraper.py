import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from agents.student.tools.job_scraper import ImprovedJobScraper
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def test_scraper():
    scraper = ImprovedJobScraper()
    keywords = ["python", "developer"]
    
    print(f"🔍 Testing with keywords: {keywords}")
    
    # Test WWR
    print("\n--- Testing WeWorkRemotely ---")
    try:
        jobs_wwr = scraper.scrape_weworkremotely(keywords, max_jobs=3)
        print(f"✅ WWR found: {len(jobs_wwr)} jobs")
        if jobs_wwr:
            print(f"Sample: {jobs_wwr[0]['title']}")
    except Exception as e:
        print(f"❌ WWR Failed: {e}")

    # Test RemoteOK
    print("\n--- Testing RemoteOK ---")
    try:
        jobs_rok = scraper.scrape_remoteok(keywords, max_jobs=3)
        print(f"✅ RemoteOK found: {len(jobs_rok)} jobs")
        if jobs_rok:
            print(f"Sample: {jobs_rok[0]['title']}")
    except Exception as e:
        print(f"❌ RemoteOK Failed: {e}")

if __name__ == "__main__":
    test_scraper()
