Simple CLI Examples
===================

Basic command-line examples for common tasks.

Building for Different Platforms
---------------------------------

ZynqMP Build
~~~~~~~~~~~~

.. code-block:: bash

   # Basic ZynqMP build
   adibuild linux build -p zynqmp -t 2023_R2

   # With clean
   adibuild linux build -p zynqmp -t 2023_R2 --clean

   # With more parallel jobs
   adibuild linux build -p zynqmp -t 2023_R2 -j 16

Zynq Build
~~~~~~~~~~

.. code-block:: bash

   # Basic Zynq build
   adibuild linux build -p zynq -t 2023_R2

   # Build only DTBs
   adibuild linux build -p zynq -t 2023_R2 --dtbs-only

Configuration Examples
----------------------

Interactive Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Run menuconfig
   adibuild linux menuconfig -p zynqmp -t 2023_R2

   # Make changes, save, and build
   adibuild linux build -p zynqmp -t 2023_R2

Building Specific DTBs
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Build single DTB
   adibuild linux dtbs -p zynqmp \
       zynqmp-zcu102-rev10-ad9361-fmcomms2-3.dtb

   # Build multiple DTBs
   adibuild linux dtbs -p zynq \
       zynq-zc702-adv7511-ad9361-fmcomms2-3.dtb \
       zynq-zc702-adv7511-ad9364-fmcomms4.dtb

Toolchain Management
--------------------

Check Toolchains
~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Show all available toolchains
   adibuild toolchain

   # Show toolchain for specific platform
   adibuild toolchain -p zynqmp

Clean Operations
----------------

.. code-block:: bash

   # Regular clean
   adibuild linux clean -p zynqmp -t 2023_R2

   # Deep clean (mrproper)
   adibuild linux clean -p zynq -t 2023_R2 --deep
