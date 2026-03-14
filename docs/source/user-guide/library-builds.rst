Library and Application Builds
================================

This guide provides detailed instructions for building and installing ADI userspace libraries and applications using ``adibuild``.

Overview
--------

The following projects are supported:

.. list-table::
   :header-rows: 1
   :widths: 20 20 60

   * - Project
     - CLI Command
     - Description
   * - **libad9361**
     - ``libad9361``
     - AD9361 device-specific library
   * - **libtinyiiod**
     - ``libtinyiiod``
     - Tiny IIO Daemon library
   * - **iio-emu**
     - ``iio-emu``
     - IIO Emulator server application
   * - **iio-oscilloscope**
     - ``osc``
     - IIO Oscilloscope GUI application
   * - **genalyzer**
     - ``genalyzer``
     - DSP analysis and generation library

Source Repositories
-------------------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Project
     - Repository URL
   * - **libad9361**
     - https://github.com/analogdevicesinc/libad9361-iio
   * - **libtinyiiod**
     - https://github.com/analogdevicesinc/libtinyiiod
   * - **iio-emu**
     - https://github.com/analogdevicesinc/iio-emu
   * - **iio-oscilloscope**
     - https://github.com/analogdevicesinc/iio-oscilloscope
   * - **genalyzer**
     - https://github.com/analogdevicesinc/genalyzer

Build Process
-------------

All userspace projects use a CMake-based build system. ``adibuild`` automates the cloning, configuration, and compilation process.

Basic Build
~~~~~~~~~~~

To build a project for a specific platform (e.g., ``arm``):

.. code-block:: bash

   adibuild libad9361 build -p arm

This will:
1. Clone the repository into ``~/.adibuild/repos/``.
2. Configure with CMake using the appropriate cross-compiler.
3. Build the project.
4. Collect artifacts into ``./build/libad9361-main-arm/``.

Handling Dependencies
~~~~~~~~~~~~~~~~~~~~~

Some projects require other pre-built libraries. For cross-compiled builds, you must provide the path to these dependencies.

**iio-emu Dependencies:**
Requires ``libiio`` and ``libtinyiiod``.

.. code-block:: bash

   adibuild iio-emu build -p arm \
     --libiio-path /path/to/libiio/install \
     --tinyiiod-path /path/to/libtinyiiod/install

**iio-oscilloscope Dependencies:**
Requires ``libiio`` and ``libad9361``.

.. code-block:: bash

   adibuild osc build -p arm \
     --libiio-path /path/to/libiio/install \
     --libad9361-path /path/to/libad9361/install

Installation Process
--------------------

While ``adibuild`` focuses on *building* and *packaging*, you can install the results to your target system or sysroot.

Manual Installation
~~~~~~~~~~~~~~~~~~~

After a successful build, artifacts are found in the output directory. To manually install them to a target filesystem:

.. code-block:: bash

   # Copy libraries
   scp build/libad9361-main-arm/libad9361.so* root@target:/usr/lib/
   
   # Copy headers
   scp build/libad9361-main-arm/ad9361.h root@target:/usr/include/

Using Sysroots
~~~~~~~~~~~~~~

When cross-compiling, you can specify a sysroot to help CMake find system dependencies (like GLib for the Oscilloscope):

.. code-block:: yaml

   platforms:
     arm:
       arch: arm
       cross_compile: arm-linux-gnueabihf-
       sysroot: /path/to/target/sysroot

Advanced Configuration
----------------------

You can pass additional CMake options via your YAML configuration:

.. code-block:: yaml

   project: libad9361
   platforms:
     native:
       arch: native
       cmake_options:
         BUILD_EXAMPLES: ON
         ENABLE_PACKAGING: OFF
