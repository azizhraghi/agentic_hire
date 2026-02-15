"""
IMPROVED JOB SCRAPER - Multiple Reliable Sources
Adapted from ai_scraper_IMPROVED.py
"""

import requests
from bs4 import BeautifulSoup
import logging
from typing import Dict, List
import time
from utils.logger import AgenticLogger

class ImprovedJobScraper:
    """Improved multi-source job scraper"""
    
    def __init__(self):
        self.name = "Improved Scraper"
        self.logger = AgenticLogger("JobScraper")
        # Rotate user agents to avoid detection
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        self.current_ua_index = 0
    
    def get_headers(self):
        """Rotate user agents"""
        self.current_ua_index = (self.current_ua_index + 1) % len(self.user_agents)
        return {
            'User-Agent': self.user_agents[self.current_ua_index],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
    def scrape_remoteok(self, keywords: List[str], max_jobs: int = 10) -> List[Dict]:
        """RemoteOK - MOST RELIABLE!"""
        self.logger.info(f"🤖 {self.name}: Scraping RemoteOK...")
        jobs = []
        
        try:
            urls = [
                "https://remoteok.com/remote-dev-jobs",
                "https://remoteok.com/remote-jobs",
            ]
            
            for url in urls:
                if len(jobs) >= max_jobs:
                    break
                    
                try:
                    response = requests.get(url, headers=self.get_headers(), timeout=10)
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    job_elements = soup.find_all('tr', class_='job')[:max_jobs]
                    
                    for job_elem in job_elements:
                        if len(jobs) >= max_jobs:
                            break
                            
                        try:
                            company_elem = job_elem.find('h3', class_='company')
                            company = company_elem.text.strip() if company_elem else "Remote Company"
                            
                            title_elem = job_elem.find('h2', itemprop='title')
                            title = title_elem.text.strip() if title_elem else None
                            
                            if not title or len(title) < 3:
                                continue
                            
                            if keywords:
                                matches_keyword = any(
                                    keyword.lower() in title.lower() or 
                                    keyword.lower() in company.lower()
                                    for keyword in keywords
                                )
                                if not matches_keyword:
                                    continue
                            
                            location_elem = job_elem.find('div', class_='location')
                            location = location_elem.text.strip() if location_elem else "Remote"
                            
                            tags = []
                            tag_elems = job_elem.find_all('span', class_='tag')
                            for tag in tag_elems[:7]:
                                tags.append(tag.text.strip())
                            
                            if tags:
                                description = f"Remote {title} position. Key skills/technologies: {', '.join(tags)}. Company: {company}."
                            else:
                                description = f"Remote {title} position at {company}."
                            
                            link_elem = job_elem.find('a', class_='preventLink')
                            job_url = f"https://remoteok.com{link_elem['href']}" if link_elem and link_elem.get('href') else ""
                            
                            job = {
                                'title': title,
                                'company': company,
                                'location': location,
                                'description': description,
                                'url': job_url,
                                'source': 'RemoteOK'
                            }
                            
                            jobs.append(job)
                            
                        except Exception:
                            continue
                    
                    time.sleep(0.5)
                    
                except Exception as e:
                    self.logger.warning(f"Failed to scrape {url}: {e}")
                    continue
            
            self.logger.info(f"✅ {self.name}: Found {len(jobs)} jobs from RemoteOK")
            return jobs
            
        except Exception as e:
            self.logger.error(f"❌ RemoteOK scraping failed: {e}")
            return []
    
    def scrape_weworkremotely(self, keywords: List[str], max_jobs: int = 10) -> List[Dict]:
        """WeWorkRemotely - VERY RELIABLE!"""
        self.logger.info(f"🤖 {self.name}: Scraping WeWorkRemotely...")
        jobs = []
        
        try:
            categories = [
                'remote-programming-jobs',
                'remote-full-stack-programming-jobs',
                'remote-devops-sysadmin-jobs',
                'remote-front-end-programming-jobs'
            ]
            
            for category in categories:
                if len(jobs) >= max_jobs:
                    break
                    
                url = f"https://weworkremotely.com/categories/{category}"
                
                try:
                    response = requests.get(url, headers=self.get_headers(), timeout=10)
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    job_elements = soup.find_all('li', class_='feature')
                    
                    for job_elem in job_elements:
                        if len(jobs) >= max_jobs:
                            break
                            
                        try:
                            title_elem = job_elem.find('span', class_='title')
                            title = title_elem.text.strip() if title_elem else None
                            
                            if not title or len(title) < 3:
                                continue
                            
                            if keywords:
                                matches_keyword = any(
                                    keyword.lower() in title.lower()
                                    for keyword in keywords
                                )
                                if not matches_keyword:
                                    continue
                            
                            company_elem = job_elem.find('span', class_='company')
                            company = company_elem.text.strip() if company_elem else "Remote Company"
                            
                            region_elem = job_elem.find('span', class_='region')
                            location = region_elem.text.strip() if region_elem else "Remote"
                            
                            link_elem = job_elem.find('a')
                            job_url = f"https://weworkremotely.com{link_elem['href']}" if link_elem and link_elem.get('href') else ""
                            
                            description = f"Remote {title} position at {company}. Location preference: {location}."
                            
                            job = {
                                'title': title,
                                'company': company,
                                'location': location,
                                'description': description,
                                'url': job_url,
                                'source': 'WeWorkRemotely'
                            }
                            
                            jobs.append(job)
                            
                        except Exception:
                            continue
                    
                    time.sleep(0.5)
                    
                except Exception:
                    continue
            
            self.logger.info(f"✅ {self.name}: Found {len(jobs)} jobs from WWR")
            return jobs
            
        except Exception as e:
            self.logger.error(f"❌ WWR scraping failed: {e}")
            return []
    
    def scrape_all_sources(self, keywords: List[str], max_jobs: int = 15) -> List[Dict]:
        """Scrape from multiple sources"""
        all_jobs = []
        
        # 1. RemoteOK
        remoteok_jobs = self.scrape_remoteok(keywords, max_jobs=max_jobs // 2)
        all_jobs.extend(remoteok_jobs)
        
        # 2. WeWorkRemotely
        wwr_jobs = self.scrape_weworkremotely(keywords, max_jobs=max_jobs // 2)
        all_jobs.extend(wwr_jobs)
        
        # Deduplicate
        seen = set()
        unique_jobs = []
        for job in all_jobs:
            key = (job['title'].lower(), job['company'].lower())
            if key not in seen:
                seen.add(key)
                unique_jobs.append(job)
        
        return unique_jobs[:max_jobs]
