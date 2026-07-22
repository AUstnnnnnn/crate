from crate.app import CrateApp
from crate.config import load_config


def main() -> None:
    CrateApp(cfg=load_config()).run()


if __name__ == "__main__":
    main()
