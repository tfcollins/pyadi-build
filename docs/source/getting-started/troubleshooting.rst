Troubleshooting
===============

This guide covers common issues and their solutions.

Toolchain Issues
----------------

No Suitable Toolchain Found
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:**

.. code-block:: text

   Error: No suitable toolchain found for arm64

**Solutions:**

1. **Let pyadi-build download ARM GNU toolchain** (recommended):

   .. code-block:: bash

      adibuild linux build -p zynqmp -t 2023_R2

   The toolchain will download automatically.

2. **Install Xilinx Vivado/Vitis**:

   If you have Vivado installed, ensure it's detected:

   .. code-block:: bash

      export XILINX_VIVADO=/opt/Xilinx/Vivado/2023.2
      export XILINX_VITIS=/opt/Xilinx/Vitis/2023.2

3. **Install system toolchain**:

   .. tab-set::

      .. tab-item:: Ubuntu/Debian

         .. code-block:: bash

            sudo apt install gcc-arm-linux-gnueabihf gcc-aarch64-linux-gnu

      .. tab-item:: Fedora/RHEL

         .. code-block:: bash

            sudo dnf install gcc-arm-linux-gnu gcc-aarch64-linux-gnu

Toolchain Download Fails
~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:**

.. code-block:: text

   Error downloading ARM GNU toolchain: Connection timeout

**Solutions:**

1. **Check internet connection**:

   .. code-block:: bash

      ping arm.com

2. **Download manually**:

   Download from `ARM Developer <https://developer.arm.com/downloads/-/arm-gnu-toolchain-downloads>`_
   and extract to ``~/.adibuild/toolchains/arm/``:

   .. code-block:: bash

      mkdir -p ~/.adibuild/toolchains/arm
      cd ~/.adibuild/toolchains/arm
      wget https://developer.arm.com/.../arm-gnu-toolchain-12.2.rel1-x86_64-aarch64-none-linux-gnu.tar.xz
      tar xf arm-gnu-toolchain-12.2.rel1-x86_64-aarch64-none-linux-gnu.tar.xz

3. **Use system toolchain as fallback**:

   .. code-block:: bash

      sudo apt install gcc-aarch64-linux-gnu

Wrong Toolchain Version
~~~~~~~~~~~~~~~~~~~~~~~

**Problem:**

.. code-block:: text

   Warning: Toolchain version mismatch (found 11.2, expected 12.2)

**Solution:**

This is usually fine. If you encounter build issues, specify the toolchain version:

.. code-block:: yaml

   toolchain:
     preferred: arm
     version: "12.2.rel1"

Build Issues
------------

Build Fails with Compilation Errors
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:**

.. code-block:: text

   error: 'struct foo' has no member named 'bar'
   make[1]: *** [scripts/Makefile.build:243: drivers/example.o] Error 1

**Solutions:**

1. **Ensure clean build**:

   .. code-block:: bash

      adibuild linux clean -p zynqmp -t 2023_R2 --deep
      adibuild linux build -p zynqmp -t 2023_R2

2. **Check toolchain compatibility**:

   The kernel may require a specific toolchain version. Use Vivado toolchains or
   ARM GNU 12.2+ for ADI kernels.

3. **Verify kernel tag**:

   Ensure you're using a valid ADI kernel tag:

   .. code-block:: bash

      git ls-remote --tags https://github.com/analogdevicesinc/linux.git

Build is Extremely Slow
~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:**

Build takes over an hour on a modern system.

**Solutions:**

1. **Increase parallel jobs**:

   .. code-block:: bash

      adibuild linux build -p zynqmp -t 2023_R2 -j $(nproc)

2. **Use local SSD** instead of network storage:

   .. code-block:: yaml

      build:
        output_dir: /tmp/build

3. **Use shallow clone** to reduce initial download:

   .. code-block:: yaml

      repository_options:
        depth: 1

Out of Disk Space
~~~~~~~~~~~~~~~~~

**Problem:**

.. code-block:: text

   No space left on device

**Solution:**

The kernel repository and build require ~10 GB. Clean up:

.. code-block:: bash

   # Remove build artifacts
   adibuild linux clean -p zynqmp -t 2023_R2 --deep

   # Remove cached repository (will re-clone on next build)
   rm -rf ~/.adibuild/work/linux

   # Remove downloaded toolchains
   rm -rf ~/.adibuild/toolchains

   # Check disk usage
   du -sh ~/.adibuild

Build Hangs
~~~~~~~~~~~

**Problem:**

Build appears to hang with no progress.

**Solutions:**

1. **Enable verbose output**:

   .. code-block:: bash

      adibuild -vv linux build -p zynqmp -t 2023_R2

2. **Check build log**:

   .. code-block:: bash

      tail -f ~/.adibuild/work/build-arm64.log

3. **Reduce parallel jobs** (might be resource contention):

   .. code-block:: bash

      adibuild linux build -p zynqmp -t 2023_R2 -j 4

Repository Issues
-----------------

Git Clone Fails
~~~~~~~~~~~~~~~

**Problem:**

.. code-block:: text

   fatal: unable to access 'https://github.com/analogdevicesinc/linux.git/':
   Could not resolve host: github.com

**Solutions:**

1. **Check internet connection**:

   .. code-block:: bash

      ping github.com

2. **Use SSH instead of HTTPS** (if you have GitHub SSH keys):

   .. code-block:: yaml

      repository: git@github.com:analogdevicesinc/linux.git

3. **Check proxy settings**:

   .. code-block:: bash

      export https_proxy=http://proxy.example.com:8080

Git Clone is Very Slow
~~~~~~~~~~~~~~~~~~~~~~

**Problem:**

Cloning the kernel repository takes over 30 minutes.

**Solutions:**

1. **Use shallow clone**:

   .. code-block:: yaml

      repository_options:
        depth: 1
        single_branch: true

   This reduces download from ~4 GB to ~500 MB.

2. **Use a faster mirror** (if available):

   .. code-block:: yaml

      repository: https://mirror.example.com/linux.git

Git Tag Not Found
~~~~~~~~~~~~~~~~~

**Problem:**

.. code-block:: text

   fatal: tag '2023_R3' not found

**Solution:**

List available tags:

.. code-block:: bash

   git ls-remote --tags https://github.com/analogdevicesinc/linux.git

Use a valid tag:

.. code-block:: bash

   adibuild linux build -p zynqmp -t 2023_R2

Configuration Issues
--------------------

Configuration File Not Found
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:**

.. code-block:: text

   Error: Configuration file not found: my_config.yaml

**Solution:**

Ensure the path is correct (use absolute path if needed):

.. code-block:: bash

   adibuild --config /full/path/to/my_config.yaml linux build -p zynqmp

Invalid YAML Syntax
~~~~~~~~~~~~~~~~~~~~

**Problem:**

.. code-block:: text

   Error parsing configuration: YAML syntax error at line 15

**Solution:**

Validate YAML syntax:

.. code-block:: bash

   adibuild config validate my_config.yaml

Common YAML errors:

- **Incorrect indentation** (use spaces, not tabs)
- **Missing colons**
- **Unquoted special characters**

Platform Not Found
~~~~~~~~~~~~~~~~~~

**Problem:**

.. code-block:: text

   Error: Platform 'zynqmp' not found in configuration

**Solution:**

Ensure the platform is defined in your configuration:

.. code-block:: yaml

   platforms:
     zynqmp:
       arch: arm64
       # ... other settings

Check available platforms:

.. code-block:: bash

   adibuild config show

Kernel Configuration Issues
----------------------------

menuconfig Fails
~~~~~~~~~~~~~~~~

**Problem:**

.. code-block:: text

   menuconfig requires ncurses library

**Solution:**

Install ncurses development libraries:

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

Configuration Changes Not Applied
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:**

After running ``menuconfig``, changes don't appear in the build.

**Solution:**

The configuration is saved in the repository. Ensure you rebuild:

.. code-block:: bash

   adibuild linux menuconfig -p zynqmp -t 2023_R2
   # Make changes and save
   adibuild linux build -p zynqmp -t 2023_R2

To use a fresh defconfig:

.. code-block:: bash

   adibuild linux configure -p zynqmp -t 2023_R2

Device Tree Issues
------------------

DTB Not Found
~~~~~~~~~~~~~

**Problem:**

.. code-block:: text

   Error: Device tree blob not found: zynqmp-custom.dtb

**Solution:**

1. **Check available DTBs**:

   .. code-block:: bash

      ls ~/.adibuild/work/linux/arch/arm64/boot/dts/xilinx/*.dts

2. **Use correct DTB name** (without path):

   .. code-block:: yaml

      dtbs:
        - zynqmp-zcu102-rev10-ad9361-fmcomms2-3.dtb

3. **Build all DTBs** if unsure:

   .. code-block:: yaml

      dtbs: []  # Empty list builds all

DTB Build Fails
~~~~~~~~~~~~~~~

**Problem:**

.. code-block:: text

   Error: DTC arch/arm64/boot/dts/xilinx/zynqmp-custom.dtb failed

**Solution:**

Check the device tree source for syntax errors:

.. code-block:: bash

   cat ~/.adibuild/work/linux/arch/arm64/boot/dts/xilinx/zynqmp-custom.dts

Enable verbose output:

.. code-block:: bash

   adibuild -vv linux build -p zynqmp -t 2023_R2

Permission Issues
-----------------

Permission Denied
~~~~~~~~~~~~~~~~~

**Problem:**

.. code-block:: text

   PermissionError: [Errno 13] Permission denied: '/opt/build'

**Solution:**

1. **Use user-writable directory**:

   .. code-block:: yaml

      build:
        output_dir: ./build  # Current directory

2. **Fix permissions** (if using system directory):

   .. code-block:: bash

      sudo chown -R $USER:$USER /opt/build

Cannot Write to ~/.adibuild
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:**

.. code-block:: text

   PermissionError: [Errno 13] Permission denied: '/home/user/.adibuild'

**Solution:**

Fix ownership:

.. code-block:: bash

   sudo chown -R $USER:$USER ~/.adibuild

Python/Environment Issues
--------------------------

Python Version Too Old
~~~~~~~~~~~~~~~~~~~~~~

**Problem:**

.. code-block:: text

   ERROR: Python 3.10 or later is required

**Solution:**

Install Python 3.10+:

.. tab-set::

   .. tab-item:: Ubuntu 22.04+

      .. code-block:: bash

         sudo apt install python3.11 python3.11-venv

   .. tab-item:: Ubuntu 20.04

      .. code-block:: bash

         sudo add-apt-repository ppa:deadsnakes/ppa
         sudo apt update
         sudo apt install python3.11 python3.11-venv

   .. tab-item:: Fedora

      .. code-block:: bash

         sudo dnf install python3.11

   .. tab-item:: macOS

      .. code-block:: bash

         brew install python@3.11

Module Not Found
~~~~~~~~~~~~~~~~

**Problem:**

.. code-block:: text

   ModuleNotFoundError: No module named 'click'

**Solution:**

Reinstall pyadi-build:

.. code-block:: bash

   pip install --force-reinstall pyadi-build

For development installations:

.. code-block:: bash

   pip install -e ".[dev]"

Command Not Found
~~~~~~~~~~~~~~~~~

**Problem:**

.. code-block:: bash

   adibuild: command not found

**Solution:**

1. **Check installation**:

   .. code-block:: bash

      pip show pyadi-build

2. **Add to PATH** (user installation):

   .. code-block:: bash

      export PATH="$HOME/.local/bin:$PATH"

3. **Activate virtual environment** (if using venv):

   .. code-block:: bash

      source venv/bin/activate

Documentation Issues
--------------------

Flowgraphs Appear as Code
~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:**

Diagrams and flowcharts in the documentation appear as raw code blocks instead of rendered images when viewing locally.

**Cause:**

Modern browsers block loading Javascript modules from ``file://`` URLs due to Cross-Origin Resource Sharing (CORS) security policies. The diagramming tool (Mermaid.js) uses ES modules.

**Solution:**

View the documentation using a local HTTP server instead of opening ``index.html`` directly:

.. code-block:: bash

   # From the docs/build/html directory
   cd docs/build/html
   python3 -m http.server

Then open http://localhost:8000 in your browser.

Getting More Help
-----------------

Enable Verbose Logging
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   adibuild -vv linux build -p zynqmp -t 2023_R2

Check Log Files
~~~~~~~~~~~~~~~

.. code-block:: bash

   # Build log
   cat ~/.adibuild/work/build-arm64.log

   # Repository operations
   cat ~/.adibuild/work/git.log

Report an Issue
~~~~~~~~~~~~~~~

If you can't resolve the issue, please report it:

1. Visit `GitHub Issues <https://github.com/analogdevicesinc/pyadi-build/issues>`_
2. Include:

   - pyadi-build version (``adibuild --version``)
   - Python version (``python --version``)
   - Operating system
   - Complete error message
   - Build log (``~/.adibuild/work/build-*.log``)

Example issue template:

.. code-block:: text

   **Version**: pyadi-build 0.1.0
   **Python**: 3.11.0
   **OS**: Ubuntu 22.04

   **Problem**: Build fails with...

   **Steps to reproduce**:
   1. adibuild linux build -p zynqmp -t 2023_R2

   **Error message**:
   ```
   [paste error here]
   ```

   **Build log**:
   ```
   [paste relevant log lines]
   ```

Next Steps
----------

- Return to :doc:`quickstart` for basic usage
- Check :doc:`../user-guide/index` for detailed documentation
- See :doc:`../examples/index` for working examples
