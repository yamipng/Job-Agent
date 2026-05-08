from bs4 import BeautifulSoup

with open('debug_linkedin.html', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

# Try different selectors
selectors = [
    ('job-search-card',             soup.find_all(class_='job-search-card')),
    ('base-search-card--link',      soup.find_all(class_='base-search-card--link')),
    ('jobs-search__results-list li',soup.select('ul.jobs-search__results-list li')),
    ('base-card',                   soup.find_all(class_='base-card')),
]

for name, results in selectors:
    print(f'{name}: {len(results)} results')

print()
print('=== First job-search-card found ===')
card = soup.find(class_='job-search-card')
if card:
    print(card.prettify()[:1500])
else:
    print('None found')
