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

    def get_matched_jobs(self, keywords: List[str], location: Optional[str] = None, max_jobs: int = 20) -> List[Dict]:
        """
        Master method to get jobs from all sources and combine them
        """
        all_jobs = []
        
        # Distribute max_jobs roughly:
        # RemoteOK: 40%
        # LinkedIn: 30%
        # WWR: 30%
        # Adzuna: Remaining/Backup
        
        limit_remoteok = max(5, int(max_jobs * 0.4))
        limit_linkedin = max(5, int(max_jobs * 0.3))
        limit_wwr = max(5, int(max_jobs * 0.3))
        
        # 1. RemoteOK (Best structured data)
        try:
            remoteok_jobs = self.scrape_remoteok(max_jobs=limit_remoteok, search_tags=keywords)
            all_jobs.extend(remoteok_jobs)
        except Exception as e:
            self.logger.error(f"RemoteOK step failed: {e}")

        # 2. LinkedIn (High volume)
        try:
            linkedin_jobs = self.scrape_linkedin(keywords, max_jobs=limit_linkedin, location=location)
            all_jobs.extend(linkedin_jobs)
        except Exception as e:
            self.logger.error(f"LinkedIn step failed: {e}")

        # 3. WeWorkRemotely (Reliable)
        try:
            wwr_jobs = self.scrape_weworkremotely(keywords, max_jobs=limit_wwr)
            all_jobs.extend(wwr_jobs)
        except Exception as e:
            self.logger.error(f"WWR step failed: {e}")
            
        # 4. Adzuna (Backup if needed)
        if len(all_jobs) < max_jobs * 0.5:
            try:
                adzuna_jobs = self.scrape_adzuna(keywords, max_jobs=limit_linkedin, location=location)
                all_jobs.extend(adzuna_jobs)
            except Exception:
                pass

        # Deduplicate by URL
        unique_jobs = []
        seen_urls = set()
        for job in all_jobs:
            if job['url'] not in seen_urls:
                unique_jobs.append(job)
                seen_urls.add(job['url'])
        
        # Limit total return
        if len(unique_jobs) > max_jobs:
            unique_jobs = unique_jobs[:max_jobs]
            
        self.logger.info(f"Total unique jobs found: {len(unique_jobs)}")
        return unique_jobs

    def scrape_all_sources(self, keywords: List[str], max_jobs: int = 20, location: Optional[str] = None) -> List[Dict]:
        """Alias for get_matched_jobs to maintain compatibility"""
        return self.get_matched_jobs(keywords, location, max_jobs)
