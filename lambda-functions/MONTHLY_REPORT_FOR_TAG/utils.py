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

#--------------------------------------------------------------------------------------------------
def determinator(month_number):
  today = datetime.now()
  results = (today.replace(day=1) - relativedelta.relativedelta(months=month_number)).strftime('%Y-%m-%d')
  #
  year = datetime.now().replace(day=1).strftime('%Y')
  date_to_compare = year + '-01-01'
  #
  if results == date_to_compare:
    return month_number
  elif results > date_to_compare:
    counter = month_number
    #
    while results != date_to_compare:
      counter += 1
      results = (today.replace(day=1) - relativedelta.relativedelta(months=counter)).strftime('%Y-%m-%d')
    return counter
  else:
    counter = month_number
    #
    while results != date_to_compare:
      counter -= 1
      results = (today.replace(day=1) - relativedelta.relativedelta(months=counter)).strftime('%Y-%m-%d')
    return counter
#--------------------------------------------------------------------------------------------------
#def first_month_ytd(MONTHLY_COST_DATES_ytd = []):
def first_month_ytd(MONTHLY_COST_DATES_ytd):
  counter = 0
  for month in MONTHLY_COST_DATES_ytd:
    if counter == 0:
      return month
#--------------------------------------------------------------------------------------------------
def generates_monthly_dates(MONTHSBACK):
  MONTHLY_COST_DATES = []
  # This generates monthly dates (every 1st and 2nd of the month) going back 180 days
  for x in range(((MONTHSBACK+1)*30), 0, -1):
  #
    if (datetime.now() - timedelta(days = x)).strftime('%d') == '01':
      temp_date = datetime.now() - timedelta(days = x)
      MONTHLY_COST_DATES.append(temp_date.strftime('%Y-%m-%d'))
  #
  return MONTHLY_COST_DATES
#------------------------------------------------------------
def prevdaycost_table(prevMonthCost, currMonthCost):
  if prevMonthCost == 0 and currMonthCost == 0:
    pctfrmprev = 0
  elif prevMonthCost != 0 and currMonthCost != 0:
    pctfrmprev = (currMonthCost / prevMonthCost) - 1
  elif prevMonthCost != 0 and currMonthCost == 0:
    currMonthCost = 0.01
    pctfrmprev = (currMonthCost / prevMonthCost) - 1
  else:
    prevMonthCost = 0.01
    pctfrmprev = (currMonthCost / prevMonthCost) - 1
  #
  return evaluate_change(pctfrmprev)
#------------------------------------------------------------
def formating_cost(cost):
  cost_td = "$ {:,.2f}".format(cost)
  return cost_td
#------------------------------------------------------------
# Function to color rows
def row_color(i_row):
  if (i_row % 2) == 0:
    return "<tr style='background-color: WhiteSmoke;'>"
  else:
    return "<tr>"
#------------------------------------------------------------
def convert_date(date_n):
  date_n = str(date_n)
  date_n = datetime.strptime(date_n, '%Y-%m-%d')
  m = date_n.strftime('%m')
  c = int(m)
  mc = calendar.month_name[c]
  #
  y = date_n.strftime('%Y')
  #
  date_convert= mc + '-' + y
  #
  return date_convert
#------------------------------------------------------------
# convert to int
def represents_int(s):
  s = str(s)
  s = s.replace('%', '')
  s = s.replace(",", "" )
  s = s.replace("$", "" )
  try: 
    if type(s) == str:
      int(s)
  except ValueError:
    b=float(s)
    return b
  else:
    b=float(s)
    return b
#------------------------------------------------------------
def clear(value):
  if type(value) == str:
    a = value.replace("$", " " )
  elif type(value) == float:
    a = value
  else:
    a = value
  return a