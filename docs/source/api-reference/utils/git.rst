GitRepository
=============

Git repository operations.

.. currentmodule:: adibuild.utils.git

.. autoclass:: GitRepository
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

   .. rubric:: Methods

   .. automethod:: clone
   .. automethod:: update
   .. automethod:: checkout
   .. automethod:: get_current_commit
   .. automethod:: get_current_branch

   .. rubric:: Example Usage

   **Cloning Repository:**

   .. code-block:: python

      from adibuild.utils.git import GitRepository
      from pathlib import Path

      repo = GitRepository('https://github.com/analogdevicesinc/linux.git')

      # Clone to directory
      work_dir = Path('/path/to/work/linux')
      repo.clone(work_dir)

      # Checkout tag
      repo.checkout('2023_R2')

   **Updating Repository:**

   .. code-block:: python

      # Update existing repository
      if work_dir.exists():
          repo.update(work_dir)
      else:
          repo.clone(work_dir)

      repo.checkout('2023_R2')

   **Getting Repository Information:**

   .. code-block:: python

      # Get current commit
      commit = repo.get_current_commit()
      print(f"Current commit: {commit}")

      # Get current branch/tag
      branch = repo.get_current_branch()
      print(f"Current branch: {branch}")

   **Shallow Clone:**

   .. code-block:: python

      # Clone with limited history
      repo = GitRepository(
          'https://github.com/analogdevicesinc/linux.git',
          depth=1,
          single_branch=True
      )
      repo.clone(work_dir)
      repo.checkout('2023_R2')

See Also
--------

- :doc:`../core/builder` - Builder usage
- :doc:`../projects/linux` - LinuxBuilder usage
