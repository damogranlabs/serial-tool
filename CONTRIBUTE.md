# Contribute

## Setup Development Environment
1. Ensure Python 3.11 is available on your machine.
2. Create local checkout of this repository, for example in a folder named */serial_tool*.
3. Navigate to this folder.
4. Prepare virtual environment with python 3.11: `python -m venv venv`
5. Activate environment.
6. Update `pip`: `python -m pip install -U pip`.
7. Install package in editable mode, while supplying `[dev]` argument:
   ```
    python -m pip install -e .[dev] 
    ```
8. Install `pre-commit` hook:
    ```
    pre-commit install
    ```

**Notes:**
1. All settings are available in *pyproject.toml*. Avoid adding any other cfg files if possible.
2. For new functionalities, tests are mandatory. Current state without test is a painful legacy.
3. Pylint is disabled in pre-commit, as there is just to many warnings. However, inspect issues before commiting anything.

## Scripts
... are available in *./scripts* directory. Windows users only, but the commands should be easily ported to any platform.

## VS Code workspace
VS Code workspace is available with already configured pytest/black/pylint actions.

