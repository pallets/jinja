from pallets_sphinx_themes import get_version
from pallets_sphinx_themes import ProjectLink

# Project --------------------------------------------------------------

project = "Jinja"
copyright = "2007 Pallets"
author = "Pallets"
release, version = get_version("Jinja2")

# General --------------------------------------------------------------

master_doc = "index"
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "pallets_sphinx_themes",
    "sphinxcontrib.log_cabinet",
    "sphinx_issues",
]
autodoc_typehints = "description"
intersphinx_mapping = {"python": ("https://docs.python.org/3/", None)}
issues_github_path = "pallets/jinja"

# HTML -----------------------------------------------------------------

html_theme = "jinja"
html_theme_options = {"index_sidebar_logo": False}
html_context = {
    "project_links": [
        ProjectLink("Donate", "https://palletsprojects.com/donate"),
        ProjectLink("PyPI Releases", "https://pypi.org/project/Jinja2/"),
        ProjectLink("Source Code", "https://github.com/pallets/jinja/"),
        ProjectLink("Issue Tracker", "https://github.com/pallets/jinja/issues/"),
        ProjectLink("Website", "https://palletsprojects.com/p/jinja/"),
        ProjectLink("Twitter", "https://twitter.com/PalletsTeam"),
        ProjectLink("Chat", "https://discord.gg/pallets"),
    ]
}
html_sidebars = {
    "index": ["project.html", "localtoc.html", "searchbox.html", "ethicalads.html"],
    "**": ["localtoc.html", "relations.html", "searchbox.html", "ethicalads.html"],
}
singlehtml_sidebars = {"index": ["project.html", "localtoc.html", "ethicalads.html"]}
html_static_path = ["_static"]
html_favicon = "_static/jinja-logo-sidebar.png"
html_logo = "_static/jinja-logo-sidebar.png"
html_title = f"Jinja Documentation ({version})"
html_show_sourcelink = False

# LaTeX ----------------------------------------------------------------

latex_documents = [(master_doc, f"Jinja-{version}.tex", html_title, author, "manual")]
