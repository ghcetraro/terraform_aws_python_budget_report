import json
import boto3
import os
import calendar
import datetime
from datetime import datetime, timedelta
from dateutil import relativedelta
from botocore.exceptions import ClientError

from get_cost_and_usage import *
from html_function import *
from reports import *
from utils import *

#--------------------------------------------------------------------------------------------------
# year to date, total cost
def year_to_date_total_cost(accountDict, MONTHLY_START_DATE_YTD, MONTHLY_END_DATE, AWS_TAG_KEY, MONTHLY_COST_DATES_YTD, MONTHSBACK, displayList, aws_tag_filter_list):
  #
  mainCostDict = ce_get_costinfo_per_account(accountDict, MONTHLY_START_DATE_YTD, MONTHLY_END_DATE, aws_tag_filter_list, AWS_TAG_KEY)
  mainDailyDict = process_costchanges_per_month(mainCostDict, MONTHLY_COST_DATES_YTD, MONTHSBACK)
  mainDisplayDict = process_costchanges_for_display(mainDailyDict, displayList)
  finalDisplayDict = process_percentchanges_per_day(mainDisplayDict,MONTHLY_COST_DATES_YTD)
  report = create_report_total(finalDisplayDict, displayList)
  #
  value_sum = 0
  for value in report:
    value_sum = value_sum + value
  #  
  return value_sum
#--------------------------------------------------------------------------------------------------
# year to date, services
def year_to_date_services(accountList, MONTHLY_START_DATE_YTD, MONTHLY_END_DATE, accountDict):
  #
  account_numbers = get_linked_accounts(accountList, MONTHLY_START_DATE_YTD, MONTHLY_END_DATE)
  cost_data_Dict = get_cost_data(account_numbers, MONTHLY_START_DATE_YTD, MONTHLY_END_DATE)
  display_cost_data_Dict = restructure_cost_data(cost_data_Dict, account_numbers)
  report = create_report_service(cost_data_Dict, display_cost_data_Dict)
  #
  # obtain total cost year to date with special filter
  #
  return report
#--------------------------------------------------------------------------------------------------
def year_to_date_services_fix(accountList, MONTHLY_START_DATE_YTD, MONTHLY_END_DATE, accountDict, AWS_TAG_KEY, MONTHLY_COST_DATES_YTD, MONTHSBACK_SELECTED, displayList, aws_tag_filter_list): 
  #
  report = year_to_date_services(accountList, MONTHLY_START_DATE_YTD, MONTHLY_END_DATE, accountDict)
  #
  report[0] = year_to_date_total_cost(accountDict, MONTHLY_START_DATE_YTD, MONTHLY_END_DATE, AWS_TAG_KEY, MONTHLY_COST_DATES_YTD, MONTHSBACK_SELECTED, displayList, aws_tag_filter_list)
  #
  return report
#--------------------------------------------------------------------------------------------------
def year_to_date_services_no_tag(matrix_ytd):
  #
  i_row = 0
  rows = len(matrix_ytd)
  #
  for data in matrix_ytd:
    #
    if i_row == 0:
      value = data
      i_row = 1
    else:
      value = value - data
  #
  return value
