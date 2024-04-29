# module-collector - Collect submodules from a package

## Overview

`module-collector` is a tool designed to automatically collect submodules from a specified Python package. This tool is available as both a CLI and API.

## Installation

```text
pip install module-collector
```

## Usage

### CLI Usage

```text
Usage: module-collecter [OPTIONS] PACKAGE
  import the `PACKAGE`, then collect its submodules and report the results.

Options:
  -v, --verbose  Give more output.
  --help         Show this message and exit.
```

### API Usage

```python
from module_collecter import collect_modules
# replace <ModuleType> with a module object
# (e.g. imported via `import` or `importlib.import_module`)
resp = collect_modules(<ModuleType>)
# returns ModuleCollecterResult.
print(resp.submodules) # dict[str, ModuleType]
```

## Contributing

Contributions are welcome! Please feel free to fork the repository, make changes, and submit pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

If you encounter any issues or have questions, please open an issue on the project's GitHub page.
