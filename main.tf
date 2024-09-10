########### role

# Policy document for Lambda trust policy
data "aws_iam_policy_document" "assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

#Lambda role
resource "aws_iam_role" "iam_for_lambda" {
  name               = var.lambda_role_name
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
  tags               = local.tags
}

#Attach AWS managed Billing policy to Lambda role
resource "aws_iam_role_policy_attachment" "aws_config_policy_b" {
  role       = aws_iam_role.iam_for_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/job-function/Billing"
  depends_on = [
    aws_iam_role.iam_for_lambda
  ]
}

resource "aws_iam_role_policy_attachment" "aws_policy_vpc" {
  role       = aws_iam_role.iam_for_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
  depends_on = [
    aws_iam_role.iam_for_lambda
  ]
}

resource "aws_iam_role_policy_attachment" "aws_policy_role" {
  role       = aws_iam_role.iam_for_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  depends_on = [
    aws_iam_role.iam_for_lambda
  ]
}

#Policy document to grant Lambda required permissions
data "aws_iam_policy_document" "aws_policy" {
  statement {
    sid    = "DescribeLogStreams"
    effect = "Allow"
    actions = [
      "logs:DescribeLogStreams",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:CreateLogGroup"

    ]
    resources = [
      "arn:aws:logs:${var.region}:${var.aws_account}:log-group:/aws/lambda/DAILY_REPORT_FOR_SERVICE:*",
      "arn:aws:logs:${var.region}:${var.aws_account}:log-group:/aws/lambda/DAILY_REPORT_FOR_TAG:*",
      "arn:aws:logs:${var.region}:${var.aws_account}:log-group:/aws/lambda/MONTHLY_REPORT_FOR_TAG:*",
    ]
  }
  statement {
    sid    = "DescribeCostCategoryDefinition"
    effect = "Allow"
    actions = [
      "ce:DescribeCostCategoryDefinition",
      "ce:GetRightsizingRecommendation",
      "ce:GetCostAndUsage",
      "ce:GetSavingsPlansUtilization",
      "ce:GetAnomalies",
      "ce:GetReservationPurchaseRecommendation",
      "ce:ListCostCategoryDefinitions",
      "ce:GetCostForecast",
      "ce:GetPreferences",
      "ce:GetReservationUtilization",
      "ce:GetCostCategories",
      "ce:GetSavingsPlansPurchaseRecommendation",
      "ce:GetDimensionValues",
      "ce:GetSavingsPlansUtilizationDetails",
      "ce:GetAnomalySubscriptions",
      "ce:GetCostAndUsageWithResources",
      "ce:DescribeReport",
      "ce:GetReservationCoverage",
      "ce:GetSavingsPlansCoverage",
      "ce:GetAnomalyMonitors",
      "ce:DescribeNotificationSubscription",
      "ce:GetTags",
      "ce:GetUsageForecast",
      "ce:GetCostAndUsage"
    ]
    resources = [
      "arn:aws:ce:${var.main_region}:${var.aws_account}:/GetCostAndUsage",
      "arn:aws:ce:${var.main_region}:${var.aws_account}:/GetDimensionValues"
    ]
  }
  statement {
    sid    = "ses"
    effect = "Allow"
    actions = [
      "ses:VerifyEmailIdentity",
      "ses:VerifyEmailAddress",
      "ses:TestRenderTemplate",
      "ses:SendTemplatedEmail",
      "ses:SendEmail"
    ]
    resources = [
      "arn:aws:ses:${var.region}:${var.aws_account}:identity/${var.RECIPIENTS}",
      "arn:aws:ses:${var.region}:${var.aws_account}:identity/${var.SENDER}"
    ]
  }
}

#Policy to grant Lambda required permissions
resource "aws_iam_policy" "aws_policy" {
  name   = var.lambda_role_name
  policy = data.aws_iam_policy_document.aws_policy.json
  tags   = local.tags
}

#Attach custom policy to lambda role
resource "aws_iam_role_policy_attachment" "aws_policy" {
  role       = aws_iam_role.iam_for_lambda.name
  policy_arn = aws_iam_policy.aws_policy.arn
  depends_on = [
    aws_iam_policy.aws_policy
  ]
}
#
####################################################### lambda

data "archive_file" "lambda_code_archive" {
  #Create files for each lambda function
  for_each = var.lambda_deploy
  #
  type        = "zip"
  source_dir  = "lambda-functions/${each.key}"
  output_path = "lambda-functions/${each.key}.zip"
  depends_on = [
    resource.local_file.accountDict,
    resource.local_file.accountMailDict
  ]
}

#Lambda functions
resource "aws_lambda_function" "lambda" {
  #Create 1 lambda function for each tfvar entry
  for_each = var.lambda_deploy
  #
  function_name    = lookup(each.value, "function_name", each.key)
  filename         = data.archive_file.lambda_code_archive[each.key].output_path
  source_code_hash = data.archive_file.lambda_code_archive[each.key].output_base64sha256
  role             = aws_iam_role.iam_for_lambda.arn
  runtime          = lookup(each.value, "runtime", var.lambda_defaults.runtime)
  handler          = lookup(each.value, "handler", var.lambda_defaults.handler)
  timeout          = 30
  #
  environment {
    variables = {
      aws_tag_filter      = lookup(each.value, "aws_tag_filter", var.lambda_defaults.aws_tag_filter)
      displayList         = lookup(each.value, "displayList", var.lambda_defaults.displayList)
      SENDER              = var.SENDER
      RECIPIENTS          = var.RECIPIENTS
      AWS_REGION_ENV      = var.region
      AWS_TAG_KEY         = lookup(each.value, "AWS_TAG_KEY", var.lambda_defaults.AWS_TAG_KEY)
      AWS_FILTER          = lookup(each.value, "AWS_FILTER", var.lambda_defaults.AWS_FILTER)
      DAYSBACK            = lookup(each.value, "DAYSBACK", var.lambda_defaults.DAYSBACK)
      MONTHSBACK          = lookup(each.value, "MONTHSBACK", var.lambda_defaults.MONTHSBACK)
      DISPLAY_BOTH_TABLES = lookup(each.value, "DISPLAY_BOTH_TABLES", var.lambda_defaults.DISPLAY_BOTH_TABLES)
    }
  }
  depends_on = [
    data.archive_file.lambda_code_archive,
    aws_iam_role.iam_for_lambda,
  ]
  tags = local.tags
}

################## cloudwatch

#Scheduled EventBridge rules
resource "aws_cloudwatch_event_rule" "cron" {
  #
  for_each = var.lambda_deploy
  #
  name                = lookup(each.value, "name", each.key)
  description         = "trigger lambda "
  schedule_expression = lookup(each.value, "cron_schedule_expression", null)
  tags                = local.tags
}

#Lambda permission to allow eventbridge to invoke the functions.
resource "aws_lambda_permission" "allow_eventbridge" {
  #
  for_each = var.lambda_deploy
  #
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = lookup(each.value, "function_name", each.key)
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.cron[each.key].arn
  depends_on = [
    aws_cloudwatch_event_rule.cron,
    aws_lambda_function.lambda
  ]
}

#Target each eventbridge rule with the corresponding lambda function 
resource "aws_cloudwatch_event_target" "lambda_target" {
  #
  for_each = var.lambda_deploy
  #
  rule      = lookup(each.value, "function_name", each.key)
  target_id = "SendToLambda"
  arn       = aws_lambda_function.lambda[each.key].arn
  depends_on = [
    aws_lambda_function.lambda
  ]
}

#Provide separate log groups per lambda function
resource "aws_cloudwatch_log_group" "log_group" {
  #
  for_each = var.lambda_deploy
  #
  name              = "/aws/lambda/${each.key}"
  retention_in_days = lookup(each.value, "cloudwatch_log_retention", var.lambda_defaults.cloudwatch_log_retention)
  tags              = local.tags
}

#Manage the SES email notifications
resource "aws_ses_email_identity" "RECIPIENT" {
  email = var.RECIPIENTS
}

resource "aws_ses_email_identity" "SENDER" {
  email = var.SENDER
}

#############################

#File containing the account dictionary information
resource "local_file" "accountDict" {
  #Create one file per lambda function
  for_each = var.lambda_deploy
  #Get the file content from the tfenv variables
  content  = lookup(each.value, "accountDict", var.lambda_defaults.accountDict)
  filename = "${path.module}/lambda-functions/${each.key}/accountDict.txt"
}
#File containing the account mail dictionary information
resource "local_file" "accountMailDict" {
  #Create one file per lambda function
  for_each = var.lambda_deploy
  #Get the file content from the tfenv variables
  content  = lookup(each.value, "accountMailDict", var.lambda_defaults.accountMailDict)
  filename = "${path.module}/lambda-functions/${each.key}/accountMailDict.txt"
}
