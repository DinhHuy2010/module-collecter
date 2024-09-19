import builtins
import os
from contextlib import contextmanager
from functools import partial, wraps
from importlib.util import find_spec

import click
import colorama
import more_itertools
import sty
from typing_extensions import Any, Iterable

from module_collecter.core import collect_modules

_echo = None
_echo_via_pager = None
_ef = sty.EfRegister()
_fg = sty.FgRegister()
_rs = sty.RsRegister()


def print_names(root: str, names: tuple[str, ...], no_pretty: bool, no_color: bool) -> None:
    def render_pretty() -> Iterable[str]:
        yield f"List of accessible submodules from {_ef.bold}{_fg.green}{root}{_rs.all}:\n"
        sorted_names = sorted(names)
        for _, is_last, item in more_itertools.mark_ends(sorted_names):
            if item == root:
                indent_level = 0
                entry = item
            else:
                parts = item[len(root) :].split(".")
                indent_level = len(parts) - 1
                entry = parts[-1]
            yield f"{' ' * (indent_level * 4)}{_ef.bold}- {_fg.blue}{entry}{_rs.all}"
            if not is_last:
                yield "\n"

    def render_no_pretty() -> Iterable[str]:
        yield f"List of accessible submodules from {root}:\n"
        sorted_names = sorted(names)
        for _, is_last, item in more_itertools.mark_ends(sorted_names):
            yield item
            if not is_last:
                yield "\n"

    render = render_no_pretty if no_pretty else render_pretty
    if no_color:
        sty.mute(_ef, _fg, _rs)

    try:
        if _echo_via_pager:
            _echo_via_pager(render())
    finally:
        if no_color:
            sty.unmute(_ef, _fg, _rs)


@contextmanager
def patch_print_for_echo():
    original_print = builtins.print

    @wraps(original_print)
    def wrapper(*args: Any, **kwargs: Any):
        out = kwargs.get("sep", " ").join(map(str, args))
        if _echo:
            _echo(out, err=True)

    setattr(builtins, "print", wrapper)
    try:
        yield
    finally:
        setattr(builtins, "print", original_print)


def _actual_main(package: str, verbose: bool, no_pretty: bool, no_color: bool):
    assert _echo is not None and _echo_via_pager is not None
    if verbose:
        _echo(f"importing package: {package!r}", err=True)
    try:
        module_spec = find_spec(package)
    except ValueError as exc:
        _echo(f"error on finding spec from {package!r}: {exc}", err=True)
        return
    if module_spec is None:
        _echo(f"{package!r} not found", err=True)
        return
    if verbose:
        _echo(f"collecting submodules from package: {package!r}", err=True)
    with patch_print_for_echo():
        resp = collect_modules(module_spec, verbose=verbose)
    origin = resp.origin
    assert origin is not None
    if resp.submodules:
        print_names(origin.fullname, tuple(resp.submodules), no_pretty, no_color)
    else:
        _echo(f"No submodules found from {origin.fullname}")


@click.command()
@click.argument("package")
@click.option("-v", "--verbose", help="Give more output.", is_flag=True)
@click.option("--no-color", help="No color output", is_flag=True)
@click.option("--no-pager", help="No pager", is_flag=True)
@click.option("--no-pretty", help="No pretty output", is_flag=True)
def main(package: str, verbose: bool, no_color: bool, no_pager: bool, no_pretty: bool):
    """
    import the `PACKAGE`,
    then collect its submodules and report the results.
    """
    global _echo, _echo_via_pager
    if no_pager:
        os.environ["TERM"] = "dumb"
    color = not (no_color or bool(os.environ.get("NO_COLOR"))) or not no_pretty
    _echo = partial(click.echo, color=color)
    _echo_via_pager = partial(click.echo_via_pager, color=color)
    with colorama.colorama_text(convert=color, strip=not color):
        _actual_main(package, verbose, no_pretty, no_color)


if __name__ == "__main__":
    main()
