import requests
import json

url = 'http://localhost:8000/api/students/20225818/academic-details'

try:
    response = requests.get(url, timeout=10)
    print(f'Status: {response.status_code}')
    
    if response.ok:
        data = response.json()
        print(f'\nTotal learned subjects: {len(data["learned_subjects"])}')
        
        if data['learned_subjects']:
            print('\nFirst learned subject:')
            first = data['learned_subjects'][0]
            print(json.dumps(first, indent=2, ensure_ascii=False))
            print(f'\n✅ subject_code field exists: {"subject_code" in first}')
    else:
        print(f'Error: {response.text}')
except Exception as e:
    print(f'Error: {e}')
