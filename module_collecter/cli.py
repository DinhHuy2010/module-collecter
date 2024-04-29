from importlib import import_module

import click

from .core import collect_modules


def print_names(root: str, names: tuple[str, ...]) -> None:
    def print_tree(tree, level):
        prefix = f"{' ' * (level * 4)}- "
        for node, subnodes in tree.items():
            click.echo(prefix + node)
            print_tree(subnodes, level + 1)

    # {root: {name1: {name2: ... ... {name(n): None}}}}
    def build_tree():
        tree = {root: {}}
        for name in sorted(names):
            *parts, last = name.split(".")[1:]
            curr = tree[root]
            for p in parts:
                curr = curr.setdefault(p, {})
            curr[last] = {}
        return tree

    tree = build_tree()

    print_tree(tree, 0)


@click.command()
@click.argument("package")
@click.option("-v", "--verbose", help="Give more output.", is_flag=True)
def main(package: str, verbose: bool):
    """
    import the `PACKAGE`,
    then collect its submodules and report the results.
    """
    click.echo(f"collecting submodules from package: {package!r}")
    if verbose:
        click.echo(f"importing package: {package!r}")
    try:
        module = import_module(package)
    except ImportError as exc:
        click.echo(f"import error from {package!r}: {exc}", err=True)
        return
    resp = collect_modules(module, verbose=verbose)
    if resp.submodules:
        click.echo(f"list of accessible submodules from {resp.origin.__name__!r}:")
        print_names(resp.origin.__name__, tuple(resp.submodules))
    else:
        click.echo(f"no submodules found from {resp.origin.__name__}")


if __name__ == "__main__":
    main()
