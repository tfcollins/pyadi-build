Examples
========

Practical examples showing how to use pyadi-build.

.. grid:: 2
   :gutter: 3

   .. grid-item-card:: Simple CLI
      :link: simple/index
      :link-type: doc
      :text-align: center

      :octicon:`terminal;2em`

      Basic CLI usage examples

   .. grid-item-card:: Python API
      :link: python-api/index
      :link-type: doc
      :text-align: center

      :octicon:`code;2em`

      Using pyadi-build as a Python library

Example Categories
------------------

Simple Examples
~~~~~~~~~~~~~~~

Basic CLI commands for common tasks:

- Building kernels for different platforms
- Configuring kernel with menuconfig
- Building specific device tree blobs

Python API Examples
~~~~~~~~~~~~~~~~~~~

Using pyadi-build programmatically:

- Basic kernel build
- Custom configuration
- Error handling
- CI/CD integration

Running Examples
----------------

All Python examples are in the ``examples/`` directory:

.. code-block:: bash

   # Run ZynqMP example
   python examples/build_zynqmp_kernel.py

   # Run Zynq example
   python examples/build_zynq_kernel.py

   # Run custom config example
   python examples/custom_config.py

.. toctree::
   :maxdepth: 2
   :hidden:

   simple/index
   python-api/index
