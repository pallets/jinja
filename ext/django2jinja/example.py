from django.conf import settings
from django2jinja import convert_templates, Writer

settings.configure(TEMPLATE_DIRS=['templates'], TEMPLATE_DEBUG=True)
writer = Writer(use_jinja_autoescape=True)
convert_templates('converted', writer=writer)
