try:
    from module_collecter.cli import main  # type: ignore
except ImportError:

    def main() -> None:
        from textwrap import dedent

        print(
            dedent("""NOTE: The CLI part is not installed.
            Install the CLI via: pip install module-collecter[cli]
            """)
        )


if __name__ == "__main__":
    main()
