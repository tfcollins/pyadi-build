Docker Builds
=============

pyadi-build can run supported Vivado-based builds inside reusable Docker images instead of relying on a host-installed Vivado tree.

Overview
--------

The Docker workflow has two parts:

1. Install Vivado and build a reusable image with ``adibuild vivado image build``.
2. Run supported build commands with ``--runner docker`` or the equivalent configuration.

Supported Docker-backed build commands currently include:

- ``adibuild hdl build``
- ``adibuild noos build`` for Xilinx no-OS platforms
- ``adibuild boot build-atf``
- ``adibuild boot build-uboot``
- ``adibuild boot build-boot``

Reusable Vivado Images
----------------------

Build a reusable image for a supported Vivado release:

.. code-block:: bash

   export AMD_USERNAME="user@example.com"
   export AMD_PASSWORD="..."
   adibuild vivado image build --version 2023.2

By default this produces an image tagged as:

.. code-block:: text

   adibuild/vivado:2023.2

You can override the tag:

.. code-block:: bash

   adibuild vivado image build --version 2025.1 --tag registry.example.com/adibuild/vivado:2025.1

Inspect and list images:

.. code-block:: bash

   adibuild vivado image list
   adibuild vivado image inspect --tag adibuild/vivado:2023.2

Running Builds in Docker
------------------------

Use ``--runner docker`` to execute a supported build inside a reusable image:

.. code-block:: bash

   adibuild hdl build -p zed_fmcomms2 --runner docker --tool-version 2023.2

Explicitly select the image:

.. code-block:: bash

   adibuild noos build -p xilinx_ad9081 \
     --runner docker \
     --docker-image adibuild/vivado:2023.2 \
     --tool-version 2023.2

Boot flows can use the same runner:

.. code-block:: bash

   adibuild boot build-atf -p zynqmp --runner docker --tool-version 2023.2
   adibuild boot build-uboot -p zynqmp --runner docker --tool-version 2023.2
   adibuild boot build-boot -p zynqmp --xsa system_top.xsa --runner docker --tool-version 2023.2

How the Runner Works
--------------------

When Docker mode is enabled, pyadi-build:

- launches ``docker run`` for each build step
- mounts the current workspace and ``~/.adibuild`` cache into the container
- sources the Vivado ``settings64.sh`` script inside the container before executing the command
- writes artifacts back to the host-mounted output directory

The host does not need a local Vivado installation for Docker mode, but it does need:

- Docker daemon access
- a reusable image that matches the requested Vivado version

Configuration
-------------

You can make Docker the default runner in a config file:

.. code-block:: yaml

   build:
     runner: docker
     docker:
       image: adibuild/vivado:2023.2
       tool_version: 2023.2

CLI flags override configuration values. If ``build.runner`` is ``docker`` and no image is configured, pyadi-build defaults to:

.. code-block:: text

   adibuild/vivado:<tool_version>

Notes
-----

- Docker mode is currently intended for Vivado-based flows only.
- Xilinx no-OS builds are supported; non-Xilinx no-OS platforms continue to use their normal host toolchains.
- ``--generate-script`` works with Docker mode and writes the equivalent ``docker run`` commands to the generated script.
