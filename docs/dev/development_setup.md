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

### Hot realoading of the streamlit app

If you are developing using the streamlit interface, you might want to enable streamlit hot realoading whever you modify a file anywhere in the `monjour` package. This can be achieved by adding the repo root directory to the PYTHONPATH environment variable before running monjour

On posix systems run this from the root directory after you entered the virtual environment:
```sh
PYTHONPATH="$PYTHONPATH;$(pwd)"
```

On windows (powershell)
```poweshell
$env:PYTHONPATH="$env:PYTHONPATH;$(pwd).Path"
```

On windows (cmd)
```batch
set PYTHONPATH=%PYTHONPATH%;%~dp0
```
