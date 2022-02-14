"""LLAMA package."""
import logging

import sentry_sdk

from llama.config import Config

CONFIG = Config()

if CONFIG.LOG_LEVEL:
    logging.basicConfig(level=getattr(logging, CONFIG.LOG_LEVEL.upper()))
else:
    logging.basicConfig(level=getattr(logging, "INFO"))
logger = logging.getLogger(__name__)
logger.info("Logging configured with level=%s", CONFIG.LOG_LEVEL or "INFO")

if CONFIG.SENTRY_DSN:
    sentry_sdk.init(CONFIG.SENTRY_DSN, environment=CONFIG.ENV)
    logger.info(
        "Sentry initialized with DSN=%s and env=%s", CONFIG.SENTRY_DSN, CONFIG.ENV
    )
else:
    logger.info("No Sentry DSN configured, not initializing Sentry")
