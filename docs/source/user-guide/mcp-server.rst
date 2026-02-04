MCP Server
==========

pyadi-build includes a Model Context Protocol (MCP) server that allows AI agents and other tools to interact with the build system programmatically.

What is MCP?
------------

The `Model Context Protocol (MCP) <https://modelcontextprotocol.io/>`_ is an open standard that enables AI models to interact with external tools and data. By running the pyadi-build MCP server, you can allow AI assistants (like Claude or Gemini) to:

- List available platforms
- Build HDL projects
- Build Linux kernels
- Retrieve version information

Installation
------------

To use the MCP server, you need to install the optional dependencies:

.. code-block:: bash

   pip install "pyadi-build[mcp]"

Or install ``fastmcp`` manually:

.. code-block:: bash

   pip install fastmcp

Starting the Server
-------------------

You can start the MCP server using the CLI:

.. code-block:: bash

   adibuild mcp

This will start the server and print instructions on how to connect to it. Typically, you would configure your MCP client (like an AI assistant app) to run this command.

Available Tools
---------------

The MCP server exposes the following tools:

get_version
~~~~~~~~~~~
Returns the current version of pyadi-build.

list_platforms
~~~~~~~~~~~~~~
Lists available platforms defined in the configuration.

build_hdl_project
~~~~~~~~~~~~~~~~~
Builds an HDL project for a specific project/carrier combination.

**Parameters:**

- ``project`` (string): HDL project name (e.g., ``fmcomms2``)
- ``carrier`` (string): Carrier board name (e.g., ``zed``)
- ``arch`` (string, optional): Architecture (default: ``unknown``)
- ``clean`` (boolean, optional): Whether to clean before building (default: ``False``)

build_linux_platform
~~~~~~~~~~~~~~~~~~~~
Builds the Linux kernel for a specific platform.

**Parameters:**

- ``platform`` (string): Target platform (e.g., ``zynq``, ``zynqmp``)
- ``config_path`` (string, optional): Path to a custom configuration file
- ``clean`` (boolean, optional): Whether to clean before building (default: ``False``)

Usage with AI Clients
---------------------

To use this with an MCP-compliant AI client, add the following configuration to your client's settings:

.. code-block:: json

   {
     "mcpServers": {
       "pyadi-build": {
         "command": "adibuild",
         "args": ["mcp"]
       }
     }
   }

Once connected, you can ask the AI to perform tasks like:

- "Build the HDL project for fmcomms2 on zedboard"
- "Compile the Linux kernel for ZynqMP"
- "List all available build platforms"
