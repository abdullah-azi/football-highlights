import json

with open('football_camera_switching.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)
    
for i, cell in enumerate(nb['cells']):
    source = ''.join(cell.get('source', []))
    if 'CAMERA SWITCHING LOGIC' in source and 'Main Version' in source:
        print(f'Main cell index: {i}')
        print(f'First line: {cell["source"][0][:100]}')
        break
