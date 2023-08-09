import structlog
import logging
import os
import sys

if sys.stdout.isatty():
    structlog.configure(
        processors=[
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M.%S"),
            structlog.processors.StackInfoRenderer(),
            structlog.dev.ConsoleRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
else:
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

log = structlog.get_logger('ts_probe')

# Get log level from environment variable


def get_log_level():
    VALID_LOG_LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    log_level = os.environ.get('LOG_LEVEL', None)

    if log_level is None:
        return logging.INFO

    if log_level.upper() not in VALID_LOG_LEVELS:
        log.error("Valid levels are: %s" % VALID_LOG_LEVELS)
        raise ValueError("Invalid log level: %s" % log_level)

    return logging.getLevelName(log_level.upper())


log.setLevel(get_log_level())
