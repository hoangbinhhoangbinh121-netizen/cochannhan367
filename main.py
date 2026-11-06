import logging
import logging.handlers

from config import Settings
from core.bot import CCNBot


def setup_logging(settings: Settings) -> None:
    settings.log_dir.mkdir(parents=True, exist_ok=True)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    console = logging.StreamHandler()
    console.setFormatter(fmt)
    root.addHandler(console)
    for name, fname in (("ccn", "bot.log"), ("ccn.admin", "admin.log")):
        h = logging.handlers.RotatingFileHandler(settings.log_dir / fname, maxBytes=5_000_000, backupCount=5, encoding="utf-8")
        h.setFormatter(fmt)
        logging.getLogger(name).addHandler(h)


def main() -> None:
    settings = Settings.load()
    setup_logging(settings)
    CCNBot(settings).run(settings.token, log_handler=None)


if __name__ == "__main__":
    main()
