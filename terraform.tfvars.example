## for terraform
customer    = "devops"
environment = "production"
region      = "us-east-1"

main_region      = "us-east-1"
aws_account      = " "
lambda_role_name = "lambda_role"

# the sender and the recipient cannot be the same otherwise the email is blocked
SENDER     = "nobody_sender@moon.com"
RECIPIENTS = "nobody_reciber@moon.com"

#Provide global defaults for lambda. These defaults can be overwritten by providing the parameter in the desired lambda map
lambda_defaults = {
  # Runtime for the lambda function
  runtime = "python3.11"
  # Handler for the lambda function
  handler = "lambda_function.lambda_handler"
  # Log retention for the lambda function
  cloudwatch_log_retention = "1"
  # Account information for the report
  accountDict = "{ \"<account id>\" : \"poc\" }"
  # Account email information for the report
  accountMailDict = "{ \"<account id>\" : \"poc@moon.com\" }"
  # Display information for the daily or monthTotal report
  displayList = "<account id> dayTotal" # or monthTotal 
  # Enable the fist table presentation in the report
  DISPLAY_BOTH_TABLES = "true"
  # how many days back from today to include in the report
  DAYSBACK = "7"
  # how many months back from today to include in the report
  MONTHSBACK = "7"
  # space separated list of values for the awsTagKey to use as filter 
  aws_tag_filter = "<some tag>"
  # Tag key to use for filter
  AWS_TAG_KEY = "<some aws tag key>"
  #Filter type. Options: TAG or SERVICE
  AWS_FILTER = "TAG"
}

#Tags that are applied to all the created resources
default_tags = {
  #AppFamily      = "Digital"
  AppFamily      = "Store System"
  Application    = "AWS Cost Explorer"
  Name           = "Terraform Deployed"
  TaggingVersion = "0.0.1"
  Environment    = "Staging"
  BusinessImpact = "Critical"
  ContactEmail   = "nobody@moon.com"
  Component      = "AWS Cost Explorer"
}

#Lambda functions to be created with their corresponding configurations.
lambda_deploy = {
  DAILY_REPORT_FOR_SERVICE = {
    # cron for lambda runs every monday at 8.30 am
    cron_schedule_expression = "cron(30 8 ? * 2 *)",
    displayList              = "<aacount id> dayTotal"
    DAYSBACK                 = "8"
  },
  DAILY_REPORT_FOR_TAG = {
    # cron for lambda runs every monday at 8.30 am
    cron_schedule_expression = "cron(30 8 ? * 2 *)",
    aws_tag_filter           = "<aws tags>"
    displayList              = "<aacount id> dayTotal"
    DAYSBACK                 = "8"
  },
  MONTHLY_REPORT_FOR_TAG = {
    # cron for lambda runs every first of the month 8.30 am
    cron_schedule_expression = "cron(30 8 1W * ? *)",
    aws_tag_filter           = "<aws tags>"
    displayList              = "<aacount id> monthTotal"
    MONTHSBACK               = "3"
    #
  },
}