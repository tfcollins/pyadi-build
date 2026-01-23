Logging
=======

Logging configuration utilities.

.. currentmodule:: adibuild.utils.logger

.. autofunction:: setup_logging

Example Usage
-------------

**Basic Setup:**

.. code-block:: python

   from adibuild.utils.logger import setup_logging
   import logging

   # Setup logging at INFO level
   setup_logging(level=logging.INFO)

   # Now use logging
   logger = logging.getLogger(__name__)
   logger.info("Building kernel...")

**Debug Logging:**

.. code-block:: python

   # Enable debug logging
   setup_logging(level=logging.DEBUG)

   # All debug messages will be shown
   logger.debug("Detailed debug information")

**Warning Only:**

.. code-block:: python

   # Show only warnings and errors
   setup_logging(level=logging.WARNING)

**Custom Logger:**

.. code-block:: python

   import logging

   # Setup logging
   from adibuild.utils.logger import setup_logging
   setup_logging(level=logging.INFO)

   # Create custom logger
   logger = logging.getLogger('my_module')
   logger.info("Custom log message")

Log Levels
----------

Standard Python logging levels:

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Level
     - Usage
   * - ``DEBUG``
     - Detailed diagnostic information
   * - ``INFO``
     - General informational messages
   * - ``WARNING``
     - Warning messages for potential issues
   * - ``ERROR``
     - Error messages for failures
   * - ``CRITICAL``
     - Critical errors

See Also
--------

- `Python logging documentation <https://docs.python.org/3/library/logging.html>`_
- :doc:`../../user-guide/python-api-usage` - Python API guide
