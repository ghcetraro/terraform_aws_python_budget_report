# Daily Cost Reporting using Lambda function

import json
import boto3
import os
from datetime import datetime, timedelta
from botocore.exceptions import ClientError
#
from total_cost import *
from html_function import *
from filters import *
#
# Create Cost Explorer service client using saved credentials
cost_explorer = boto3.client('ce')

#--------------------------------------------------------------------------------------------------
# Reporting periods
#
DAYSBACK = int(os.environ['DAYSBACK'])
#
COLUMNS = DAYSBACK * 2
START_DATE = (datetime.now() - timedelta(days = DAYSBACK)).strftime('%Y-%m-%d')
END_DATE = (datetime.now()).strftime('%Y-%m-%d')
YESTERDAY = (datetime.now() - timedelta(days = 1)).strftime('%Y-%m-%d')
#
DAILY_COST_DATES = [] # holder for dates used in daily cost changes
#
for x in range(DAYSBACK+1, 1, -1):
    # This generates dates from 8 days back to yesterday
    temp_date = datetime.now() - timedelta(days = x-1)
    #if temp_date.strftime('%d') != '01':
    DAILY_COST_DATES.append(temp_date.strftime('%Y-%m-%d'))
#
MONTHLY_COST_DATES = [] # holder for dates used in monthly cost changes (every 1st of the month)
MONTHLY_COST_DATES2 = [] # holder for dates used in monthly cost changes (every 2nd of the month)
#
# This generates monthly dates (every 1st and 2nd of the month) going back 180 days
for x in range(180, 0, -1):
#
    if (datetime.now() - timedelta(days = x)).strftime('%d') == '01':
        temp_date = datetime.now() - timedelta(days = x)
        MONTHLY_COST_DATES.append(temp_date.strftime('%Y-%m-%d'))

        temp_date = datetime.now() - timedelta(days = x-1)
        MONTHLY_COST_DATES2.append(temp_date.strftime('%Y-%m-%d'))
#
BODY_HTML = '<h2>AWS Daily Cost Report for Accounts - Summary</h2>'
#
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
                    percentDelta = (reportCostDict_input[DAILY_COST_DATES[i]][account]['Cost']
                        / reportCostDict_input[DAILY_COST_DATES[i-1]][account]['Cost'] - 1
                    )
                    reportCostDict_input[DAILY_COST_DATES[i]][account].update({'percentDelta':percentDelta})
                except ZeroDivisionError:
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

    BODY_HTML = BODY_HTML + '<tr style="background-color: SteelBlue;">' + "<td style='text-align: right; padding: 4px;'>0.00</td>" # start row; blank space in the top left corner

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

    for reportDate in emailDisplayDict_input:

        # Use different style for the LAST ROW
        if reportDate == END_DATE or reportDate == YESTERDAY:
            BODY_HTML = BODY_HTML + row_color(i_row) + "<td style='text-align: center; color: Teal'><i>" + reportDate + "*</i></td>"

            for accountNum in displayList:
                BODY_HTML = BODY_HTML + "<td style='text-align: right; padding: 4px; color: Teal'> \
                            <i>$ {:,.2f}</i></td>".format(round(emailDisplayDict_input[reportDate][accountNum]['Cost'],2))

                if emailDisplayDict_input[reportDate][accountNum]['percentDelta'] == None:
                    BODY_HTML = BODY_HTML + "0.00% </td>"
                else:
                    BODY_HTML = BODY_HTML + "<td style='text-align: right; padding: 4px; color: Teal'> \
                                <i>{:.2%}</i></td>".format(emailDisplayDict_input[reportDate][accountNum]['percentDelta'])

            BODY_HTML = BODY_HTML + "</tr>\n"

            continue

        BODY_HTML = BODY_HTML + row_color(i_row) + "<td style='text-align: center;'>" + reportDate + "</td>"

        # Use normal format for MIDDLE ROWS
        for accountNum in displayList:
            BODY_HTML = BODY_HTML + "<td style='text-align: right; padding: 4px;'> \
                        $ {:,.2f}</td>".format(round(emailDisplayDict_input[reportDate][accountNum]['Cost'],2))

            if emailDisplayDict_input[reportDate][accountNum]['percentDelta'] == None:
                BODY_HTML = BODY_HTML + "<td style='text-align: right; padding: 4px;'>0.00%</td>"
            else:
                BODY_HTML = BODY_HTML + evaluate_change(emailDisplayDict_input[reportDate][accountNum]['percentDelta'])

        BODY_HTML = BODY_HTML + "</tr>\n"

        i_row += 1

    BODY_HTML = BODY_HTML + "</table><br>\n"

    # * Note that total costs for this date are not reflected on this report.
    BODY_HTML = BODY_HTML + "<div style='color: Teal; font-size: 12px; font-style: italic;'> \
                * Note that total costs for this date are not reflected on this report.</div>\n"
    BODY_HTML = BODY_HTML + "<div style='color: Teal; font-size: 12px; font-style: italic;'> \
                *Color Legend : The color change is dynamically determined ranging from Red to Blue including Black.</div>\n"

    return BODY_HTML

# =================================================================================================
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
      account_no = cost['Keys'][0]        # Account Number
      account_name = cost['Keys'][1]      # Service Name

      try:
        display_cost_data_Dict[account_no].update({account_name: {}})
      except:
        continue

  # for each service, save costs per period
  for timeperiods in cost_data_Dict:
    date = timeperiods['TimePeriod']['Start']

    for cost in timeperiods['Groups']:
      account_no = cost['Keys'][0]                            # Account Number
      account_name = cost['Keys'][1]                          # Service Name
      amount = cost['Metrics']['UnblendedCost']['Amount']     # Period Cost

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
# Generate Table HTML Codes for e-mail formatting

def generate_html_table(cost_data_Dict, display_cost_data_Dict, emailDisplayDict):

  hide_column = 1

  # Start HTML table
  emailHTML = '<h2>AWS Daily Cost Report for Accounts - Per Service Breakdown</h2>' + \
        '<table border="1" style="border-collapse: collapse;">'

  for accounts in display_cost_data_Dict:

    # table headers
    if hide_column == 0:
      global COLUMNS
      COLUMNS = COLUMNS + 2
    #

    # table headers
    emailHTML = emailHTML + '<tr style="background-color: SteelBlue;">' + \
          '<td colspan="' + str(COLUMNS) + '" style="text-align: center; font-weight: bold">' + \
                    accountDict[accounts] + ' (' + accounts + ')</td></tr>'
    emailHTML = emailHTML + '<tr style="background-color: LightSteelBlue;">' + \
          '<td style="text-align: center; font-weight: bold">Service Name</td>'

    # timeperiod headers
    for timeperiods in cost_data_Dict:
      #high firts date
      if timeperiods['TimePeriod']['Start'] == START_DATE and hide_column == 1:
        nada = 0
      else:
        emailHTML = emailHTML + '<td colspan=2 style="text-align: center; font-weight: bold">' + timeperiods['TimePeriod']['Start']
      #
      if timeperiods['TimePeriod']['Start'] == END_DATE or timeperiods['TimePeriod']['Start'] == YESTERDAY:
        emailHTML = emailHTML + '</td>'
        emailHTML = emailHTML + '<td style="text-align: center; font-weight: bold">&Delta; % Overall'
      #
      emailHTML = emailHTML + '</td>'
    emailHTML = emailHTML + '</tr>'

    i_row = 0 # row counter for tracking row background color

    # services and costs per timeperiod
    for service in display_cost_data_Dict[accounts]:
      rsrcrowHTML = ''        # Resource row HTML code
      #
      if i_row == 0:
        rsrcrowHTML = rsrcrowHTML + row_color(i_row)
        rsrcrowHTML = rsrcrowHTML + total_cost(emailDisplayDict, displayList, hide_column)
        rsrcrowHTML = rsrcrowHTML + '</tr>'
      #
      # Leading the row with Service Name
      rsrcrowHTML = rsrcrowHTML + row_color(i_row)
      rsrcrowHTML = rsrcrowHTML + '<td style="text-align: left;">' + service + '</td>'
      #
      prevdaycost = 0  # previous month cost
      currdaycost = 0  # current month cost
      pctfrmprev  = 0  # percentage delta from previous to curent day
      # to calculate last colum
      cost_first_colum = 0
      cost_first_colum_count = 0
      cost_last_colum = 0
      i_column = 0
      #
      #
      for timeperiods in cost_data_Dict:
        date = timeperiods['TimePeriod']['Start']
        ###################
        try:
          cost_td = round(float(display_cost_data_Dict[accounts][service][date]),2)
          #prevdaycost = (round(float(display_cost_data_Dict[accounts][service][date]),2))
        except:
          cost_td = 0
        #
        # for total cost use
        if cost_first_colum_count == 0 and hide_column == 1: # hide first column
          nada = 0
        else:
          rsrcrowHTML = rsrcrowHTML + '<td style="text-align: right; padding: 4px;">'
          rsrcrowHTML = rsrcrowHTML + "$ {:,.2f}".format(cost_td) + '</td>'
        #
        currdaycost = cost_td
        #
        if cost_first_colum_count == 0 and hide_column == 1: # hide first column
          nada = 0
        else:
          rsrcrowHTML = rsrcrowHTML + prevdaycost_table(prevdaycost, currdaycost)
        #
        prevdaycost = currdaycost
        #
        ##############################################################
        # obtain firt colum data
        if i_row > 0 :
          if cost_first_colum_count == 0:
            cost_first_colum = currdaycost
        else:
          if cost_first_colum_count == 0:
            cost_first_colum = total_cost_first_column(emailDisplayDict, displayList)
        #
        cost_first_colum_count += 1
      #
      ##############################################################
      # obtain last colum data
      if i_row > 0 :
        cost_last_colum = currdaycost
      else:
        cost_last_colum = total_cost_last_column(emailDisplayDict, displayList)
      #
      rsrcrowHTML = rsrcrowHTML + evaluate_change(overall_percent_delta_calculation(cost_first_colum,cost_last_colum))
      rsrcrowHTML = rsrcrowHTML + '</tr>'
      #
      emailHTML = emailHTML + rsrcrowHTML     # Include row for displaying
      i_row += 1                              # row counter

  emailHTML = emailHTML + '</table><br>\n'

  # comments
  emailHTML = emailHTML + "<div style='color: Teal; font-size: 12px; font-style: italic;'> \
              **Color Legend : The color change is dynamically determined ranging from Red to Blue including Black.</div>\n"

  return emailHTML

# =================================================================================================

#--------------------------------------------------------------------------------------------------
# Compile and send HTML E-mail

def send_report_email(BODY_HTML):

    SENDER = os.environ['SENDER']
    RECIPIENTS = os.environ['RECIPIENTS']
    AWS_REGION_ENV = os.environ['AWS_REGION_ENV']
    SUBJECT = "AWS Daily Cost Report for Selected Accounts"

    # The email body for recipients with non-HTML email clients.
    BODY_TEXT = ("Amazon SES\r\n"
                "An HTML email was sent to this address."
                )

    # The character encoding for the email.
    CHARSET = "UTF-8"

    # Create a new SES resource and specify a region.
    client = boto3.client('ses',region_name=AWS_REGION_ENV)

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
# Lambda Handler

def lambda_handler(context=None, event=None):

    DISPLAY_BOTH_TABLES = os.environ['DISPLAY_BOTH_TABLES']

    # Using dictionary of 23 named accounts, get cost info from Cost Explorer
    # Result is dictionary keyed by account number
    mainCostDict = ce_get_costinfo_per_account(accountDict, START_DATE, END_DATE)

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

    account_numbers = get_linked_accounts(accountList, START_DATE, END_DATE)

    # Get cost data from the Master Payer Account
    cost_data_Dict = get_cost_data(account_numbers, START_DATE, END_DATE)

    # Restruction dictionary for email message display
    display_cost_data_Dict = restructure_cost_data(cost_data_Dict, account_numbers)

    # Put the restructured dictionary in HTML table
    html_for_email = generate_html_table(cost_data_Dict, display_cost_data_Dict, finalDisplayDict)

    #print("html_for_email", html_for_email)

    # to activate the first table
    if DISPLAY_BOTH_TABLES == 'true' :
      html_for_email = summary_html + '<br><br>' + html_for_email
    else :
      html_for_email = html_for_email

    # Send HTML e-mail
    send_report_email(html_for_email)