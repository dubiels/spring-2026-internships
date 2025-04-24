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
        # GitHub credentials from environment variables
        self.github_token = os.environ.get('GITHUB_TOKEN')
        self.repo_name = os.environ.get('GITHUB_REPO')
        
        # Initialize GitHub client
        self.github = Github(self.github_token)
        self.repo = self.github.get_repo(self.repo_name)
        
        # Tech keywords for strict filtering
        self.tech_keywords = [
            'software', 'developer', 'programming', 'coding', 'engineer', 
            'backend', 'frontend', 'full stack', 'fullstack', 'web dev',
            'devops', 'cloud', 'cyber', 'security', 'machine learning',
            'data science', 'artificial intelligence', 'ai', 'ml',
            'mobile', 'application', 'systems', 'network', 'IT', 'tech', 
            'computer', 'SWE', 'development', 'QA engineer', 'test engineer', 'technical'
        ]
        
        # Non-tech exclusion keywords
        self.non_tech_keywords = [
            'accounting', 'finance', 'tax', 'audit', 'business', 'marketing',
            'sales', 'hr', 'human resources', 'legal', 'law', 'communications',
            'public relations', 'operations', 'logistics', 'supply chain'
        ]
        
        # Company career URLs (no Google fallbacks)
        self.company_career_urls = {
            'Google': 'https://careers.google.com/jobs/results/?distance=50&q=Software%20Engineering%20Intern',
            'Microsoft': 'https://careers.microsoft.com/students/us/en/search-results?keywords=intern',
            # ... (keep other company URLs but remove Google search entries)
        }
        
        # Job sites configuration
        self.search_sites = [
            {
                'name': 'LinkedIn',
                'url': 'https://www.linkedin.com/jobs/search/?keywords=spring%202026%20software%20engineering%20internship',
                'parser': self.parse_linkedin
            },
            # ... (other site configurations remain unchanged)
        ]
        
        # Browser headers
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9'
        }
        
        # Load existing data with strict filtering
        self.internships = self.load_and_filter_existing_data()

    def get_career_link(self, company_name):
        """Get career page URL without Google fallback"""
        return self.company_career_urls.get(company_name, None)

    def parse_linkedin(self, html):
        """Parse LinkedIn with updated selectors"""
        soup = BeautifulSoup(html, 'html.parser')
        internships = []
        
        for card in soup.find_all('div', class_='base-card'):
            try:
                title_elem = card.find('h3', class_='base-search-card__title')
                company_elem = card.find('h4', class_='base-search-card__subtitle')
                apply_link_elem = card.find('a', class_='base-card__full-link')
                
                if all([title_elem, company_elem, apply_link_elem]):
                    apply_link = apply_link_elem['href'].split('?')[0]  # Clean URL parameters
                    company = company_elem.text.strip()
                    
                    # Only use career URL if no direct link found
                    if '/jobs/view/' not in apply_link:
                        apply_link = self.get_career_link(company) or apply_link
                    
                    internships.append({
                        'company': company,
                        'title': title_elem.text.strip(),
                        'apply_link': apply_link,
                        # ... (other fields)
                    })
            except Exception as e:
                print(f"LinkedIn parse error: {e}")
        return internships

    def parse_indeed(self, html):
        """Parse Indeed with improved link handling"""
        soup = BeautifulSoup(html, 'html.parser')
        internships = []
        
        for card in soup.find_all('div', class_='job_seen_beacon'):
            try:
                link_elem = card.find('a', class_='jcs-JobTitle')
                if link_elem:
                    apply_link = f"https://indeed.com{link_elem['href']}"
                    # ... (other fields)
                    internships.append({
                        'apply_link': apply_link,
                        # ... (other data)
                    })
            except Exception as e:
                print(f"Indeed parse error: {e}")
        return internships

    def update_readme(self, internships):
        """Generate README with validated links"""
        readme_content = "# Spring 2026 Tech Internship Opportunities\n\n"
        readme_content += "| Company | Role | Application |\n"
        readme_content += "|---------|------|-------------|\n"
        
        for job in sorted(internships, key=lambda x: x['date_posted'], reverse=True):
            apply_link = job.get('apply_link', '')
            
            # Validate and clean links
            if not apply_link or any(bad in apply_link for bad in ['google.com', '?']):
                apply_link = self.get_career_link(job['company']) or '#'
            
            if apply_link == '#':
                apply_button = "Check Company Site"
            else:
                apply_button = f"[Apply]({apply_link})"
            
            readme_content += f"| {job['company']} | {job['title']} | {apply_button} |\n"
        
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