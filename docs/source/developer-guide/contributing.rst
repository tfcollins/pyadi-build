Contributing
============

Thank you for your interest in contributing to pyadi-build!

Development Setup
-----------------

Prerequisites
~~~~~~~~~~~~~

- Python 3.10 or later
- Git
- Make (optional, for convenience commands)

Installation
~~~~~~~~~~~~

.. code-block:: bash

   git clone https://github.com/yourusername/pyadi-build.git
   cd pyadi-build
   pip install -e ".[dev]"

Development Workflow
--------------------

Running Tests
~~~~~~~~~~~~~

.. code-block:: bash

   # Run fast unit tests
   nox -s tests

   # Run all tests for all Python versions
   nox

   # Run specific test file
   pytest test/core/test_config.py -v

Code Style
~~~~~~~~~~

We use ``ruff`` for code formatting and linting.

.. code-block:: bash

   # Format code
   nox -s format

   # Check linting
   nox -s lint

   # Type checking
   nox -s typecheck

Before Submitting
~~~~~~~~~~~~~~~~~

1. **Run the test suite**: Ensure all tests pass
2. **Format your code**: Run ``nox -s format``
3. **Check linting**: Run ``nox -s lint``
4. **Update documentation**: If you add features, update docs
5. **Add tests**: New features should include tests
6. **Update CHANGELOG.md**: Add an entry describing your changes

Code Guidelines
---------------

Python Style
~~~~~~~~~~~~

- Follow PEP 8
- Use type hints for function signatures
- Use Google-style docstrings
- Maximum line length: 100 characters

Example:

.. code-block:: python

   def my_function(param1: str, param2: int) -> bool:
       """
       Brief description of function.

       Args:
           param1: Description of param1
           param2: Description of param2

       Returns:
           Description of return value

       Raises:
           ValueError: When something is wrong
       """
       pass

Testing Guidelines
~~~~~~~~~~~~~~~~~~

- Write unit tests for new functionality
- Use mocking for external dependencies
- Aim for >90% code coverage
- Test both success and error cases

Documentation Guidelines
~~~~~~~~~~~~~~~~~~~~~~~~

- Update docstrings for modified functions/classes
- Update user guide for new features
- Add examples for complex functionality
- Keep README.md up to date

Pull Request Process
---------------------

1. **Fork the repository** on GitHub
2. **Create a branch** for your feature or bugfix:

   .. code-block:: bash

      git checkout -b feature/my-new-feature

3. **Make your changes** and commit:

   .. code-block:: bash

      git add .
      git commit -m "Add my new feature"

4. **Push to your fork**:

   .. code-block:: bash

      git push origin feature/my-new-feature

5. **Submit a pull request** on GitHub

6. **Wait for review** and address any feedback

Commit Message Guidelines
~~~~~~~~~~~~~~~~~~~~~~~~~~

- Use clear, descriptive commit messages
- Start with a verb in imperative mood
- Keep first line under 72 characters
- Add detailed description if needed

Examples:

.. code-block:: text

   Add support for custom defconfig
   Fix toolchain detection on macOS
   Update documentation for new platform
   Refactor BuildConfig for better testability

Code Review
-----------

All submissions require review before merging. Reviewers will check:

- Code quality and style
- Test coverage
- Documentation updates
- Breaking changes

Getting Help
------------

- Open an issue on GitHub for questions
- Check existing issues and pull requests
- Review the documentation

License
-------

By contributing, you agree that your contributions will be licensed under the BSD 3-Clause License.

See Also
--------

- :doc:`architecture` - Architecture overview
- :doc:`../api-reference/index` - API reference
- `GitHub Repository <https://github.com/analogdevicesinc/pyadi-build>`_
