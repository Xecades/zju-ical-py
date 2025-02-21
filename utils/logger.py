import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s (%(name)s): %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)


def getLogger(name: str) -> logging.Logger:
    return logging.getLogger(name)
