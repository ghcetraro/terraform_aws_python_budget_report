import json
import boto3
import os
import calendar
import datetime
from datetime import datetime, timedelta
from dateutil import relativedelta
from botocore.exceptions import ClientError

from utils import *
from html import *

#------------------------------------------------------------
def create_report_total(emailDisplayDict,displayList):
  i_row = 0 
  arr_totals = []
  #
  for reportMonth in emailDisplayDict:
    for accountNum in displayList:
      if i_row == 0:
        arr_totals.append(round(emailDisplayDict[reportMonth]['monthTotal']['Cost'],2))
        i_row += 1
      else:
        i_row = 0
  return arr_totals
#------------------------------------------------------------
def create_report_total_percent(emailDisplayDict,displayList):
  i_row = 0 
  arr_totals_percent = []
  #
  for reportMonth in emailDisplayDict:
    for accountNum in displayList:
      if i_row == 0:
        if emailDisplayDict[reportMonth]['monthTotal']['percentDelta'] == None:
          arr_totals_percent.append(evaluate_change(0))
        else:
          arr_totals_percent.append(evaluate_change(emailDisplayDict[reportMonth]['monthTotal']['percentDelta']))
        i_row += 1
      else:
        i_row = 0
  return arr_totals_percent
#------------------------------------------------------------
def create_report_service(cost_data_Dict, display_cost_data_Dict):
  #
  for accounts in display_cost_data_Dict:
  #
    matrix = []
    #
    i_row = 0
    for service in display_cost_data_Dict[accounts]:
      value = 0
      for timeperiods in cost_data_Dict:
        #
        date = timeperiods['TimePeriod']['Start']
        try:
          cost_td = round(float(display_cost_data_Dict[accounts][service][date]),2)
        except:
          cost_td = 0
        #
        value = value + cost_td
      #
      matrix.append(value)
      i_row += 1
  #
  return matrix
#--------------------------------------------------------------------------------------------------
#
def projected_year(last_month, last_value, year_to_date):
  date_n = str(last_month)
  date_n = datetime.strptime(date_n, '%Y-%m-%d')
  m = date_n.strftime('%m')
  c = int(m)
  #
  months_left = 12 - c
  #
  last_value = represents_int(last_value)
  projected_month = year_to_date + last_value * months_left
  #
  return projected_month