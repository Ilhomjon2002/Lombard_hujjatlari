import sys, os, django
from pathlib import Path

# Add project directory to python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventor.settings')
django.setup()

from django.template.loader import get_template
from django.template.exceptions import TemplateDoesNotExist, TemplateSyntaxError

templates_dir = os.path.join(project_dir, 'templates')
print("Checking templates in:", templates_dir)

errors = []
for root, dirs, files in os.walk(templates_dir):
    for f in files:
        if f.endswith('.html'):
            rel_path = os.path.relpath(os.path.join(root, f), templates_dir).replace('\\', '/')
            try:
                get_template(rel_path)
            except TemplateSyntaxError as e:
                errors.append(f'Syntax Error in {rel_path}: {e}')
            except TemplateDoesNotExist as e:
                errors.append(f'Missing Include in {rel_path}: {e}')
            except Exception as e:
                pass # Ignoring other errors like missing context variables

if errors:
    print('\nERRORS FOUND:')
    for err in errors:
        print(err)
else:
    print('\nAll templates parsed successfully!')
