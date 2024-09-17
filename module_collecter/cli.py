import builtins
from contextlib import contextmanager
from functools import wraps
from importlib.util import find_spec

import click
from typing_extensions import Any

from module_collecter.core import collect_modules


def print_names(root: str, names: tuple[str, ...]) -> None:
    def print_tree(tree: dict[str, Any], level: int) -> None:
        prefix = f"{' ' * (level * 4)}- "
        for node, subnodes in tree.items():
            click.echo(prefix + node)
            print_tree(subnodes, level + 1)

    # {root: {name1: {name2: ... ... {name(n): None}}}}
    def build_tree() -> dict[str, Any]:
        tree: dict[str, Any] = {root: {}}
        root_len = len(root.split("."))
        for name in sorted(names):
            *parts, last = name.split(".")[root_len:]
            curr = tree[root]
            for p in parts:
                curr = curr.setdefault(p, {})
            curr[last] = {}
        return tree

    tree = build_tree()

    print_tree(tree, 0)


@contextmanager
def patch_print_for_echo():
    original_print = builtins.print

    @wraps(original_print)
    def wrapper(*args: Any, **kwargs: Any):
        out = kwargs.get("sep", " ").join(map(str, args))
        click.echo(out, err=True)

    setattr(builtins, "print", wrapper)
    try:
        yield
    finally:
        setattr(builtins, "print", original_print)


@click.command()
@click.argument("package")
@click.option("-v", "--verbose", help="Give more output.", is_flag=True)
def main(package: str, verbose: bool):
    """
    import the `PACKAGE`,
    then collect its submodules and report the results.
    """
    if verbose:
        click.echo(f"importing package: {package!r}", err=True)
    try:
        module_spec = find_spec(package)
    except ValueError as exc:
        click.echo(f"error on finding spec from {package!r}: {exc}", err=True)
        return
    if module_spec is None:
        click.echo(f"{package!r} not found", err=True)
        return
    if verbose:
        click.echo(f"collecting submodules from package: {package!r}", err=True)
    with patch_print_for_echo():
        resp = collect_modules(module_spec, verbose=verbose)
    origin = resp.origin
    assert origin is not None
    if resp.submodules:
        click.echo(f"list of accessible submodules from {origin.fullname!r}:")
        print_names(origin.fullname, tuple(resp.submodules))
    else:
        click.echo(f"no submodules found from {origin.fullname}")


if __name__ == "__main__":
    main()
