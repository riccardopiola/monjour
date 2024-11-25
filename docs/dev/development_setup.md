# Development setup

### Setup

To contribute to Monjour, start by cloning the repository in a subdirectory

`git clone https://github.com/riccardopiola/monjour.git`

> It is recommended to create a virtual environment at this point

The development dependencies are stored in `requirements.txt`

`pip install -r requirements.txt`

### Adding a new dependency

1. Add the dependency to `pyproject.toml` in the `dependencies` field or `project.optional-dependencies.st` if it is streamlit-only
2. Run `pip-compile --extra=dev --extra=st pyproject.toml` to regenerate `requirements.txt`
3. Re-run `pip install -r requirements.txt` to download and install the new dependency
