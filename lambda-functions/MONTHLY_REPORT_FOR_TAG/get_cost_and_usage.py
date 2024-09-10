import json
import boto3
import os
import calendar
import datetime
from datetime import datetime, timedelta
from dateutil import relativedelta
from botocore.exceptions import ClientError

# Create Cost Explorer service client using saved credentials
cost_explorer = boto3.client('ce')

# Get cost information for accounts defined in accountDict
#
def ce_get_costinfo_per_account(accountDict, MONTHLY_START_DATE, MONTHLY_END_DATE, aws_tag_filter_list, AWS_TAG_KEY):
    #
    accountCostDict = {} # main dictionary of cost info for each account
    #
    for key in accountDict:
        if not aws_tag_filter_list:
          # Retrieve cost and usage metrics for specified account
          response = cost_explorer.get_cost_and_usage(
              TimePeriod={ 'Start': MONTHLY_START_DATE, 'End': MONTHLY_END_DATE }, 
              Granularity='MONTHLY',
                Filter={ 'Dimensions': { 'Key': 'LINKED_ACCOUNT', 'Values': [ key, ]},},   # key is AWS account number
              Metrics=[ 'UnblendedCost', ], )
        else:
          # Retrieve cost and usage metrics for specified account
          response = cost_explorer.get_cost_and_usage(
              TimePeriod={ 'Start': MONTHLY_START_DATE, 'End': MONTHLY_END_DATE }, Granularity='MONTHLY',
              Filter = {'And': [
                            {'Dimensions': {'Key': 'LINKED_ACCOUNT', 'Values': [key,]} },
                            {'Tags': {'Key': AWS_TAG_KEY, 'Values': aws_tag_filter_list } }
                          ]
                        },
              Metrics=[ 'UnblendedCost', ], )
          #
        periodCost = 0      # holder for cost of the account in reporting period
        #
        # Calculate cost of the account in reporting period
        for monthCost in response['ResultsByTime']:
            periodCost = periodCost + float(monthCost['Total']['UnblendedCost']['Amount'])
        print('Cost of account ', key, ' for the period is: ', periodCost )
        #
        # Only include accounts that have non-zero cost in the dictionary
        if periodCost > 0:
            accountCostDict.update({key:response})
    return accountCostDict
    #
#--------------------------------------------------------------------------------------------------
# Get Cost Data from Master Payer Cost Explorer
def get_cost_data(account_numbers, MONTHLY_START_DATE, MONTHLY_END_DATE):

  AWS_TAG_KEY = os.environ['AWS_TAG_KEY']
  AWS_FILTER = os.environ['AWS_FILTER']
  results = []  # holder for service costs
  token = None  # holder for NextPageToken

  while True:

    if token:
      kwargs = {'NextPageToken': token}   # get the NextPageToken

    else:
      kwargs = {} # empty if the NextPageToken doesn' exist

    data = cost_explorer.get_cost_and_usage(

      # Monthly cost and grouped by Account and Service
      TimePeriod={'Start': MONTHLY_START_DATE, 'End': MONTHLY_END_DATE},
      Granularity='MONTHLY',
      Metrics=['UnblendedCost'],
      GroupBy=[
        {'Type': 'DIMENSION', 'Key': 'LINKED_ACCOUNT'},
        {'Type': AWS_FILTER, 'Key': AWS_TAG_KEY}
      ],

      # Filter using active accounts listed in MEDaily Spend View
       Filter = 
              {'Dimensions': {'Key': 'LINKED_ACCOUNT', 'Values': account_numbers} },
              **kwargs)

    results += data['ResultsByTime']
    token = data.get('NextPageToken')
    if not token:
      break

  return results
#--------------------------------------------------------------------------------------------------
def process_percentchanges_per_day(reportCostDict, MONTHLY_COST_DATES):
    period = len(MONTHLY_COST_DATES)
    i = 0
    # Calculate the delta percent change; add Change:Percent key value pair to daily dictionary
    while i < period:
        # No percentage delta calculation for first day
        if i == 0:
            for account in reportCostDict[MONTHLY_COST_DATES[i]]:
                reportCostDict[MONTHLY_COST_DATES[i]][account].update({'percentDelta':None})
        if i > 0:
            for account in reportCostDict[MONTHLY_COST_DATES[i]]:
                try:
                    #percentDelta = 0.0      # daily percent change holder for each account cost
                    percentDelta = 0      # daily percent change holder for each account cost
                    currentMonthCost = round(reportCostDict[MONTHLY_COST_DATES[i]][account]['Cost'], 2)
                    prevMonthCost = round(reportCostDict[MONTHLY_COST_DATES[i-1]][account]['Cost'], 2)
                    #
                    if(currentMonthCost != prevMonthCost):
                        percentDelta = currentMonthCost / prevMonthCost -1
                    reportCostDict[MONTHLY_COST_DATES[i]][account].update({'percentDelta':percentDelta})
                except ZeroDivisionError:
                    if prevMonthCost == 0 and currentMonthCost != 0:
                        percentDelta = currentMonthCost / 0.01 -1
                        # update percent
                        reportCostDict[MONTHLY_COST_DATES[i]][account].update({'percentDelta':percentDelta})
                    else:
                        reportCostDict[MONTHLY_COST_DATES[i]][account].update({'percentDelta':None})
                        print('ERROR: Division by Zero')
        i += 1
    return reportCostDict
#--------------------------------------------------------------------------------------------------
# Get Linked Account Dimension values from Master Payer Cost Explorer
def get_linked_accounts(accountList, MONTHLY_START_DATE, MONTHLY_END_DATE):

  results = []  # holder for full linked account results
  token = None  # holder for NextPageToken

  while True:

    if token:
      kwargs = {'NextPageToken': token}   # get the NextPageToken
    else:
      kwargs = {} # empty if the NextPageToken does not exist

    linked_accounts = cost_explorer.get_dimension_values(

            # Get all linked account numbers in the time period requested
            TimePeriod={'Start': MONTHLY_START_DATE, 'End': MONTHLY_END_DATE},
            Dimension='LINKED_ACCOUNT',
            **kwargs
        )

    # Save results - active accounts in time period
    results += linked_accounts['DimensionValues']
    token = linked_accounts.get('NextPageToken')
    if not token:
      break

  active_accounts = []  # holder for just linked account numbers
  defined_accounts = [] # holder for reporting accounts

  for accountnumbers in results:
    active_accounts.append(accountnumbers['Value'])

  # use account number for report if it exists in dimension values
  for accountnumbers in accountList:
    if accountnumbers in active_accounts:
      defined_accounts.append(accountnumbers)

  return defined_accounts
#--------------------------------------------------------------------------------------------------
def restructure_cost_data(cost_data_Dict, account_numbers):
  #
  display_cost_data_Dict = {}             # holder for restructured dictionary for e-mail/display
  sorted_display_cost_data_Dict = {}      # holder for sorted dictionary for e-mail/display
  #
  # use account numbers as main dictionary keys
  for account in account_numbers:
    display_cost_data_Dict.update({account: {}})
  #
  # use service names as second dictionary keys
  for timeperiods in cost_data_Dict:

    for cost in timeperiods['Groups']:
      account_no = cost['Keys'][0]      # Account Number
      account_name = cost['Keys'][1]        # Service Name
      try:
        display_cost_data_Dict[account_no].update({account_name: {}})
      except:
        continue
  #
  # for each service, save costs per period
  for timeperiods in cost_data_Dict:
    date = timeperiods['TimePeriod']['Start']
    for cost in timeperiods['Groups']:
      account_no = cost['Keys'][0]                          # Account Number
      account_name = cost['Keys'][1]                            # Service Name
      amount = cost['Metrics']['UnblendedCost']['Amount']       # Period Cost
      try:
        display_cost_data_Dict[account_no][account_name].update({date: amount})
      except:
        continue
  #
  # sort the dictionary (per service) for each account
  for accounts in display_cost_data_Dict:
      sorted_display_cost_data_Dict.update({accounts:{}})
      sorted_display_cost_data_Dict[accounts].update(sorted(display_cost_data_Dict[accounts].items()))
  #
  #return display_cost_data_Dict
  return sorted_display_cost_data_Dict
#--------------------------------------------------------------------------------------------------
# Create new dictionary and process totals for the reporting period
def process_costchanges_per_month(accountCostDict, MONTHLY_COST_DATES, MONTHSBACK):
    #
    reportCostDict = {} # main dictionary for displaying cost
    reportCostDict2 = {} # main dictionary for displaying cost with 1st of month removed
    period = MONTHSBACK
    i = 0
    #
    for x in range(((period+1)*30), 0, -1):
        if (datetime.now() - timedelta(days = x)).strftime('%d') == '01':
            reportMonth = datetime.now() - timedelta(days = x)
            reportCostDict.update({reportMonth.strftime('%Y-%m-%d'):None})
            reportCostDict[reportMonth.strftime('%Y-%m-%d')] = {}
    #
    # Fill up each daily dictionary with Account:Cost key value pairs
    for key in accountCostDict:
        for monthCost in accountCostDict[key]['ResultsByTime']:
            reportCostDict[monthCost['TimePeriod']['Start']].update(
                {key: {'Cost': float(monthCost['Total']['UnblendedCost']['Amount'])}}
            )
    # Get the total cost for each reporting day
    for key in reportCostDict:
        monthTotal = 0      # holder for total cost every key; key is the reporting month

        for account in reportCostDict[key]:
            monthTotal = monthTotal + reportCostDict[key][account]['Cost']
        reportCostDict[key].update({'monthTotal': {'Cost': monthTotal}})
    #
    # Create a new dictionary with just the dates specified in MONTHLY_COST_DATES
    for month in MONTHLY_COST_DATES:
        reportCostDict2.update({month:reportCostDict[month]})
    #
    return reportCostDict2
#--------------------------------------------------------------------------------------------------
# Create new dictionary for displaying/e-mailing the reporting period
# This takes the existing dictionary, displays accounts in displayList, and totals the
#   other accounts in Others.

def process_costchanges_for_display(reportCostDict, displayList):
    displayReportCostDict = {}      # holder for new dictionary
    for reportMonth in reportCostDict:
        displayReportCostDict.update({reportMonth: None})
        displayReportCostDict[reportMonth] = {}

        #otherAccounts = 0.0     # holder for total cost in other accounts
        otherAccounts = 0     # holder for total cost in other accounts
        # Loop through accounts. Note that dayTotal is listed in displayList
        for accountNum in reportCostDict[reportMonth]:
            # Only add account if in displayList; add everything else in Others
            if accountNum in displayList:
                displayReportCostDict[reportMonth].update(
                    {accountNum: reportCostDict[reportMonth][accountNum]}
                )
            else:
                otherAccounts = otherAccounts + reportCostDict[reportMonth][accountNum]['Cost']

        # Enter total for 'Others' in the dictionary
        displayReportCostDict[reportMonth].update({'Others': {'Cost': otherAccounts}})
    return displayReportCostDict