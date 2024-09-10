# Daily Cost Reporting using Lambda function

import json
import boto3
import os
from datetime import datetime, timedelta
from botocore.exceptions import ClientError

# Create Cost Explorer service client using saved credentials
cost_explorer = boto3.client('ce')

# variable for total costs
arr_totals = []
arr_totals_percent = []

#--------------------------------------------------------------------------------------------------
# Reporting periods

DAYSBACK = int(os.environ['DAYSBACK'])

# add 1 for the last colum
COLUMNS = DAYSBACK * 2 +1
START_DATE = (datetime.now() - timedelta(days = DAYSBACK)).strftime('%Y-%m-%d')
END_DATE = (datetime.now()).strftime('%Y-%m-%d')
YESTERDAY = (datetime.now() - timedelta(days = 1)).strftime('%Y-%m-%d')

DAILY_COST_DATES = [] # holder for dates used in daily cost changes

for x in range(DAYSBACK+1, 1, -1):

    # This generates dates from 8 days back to yesterday
    temp_date = datetime.now() - timedelta(days = x-1)
    DAILY_COST_DATES.append(temp_date.strftime('%Y-%m-%d'))

MONTHLY_COST_DATES = [] # holder for dates used in monthly cost changes (every 1st of the month)
MONTHLY_COST_DATES2 = [] # holder for dates used in monthly cost changes (every 2nd of the month)

# This generates monthly dates (every 1st and 2nd of the month) going back 180 days
for x in range(180, 0, -1):

    if (datetime.now() - timedelta(days = x)).strftime('%d') == '01':
        temp_date = datetime.now() - timedelta(days = x)
        MONTHLY_COST_DATES.append(temp_date.strftime('%Y-%m-%d'))

        temp_date = datetime.now() - timedelta(days = x-1)
        MONTHLY_COST_DATES2.append(temp_date.strftime('%Y-%m-%d'))

BODY_HTML = '<h2>AWS Daily Cost Report for Accounts - Summary</h2>'

#--------------------------------------------------------------------------------------------------
# Tuple for all the accounts listed in MEDailySpendView settings

with open('accountMailDict.txt') as f:
    data_a = f.read()
accountMailDict = json.loads(data_a)

# Dictionary of named accounts

with open('accountDict.txt') as f:
    data_b = f.read()
accountDict = json.loads(data_b)

# Create an account list based on dictionary keys
accountList = []
for key in accountDict.keys():
    accountList.append(key)

# This list controls the number of accounts to have detailed report
# Accounts not listed here will be added to "Others". DO NOT remove 'Others' and 'dayTotal'

displayList_list = os.environ['displayList']
displayList = displayList_list.split()

# Get cost information for accounts defined in accountDict

def ce_get_costinfo_per_account(accountDict_input):
    
    aws_tag_filter_list = os.environ['aws_tag_filter'].split(",") if os.environ['aws_tag_filter'] else []

    AWS_TAG_KEY = os.environ['AWS_TAG_KEY']
    accountCostDict = {} # main dictionary of cost info for each account

    for key in accountDict_input:
        # if aws_tag_filter_list is empty
        if not aws_tag_filter_list: 
            #
            # Retrieve cost and usage metrics for specified account
            response = cost_explorer.get_cost_and_usage(
                TimePeriod={
                    'Start': START_DATE,
                    'End': END_DATE
                },
                Granularity='DAILY',
                Filter={
                    'Dimensions': {
                        'Key': 'LINKED_ACCOUNT',
                        'Values': [
                            key,    # key is AWS account number
                        ]
                    },
                },
                Metrics=[
                    'UnblendedCost',
                ],
            )
        else:
          # Retrieve cost and usage metrics for specified account
          response = cost_explorer.get_cost_and_usage(
              TimePeriod={
                  'Start': START_DATE,
                  'End': END_DATE
              },
              Granularity='DAILY',
              Filter = {'And': [
                            {'Dimensions': 
                              {'Key': 'LINKED_ACCOUNT', 'Values': [key,]}
                            },
                            {'Tags': 
                              {'Key': AWS_TAG_KEY, 'Values': aws_tag_filter_list }
                            }
                          ]
                        },
              Metrics=[
                  'UnblendedCost',
              ],
          )

        periodCost = 0      # holder for cost of the account in reporting period

        # Calculate cost of the account in reporting period
        for dayCost in response['ResultsByTime']:
            periodCost = periodCost + float(dayCost['Total']['UnblendedCost']['Amount'])

        print('Cost of account ', key, ' for the period is: ', periodCost )

        if periodCost > 0:
            accountCostDict.update({key:response})

    return accountCostDict

#--------------------------------------------------------------------------------------------------
# Create new dictionary and process totals for the reporting period

def process_costchanges_per_day(accountCostDict_input):

    reportCostDict = {} # main dictionary for displaying cost
    reportCostDict2 = {} # main dictionary for displaying cost with 1st of month removed


    period = DAYSBACK
    i = 0

    # Create a dictionary for every day of the reporting period
    while i < period:
        reportDate = (datetime.now() - timedelta(days = period - i))
        reportCostDict.update({reportDate.strftime('%Y-%m-%d'):None})
        reportCostDict[reportDate.strftime('%Y-%m-%d')] = {}
        i += 1

    # Fill up each daily dictionary with Account:Cost key value pairs
    for key in accountCostDict_input:

        for dayCost in accountCostDict_input[key]['ResultsByTime']:
            
            reportCostDict[dayCost['TimePeriod']['Start']].update(
                {key: {'Cost': float(dayCost['Total']['UnblendedCost']['Amount'])}}
            )

    # Get the total cost for each reporting day
    for key in reportCostDict:

        dayTotal = 0.0      # holder for total cost every key; key is the reporting day

        for account in reportCostDict[key]:
            dayTotal = dayTotal + reportCostDict[key][account]['Cost']

        reportCostDict[key].update({'dayTotal': {'Cost': dayTotal}})

    # Create a new dictionary with just the dates specified in DAILY_COST_DATES
    for day in DAILY_COST_DATES:
        reportCostDict2.update({day:reportCostDict[day]})

    return reportCostDict2


#--------------------------------------------------------------------------------------------------
# Create new dictionary for displaying/e-mailing the reporting period
# This takes the existing dictionary, displays accounts in displayList, and totals the
#   other accounts in Others.

def process_costchanges_for_display(reportCostDict_input):

    displayReportCostDict = {}      # holder for new dictionary

    # Enter dictionary report dates
    for reportDate in reportCostDict_input:
        displayReportCostDict.update({reportDate: None})
        displayReportCostDict[reportDate] = {}

        otherAccounts = 0.0     # holder for total cost in other accounts

        # Loop through accounts. Note that dayTotal is listed in displayList
        for accountNum in reportCostDict_input[reportDate]:

            # Only add account if in displayList; add everything else in Others
            if accountNum in displayList:
                displayReportCostDict[reportDate].update(
                    {accountNum: reportCostDict_input[reportDate][accountNum]}
                )
            else:
                otherAccounts = otherAccounts + reportCostDict_input[reportDate][accountNum]['Cost']

        # Enter total for 'Others' in the dictionary
        displayReportCostDict[reportDate].update({'Others': {'Cost': otherAccounts}})

    return displayReportCostDict


#--------------------------------------------------------------------------------------------------
# Process percentage changes for the reporting period

def process_percentchanges_per_day(reportCostDict_input):

    period = len(DAILY_COST_DATES)
    i = 0

    # Calculate the delta percent change; add Change:Percent key value pair to daily dictionary
    while i < period:

        # No percentage delta calculation for first day
        if i == 0:
            for account in reportCostDict_input[DAILY_COST_DATES[i]]:
                reportCostDict_input[DAILY_COST_DATES[i]][account].update({'percentDelta':None})

        if i > 0:
            for account in reportCostDict_input[DAILY_COST_DATES[i]]:
                try:
                    percentDelta = 0.0      # daily percent change holder for each account cost
                    todayCost = round(reportCostDict_input[DAILY_COST_DATES[i]][account]['Cost'], 2)
                    prevdayCost = round(reportCostDict_input[DAILY_COST_DATES[i-1]][account]['Cost'], 2)
                    
                    if(todayCost != prevdayCost):
                        percentDelta = todayCost / prevdayCost -1

                    reportCostDict_input[DAILY_COST_DATES[i]][account].update({'percentDelta':percentDelta})

                except ZeroDivisionError:
                    if prevdayCost == 0 and todayCost != 0:
                        percentDelta = todayCost / 0.01 -1
                        # update percent
                        reportCostDict_input[DAILY_COST_DATES[i]][account].update({'percentDelta':percentDelta})
                    else:
                        print('ERROR: Division by Zero')
                        reportCostDict_input[DAILY_COST_DATES[i]][account].update({'percentDelta':None})
        i += 1

    return reportCostDict_input

#--------------------------------------------------------------------------------------------------
# Compile HTML for E-mail Body

def create_report_html(emailDisplayDict_input, BODY_HTML):

    # The HTML body of the email.
    BODY_HTML = BODY_HTML + "<table border=1 style='border-collapse: collapse; \
                font-family: Arial, Calibri, Helvetica, sans-serif; font-size: 12px;'>"

    # Generate the header of the report/e-mail:
    BODY_HTML = BODY_HTML + '<tr style="background-color: SteelBlue;">' + "<td>&nbsp;</td>" # start row; blank space in the top left corner

    # AWS Account names as labels in the TOP/FIRST ROW
    for accountNum in displayList:
        if accountNum in accountDict:
            BODY_HTML = BODY_HTML + "<td colspan=2 style='text-align: center;'><b>" + accountDict[accountNum] + "</b></td>"
        elif accountNum == 'Others':
            BODY_HTML = BODY_HTML + "<td colspan=2 style='text-align: center;'><b>Others</b></td>"
        elif accountNum == 'dayTotal':
            BODY_HTML = BODY_HTML + "<td colspan=2 style='text-align: center;'><b>Total</b></td>"

    BODY_HTML = BODY_HTML + "</tr>\n" # end row

    BODY_HTML = BODY_HTML + '<tr style="background-color: LightSteelBlue;">' + "<td style='text-align: center; width: 80px;'>Date</td>" # start next row; Date label

    # AWS Account numbers in the SECOND ROW
    for accountNum in displayList:
        if accountNum in accountDict:
            BODY_HTML = BODY_HTML + "<td style='text-align: center; width: 95px;'>" \
                        + accountNum + "</td><td style='text-align: center;'>&Delta; %</td>"
        elif accountNum == 'Others':
            BODY_HTML = BODY_HTML + "<td style='text-align: center; width: 95px;'> \
                        Other Accounts</td><td style='text-align: center;'>&Delta; %</td>"
        elif accountNum == 'dayTotal':
            BODY_HTML = BODY_HTML + "<td style='text-align: center; width: 95px;'> \
                        All Accounts</td><td style='text-align: center;'>&Delta; %</td>"

    BODY_HTML = BODY_HTML + "</tr>\n" # end row

    # Generate the table contents for report/e-mail:
    i_row=0 
    #
    for reportDate in emailDisplayDict_input:
        # Use different style for the LAST ROW
        if reportDate == END_DATE or reportDate == YESTERDAY:
            BODY_HTML = BODY_HTML + row_color(i_row) + "<td style='text-align: center; color: Teal'><i>" + reportDate + "*</i></td>"

            for accountNum in displayList:
                BODY_HTML = BODY_HTML + "<td style='text-align: right; padding: 4px; color: Teal'> <i>$ {:,.2f}</i></td>".format(round(emailDisplayDict_input[reportDate][accountNum]['Cost'],2))
                arr_totals.append("$ {:,.2f}" .format(round(emailDisplayDict_input[reportDate][accountNum]['Cost'],2)))

                if emailDisplayDict_input[reportDate][accountNum]['percentDelta'] == None:
                    BODY_HTML = BODY_HTML + "<td style='text-align: right; padding: 4px; color: Teal'>0.00%</td>"
                    arr_totals_percent.append("<td style='text-align: right; padding: 4px; color: Teal'>0.00%</td>")
                else:
                    BODY_HTML = BODY_HTML + "<td style='text-align: right; padding: 4px; color: Teal'> <i>{:.2%}</i></td>".format(emailDisplayDict_input[reportDate][accountNum]['percentDelta'])
                    test=evaluate_change(emailDisplayDict_input[reportDate][accountNum]['percentDelta'])
                    arr_totals_percent.append(test)

            BODY_HTML = BODY_HTML + "</tr>\n"

            continue

        BODY_HTML = BODY_HTML + row_color(i_row) + "<td style='text-align: center;'>" + reportDate + "</td>"
        # Use normal format for MIDDLE ROWS
        for accountNum in displayList:
            BODY_HTML = BODY_HTML + "<td style='text-align: right; padding: 4px;'> $ {:,.2f}</td>".format(round(emailDisplayDict_input[reportDate][accountNum]['Cost'],2))
            arr_totals.append("$ {:,.2f} ".format(round(emailDisplayDict_input[reportDate][accountNum]['Cost'],2)))
            indice_n= len(arr_totals)
            indice_na=indice_n-1
            
            if emailDisplayDict_input[reportDate][accountNum]['percentDelta'] == None:
              BODY_HTML = BODY_HTML + "<td style='text-align: right; padding: 4px; color: Teal'>0.00%</td>"
              arr_totals_percent.append("<td style='text-align: right; padding: 4px; color: Teal'>0.00%</td>")
            else:
              BODY_HTML = BODY_HTML + evaluate_change(emailDisplayDict_input[reportDate][accountNum]['percentDelta'])
              arr_totals_percent.append(evaluate_change(emailDisplayDict_input[reportDate][accountNum]['percentDelta']))
              indice_p= len(arr_totals_percent)

        BODY_HTML = BODY_HTML + "</tr>\n"

        i_row += 1

    BODY_HTML = BODY_HTML + "</table><br>\n"

    BODY_HTML = BODY_HTML + "<div style='color: Teal; font-size: 12px; font-style: italic;'> \
                * Note that total costs for this date are not reflected on this report.</div>\n"
    BODY_HTML = BODY_HTML + "<div style='color: Teal; font-size: 12px; font-style: italic;'> \
                *Color Legend : The color change is dynamically determined ranging from Red to Blue including Black.</div>\n"

    return BODY_HTML
    #return None

# =================================================================================================

#--------------------------------------------------------------------------------------------------
# Get Linked Account Dimension values from Master Payer Cost Explorer

def get_linked_accounts(accountList):

  results = []  # holder for full linked account results
  token = None  # holder for NextPageToken

  while True:

    if token:
      kwargs = {'NextPageToken': token}   # get the NextPageToken
    else:
      kwargs = {} # empty if the NextPageToken does not exist

    linked_accounts = cost_explorer.get_dimension_values(

            # Get all linked account numbers in the time period requested
            TimePeriod={'Start': START_DATE, 'End': END_DATE},
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
# Get Cost Data from Master Payer Cost Explorer

def get_cost_data(account_numbers):

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
      TimePeriod={'Start': START_DATE, 'End': END_DATE},
      Granularity='DAILY',
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

def restructure_cost_data(cost_data_Dict, account_numbers):

  display_cost_data_Dict = {}             # holder for restructured dictionary for e-mail/display
  sorted_display_cost_data_Dict = {}      # holder for sorted dictionary for e-mail/display

  # use account numbers as main dictionary keys
  for account in account_numbers:
    display_cost_data_Dict.update({account: {}})

  # use service names as second dictionary keys
  for timeperiods in cost_data_Dict:

    for cost in timeperiods['Groups']:
      account_no = cost['Keys'][0]      # Account Number
      account_name = cost['Keys'][1]        # Service Name

      try:
        display_cost_data_Dict[account_no].update({account_name: {}})
      except:
        continue

  # for each service, save costs per period
  for timeperiods in cost_data_Dict:
    date = timeperiods['TimePeriod']['Start']

    for cost in timeperiods['Groups']:
      account_no = cost['Keys'][0]                              # Account Number
      account_name = cost['Keys'][1]                            # Service Name
      amount = cost['Metrics']['UnblendedCost']['Amount']       # Period Cost

      try:
        display_cost_data_Dict[account_no][account_name].update({date: amount})
      except:
        continue

    # sort the dictionary (per service) for each account
  for accounts in display_cost_data_Dict:
      sorted_display_cost_data_Dict.update({accounts:{}})
      sorted_display_cost_data_Dict[accounts].update(sorted(display_cost_data_Dict[accounts].items()))
  
  #return display_cost_data_Dict
  return sorted_display_cost_data_Dict


#--------------------------------------------------------------------------------------------------
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
#------------------------------------------------------------
# Function to color rows
def row_color(i_row):
  if (i_row % 2) == 0:
    return "<tr style='background-color: WhiteSmoke;'>"
  else:
    return "<tr>"
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
def prevdaycost_table(prevdaycost, currdaycost):
  if prevdaycost == 0 and currdaycost == 0:
    pctfrmprev = 0
  elif prevdaycost != 0 and currdaycost != 0:
    pctfrmprev = (currdaycost / prevdaycost) - 1
  elif prevdaycost != 0 and currdaycost == 0:
    currdaycost = 0.01
    pctfrmprev = (currdaycost / prevdaycost) - 1
  else:
    prevdaycost = 0.01
    pctfrmprev = (currdaycost / prevdaycost) - 1
  #
  return evaluate_change(pctfrmprev)

#------------------------------------------------------------
def formating_cost(cost):
  cost_td = "$ {:,.2f}".format(cost)
  return cost_td
#------------------------------------------------------------
def clear(value):
  if type(value) == str:
    a = value.replace("$", " " )
  elif type(value) == float:
    a = value
  else:
    a = value
  return a
#------------------------------------------------------------

# Generate Table HTML Codes for e-mail formatting
def generate_html_table(cost_data_Dict, display_cost_data_Dict):

  AWS_TAG_KEY = os.environ['AWS_TAG_KEY']
  AWS_FILTER = os.environ['AWS_FILTER']
  #
  aws_tag_filter_list = os.environ['aws_tag_filter'].split(",") if os.environ['aws_tag_filter'] else []
  #
  tag_key_len = len(AWS_TAG_KEY)
  tag_key_len += 1
  arguments = len(arr_totals)
  hide_column = 1

  column_p = 0
  column_pa = 0
  
  # Start HTML table
  emailHTML = '<h2>AWS Daily Cost Report for Accounts - Per ' + AWS_FILTER + ' Group</h2>' + \
        '<table border="1" style="border-collapse: collapse;">'
  #
  for accounts in display_cost_data_Dict:
    #
    matrix_rows = len(display_cost_data_Dict[accounts])
    matrix_cols = len(cost_data_Dict)
    matrix = [([0]*matrix_cols) for i in range(matrix_rows)] 

    # table headers
    if hide_column == 0:
      global COLUMNS
      COLUMNS = COLUMNS + 2
    #
    emailHTML = emailHTML + '<tr style="background-color: SteelBlue;">' + '<td colspan="' + str(COLUMNS) + '" style="text-align: center; font-weight: bold">' + \
                    accountDict[accounts] + ' (' + accounts + ')</td></tr>'
    emailHTML = emailHTML + '<tr style="background-color: LightSteelBlue;">' + '<td style="text-align: center; font-weight: bold">' + AWS_TAG_KEY # + '</td>'

    # timeperiod headers
    for timeperiods in cost_data_Dict:
      #high firts date
      if timeperiods['TimePeriod']['Start'] == START_DATE and hide_column == 1:
        nada = 0
      else:
        emailHTML = emailHTML + '<td colspan="2" style="text-align: center; font-weight: bold">' + timeperiods['TimePeriod']['Start']
      if timeperiods['TimePeriod']['Start'] == END_DATE or timeperiods['TimePeriod']['Start'] == YESTERDAY:
        emailHTML = emailHTML + '</td>'
        emailHTML = emailHTML + '<td style="text-align: center; font-weight: bold">&Delta; % Overall'
      emailHTML = emailHTML + '</td>'
    emailHTML = emailHTML + '</tr>'

    i_row = 0   # row counter for tracking row background color
    tag_key_length = len(display_cost_data_Dict[accounts])
    
    # services and costs per timeperiod
    for service in display_cost_data_Dict[accounts]:
      rsrcrowHTML = ''      # Resource row HTML code
      rsrcrowHTML = rsrcrowHTML + row_color(i_row)
      
      # Leading the row with Service Name
      if i_row > 0:
        rsrcrowHTML = rsrcrowHTML + '<td style="text-align: left;"> ' + service[tag_key_len:] + ' </td>'
      else:
        new_service = service.replace(AWS_TAG_KEY, "Total Costs" )
        # remove extra characters
        new_service = new_service.replace("$", " " )
        rsrcrowHTML = rsrcrowHTML + '<td style="text-align: left;"> ' + new_service + ' </td>'

      # set in cero the provious day
      #prevdaycost = None    # previous month cost
      prevdaycost = 0    # previous month cost
      currdaycost = 0.0 # current month cost
      pctfrmprev = 0.0  # percentage delta from previous to curent day
      columna_v = 0
      column_p = 0
      matrix_column = 0
      #
      # to calculate last colum
      cost_first_colum = 0
      cost_first_colum_count = 0
      cost_last_colum = 0
      i_column = 0
      #
      for timeperiods in cost_data_Dict:
        date = timeperiods['TimePeriod']['Start']
        
        ###########################
        try:
          cost_td = round(float(display_cost_data_Dict[accounts][service][date]),2)
        except:
          cost_td = 0
        #
        # for total cost use
        if cost_first_colum_count == 0 and hide_column == 1: # hide first column
          columna_v += 2
          matrix[i_row][matrix_column] = clear(cost_td)
          matrix_column += 1
        else:
          if i_row > 0 :
            rsrcrowHTML = rsrcrowHTML + '<td style="text-align: right; padding: 4px;">'
            rsrcrowHTML = rsrcrowHTML + formating_cost(cost_td) + '</td>'
            #
            matrix[i_row][matrix_column] = clear(cost_td)
            matrix_column += 1
          else:
            if columna_v >= arguments :
              rsrcrowHTML = rsrcrowHTML + '<td style="text-align: right; padding: 4px;"> $0.00 </td>'
              matrix[i_row][matrix_column] = 0
              matrix_column += 1
            else:
              rsrcrowHTML = rsrcrowHTML + '<td style="text-align: right; padding: 4px;">' + arr_totals[columna_v] + '</td>'
              matrix[i_row][matrix_column] = clear(arr_totals[columna_v])
              columna_v += 2
              matrix_column += 1

        ###########################
        # Calculate delta(s) after the first month <td>
        currdaycost = cost_td
        # Calculate % if previous and current costs are not zero
        # calculate the percent
        # for total cost use
        if cost_first_colum_count == 0 and hide_column == 1: # hide first column
          column_pa += 2
        else:
          if i_row > 0 :
            rsrcrowHTML = rsrcrowHTML + prevdaycost_table(prevdaycost, currdaycost)
          else:
            if column_p == 0 :
              rsrcrowHTML = rsrcrowHTML + arr_totals_percent[column_pa]
              column_p += 1
              column_pa += 2
              arr_totals_percent.append('<td style="text-align: right; padding: 4px;">0.00%</td>')
            else:
              # remove extra characters
              value_set = arr_totals_percent[column_pa].replace("$", " " )
              rsrcrowHTML = rsrcrowHTML + value_set
              column_pa += 2
        prevdaycost = cost_td
        ###########################    
        # obtain firt colum data
        if i_row > 0 :
          if cost_first_colum_count == 0:
            cost_first_colum = cost_td
        else:
          if cost_first_colum_count == 0:
            cost_first_colum = arr_totals[columna_v - 2]
        #
        cost_first_colum_count += 1
        #
        # obtain last colum data
        i_column += 2
        if i_row > 0 :
          if arguments == i_column:
            cost_last_colum = cost_td
        else:
          if arguments == i_column:
            cost_last_colum = arr_totals[columna_v - 2]
      #
      ##############################################################
      # las colum
      #
      cost_last_colum = represents_int(cost_last_colum)
      cost_first_colum = represents_int(cost_first_colum)
      #
      try:
        # overall percent delta calculation
        last_cost_percent = round(float(matrix[i_row][matrix_cols-1])/float(matrix[i_row][1]),2)-1   
      except ZeroDivisionError:
        if cost_last_colum == 0 and cost_first_colum == 0:
          last_cost_percent = 0
        else:
          last_cost_percent = cost_last_colum / 0.01 - 1
      #  
      rsrcrowHTML = rsrcrowHTML + evaluate_change(last_cost_percent)
      rsrcrowHTML = rsrcrowHTML + '</tr>'

      emailHTML = emailHTML + rsrcrowHTML       # Include row for displaying

      i_row += 1                                # row counter
    #
    if not aws_tag_filter_list:
      # last row
      i_column = 0
      rsrcrowHTML = ''      # Resource row HTML code
      rsrcrowHTML = row_color(i_row)
      rsrcrowHTML = rsrcrowHTML + '<td style="text-align: left;"> No tag key:' + AWS_TAG_KEY + '</td>'
      #
      for temporal in range(matrix_column):
        if i_column <= matrix_column:
          #
          i_row = 0
          for rou in range(matrix_rows):
            #
            if rou == 0:
              data = represents_int(matrix[i_row][i_column])
            else:
              data = data - represents_int(matrix[i_row][i_column])
            i_row += 1
          #
          data = round(data,2)
          curr_day_cost = data
          #
          if i_column == 0:
            cost_first_colum_no_tag = curr_day_cost
          #
          #data = str(data)
          if i_column != 0:
            rsrcrowHTML = rsrcrowHTML + '<td>' + formating_cost(data) + '</td>'
            # percent calculation
            rsrcrowHTML = rsrcrowHTML + prevdaycost_table(prev_day_cost, curr_day_cost) 
            #
            prev_day_cost = curr_day_cost
          else:
            if hide_column == 0:
              rsrcrowHTML = rsrcrowHTML + '<td>' + formating_cost(0) + '</td>'
              rsrcrowHTML = rsrcrowHTML + prevdaycost_table(0, 0) 
            prev_day_cost = curr_day_cost
        #
        i_column += 1
      #
      cost_last_colum_no_tag = curr_day_cost
      rsrcrowHTML = rsrcrowHTML + prevdaycost_table(cost_first_colum_no_tag, cost_last_colum_no_tag)  + '</tr>'
      emailHTML = emailHTML + rsrcrowHTML       # Include row for displaying
  #
  emailHTML = emailHTML + '</table><br>\n'
  # comments
  emailHTML = emailHTML + "<div style='color: Teal; font-size: 12px; font-style: italic;'> \
              **Color Legend : The color change is dynamically determined ranging from Red to Blue including Black.</div>\n"

  print("emailHTML", emailHTML)

  return emailHTML

# =================================================================================================

#--------------------------------------------------------------------------------------------------
# Compile and send HTML E-mail

def send_report_email(BODY_HTML):

    SENDER = os.environ['SENDER']
    RECIPIENTS = os.environ['RECIPIENTS']
    AWS_REGION = os.environ['AWS_REGION_ENV']
    SUBJECT = "AWS Daily Cost Report for Selected Accounts"

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


#--------------------------------------------------------------------------------------------------
# Lambda Handler+-----

def lambda_handler(context=None, event=None):

    DISPLAY_BOTH_TABLES = os.environ['DISPLAY_BOTH_TABLES']

    # Using dictionary of 23 named accounts, get cost info from Cost Explorer
    # Result is dictionary keyed by account number
    mainCostDict = ce_get_costinfo_per_account(accountDict)

    # Re-sort the mainCostDict; create a new dictionary keyed by reporting date
    mainDailyDict = process_costchanges_per_day(mainCostDict)

    # Create a new dictionary (from mainDailyDict) with only big cost accounts labeled
    # Combine other accounts into "Others"
    mainDisplayDict = process_costchanges_for_display(mainDailyDict)

    # Update mainDisplayDict dictionary to include daily percent changes
    finalDisplayDict = process_percentchanges_per_day(mainDisplayDict)

    # Generate HTML code using finalDisplayDict and send HTML e-mail
    summary_html = create_report_html(finalDisplayDict, BODY_HTML)


    # =============================================================================================

    account_numbers = get_linked_accounts(accountList)

    # Get cost data from the Master Payer Account
    cost_data_Dict = get_cost_data(account_numbers)

    # Restruction dictionary for email message display
    display_cost_data_Dict = restructure_cost_data(cost_data_Dict, account_numbers)

    # Put the restructured dictionary in HTML table
    html_for_email = generate_html_table(cost_data_Dict, display_cost_data_Dict)

    # to activate the first table
    if DISPLAY_BOTH_TABLES == 'true' :
      html_for_email = summary_html + '<br><br>' + html_for_email
    # else :
    #   html_for_email = html_for_email

    # Send HTML e-mail
    send_report_email(html_for_email)
