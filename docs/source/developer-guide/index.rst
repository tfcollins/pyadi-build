Developer Guide
===============

Welcome to the pyadi-build developer guide. This section covers contributing to pyadi-build, understanding the architecture, and extending functionality.

.. grid:: 2
   :gutter: 3

   .. grid-item-card:: Architecture
      :link: architecture
      :link-type: doc
      :text-align: center

      :octicon:`repo;2em`

      System design and architecture overview

   .. grid-item-card:: Contributing
      :link: contributing
      :link-type: doc
      :text-align: center

      :octicon:`git-pull-request;2em`

      How to contribute to pyadi-build

For Developers
--------------

This section is for:

- Contributors to pyadi-build
- Developers extending functionality
- Anyone interested in the internal architecture

Quick Start for Development
----------------------------

.. code-block:: bash

   # Clone repository
   git clone https://github.com/analogdevicesinc/pyadi-build.git
   cd pyadi-build

   # Create virtual environment
   python3 -m venv venv
   source venv/bin/activate

   # Install with development dependencies
   pip install -e ".[dev]"

   # Run tests
   nox -s tests

   # Format code
   nox -s format

   # Run linting
   nox -s lint

.. toctree::
   :maxdepth: 2
   :hidden:

   architecture
   contributing
