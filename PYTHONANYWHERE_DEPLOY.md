# PythonAnywhere Deployment

Target domain:

```text
https://hamzaathar789.pythonanywhere.com
```

## Bash Console

```bash
cd ~
git clone YOUR_GITHUB_REPO_URL ecommerce
cd ecommerce
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

For production settings:

```bash
echo "export DJANGO_DEBUG=False" >> ~/.bashrc
echo "export DJANGO_SECRET_KEY='CHANGE_THIS_TO_A_LONG_RANDOM_SECRET'" >> ~/.bashrc
source ~/.bashrc
```

## Web Tab

Create a manual web app:

```text
Framework: Manual configuration
Python: 3.10
Source code: /home/hamzaathar789/ecommerce
Working directory: /home/hamzaathar789/ecommerce
Virtualenv: /home/hamzaathar789/ecommerce/venv
```

WSGI file content:

```python
import os
import sys

path = '/home/hamzaathar789/ecommerce'
if path not in sys.path:
    sys.path.insert(0, path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
os.environ.setdefault('DJANGO_DEBUG', 'False')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

Static files:

```text
URL: /static/
Directory: /home/hamzaathar789/ecommerce/staticfiles
```

Media files:

```text
URL: /media/
Directory: /home/hamzaathar789/ecommerce/media
```

After saving, press **Reload** on the Web tab.
