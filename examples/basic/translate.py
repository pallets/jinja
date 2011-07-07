from jinja2 import Environment
import gettext

e = Environment(extensions=['jinja2.ext.i18n'])
e.install_gettext_translations(gettext.NullTranslations())
print e.from_string("""\
{% trans %}Hello {{ user }}!{% endtrans %}
{% trans count=users|count %}{{ count }} user{% pluralize %}{{ count }} users{% endtrans %}
""").render(user="someone")
