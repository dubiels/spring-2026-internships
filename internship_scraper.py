import requests
from bs4 import BeautifulSoup
import datetime
import time
import random
import os
import json
import base64
from github import Github

class InternshipScraper:
    def __init__(self):
        # GitHub credentials from environment variables (set by GitHub Actions)
        self.github_token = os.environ.get('GITHUB_TOKEN')
        self.repo_name = os.environ.get('GITHUB_REPO')
        
        # Initialize GitHub client
        self.github = Github(self.github_token)
        self.repo = self.github.get_repo(self.repo_name)
        
        # Load existing internships from GitHub if available
        self.internships = self.load_existing_data()
        
        # Tech keywords for strict filtering
        self.tech_keywords = [
            'software', 'developer', 'programming', 'coding', 'engineer', 
            'backend', 'frontend', 'full stack', 'fullstack', 'web dev',
            'devops', 'cloud', 'cyber', 'security', 'machine learning',
            'data science', 'artificial intelligence', 'ai', 'ml',
            'mobile', 'application', 'systems', 'network',
            'IT', 'tech', 'computer', 'SWE', 'development',
            'QA engineer', 'test engineer', 'technical'
        ]
        
        # Non-tech keywords to explicitly exclude
        self.non_tech_keywords = [
            'accounting', 'finance', 'tax', 'audit', 'business', 'marketing',
            'sales', 'hr', 'human resources', 'legal', 'law', 'communications',
            'public relations', 'operations', 'logistics', 'supply chain'
        ]
        
        # Job search sites to scrape
        self.search_sites = [
            {
                'name': 'LinkedIn',
                'url': 'https://www.linkedin.com/jobs/search/?keywords=spring%202026%20software%20engineering%20internship',
                'parser': self.parse_linkedin
            },
            {
                'name': 'LinkedIn Software',
                'url': 'https://www.linkedin.com/jobs/search/?keywords=spring%202026%20software%20developer%20internship',
                'parser': self.parse_linkedin
            },
            {
                'name': 'LinkedIn Tech',
                'url': 'https://www.linkedin.com/jobs/search/?keywords=spring%202026%20tech%20internship',
                'parser': self.parse_linkedin
            },
            {
                'name': 'LinkedIn SWE',
                'url': 'https://www.linkedin.com/jobs/search/?keywords=spring%202026%20swe%20internship',
                'parser': self.parse_linkedin
            },
            {
                'name': 'Indeed',
                'url': 'https://www.indeed.com/jobs?q=spring+2026+software+engineering+internship',
                'parser': self.parse_indeed
            },
            {
                'name': 'Indeed Tech',
                'url': 'https://www.indeed.com/jobs?q=spring+2026+tech+internship',
                'parser': self.parse_indeed
            },
            {
                'name': 'Glassdoor',
                'url': 'https://www.glassdoor.com/Job/software-engineer-spring-2026-internship-jobs-SRCH_KO0,37.htm',
                'parser': self.parse_glassdoor
            }
        ]
        
        # Headers to mimic a browser
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
    def load_existing_data(self):
        """Load existing internship data from GitHub if available"""
        try:
            # Try to get the data file from GitHub
            content = self.repo.get_contents("internships.json")
            data = json.loads(base64.b64decode(content.content).decode('utf-8'))
            print(f"Loaded {len(data)} existing internships from GitHub")
            return data
        except Exception as e:
            print(f"No existing internships found or error: {e}")
            return []
    
    def save_data(self, internships):
        """Save internship data to GitHub"""
        try:
            data_json = json.dumps(internships, indent=2)
            try:
                # Update file if it exists
                contents = self.repo.get_contents("internships.json")
                self.repo.update_file(
                    contents.path,
                    f"Updated internship data - {datetime.datetime.now().strftime('%Y-%m-%d')}",
                    data_json,
                    contents.sha
                )
                print("Internship data updated successfully!")
            except:
                # Create file if it doesn't exist
                self.repo.create_file(
                    "internships.json",
                    f"Initial internship data - {datetime.datetime.now().strftime('%Y-%m-%d')}",
                    data_json
                )
                print("Internship data created successfully!")
        except Exception as e:
            print(f"Error saving data: {e}")
    
    def is_tech_role(self, title):
        """Determine if a job title is for a tech role using strict filtering"""
        title_lower = title.lower()
        
        # Check if any non-tech keywords are present
        if any(keyword in title_lower for keyword in self.non_tech_keywords):
            return False
        
        # Check if any tech keywords are present
        return any(keyword in title_lower for keyword in self.tech_keywords)
    
    def parse_linkedin(self, html):
        """Parse LinkedIn job listings"""
        soup = BeautifulSoup(html, 'html.parser')
        internships = []
        
        job_cards = soup.find_all('div', class_='job-search-card')
        for card in job_cards:
            try:
                title_elem = card.find('h3', class_='base-search-card__title')
                company_elem = card.find('h4', class_='base-search-card__subtitle')
                location_elem = card.find('span', class_='job-search-card__location')
                date_elem = card.find('time', class_='job-search-card__listdate')
                apply_link_elem = card.find('a', class_='base-card__full-link')
                
                if title_elem and company_elem:
                    title = title_elem.text.strip()
                    company = company_elem.text.strip()
                    location = location_elem.text.strip() if location_elem else "Remote/Not specified"
                    date_posted = date_elem.get('datetime') if date_elem else datetime.datetime.now().strftime('%Y-%m-%d')
                    apply_link = apply_link_elem.get('href') if apply_link_elem else "#"
                    
                    # Filter for Spring 2026 tech internships
                    title_lower = title.lower()
                    is_spring_2026 = "2026" in title_lower and any(term in title_lower for term in ["spring", "january", "february", "jan", "feb"])
                    
                    if "intern" in title_lower and is_spring_2026 and self.is_tech_role(title):
                        internships.append({
                            'company': company,
                            'title': title,
                            'location': location,
                            'date_posted': date_posted,
                            'apply_link': apply_link,
                            'source': 'LinkedIn'
                        })
            except Exception as e:
                print(f"Error parsing LinkedIn job: {e}")
        
        return internships
    
    def parse_indeed(self, html):
        """Parse Indeed job listings"""
        soup = BeautifulSoup(html, 'html.parser')
        internships = []
        
        job_cards = soup.find_all('div', class_='job_seen_beacon')
        for card in job_cards:
            try:
                title_elem = card.find('h2', class_='jobTitle')
                company_elem = card.find('span', class_='companyName')
                location_elem = card.find('div', class_='companyLocation')
                date_elem = card.find('span', class_='date')
                apply_link_elem = card.find('a', class_='jcs-JobTitle')
                
                if title_elem and company_elem:
                    title = title_elem.text.strip()
                    company = company_elem.text.strip()
                    location = location_elem.text.strip() if location_elem else "Remote/Not specified"
                    date_raw = date_elem.text.strip() if date_elem else "Just posted"
                    apply_link = "https://indeed.com" + apply_link_elem.get('href') if apply_link_elem and apply_link_elem.get('href') else "#"
                    
                    # Convert relative date to absolute date
                    today = datetime.datetime.now()
                    if "just posted" in date_raw.lower() or "today" in date_raw.lower():
                        date_posted = today.strftime('%Y-%m-%d')
                    elif "day ago" in date_raw.lower() or "days ago" in date_raw.lower():
                        days = int(''.join(filter(str.isdigit, date_raw)) or 1)
                        date_posted = (today - datetime.timedelta(days=days)).strftime('%Y-%m-%d')
                    else:
                        date_posted = today.strftime('%Y-%m-%d')
                    
                    # Filter for Spring 2026 tech internships
                    title_lower = title.lower()
                    is_spring_2026 = "2026" in title_lower and any(term in title_lower for term in ["spring", "january", "february", "jan", "feb"])
                    
                    if "intern" in title_lower and is_spring_2026 and self.is_tech_role(title):
                        internships.append({
                            'company': company,
                            'title': title,
                            'location': location,
                            'date_posted': date_posted,
                            'apply_link': apply_link,
                            'source': 'Indeed'
                        })
            except Exception as e:
                print(f"Error parsing Indeed job: {e}")
        
        return internships
    
    def parse_glassdoor(self, html):
        """Parse Glassdoor job listings"""
        soup = BeautifulSoup(html, 'html.parser')
        internships = []
        
        job_cards = soup.find_all('li', class_='react-job-listing')
        for card in job_cards:
            try:
                title_elem = card.find('a', class_='jobLink')
                company_elem = card.find('div', class_='empName')
                location_elem = card.find('span', class_='loc')
                apply_link_elem = card.find('a', class_='jobLink')
                
                if title_elem and company_elem:
                    title = title_elem.text.strip()
                    company = company_elem.text.strip()
                    location = location_elem.text.strip() if location_elem else "Remote/Not specified"
                    date_posted = datetime.datetime.now().strftime('%Y-%m-%d')  # Glassdoor doesn't always show posting date
                    apply_link = "https://www.glassdoor.com" + apply_link_elem.get('href') if apply_link_elem and apply_link_elem.get('href') else "#"
                    
                    # Filter for Spring 2026 tech internships
                    title_lower = title.lower()
                    is_spring_2026 = "2026" in title_lower and any(term in title_lower for term in ["spring", "january", "february", "jan", "feb"])
                    
                    if "intern" in title_lower and is_spring_2026 and self.is_tech_role(title):
                        internships.append({
                            'company': company,
                            'title': title,
                            'location': location,
                            'date_posted': date_posted,
                            'apply_link': apply_link,
                            'source': 'Glassdoor'
                        })
            except Exception as e:
                print(f"Error parsing Glassdoor job: {e}")
        
        return internships
    
    def scrape_site(self, site):
        """Scrape a specific job site"""
        print(f"Scraping {site['name']}...")
        try:
            response = requests.get(site['url'], headers=self.headers, timeout=30)
            if response.status_code == 200:
                return site['parser'](response.text)
            else:
                print(f"Failed to scrape {site['name']}: Status code {response.status_code}")
                return []
        except Exception as e:
            print(f"Error scraping {site['name']}: {e}")
            return []
    
    def update_readme(self, internships):
        """Update the GitHub README with latest internship listings"""
        # Sort internships by date (newest first)
        sorted_internships = sorted(
            internships, 
            key=lambda x: datetime.datetime.strptime(x['date_posted'], '%Y-%m-%d'), 
            reverse=True
        )
        
        # Generate README content
        readme_content = "# Spring 2026 Tech Internship Opportunities\n\n"
        readme_content += f"*Last updated: {datetime.datetime.now().strftime('%Y-%m-%d')}*\n\n"
        readme_content += "This README is automatically updated daily with new Spring 2026 tech internship postings using GitHub Actions.\n\n"
        readme_content += "* Does NOT offer Sponsorship\n"
        readme_content += "* us - Requires U.S. Citizenship\n"
        readme_content += "* Internship application is closed\n\n"
        
        readme_content += "| Company | Role | Location | Application | Date Posted |\n"
        readme_content += "|---------|------|----------|-------------|------------|\n"
        
        for job in sorted_internships:
            # Add Apply button with real link
            apply_button = f"[Apply]({job['apply_link']})"
            readme_content += f"| {job['company']} | {job['title']} | {job['location']} | {apply_button} | {job['date_posted']} |\n"
        
        # Update README on GitHub
        try:
            # Get the README file if it exists
            try:
                contents = self.repo.get_contents("README.md")
                self.repo.update_file(
                    contents.path,
                    f"Updated internship listings - {datetime.datetime.now().strftime('%Y-%m-%d')}",
                    readme_content,
                    contents.sha
                )
                print("README updated successfully!")
            except:
                # Create README if it doesn't exist
                self.repo.create_file(
                    "README.md",
                    f"Initial internship listings - {datetime.datetime.now().strftime('%Y-%m-%d')}",
                    readme_content
                )
                print("README created successfully!")
        except Exception as e:
            print(f"Error updating README: {e}")
    
    def run(self):
        """Run the scraper on all sites and update the README"""
        new_internships = []
        
        # Scrape all sites
        for site in self.search_sites:
            site_internships = self.scrape_site(site)
            new_internships.extend(site_internships)
            time.sleep(random.uniform(2, 5))  # Random delay to avoid being blocked
        
        # Check for new internships
        existing_ids = {f"{job['company']}:{job['title']}" for job in self.internships}
        added_count = 0
        
        for job in new_internships:
            job_id = f"{job['company']}:{job['title']}"
            if job_id not in existing_ids:
                self.internships.append(job)
                existing_ids.add(job_id)
                added_count += 1
        
        print(f"Found {len(new_internships)} internships, {added_count} new")
        
        # Save data and update README
        self.save_data(self.internships)
        self.update_readme(self.internships)
        print(f"Added {added_count} new internships!")

if __name__ == "__main__":
    print("Starting Spring 2026 tech internship scraper...")
    scraper = InternshipScraper()
    scraper.run()