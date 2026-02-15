import requests
from bs4 import BeautifulSoup

def test_wwr():
    url = "https://weworkremotely.com/categories/remote-programming-jobs"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    }
    
    print(f"Fetching {url}...")
    try:
        response = requests.get(url, headers=headers, timeout=15)
        print(f"Status Code: {response.status_code}")
        print(f"Content Length: {len(response.content)}")
        
        with open("wwr_debug.html", "wb") as f:
            f.write(response.content)
        print("Saved content to wwr_debug.html")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        jobs = soup.select('section.jobs li.feature')
        print(f"Found {len(jobs)} jobs (li.feature)")
        
        if jobs:
            print("First job title:", jobs[0].find('span', class_='title').text.strip())
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_wwr()
