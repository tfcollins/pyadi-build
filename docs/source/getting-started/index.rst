Getting Started
===============

Welcome to pyadi-build! This section will help you get up and running quickly.

.. grid:: 2
   :gutter: 3

   .. grid-item-card:: Installation
      :link: installation
      :link-type: doc
      :text-align: center

      :octicon:`download;2em`

      Install pyadi-build on your system

   .. grid-item-card:: Quick Start
      :link: quickstart
      :link-type: doc
      :text-align: center

      :octicon:`zap;2em`

      Run your first build in minutes

   .. grid-item-card:: First Build
      :link: first-build
      :link-type: doc
      :text-align: center

      :octicon:`rocket;2em`

      Detailed walkthrough of your first kernel build

   .. grid-item-card:: Configuration Basics
      :link: configuration-basics
      :link-type: doc
      :text-align: center

      :octicon:`gear;2em`

      Learn essential configuration concepts

.. grid:: 2
   :gutter: 3

   .. grid-item-card:: Troubleshooting
      :link: troubleshooting
      :link-type: doc
      :text-align: center

      :octicon:`tools;2em`

      Common issues and solutions

What You'll Learn
-----------------

In this section, you will learn:

1. **Installation** - How to install pyadi-build using pip or from source
2. **Quick Start** - Run your first build with minimal setup
3. **First Build** - A detailed walkthrough of building a kernel
4. **Configuration Basics** - Understanding YAML configuration files
5. **Troubleshooting** - Solving common issues

Prerequisites
-------------

Before you begin, ensure you have:

- **Python 3.10 or later**
- **Git** - For cloning kernel repositories
- **Make** - For building the kernel
- **Internet connection** - For downloading toolchains and repositories

Optional but recommended:

- **ncurses libraries** - For ``menuconfig`` support
- **Xilinx Vivado/Vitis** - For Vivado-bundled toolchains (or use auto-download)

Next Steps
----------

Ready to get started? Begin with :doc:`installation` to install pyadi-build.

.. toctree::
   :maxdepth: 2
   :hidden:

   installation
   quickstart
   first-build
   configuration-basics
   troubleshooting
