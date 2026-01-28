import os
import sys
import traceback

import boto3
import botocore

import logging
logger = logging.getLogger(__name__)

from .. import logconfig, build_info
from . import main
from .utils import publish

def figure_out_log_stream_url(context):
    region = os.environ['AWS_REGION']
    return f"https://{region}.console.aws.amazon.com" \
        + f"/cloudwatch/home?region={region}" \
        + f"#logEventViewer:group={context.log_group_name};stream={context.log_stream_name}"

def report_exception(event, context):
    exc = sys.exception()
    msg = str(exc) or repr(exc)
    subject = f"{context.function_name}: {msg}"
    payload = {
        "exception": repr(exc),
        "traceback": traceback.format_exc().splitlines(),
        "event": event,
        "invocation": {
            "region": os.environ["AWS_REGION"],
            "function_arn": context.invoked_function_arn,
            "aws_request_id": context.aws_request_id,
            "log": {
                "group": context.log_group_name,
                "stream": context.log_stream_name,
                "url": figure_out_log_stream_url(context),
            },
        },
        "build": build_info.to_dict(),
    }
    publish(topic_arn=os.environ["ALERT_SNS_TOPIC_ARN"], subject=subject, payload=payload)

def harness(event, context):
    os.environ["AWS_REQUEST_ID"] = context.aws_request_id

    logconfig.remove_default_logging()
    _, handler = logconfig.setup()

    logger.debug("version: %s", build_info.semver())
    logger.debug("build_info: %s", build_info.to_dict())

    logger.debug("boto3: %s", boto3.__version__)
    logger.debug("botocore: %s", botocore.__version__)

    logger.debug("context: %s", context)
    logger.debug("event: %s", event)

    try:
        main.on_event(event)
    except:
        logger.exception("uncaught exception from harness")
        report_exception(event, context)
        raise
    finally:
        handler.flush()
