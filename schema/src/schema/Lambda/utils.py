import json

import boto3

try:
    from .. import pretty
    dumps = pretty.dumps0
except ImportError:
    dumps = lambda x: json.dumps(x, indent=2)

def region_of_arn(arn):
    return arn.split(":")[3]

def publish(topic_arn, subject, payload):
    boto3.client("sns", region_name=region_of_arn(topic_arn)).publish(
        TopicArn = topic_arn,
        Subject = subject[:100],
        MessageStructure = "json",
        Message = json.dumps({
            "default": dumps(payload),
            "SMS": subject[:140],
            "EMAIL": dumps(payload),
        }),
    )
