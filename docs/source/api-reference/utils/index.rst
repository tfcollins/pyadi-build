Utilities API
=============

Utility modules for common operations.

Modules
-------

.. toctree::
   :maxdepth: 1

   git
   logger
   validators

Overview
--------

The utils package contains utility modules:

- **git** - Git repository operations
- **logger** - Logging configuration
- **validators** - Configuration validation

Quick Example
-------------

.. code-block:: python

   from adibuild.utils.git import GitRepository
   from adibuild.utils.logger import setup_logging
   import logging

   # Setup logging
   setup_logging(level=logging.INFO)

   # Clone repository
   repo = GitRepository('https://github.com/analogdevicesinc/linux.git')
   repo.clone('/path/to/work/linux')
   repo.checkout('2023_R2')
