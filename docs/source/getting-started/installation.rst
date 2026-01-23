Installation
============

This guide covers different ways to install pyadi-build.

From PyPI (Recommended)
-----------------------

Install the latest stable version from PyPI:

.. code-block:: bash

   pip install pyadi-build

Verify the installation:

.. code-block:: bash

   adibuild --version

From Source (Development)
--------------------------

Install from the GitHub repository for development or to get the latest features:

.. code-block:: bash

   git clone https://github.com/analogdevicesinc/pyadi-build.git
   cd pyadi-build
   pip install -e ".[dev]"

This installs pyadi-build in editable mode with development dependencies.

Virtual Environment (Recommended)
----------------------------------

Using a virtual environment is recommended to avoid conflicts with system packages:

.. code-block:: bash

   # Create virtual environment
   python3 -m venv venv

   # Activate (Linux/macOS)
   source venv/bin/activate

   # Activate (Windows)
   venv\Scripts\activate

   # Install pyadi-build
   pip install pyadi-build

   # Verify installation
   adibuild --version

User Installation
-----------------

Install for the current user only (no root/admin required):

.. code-block:: bash

   pip install --user pyadi-build

.. note::
   On Linux, you may need to add ``~/.local/bin`` to your PATH:

   .. code-block:: bash

      export PATH="$HOME/.local/bin:$PATH"

   Add this to your ``~/.bashrc`` or ``~/.zshrc`` to make it permanent.

System Requirements
-------------------

Python Version
~~~~~~~~~~~~~~

pyadi-build requires **Python 3.10 or later**. Check your Python version:

.. code-block:: bash

   python3 --version

If you need to install or upgrade Python:

.. tab-set::

   .. tab-item:: Ubuntu/Debian

      .. code-block:: bash

         sudo apt update
         sudo apt install python3 python3-pip python3-venv

   .. tab-item:: Fedora/RHEL

      .. code-block:: bash

         sudo dnf install python3 python3-pip

   .. tab-item:: macOS

      .. code-block:: bash

         brew install python@3.11

   .. tab-item:: Windows

      Download from `python.org <https://www.python.org/downloads/>`_

Required Tools
~~~~~~~~~~~~~~

Install required system tools:

.. tab-set::

   .. tab-item:: Ubuntu/Debian

      .. code-block:: bash

         sudo apt install git make gcc

   .. tab-item:: Fedora/RHEL

      .. code-block:: bash

         sudo dnf install git make gcc

   .. tab-item:: macOS

      .. code-block:: bash

         xcode-select --install

   .. tab-item:: Windows

      Install Git from `git-scm.com <https://git-scm.com/>`_ and
      Make from `gnuwin32.sourceforge.net <http://gnuwin32.sourceforge.net/packages/make.htm>`_

Optional: menuconfig Support
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For interactive kernel configuration (``adibuild linux menuconfig``), install ncurses:

.. tab-set::

   .. tab-item:: Ubuntu/Debian

      .. code-block:: bash

         sudo apt install libncurses5-dev libncursesw5-dev

   .. tab-item:: Fedora/RHEL

      .. code-block:: bash

         sudo dnf install ncurses-devel

   .. tab-item:: macOS

      .. code-block:: bash

         brew install ncurses

Optional Dependencies
---------------------

Development Dependencies
~~~~~~~~~~~~~~~~~~~~~~~~

For contributing to pyadi-build:

.. code-block:: bash

   pip install -e ".[dev]"

This includes:

- **pytest** - Testing framework
- **ruff** - Linting and formatting
- **mypy** - Type checking
- **nox** - Test automation

Documentation Dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~~~

For building documentation:

.. code-block:: bash

   pip install -e ".[docs]"

This includes Sphinx and all required extensions.

Verifying Installation
----------------------

Check that all components are working:

.. code-block:: bash

   # Check pyadi-build version
   adibuild --version

   # Check Git
   git --version

   # Check Make
   make --version

   # Check available toolchains
   adibuild toolchain

Expected output:

.. code-block:: text

   pyadi-build version 0.1.0

   Checking available toolchains...

   No Xilinx Vivado/Vitis found
   No cached ARM GNU toolchains
   System toolchains: Not found

   ARM GNU toolchain will be downloaded automatically when needed.

.. note::
   Don't worry if no toolchains are found. pyadi-build will automatically download
   the ARM GNU toolchain when you run your first build.

Next Steps
----------

Now that pyadi-build is installed, proceed to :doc:`quickstart` to run your first build.

Upgrading
---------

To upgrade to the latest version:

.. code-block:: bash

   pip install --upgrade pyadi-build

For development installations:

.. code-block:: bash

   cd pyadi-build
   git pull
   pip install -e ".[dev]"

Uninstallation
--------------

To uninstall pyadi-build:

.. code-block:: bash

   pip uninstall pyadi-build

To also remove cached data:

.. code-block:: bash

   rm -rf ~/.adibuild
