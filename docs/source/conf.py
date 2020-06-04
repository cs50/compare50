import os
import sys
import time

_tool = "compare50"

# Add path to module for autodoc
sys.path.insert(0, os.path.abspath(f'../../{_tool}'))

extensions = ['sphinx.ext.autodoc']

html_css_files = ["https://cs50.readthedocs.io/_static/custom.css?" + str(round(time.time()))]
html_js_files = ["https://cs50.readthedocs.io/_static/custom.js?" + str(round(time.time()))]
html_theme = "sphinx_rtd_theme"
html_theme_options = {
    "display_version": False,
    "prev_next_buttons_location": False,
    "sticky_navigation": False
}
html_title = f'{_tool} Docs'

project = f'{_tool}'
