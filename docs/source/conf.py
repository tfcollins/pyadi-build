# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

# -- Path setup --------------------------------------------------------------
sys.path.insert(0, os.path.abspath("../.."))

# -- Project information -----------------------------------------------------
project = "pyadi-build"
copyright = "2025, Analog Devices, Inc."
author = "Analog Devices, Inc."

# The full version, including alpha/beta/rc tags
release = "0.1.0"
version = "0.1.0"

# -- General configuration ---------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",  # Auto-generate API docs
    "sphinx.ext.napoleon",  # Google-style docstrings
    "sphinx.ext.autosummary",  # Summary tables
    "sphinx.ext.viewcode",  # Source code links
    "sphinx.ext.intersphinx",  # External links
    "sphinx.ext.coverage",  # Coverage checking
    "sphinx.ext.githubpages",  # GitHub Pages
    "myst_parser",  # Markdown support
    "sphinxcontrib.mermaid",  # Diagrams
    "sphinx_design",  # Grid cards
    "sphinx_copybutton",  # Copy button for code
    "adi_doctools",  # ADI custom tools
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
html_theme = "cosmic"
html_title = "pyadi-build Documentation"
html_short_title = "pyadi-build"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]
# html_css_files = ["css/custom.css"]

# Theme options
html_theme_options = {
    "navigation_depth": 4,
    "show_prev_next": True,
}

# Logo files (light and dark variants)
html_logo = "_static/images/logo-light.svg"
html_theme_options["logo"] = {
    "image_light": "_static/images/logo-light.svg",
    "image_dark": "_static/images/logo-dark.svg",
}

# -- Options for autodoc -----------------------------------------------------
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "special-members": "__init__",
    "undoc-members": True,
    "show-inheritance": True,
}
autodoc_typehints = "description"
autodoc_typehints_description_target = "documented"

# Generate autodoc stubs
autosummary_generate = True
autosummary_imported_members = False

# -- Options for napoleon ----------------------------------------------------
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = True

# -- Options for intersphinx -------------------------------------------------
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "click": ("https://click.palletsprojects.com/", None),
    "pyyaml": ("https://pyyaml.org/", None),
}

# -- Options for MyST parser -------------------------------------------------
myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "substitution",
    "tasklist",
]
myst_heading_anchors = 3

# -- Options for copy button -------------------------------------------------
copybutton_prompt_text = r">>> |\.\.\. |\$ |In \[\d*\]: | {2,5}\.\.\.: | {5,8}: "
copybutton_prompt_is_regexp = True

# -- Options for Mermaid -----------------------------------------------------
mermaid_version = "10.6.1"

# -- Options for coverage ----------------------------------------------------
coverage_show_missing_items = True
