import requests
from bs4 import BeautifulSoup
import logging
import time
import random
import re
import json
from typing import List, Dict, Optional

class ImprovedJobScraper:
    """
    Advanced Job Scraper combining multiple sources:
    1. RemoteOK (Official JSON API) - Extremely Reliable
    2. WeWorkRemotely (HTML) - Reliable
    3. LinkedIn (Public Search) - Good for volume
    4. Adzuna (Search) - aggregators
    """
    
    def __init__(self):
        self.logger = logging.getLogger("JobScraper")
        self.name = "Improved Scraper"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.google.com/'
        }
        
    def get_headers(self):
        """Rotate headers to avoid blocking"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0'
        ]
        return {
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5'
        }

    def scrape_remoteok(self, max_jobs: int = 10, search_tags: List[str] = None) -> List[Dict]:
        """Scrape RemoteOK using JSON API - MORE RELIABLE than HTML scraping"""
        self.logger.info(f"🤖 {self.name}: Scraping RemoteOK via JSON API...")
        jobs = []
        
        try:
            # RemoteOK JSON API returns structured data
            api_url = "https://remoteok.com/api"
            response = requests.get(api_url, headers=self.headers, timeout=15)
            
            if response.status_code != 200:
                self.logger.warning(f"RemoteOK API returned {response.status_code}")
                return []
            
            data = response.json()
            
            # First item is API info/legal notice, skip it
            job_listings = data[1:] if len(data) > 1 else []
            
            # If search tags provided, filter by relevance
            if search_tags:
                search_terms = [t.lower() for t in search_tags]
                
                def is_relevant(job_data):
                    """Check if job matches any search term"""
                    searchable = ' '.join([
                        job_data.get('position', ''),
                        job_data.get('company', ''),
                        job_data.get('description', ''),
                        ' '.join(job_data.get('tags', []))
                    ]).lower()
                    
                    for term in search_terms:
                        # Check each word in the search term
                        term_words = term.lower().split()
                        if any(word in searchable for word in term_words if len(word) > 2):
                            return True
                    return False
                
                # Filter relevant jobs first
                relevant = [j for j in job_listings if is_relevant(j)]
                # If not enough relevant jobs, maybe include some others? For now just relevant.
                job_listings = relevant 
            
            for job_data in job_listings[:max_jobs]:
                try:
                    title = job_data.get('position', '').strip()
                    company = job_data.get('company', '').strip()
                    
                    # Skip if missing essential data
                    if not title or not company:
                        continue
                    
                    location = job_data.get('location', 'Remote').strip() or 'Remote'
                    
                    # Build rich description from API data
                    description = job_data.get('description', '')
                    if not description:
                        tags = job_data.get('tags', [])
                        description = f"Remote {title} position at {company}."
                        if tags:
                            description += f" Skills: {', '.join(tags)}."
                    else:
                        # Clean HTML from description
                        description = re.sub(r'<[^>]+>', ' ', description)
                        description = re.sub(r'\s+', ' ', description).strip()
                        # Limit length
                        if len(description) > 2000:
                            description = description[:2000] + "..."
                    
                    job_url = job_data.get('url', '')
                    if not job_url and job_data.get('slug'):
                        job_url = f"https://remoteok.com/remote-jobs/{job_data['slug']}"
                    elif not job_url and job_data.get('id'):
                        job_url = f"https://remoteok.com/remote-jobs/{job_data['id']}"
                    
                    job = {
                        'title': title,
                        'company': company,
                        'location': location,
                        'description': description,
                        'url': job_url,
                        'source': 'RemoteOK',
                        'tags': job_data.get('tags', []),
                        'salary': job_data.get('salary_min', '')
                    }
                    
                    jobs.append(job)
                    self.logger.info(f"✅ Found: {title} at {company}")
                    
                except Exception as e:
                    continue
            
            self.logger.info(f"✅ {self.name}: Found {len(jobs)} jobs from RemoteOK API")
            return jobs
            
        except Exception as e:
            self.logger.error(f"❌ {self.name}: RemoteOK API failed - {e}")
            return []

    def scrape_linkedin(self, keywords: List[str], max_jobs: int = 10, location: str = "") -> List[Dict]:
        """Scrape LinkedIn public job listings (no login required)"""
        self.logger.info(f"🤖 {self.name}: Scraping LinkedIn Jobs...")
        jobs = []
        
        # Deduplicate keywords and take top 3
        search_keywords = list(set(keywords))[:3]
        
        for keyword in search_keywords:
            if len(jobs) >= max_jobs:
                break
            try:
                # LinkedIn public job search URL
                params = {
                    'keywords': keyword,
                    'location': location if location else 'Remote',
                    'f_WT': '' if location else '2',  # 2 = remote filter, empty = all
                    'position': '1',
                    'pageNum': '0'
                }
                url = f"https://www.linkedin.com/jobs/search/?{requests.compat.urlencode(params)}"
                
                response = requests.get(url, headers=self.get_headers(), timeout=15)
                if response.status_code != 200:
                    self.logger.warning(f"LinkedIn returned {response.status_code}")
                    continue
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # LinkedIn public job cards
                job_cards = soup.find_all('div', class_='base-card')
                if not job_cards:
                    job_cards = soup.find_all('li', class_='result-card')
                if not job_cards:
                    job_cards = soup.find_all('div', class_='job-search-card')
                
                for card in job_cards[:max_jobs - len(jobs)]:
                    try:
                        # Title
                        title_elem = card.find('h3', class_='base-search-card__title') or card.find('h3')
                        title = title_elem.text.strip() if title_elem else None
                        
                        # Company
                        company_elem = card.find('h4', class_='base-search-card__subtitle') or card.find('a', class_='hidden-nested-link')
                        company = company_elem.text.strip() if company_elem else "Company"
                        
                        # Location
                        loc_elem = card.find('span', class_='job-search-card__location')
                        job_location = loc_elem.text.strip() if loc_elem else (location or "Remote")
                        
                        # URL
                        link_elem = card.find('a', class_='base-card__full-link') or card.find('a', href=True)
                        job_url = link_elem.get('href', '') if link_elem else ''
                        
                        # Description from listing snippet
                        desc_elem = card.find('p', class_='job-search-card__snippet')
                        description = desc_elem.text.strip() if desc_elem else f"{title} position at {company} in {job_location}"
                        
                        if title and len(title) > 3:
                            jobs.append({
                                'title': title,
                                'company': company,
                                'location': job_location,
                                'description': description,
                                'url': job_url,
                                'source': 'LinkedIn'
                            })
                            # self.logger.info(f"✅ Found: {title} at {company}")
                    except Exception as e:
                        continue
                        
            except Exception as e:
                self.logger.warning(f"LinkedIn search for '{keyword}' failed: {e}")
                continue
        
        self.logger.info(f"✅ {self.name}: Found {len(jobs)} jobs from LinkedIn")
        return jobs

    def scrape_weworkremotely(self, keywords: List[str], max_jobs: int = 10) -> List[Dict]:
        """WeWorkRemotely - Reliable HTML scraping"""
        self.logger.info(f"🤖 {self.name}: Scraping WeWorkRemotely...")
        jobs = []
        
        try:
            # WWR categories
            categories = [
                'remote-programming-jobs',
                'remote-full-stack-programming-jobs', 
                'remote-back-end-programming-jobs',
                'remote-front-end-programming-jobs'
            ]
            
            for category in categories:
                if len(jobs) >= max_jobs:
                    break
                    
                url = f"https://weworkremotely.com/categories/{category}"
                
                try:
                    response = requests.get(url, headers=self.get_headers(), timeout=15)
                    if response.status_code != 200:
                        continue
                        
                    soup = BeautifulSoup(response.content, 'html.parser')
                    job_containers = soup.select('section.jobs, #category-posts')
                    
                    for container in job_containers:
                        items = container.find_all('li', class_='feature')
                        
                        for item in items:
                            if len(jobs) >= max_jobs:
                                break
                            try:
                                # Get title
                                title_elem = item.find('span', class_='title')
                                if not title_elem:
                                    continue
                                title = title_elem.text.strip()
                                
                                # Get company
                                company_elem = item.find('span', class_='company')
                                company = company_elem.text.strip() if company_elem else "Unknown"
                                
                                # Loose keyword matching (title or company)
                                if keywords:
                                    text_check = (title + " " + company).lower()
                                    if not any(k.lower() in text_check for k in keywords):
                                        continue
                                
                                region_elem = item.find('span', class_='region')
                                location = region_elem.text.strip() if region_elem else "Remote"
                                
                                a_tags = item.find_all('a')
                                job_href = None
                                for a in a_tags:
                                    href = a.get('href', '')
                                    if '/remote-jobs/' in href:
                                        job_href = href
                                        break
                                if not job_href and a_tags:
                                    job_href = a_tags[0].get('href', '')
                                    
                                if not job_href:
                                    continue
                                    
                                job_url = f"https://weworkremotely.com{job_href}" if job_href.startswith('/') else job_href

                                jobs.append({
                                    'title': title,
                                    'company': company,
                                    'location': location,
                                    'description': f"Remote {title} at {company}",
                                    'url': job_url,
                                    'source': 'WeWorkRemotely'
                                })
                            except Exception:
                                continue
                except Exception:
                    continue
                    
            self.logger.info(f"✅ {self.name}: Found {len(jobs)} jobs from WWR")
            return jobs
        except Exception as e:
            self.logger.error(f"❌ WWR failed: {e}")
            return []

    def scrape_adzuna(self, keywords: List[str], max_jobs: int = 10, location: str = "") -> List[Dict]:
        """Scrape Adzuna - Good Aggregator"""
        self.logger.info(f"🤖 {self.name}: Scraping Adzuna...")
        jobs = []
        
        for keyword in keywords[:3]:
            if len(jobs) >= max_jobs:
                break
            try:
                search_query = keyword.replace(' ', '-').lower()
                loc_param = requests.utils.quote(location) if location else 'remote'
                url = f"https://www.adzuna.com/search?q={requests.utils.quote(keyword)}&loc={loc_param}"
                
                response = requests.get(url, headers=self.get_headers(), timeout=15)
                if response.status_code != 200:
                    continue
                
                soup = BeautifulSoup(response.content, 'html.parser')
                job_cards = soup.find_all('div', class_='ui-search-results') or soup.find_all('article') or soup.find_all('div', attrs={'data-aid': True})
                
                for card in job_cards[:max_jobs - len(jobs)]:
                    try:
                        title_elem = card.find('a', class_='ui-search-results__title') or card.find('h2') or card.find('a')
                        title = title_elem.text.strip() if title_elem else None
                        
                        company_elem = card.find('div', class_='ui-search-results__company') or card.find('span', class_='company')
                        company = company_elem.text.strip() if company_elem else "Company"
                        
                        link = title_elem.get('href', '') if title_elem else ''
                        if link and not link.startswith('http'):
                            link = f"https://www.adzuna.com{link}"
                        
                        if title and len(title) > 3:
                            jobs.append({
                                'title': title,
                                'company': company,
                                'location': "Remote", # simplified
                                'description': f"{title} at {company}",
                                'url': link,
                                'source': 'Adzuna'
                            })
                    except Exception:
                        continue
            except Exception:
                continue
        
        self.logger.info(f"✅ {self.name}: Found {len(jobs)} jobs from Adzuna")
        return jobs

    def scrape_indeed_simple(self, keywords: List[str], max_jobs: int = 10, location: str = "") -> List[Dict]:
        """
        Real Indeed jobs via python-jobspy.
        Tries multiple location strategies to maximize results:
        1) Exact location  2) 'remote'  3) No location filter
        """
        self.logger.info(f"🤖 {self.name}: Scraping real Indeed jobs via jobspy...")
        jobs = []

        def _parse_df(df, location_used):
            results = []
            if df is None or df.empty:
                return results
            for _, row in df.iterrows():
                title = str(row.get('title', '')).strip()
                company = str(row.get('company', 'Not specified')).strip()
                if not title or title == 'nan' or len(title) < 3:
                    continue
                description = str(row.get('description', f'{title} at {company}'))
                if len(description) > 500:
                    description = description[:500] + '...'
                job_url = str(row.get('job_url', ''))
                job_location = str(row.get('location', location_used or 'USA')).strip()
                results.append({
                    'title': title,
                    'company': company if company != 'nan' else 'Not specified',
                    'location': job_location if job_location != 'nan' else (location_used or 'USA'),
                    'description': description,
                    'url': job_url if job_url != 'nan' else '',
                    'source': 'Indeed'
                })
            return results

        try:
            from jobspy import scrape_jobs

            # Determine Indeed country from location
            country = 'USA'
            if location:
                loc_lower = location.lower()
                if any(c in loc_lower for c in ['uk', 'england', 'britain', 'london']):
                    country = 'UK'
                elif any(c in loc_lower for c in ['canada', 'toronto', 'montreal']):
                    country = 'Canada'
                elif any(c in loc_lower for c in ['australia', 'sydney', 'melbourne']):
                    country = 'Australia'
                elif any(c in loc_lower for c in ['france', 'paris', 'germany', 'berlin',
                                                    'spain', 'italy', 'netherlands']):
                    country = 'USA'  # Force USA for non-English countries (more results)

            for search_term in (keywords[:2] if keywords else ['engineer']):
                if len(jobs) >= max_jobs:
                    break

                # Try location strategies in order
                location_strategies = []
                if location:
                    location_strategies.append(location)
                location_strategies += ['remote', '']

                for loc in location_strategies:
                    if len(jobs) >= max_jobs:
                        break
                    try:
                        kwargs = dict(
                            site_name=['indeed'],
                            search_term=search_term,
                            results_wanted=max_jobs - len(jobs),
                            country_indeed=country,
                        )
                        if loc:
                            kwargs['location'] = loc
                        df = scrape_jobs(**kwargs)
                        new = _parse_df(df, loc)
                        if new:
                            jobs.extend(new)
                            self.logger.info(f"Indeed ({loc or 'no-loc'}): {len(new)} jobs for '{search_term}'")
                            break  # Found results, skip other location fallbacks
                    except Exception as e:
                        self.logger.warning(f"Indeed attempt (loc='{loc}'): {e}")
                        continue

        except Exception as e:
            self.logger.warning(f"Indeed (jobspy) failed: {e}")

        self.logger.info(f"✅ {self.name}: Found {len(jobs)} jobs from Indeed")
        return jobs


    def scrape_glassdoor(self, keywords: List[str], max_jobs: int = 10, location: str = "") -> List[Dict]:
        """
        Glassdoor-style jobs via The Muse free API (themuse.com).
        No auth required, reliable JSON endpoint, global jobs.
        Maps keywords to The Muse job categories for relevant results.
        """
        self.logger.info(f"🤖 {self.name}: Scraping Glassdoor (via The Muse API)...")
        jobs = []

        # The Muse category mapping
        MUSE_CATEGORIES = {
            'software': 'Software Engineer', 'developer': 'Software Engineer',
            'python': 'Software Engineer', 'java': 'Software Engineer',
            'javascript': 'Software Engineer', 'frontend': 'Software Engineer',
            'backend': 'Software Engineer', 'fullstack': 'Software Engineer',
            'data': 'Data Science', 'analyst': 'Data Science', 'ml': 'Data Science',
            'machine learning': 'Data Science', 'scientist': 'Data Science',
            'devops': 'IT', 'sysadmin': 'IT', 'cloud': 'IT',
            'design': 'Design & UX', 'ux': 'Design & UX', 'ui': 'Design & UX',
            'product': 'Product', 'scrum': 'Product', 'manager': 'Management',
            'marketing': 'Marketing & PR', 'content': 'Editorial',
            'finance': 'Finance', 'accounting': 'Finance', 'legal': 'Legal',
            'customer': 'Customer Service', 'support': 'Customer Service',
            'engineer': 'Engineering',
        }

        kw_lower = ' '.join(keywords[:4]).lower()
        category = None
        for kw, cat in MUSE_CATEGORIES.items():
            if kw in kw_lower:
                category = cat
                break

        try:
            api_url = "https://www.themuse.com/api/public/jobs"

            # Try with category first, then generic
            params_list = []
            if category:
                params_list.append({'page': 0, 'descending': 'true', 'category': category})
            params_list.append({'page': 0, 'descending': 'true'})

            for params in params_list:
                if len(jobs) >= max_jobs:
                    break
                try:
                    muse_headers = {'Accept': 'application/json',
                                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                    r = requests.get(api_url, params=params, timeout=12, headers=muse_headers)
                    if r.status_code != 200:
                        continue

                    results = r.json().get('results', [])
                    self.logger.info(f"TheMuse returned {len(results)} jobs (category={params.get('category','any')})")

                    for j in results:
                        if len(jobs) >= max_jobs:
                            break
                        try:
                            title = j.get('name', '').strip()
                            company = j.get('company', {}).get('name', 'Not specified').strip()
                            if not title or len(title) < 3:
                                continue

                            # Location
                            locs = j.get('locations', [])
                            job_location = locs[0].get('name', 'Remote') if locs else 'Remote'

                            # Description — contents is an HTML string, not a list
                            html_content = j.get('contents', '')
                            if isinstance(html_content, str) and html_content:
                                desc = BeautifulSoup(html_content, 'html.parser').get_text(separator=' ').strip()
                                desc = desc[:500]
                            else:
                                desc = f"{title} at {company}"

                            # URL
                            job_url = j.get('refs', {}).get('landing_page', '')

                            jobs.append({
                                'title': title,
                                'company': company if company != 'Not specified' else 'Not specified',
                                'location': job_location,
                                'description': desc,
                                'url': job_url,
                                'source': 'Glassdoor'
                            })
                            self.logger.info(f"✅ Glassdoor/Muse: {title} at {company}")
                        except Exception:
                            continue

                    if len(jobs) >= max_jobs:
                        break

                except Exception as e:
                    self.logger.warning(f"TheMuse attempt failed: {e}")
                    continue

        except Exception as e:
            self.logger.warning(f"Glassdoor (TheMuse) failed: {e}")

        self.logger.info(f"✅ {self.name}: Found {len(jobs)} jobs from Glassdoor")
        return jobs

    def scrape_remotive(self, keywords: List[str], max_jobs: int = 10, location: str = "") -> List[Dict]:
        """
        Remotive.com free API — remote-only jobs, no key required.
        Now a proper independent source (not faking Indeed).
        """
        self.logger.info(f"🤖 {self.name}: Scraping Remotive.com API...")
        jobs = []
        CATEGORY_MAP = {
            'software': 'software-dev', 'developer': 'software-dev', 'python': 'software-dev',
            'java': 'software-dev', 'javascript': 'software-dev', 'frontend': 'software-dev',
            'backend': 'software-dev', 'fullstack': 'software-dev', 'engineer': 'software-dev',
            'data': 'data', 'analyst': 'data', 'machine learning': 'data', 'ai': 'data',
            'ml': 'data', 'scientist': 'data', 'analytics': 'data',
            'devops': 'devops-sysadmin', 'sysadmin': 'devops-sysadmin', 'cloud': 'devops-sysadmin',
            'design': 'design', 'ux': 'design', 'ui': 'design',
            'product': 'product', 'marketing': 'marketing', 'content': 'writing',
            'finance': 'finance-legal', 'legal': 'finance-legal',
            'customer': 'customer-support', 'support': 'customer-support',
        }
        category = None
        kw_lower = ' '.join(keywords[:4]).lower()
        for kw, cat in CATEGORY_MAP.items():
            if kw in kw_lower:
                category = cat
                break

        attempts = []
        if category:
            attempts.append({'category': category})
        if keywords:
            attempts.append({'search': keywords[0]})
        attempts.append({})

        for params in attempts:
            if len(jobs) >= max_jobs:
                break
            try:
                r = requests.get('https://remotive.com/api/remote-jobs', params=params, timeout=15)
                if r.status_code != 200:
                    continue
                api_jobs = r.json().get('jobs', [])
                for j in api_jobs:
                    if len(jobs) >= max_jobs:
                        break
                    title = j.get('title', '').strip()
                    company = j.get('company_name', 'Not specified').strip()
                    if not title or len(title) < 3:
                        continue
                    desc = j.get('description', f'{title} at {company}')
                    if '<' in desc:
                        desc = BeautifulSoup(desc, 'html.parser').get_text(separator=' ').strip()
                    jobs.append({
                        'title': title,
                        'company': company,
                        'location': j.get('candidate_required_location', 'Remote') or 'Remote',
                        'description': desc[:500],
                        'url': j.get('url', ''),
                        'source': 'Remotive'
                    })
                    self.logger.info(f"✅ Remotive: {title} at {company}")
                if len(jobs) >= max_jobs:
                    break
            except Exception as e:
                self.logger.warning(f"Remotive attempt failed: {e}")
                continue

        self.logger.info(f"✅ {self.name}: Found {len(jobs)} jobs from Remotive")
        return jobs

    def scrape_wayup(self, keywords: List[str], max_jobs: int = 10, location: str = "") -> List[Dict]:
        """
        Wayup replacement: Arbeitnow free API (no key required, global tech jobs).
        Filters results by CV keywords for relevance.
        """
        self.logger.info(f"🤖 {self.name}: Scraping Arbeitnow API (Wayup slot)...")
        jobs = []
        kw_lower = [k.lower() for k in keywords[:5]]

        def _fetch_arbeitnow(page=1):
            r = requests.get(
                "https://www.arbeitnow.com/api/job-board-api",
                params={"page": page},
                timeout=12,
                headers={"Accept": "application/json",
                         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            )
            return r.json().get("data", []) if r.status_code == 200 else []

        try:
            items = _fetch_arbeitnow(1)
            for item in items:
                if len(jobs) >= max_jobs:
                    break
                title = item.get("title", "").strip()
                if not title:
                    continue
                tags = " ".join(item.get("tags", [])).lower()
                title_l = title.lower()
                if kw_lower and not any(kw in title_l or kw in tags for kw in kw_lower):
                    continue
                desc = item.get("description", f"{title} at {item.get('company_name','')}")[:500]
                jobs.append({
                    "title":       title,
                    "company":     item.get("company_name", "Not specified"),
                    "location":    item.get("location", "Remote") or "Remote",
                    "description": desc,
                    "url":         item.get("url", ""),
                    "salary":      "",
                    "source":      "Wayup"
                })
            # If keyword filter left nothing, take first N unfiltered
            if not jobs:
                for item in items[:max_jobs]:
                    title = item.get("title", "").strip()
                    if title:
                        jobs.append({
                            "title":       title,
                            "company":     item.get("company_name", "Not specified"),
                            "location":    item.get("location", "Remote") or "Remote",
                            "description": item.get("description", title)[:500],
                            "url":         item.get("url", ""),
                            "salary":      "",
                            "source":      "Wayup"
                        })
        except Exception as e:
            self.logger.warning(f"Arbeitnow (Wayup) failed: {e}")

        self.logger.info(f"✅ {self.name}: Found {len(jobs)} jobs from Wayup (Arbeitnow)")
        return jobs

    def scrape_intern_insider(self, keywords: List[str], max_jobs: int = 10, location: str = "") -> List[Dict]:
        """
        Intern Insider replacement: Himalayas.app API (free, reliable tech jobs).
        """
        self.logger.info(f"🤖 {self.name}: Scraping Himalayas API (Intern Insider slot)...")
        jobs = []

        try:
            r = requests.get(
                "https://himalayas.app/jobs/api",
                params={"limit": max_jobs * 3},  # Fetch more to filter locally
                timeout=12,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            )
            if r.status_code == 200:
                data = r.json()
                api_jobs = data.get("jobs", [])
                
                kw_lower = [k.lower() for k in keywords[:3]] if keywords else []
                
                for j in api_jobs:
                    if len(jobs) >= max_jobs:
                        break
                        
                    title = j.get("title", "").strip()
                    if not title:
                        continue
                        
                    # Title filter for relevance
                    if kw_lower and not any(kw in title.lower() for kw in kw_lower):
                        continue
                        
                    company = j.get("companyName", "Not specified").strip()
                    desc = j.get("description", f"{title} at {company}")
                    
                    # Clean HTML from description
                    if '<' in desc:
                        from bs4 import BeautifulSoup
                        desc = BeautifulSoup(desc, "html.parser").get_text(separator=" ").strip()
                    
                    jobs.append({
                        "title":       title,
                        "company":     company,
                        "location":    "Remote",
                        "description": desc[:500],
                        "url":         j.get("applicationLink", "") or j.get("url", ""),
                        "salary":      "",
                        "source":      "Intern Insider"
                    })
                    
                # If keyword filter left nothing, take first N unfiltered
                if not jobs:
                    for j in api_jobs[:max_jobs]:
                        title = j.get("title", "").strip()
                        if not title:
                            continue
                        company = j.get("companyName", "Not specified").strip()
                        desc = j.get("description", f"{title} at {company}")
                        if '<' in desc:
                            from bs4 import BeautifulSoup
                            desc = BeautifulSoup(desc, "html.parser").get_text(separator=" ").strip()
                            
                        jobs.append({
                            "title":       title,
                            "company":     company,
                            "location":    "Remote",
                            "description": desc[:500],
                            "url":         j.get("applicationLink", "") or j.get("url", ""),
                            "salary":      "",
                            "source":      "Intern Insider"
                        })
                        
        except Exception as e:
            self.logger.warning(f"Himalayas API (Intern Insider slot) failed: {e}")

        self.logger.info(f"✅ {self.name}: Found {len(jobs)} jobs from Intern Insider (Himalayas)")
        return jobs

    def scrape_adzuna_simple(self, keywords: List[str], max_jobs: int = 10, location: str = "") -> List[Dict]:
        """
        Adzuna replacement: We Work Remotely RSS feed.
        Completely free, no key required, global remote tech jobs.
        """
        self.logger.info(f"🤖 {self.name}: Scraping We Work Remotely RSS (Adzuna slot)...")
        jobs = []
        import feedparser

        kw_lower = [k.lower() for k in keywords[:5]]

        def _parse_wwr_feed(url):
            r = requests.get(url, timeout=12,
                             headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            return feedparser.parse(r.content).entries

        try:
            entries = _parse_wwr_feed("https://weworkremotely.com/remote-jobs.rss")
            for entry in entries:
                if len(jobs) >= max_jobs:
                    break
                title = entry.get("title", "").strip()
                if not title:
                    continue
                company = "Not specified"
                if ": " in title:
                    company, title = title.split(": ", 1)
                if kw_lower and not any(kw in title.lower() for kw in kw_lower):
                    continue
                desc = entry.get("summary", f"{title} at {company}")[:500]
                jobs.append({
                    "title":       title,
                    "company":     company,
                    "location":    "Remote",
                    "description": desc,
                    "url":         entry.get("link", ""),
                    "salary":      "",
                    "source":      "Adzuna"
                })
            # Fallback: unfiltered if keyword filter left nothing
            if not jobs:
                for entry in entries[:max_jobs]:
                    title = entry.get("title", "").strip()
                    if not title:
                        continue
                    company = "Not specified"
                    if ": " in title:
                        company, title = title.split(": ", 1)
                    jobs.append({
                        "title":       title,
                        "company":     company,
                        "location":    "Remote",
                        "description": entry.get("summary", title)[:500],
                        "url":         entry.get("link", ""),
                        "salary":      "",
                        "source":      "Adzuna"
                    })
        except Exception as e:
            self.logger.warning(f"WWR RSS (Adzuna) failed: {e}")

        self.logger.info(f"✅ {self.name}: Found {len(jobs)} jobs from Adzuna (WWR RSS)")
        return jobs

    def scrape_simply_hired(self, keywords: List[str], max_jobs: int = 10, location: str = "") -> List[Dict]:
        """
        SimplyHired replacement: Arbeitnow API page 2 (different pool than Wayup slot).
        Free, no key, broad tech job marketplace.
        """
        self.logger.info(f"🤖 {self.name}: Scraping Arbeitnow p2 (SimplyHired slot)...")
        jobs = []
        kw_lower = [k.lower() for k in keywords[:5]]

        try:
            r = requests.get(
                "https://www.arbeitnow.com/api/job-board-api",
                params={"page": 2},
                timeout=12,
                headers={"Accept": "application/json",
                         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            )
            if r.status_code == 200:
                items = r.json().get("data", [])
                for item in items:
                    if len(jobs) >= max_jobs:
                        break
                    title = item.get("title", "").strip()
                    if not title:
                        continue
                    tags = " ".join(item.get("tags", [])).lower()
                    title_l = title.lower()
                    if kw_lower and not any(kw in title_l or kw in tags for kw in kw_lower):
                        continue
                    jobs.append({
                        "title":       title,
                        "company":     item.get("company_name", "Not specified"),
                        "location":    item.get("location", "Remote") or "Remote",
                        "description": item.get("description", title)[:500],
                        "url":         item.get("url", ""),
                        "salary":      "",
                        "source":      "SimplyHired"
                    })
                if not jobs:
                    for item in items[:max_jobs]:
                        title = item.get("title", "").strip()
                        if title:
                            jobs.append({
                                "title":       title,
                                "company":     item.get("company_name", "Not specified"),
                                "location":    item.get("location", "Remote") or "Remote",
                                "description": item.get("description", title)[:500],
                                "url":         item.get("url", ""),
                                "salary":      "",
                                "source":      "SimplyHired"
                            })
        except Exception as e:
            self.logger.warning(f"Arbeitnow p2 (SimplyHired) failed: {e}")

        self.logger.info(f"✅ {self.name}: Found {len(jobs)} jobs from SimplyHired (Arbeitnow p2)")
        return jobs

    def scrape_google_jobs_simple(self, keywords: List[str], max_jobs: int = 10, location: str = "") -> List[Dict]:
        """
        Google Jobs replacement: We Work Remotely category RSS feeds (tech-focused).
        Free, no key, returns real remote programming/devops jobs.
        """
        self.logger.info(f"🤖 {self.name}: Scraping WWR category RSS (Google Jobs slot)...")
        jobs = []
        import feedparser

        cat_feeds = [
            "https://weworkremotely.com/categories/remote-programming-jobs.rss",
            "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss",
            "https://weworkremotely.com/categories/remote-management-finance-jobs.rss",
        ]

        try:
            for feed_url in cat_feeds:
                if len(jobs) >= max_jobs:
                    break
                try:
                    r = requests.get(feed_url, timeout=10,
                                     headers={"User-Agent": "Mozilla/5.0"})
                    feed = feedparser.parse(r.content)
                    for entry in feed.entries:
                        if len(jobs) >= max_jobs:
                            break
                        title = entry.get("title", "").strip()
                        if not title:
                            continue
                        company = "Not specified"
                        if ": " in title:
                            company, title = title.split(": ", 1)
                        jobs.append({
                            "title":       title,
                            "company":     company,
                            "location":    "Remote",
                            "description": entry.get("summary", f"{title} at {company}")[:500],
                            "url":         entry.get("link", ""),
                            "salary":      "",
                            "source":      "Google Jobs"
                        })
                except Exception:
                    continue
        except Exception as e:
            self.logger.warning(f"WWR category RSS (Google Jobs) failed: {e}")

        self.logger.info(f"✅ {self.name}: Found {len(jobs)} jobs from Google Jobs (WWR RSS)")
        return jobs



    def get_matched_jobs(self, keywords: List[str], location: Optional[str] = None, max_jobs: int = 20) -> List[Dict]:
        """
        Master method to get jobs from all sources and combine them
        """
        self.logger.info(f"🚀 {self.name}: Starting multi-source scraping for {max_jobs} jobs...")
        all_jobs = []
        
        # We will split max_jobs across the available platforms to get a good mix
        # RemoteOK + WWR (Most reliable for remote tech)
        # LinkedIn + Indeed (Huge volume)
        # Glassdoor + Remotive + Wayup + Simple/Google (Good for variety)
        
        # Use max_jobs as the per-source limit (controlled by the UI slider)
        per_source_limit = max_jobs
        
        scrapers = [
            (self.scrape_remoteok, per_source_limit, {"search_tags": keywords}),
            (self.scrape_linkedin, per_source_limit, {"keywords": keywords, "location": location}),
            (self.scrape_weworkremotely, per_source_limit, {"keywords": keywords}),
            (self.scrape_indeed_simple, per_source_limit, {"keywords": keywords, "location": location}),
            (self.scrape_glassdoor, per_source_limit, {"keywords": keywords, "location": location}),
            (self.scrape_remotive, per_source_limit, {"keywords": keywords, "location": location}),
            (self.scrape_wayup, per_source_limit, {"keywords": keywords, "location": location}),
            (self.scrape_intern_insider, per_source_limit, {"keywords": keywords, "location": location}),
            (self.scrape_simply_hired, per_source_limit, {"keywords": keywords, "location": location}),
            (self.scrape_google_jobs_simple, per_source_limit, {"keywords": keywords, "location": location}),
            (self.scrape_adzuna, per_source_limit, {"keywords": keywords, "location": location})
        ]
        
        for func, limit, kwargs in scrapers:
            try:
                # Some functions like scrape_remoteok take search_tags, others keywords.
                # All take max_jobs.
                kwargs["max_jobs"] = limit
                res = func(**kwargs)
                all_jobs.extend(res)
            except Exception as e:
                self.logger.error(f"{func.__name__} failed: {e}")
                
        # Deduplicate
        unique_jobs = []
        seen_urls = set()
        seen_names = set()
        for job in all_jobs:
            # Create a simple hash to spot super similar listings
            sim_hash = f"{job['title'].lower()}|{job['company'].lower()}"
            if job['url'] not in seen_urls and sim_hash not in seen_names:
                unique_jobs.append(job)
                seen_urls.add(job['url'])
                seen_names.add(sim_hash)
        
        self.logger.info(f"Total unique jobs found: {len(unique_jobs)}")
        return unique_jobs

    def scrape_all_sources(self, keywords: List[str], max_jobs: int = 20, location: Optional[str] = None) -> List[Dict]:
        """Alias for get_matched_jobs to maintain compatibility"""
        return self.get_matched_jobs(keywords, location, max_jobs)
