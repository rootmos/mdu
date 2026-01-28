import logging
logger = logging.getLogger(__name__)

def on_event(event):
    logger.info("Hello schema world!")
    raise NotImplementedError()
