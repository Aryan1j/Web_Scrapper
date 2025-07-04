import requests
from flask import Flask, render_template, request, jsonify
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import warnings
warnings.filterwarnings('ignore')

app = Flask(__name__)

class OptimizedWebScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def scrape_website(self, url):
        """Optimized scraping function for text, images, and links"""
        try:
            # Add protocol if missing
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract optimized data
            data = {
                'url': url,
                'title': self.get_title(soup),
                'text_content': self.get_optimized_text(soup),
                'text_stats': self.get_text_statistics(soup),
                'images': self.get_optimized_images(soup, url),
                'links': self.get_optimized_links(soup, url),
                'status': 'success'
            }
            
            return {'success': True, 'data': data}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_title(self, soup):
        """Extract page title with fallbacks"""
        # Try multiple title sources
        title = soup.find('title')
        if title and title.get_text().strip():
            return title.get_text().strip()
        
        # Fallback to h1
        h1 = soup.find('h1')
        if h1 and h1.get_text().strip():
            return h1.get_text().strip()
        
        # Fallback to meta title
        meta_title = soup.find('meta', attrs={'property': 'og:title'})
        if meta_title and meta_title.get('content'):
            return meta_title.get('content').strip()
        
        return 'No title found'
    
    def get_optimized_text(self, soup):
        """Extract and optimize text content with better cleaning"""
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'noscript']):
            element.decompose()
        
        # Focus on main content areas
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile(r'content|main|article', re.I))
        
        if main_content:
            text_source = main_content
        else:
            text_source = soup
        
        # Extract text from paragraphs, headings, and lists
        text_elements = []
        
        # Get headings
        for heading in text_source.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            text = heading.get_text().strip()
            if text and len(text) > 2:
                text_elements.append(f"[HEADING] {text}")
        
        # Get paragraphs
        for para in text_source.find_all('p'):
            text = para.get_text().strip()
            if text and len(text) > 10:  # Filter out very short paragraphs
                text_elements.append(text)
        
        # Get list items
        for li in text_source.find_all('li'):
            text = li.get_text().strip()
            if text and len(text) > 5:
                text_elements.append(f"• {text}")
        
        # Get div content if no paragraphs found
        if not text_elements:
            for div in text_source.find_all('div'):
                text = div.get_text().strip()
                if text and len(text) > 20:
                    text_elements.append(text)
        
        # Clean and join text
        if text_elements:
            full_text = '\n\n'.join(text_elements)
        else:
            # Fallback to all text
            full_text = text_source.get_text()
        
        # Clean the text
        lines = (line.strip() for line in full_text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        clean_text = ' '.join(chunk for chunk in chunks if chunk and len(chunk) > 1)
        
        # Remove extra whitespace
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        return clean_text
    
    def get_text_statistics(self, soup):
        """Get detailed text statistics"""
        text = self.get_optimized_text(soup)
        
        if not text:
            return {
                'word_count': 0,
                'character_count': 0,
                'paragraph_count': 0,
                'heading_count': 0
            }
        
        words = text.split()
        paragraphs = len(soup.find_all('p'))
        headings = len(soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']))
        
        return {
            'word_count': len(words),
            'character_count': len(text),
            'paragraph_count': paragraphs,
            'heading_count': headings,
            'reading_time': round(len(words) / 200, 1)  # Average reading speed
        }
    
    def get_optimized_images(self, soup, base_url):
        """Extract images with better filtering and information"""
        images = []
        seen_urls = set()
        
        for img in soup.find_all('img'):
            src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
            
            if not src:
                continue
            
            # Convert to absolute URL
            full_url = urljoin(base_url, src)
            
            # Skip duplicates
            if full_url in seen_urls:
                continue
            seen_urls.add(full_url)
            
            # Skip very small images (likely icons/decorative)
            width = img.get('width')
            height = img.get('height')
            
            # Skip if explicitly small
            if width and height:
                try:
                    if int(width) < 50 or int(height) < 50:
                        continue
                except:
                    pass
            
            # Skip common icon/logo patterns
            if any(pattern in src.lower() for pattern in ['icon', 'logo', 'favicon', 'sprite', 'pixel']):
                if not any(size in src.lower() for size in ['large', 'big', 'main', 'hero']):
                    continue
            
            alt_text = img.get('alt', '').strip()
            title_text = img.get('title', '').strip()
            
            # Determine image type
            img_type = 'Unknown'
            if any(word in (alt_text + title_text + src).lower() for word in ['logo', 'brand']):
                img_type = 'Logo/Brand'
            elif any(word in (alt_text + title_text + src).lower() for word in ['photo', 'image', 'picture']):
                img_type = 'Photo'
            elif any(word in (alt_text + title_text + src).lower() for word in ['icon', 'button']):
                img_type = 'Icon/Button'
            elif any(word in (alt_text + title_text + src).lower() for word in ['banner', 'hero', 'header']):
                img_type = 'Banner/Hero'
            
            images.append({
                'src': full_url,
                'alt': alt_text or 'No alt text',
                'title': title_text,
                'width': width or 'Unknown',
                'height': height or 'Unknown',
                'type': img_type,
                'has_alt': bool(alt_text),
                'file_extension': src.split('.')[-1].lower() if '.' in src else 'Unknown'
            })
        
        return images
    
    def get_optimized_links(self, soup, base_url):
        """Extract links with better categorization and filtering"""
        links = []
        seen_urls = set()
        base_domain = urlparse(base_url).netloc
        
        for link in soup.find_all('a', href=True):
            href = link['href'].strip()
            text = link.get_text().strip()
            
            # Skip empty links or javascript/mailto links
            if not href or href.startswith(('javascript:', 'mailto:', 'tel:', '#')):
                continue
            
            # Skip if no meaningful text
            if not text or len(text) < 2:
                continue
            
            # Convert to absolute URL
            full_url = urljoin(base_url, href)
            
            # Skip duplicates
            if full_url in seen_urls:
                continue
            seen_urls.add(full_url)
            
            # Determine link type
            link_domain = urlparse(full_url).netloc
            is_external = link_domain != base_domain
            
            # Categorize link
            link_category = 'Internal'
            if is_external:
                if any(social in link_domain.lower() for social in ['facebook', 'twitter', 'instagram', 'linkedin', 'youtube']):
                    link_category = 'Social Media'
                elif any(domain in link_domain.lower() for domain in ['github', 'gitlab', 'bitbucket']):
                    link_category = 'Code Repository'
                elif any(domain in link_domain.lower() for domain in ['google', 'bing', 'yahoo']):
                    link_category = 'Search Engine'
                else:
                    link_category = 'External'
            
            # Check if it's a navigation link
            parent_nav = link.find_parent(['nav', 'header', 'footer'])
            if parent_nav:
                link_category += ' (Navigation)'
            
            links.append({
                'text': text[:100] + '...' if len(text) > 100 else text,  # Truncate long text
                'url': full_url,
                'is_external': is_external,
                'category': link_category,
                'domain': link_domain,
                'title': link.get('title', ''),
                'target': link.get('target', ''),
                'rel': link.get('rel', [])
            })
        
        return links

# Initialize scraper
scraper = OptimizedWebScraper()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/scrape', methods=['POST'])
def scrape():
    data = request.get_json()
    url = data.get('url')
    
    if not url:
        return jsonify({'success': False, 'error': 'URL is required'})
    
    result = scraper.scrape_website(url)
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=9000)