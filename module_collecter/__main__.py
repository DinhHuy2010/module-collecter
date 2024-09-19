try:
    from module_collecter.cli import main  # type: ignore
except ImportError:

    def main() -> None:
        print("NOTE: The CLI part is not installed.")
        print("Install the CLI via: pip install module-collecter[cli]")


if __name__ == "__main__":
    main()
