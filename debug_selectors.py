import re

with open('debug_linkedin.html', encoding='utf-8') as f:
    html = f.read()

print('File size:', len(html))
print()

classes = re.findall(r'class="([^"]*job[^"]*?)"', html)
unique = list(set(classes))[:40]
print('=== Job-related classes found ===')
for c in unique:
    print(c)

print()
print('=== Checking for known selectors ===')
checks = [
    'job-search-card',
    'base-search-card__title',
    'base-search-card__subtitle',
    'jobs-search__results-list',
    'scaffold-layout__list-container',
    'job-card-container',
    'jobs-job-board-list',
]
for sel in checks:
    print(f'  {sel}: {"FOUND" if sel in html else "NOT FOUND"}')
