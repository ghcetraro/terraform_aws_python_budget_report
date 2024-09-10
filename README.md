# AWS Cost Analysis

This repository is used to install a lambda with a python reporter in aws

For more information please visit [AWS Cost Explorer](https://aws.amazon.com/es/aws-cost-management/aws-cost-explorer/)

### *Terraform Individual Variables*

```
  region                   # aws region
  main_region              # Cost Explorer service is available ONLY in us-east-1 region. 
                           # Hence, value for this variable must be set to us-east-1
  aws_account              # aws account number
  lambda_role_name         # lambda role name
  SENDER                   # SENDER email    
  RECIPIENT                # RECIPIENT email
  default_tags             # aws tags
```

### *Terraform Group Variables*

The different reports will be displayed using Lambda functions that are deployed via this Terraform map variable. Lambda funtions will  maintain the same role and email, but different configuration parameters

```
  lambda_deploy
```

### *Terraform Group Variables Definition*

In order to populate the required parameters to generate the reports, you can use this reference:

  * cron_schedule_expression  = "cron(<Minutes Hours Day-of-month Month Day-of-week Year>)"
  * displayList               = "<aws account number> <dayTotal|monthTotal>"
  * accountDict               = "{ \"<aws account number>\" : \"<account name>\" }"
  * accountMailDict           = "{ \"<aws account number>\" : \"<report receiving email address>\" }"
  * DISPLAY_BOTH_TABLES       = "<true|false>"
  * DAYSBACK                  = "<how many days back from today to include in the report>"
  * MONTHSBACK                = "<how many months back from today to include in the report>"
  * aws_tag_filter            = "<coma separated list of values for the awsTagKey to be used as filters>"                                   
                              * "or put empty string without spaces to show all the tags"
  * AWS_FILTER                = "<TAG|SERVICE>"
  * AWS_TAG_KEY               = "<resource TAG key to use for the filter>"
              
### *Examples for lambda functions*

** DAILY_REPORT_FOR_TAG
```
  DAILY_REPORT_FOR_TAG = {
    cron_schedule_expression  = "cron(45 20 * * ? *)",                   
    accountDict               = "{ \"<aws account number>\" : \"<account name>\" }"
    accountMailDict           = "{ \"<aws account number>\" : \"no-replay@moon.com\" }"                                    
    DAYSBACK                  = "7"                                    
  },
```

** MONTHLY_REPORT_FOR_TAG
```
  MONTHLY_REPORT_FOR_TAG = {
    cron_schedule_expression  = "cron(30 8 1W * ? *)",                   
    aws_tag_filter            = "<value for the awsTagKey to filter>"
    displayList               = "<aws account number>  monthTotal"                                
    MONTHSBACK                = "3"                                     
  },
``` 

** Default values for the lambda functions

  In order to avoid repetitive values, this variables presents the default values to apply to all the lambda functions. These values can be override by adding the same parameter to the lambda definition and provide de desired values.

```
  lambda_defaults = {
    # Runtime for the lambda function
    runtime = "python3.11"

    # Handler for the lambda function
    handler = "lambda_function.lambda_handler"
    
    # Log retention for the lambda function
    cloudwatch_log_retention = "1"
    
    # Account information for the report
    accountDict = "{ \"<aws account number>\" : \"<aws account name>\" }"
    
    # Account email information for the report
    accountMailDict = "{ \"<aws account number>\" : \"<aws account email id>\" }"
    
    # Display information for the daily or monthTotal report
    displayList = "<aws account number> dayTotal"
    
    # Enable the fist table presentation in the report
    DISPLAY_BOTH_TABLES = "false"
    
    # how many days back from today to include in the report
    DAYSBACK = "7"
    
    # how many months back from today to include in the report
    MONTHSBACK = "3"
    
    # coma separated list of values for the awsTagKey to use as filter 
    aws_tag_filter = "<tag names>"
    
    # Tag key to use for filter
    AWS_TAG_KEY = "<tag family>"
    
    # Filter type. Options: TAG or SERVICE
    AWS_FILTER = "TAG" 
}
```
## Running

To run the following scripts, you will need to have ADMIN privileges.

  Following 3 commands need to be executed for every deployment
``` 
  terraform init  
  terraform plan  
  terraform apply  
``` 

## Assumptions

- The script assumes the same identity as the one you have in your _default_ AWS CLI profile.

## Pre-requisites

- Terraform CLI is [installed](https://learn.hashicorp.com/tutorials/terraform/install-cli).
- AWS CLI [installed](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html).

### Required software versions on the client

  - Terraform  
  
    To work with this terraform code it is necessary to have version "1.4.6" of terraform or compatible installed.

  - AWS Cli 
    
    To work with this terraform code it is necessary to have version "2" of aws cli or compatible installed.

## Terraform Scripts
``` 
    locals.tf
    main.tf
    provider.tf
    variables.tf
```

## Pre-Commit

Before commiting the code, run the following commands to validate syntax and formatting of the code.
```
    terraform validate
    terraform fmt -write=true -recursive
```

### Helpers

Terraform provides detailed logs feature that you can enable by setting the TF_LOG environment variable to any value. Allowed values are - TRACE, DEBUG, INFO, WARN or ERROR. Enabling this setting causes detailed logs to appear on stderr.
```
    Bash: 
        export TF_LOG="DEBUG"

    PowerShell: 
        $env:TF_LOG="DEBUG"
```

## Mininal requirements for a script

- **Inmutability as first target**
  
    The script should generate the exact result no matter how many times its executed.

- **Make it work first, we may need to discard it later**

    Some infra changes may change in the future. So the custom scripts should be as specific as possible (instead of generic) because changes may occur in the future.

## Resources

Resources that are going to be deployed to apply the "aws config" service

```
- aws lmabda
- iam roles
- iam policies 
- ses email identity
- cloudwatch event rule
- cloudwatch event target
- cloudwatch log group
```
