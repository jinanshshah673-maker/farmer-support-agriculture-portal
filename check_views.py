import os
import django
from django.test import Client

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pro1.settings')
django.setup()

client = Client()
response = client.get('/market_price/')

print(f"Status Code: {response.status_code}")
if response.status_code == 200:
    print("Market Price View Rendered Successfully!")
else:
    print(response.content)
