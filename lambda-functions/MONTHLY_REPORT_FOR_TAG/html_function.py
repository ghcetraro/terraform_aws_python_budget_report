import json
import boto3
import os
import calendar
import datetime
from datetime import datetime, timedelta
from dateutil import relativedelta
from botocore.exceptions import ClientError

# Function to create styles depending on percent change
def evaluate_change(value):
  if value < -.15:
    text_out = "<td style='text-align: right; padding: 4px; color: Navy; font-weight: bold;'>{:.2%}</td>".format(value)
  elif -.15 <= value < -.10:
    text_out = "<td style='text-align: right; padding: 4px; color: Blue; font-weight: bold;'>{:.2%}</td>".format(value)
  elif -.10 <= value < -.05:
    text_out = "<td style='text-align: right; padding: 4px; color: DodgerBlue; font-weight: bold;'>{:.2%}</td>".format(value)
  elif -.05 <= value < -.02:
    text_out = "<td style='text-align: right; padding: 4px; color: DeepSkyBlue; font-weight: bold;'>{:.2%}</td>".format(value)
  elif -.02 <= value <= .02:
    text_out = "<td style='text-align: right; padding: 4px;'>{:.2%}</td>".format(value)
  elif .02 < value <= .05:
    text_out = "<td style='text-align: right; padding: 4px; color: Orange; font-weight: bold;'>{:.2%}</td>".format(value)
  elif .05 < value <= .10:
    text_out = "<td style='text-align: right; padding: 4px; color: DarkOrange; font-weight: bold;'>{:.2%}</td>".format(value)
  elif .10 < value <= .15:
    text_out = "<td style='text-align: right; padding: 4px; color: OrangeRed; font-weight: bold;'>{:.2%}</td>".format(value)
  elif value > .15:
    text_out = "<td style='text-align: right; padding: 4px; color: Red; font-weight: bold;'>{:.2%}</td>".format(value)
  else:
    text_out = "<td style='text-align: right; padding: 4px;'>{:.2%}</td>".format(value)
  return text_out
#--------------------------------------------------------------------------------------------------
# Compile and send HTML E-mail
def send_report_email(BODY_HTML):
    SENDER = os.environ['SENDER']
    RECIPIENTS = os.environ['RECIPIENTS']
    AWS_REGION = os.environ['AWS_REGION_ENV']
    SUBJECT = "AWS Monthly Cost Report for Selected Accounts"
    # The email body for recipients with non-HTML email clients.
    BODY_TEXT = ("Amazon SES\r\n"
                "An HTML email was sent to this address."
                )

    # The character encoding for the email.
    CHARSET = "UTF-8"
    # Create a new SES resource and specify a region.
    client = boto3.client('ses',region_name=AWS_REGION)
    # Try to send the email.
    try:
        #Provide the contents of the email.
        response = client.send_email(
            Destination={
                'ToAddresses': [
                    RECIPIENTS,
                ],
            },
            Message={
                'Body': {
                    'Html': {
                        'Charset': CHARSET,
                        'Data': BODY_HTML,
                    },
                    'Text': {
                        'Charset': CHARSET,
                        'Data': BODY_TEXT,
                    },
                },
                'Subject': {
                    'Charset': CHARSET,
                    'Data': SUBJECT,
                },
            },
            Source=SENDER,

        )
    # Display an error if something goes wrong.
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])