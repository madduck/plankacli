import logging
import click

FORMAT = (
    "%(asctime)s %(levelname)-8s %(message)s "
    "(%(filename)s:%(lineno)d, logger: %(name)s)"
)
DATEFMT = "%F %T"

logging.TRACE = logging.DEBUG - 1
logging.addLevelName(logging.TRACE, "TRACE")


def _trace(self, msg, *args, **kwargs):
    return self.log(logging.TRACE, msg, *args, stacklevel=2, **kwargs)


logging.trace = _trace


class LoggerWithTrace(logging.Logger):
    trace = _trace


logging.setLoggerClass(LoggerWithTrace)


class ClickStyleFormatter(logging.Formatter):

    STYLES = {
        logging.TRACE: {"fg": "bright_cyan"},
        logging.DEBUG: {"fg": "cyan"},
        logging.INFO: {},
        logging.WARNING: {"fg": "black", "bg": "bright_yellow"},
        logging.ERROR: {"fg": "white", "bg": "bright_red", "bold": True},
        logging.CRITICAL: {
            "fg": "bright_yellow",
            "bg": "bright_red",
            "bold": True,
            "blink": True,
        },
    }

    def format(self, record):
        style = self.STYLES.get(record.levelno, {})
        message = super().format(record)
        return click.style(message, **style)


class ClickEchoHandler(logging.StreamHandler):
    def emit(self, record):
        msg = self.format(record)
        click.echo(msg + self.terminator, nl=False, file=self.stream)


def get_logger(
    name=None,
    level=logging.WARNING,
    fmt=FORMAT,
    datefmt=DATEFMT,
    propagate=False,
):

    if name is None:
        streamhandler = ClickEchoHandler()
        streamhandler.setFormatter(
            ClickStyleFormatter(
                fmt=fmt,
                datefmt=datefmt,
            )
        )

        logger = logging.getLogger(None)  # root logger
        logger.setLevel(level)
        logger.addHandler(streamhandler)

    else:
        logger = logging.getLogger(name)
        logger.setLevel(logging.NOTSET)

    return logger


def log_level_from_cli(logger, verbosity, *, quiet=False):

    if quiet:
        loglevel = logging.ERROR
    elif verbosity >= 3:
        loglevel = logging.DEBUG - verbosity + 2
    else:
        loglevel = logging.WARNING - verbosity * 10

    if loglevel <= logging.NOTSET:
        logger.warning("Log level at or below NOTSET")

    logger.setLevel(loglevel)


class IncludeExtraInfoAdapter(logging.LoggerAdapter):

    def process(self, msg, kwargs):
        if self.extra:
            return super().process(f"{msg} [{self.extra}]", kwargs)
        else:
            return super().process(msg, kwargs)
