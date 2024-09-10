# Month Cost Reporting using Lambda function

# maximun history 13 month
# 9 se rompe

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
from special_calcs import *
from utils import *

# Create Cost Explorer service client using saved credentials
cost_explorer = boto3.client('ce')

# variables for total costs
arr_totals = []
arr_totals_percent = []

#--------------------------------------------------------------------------------------------------

# Reporting periods
MONTHSBACK = int(os.environ['MONTHSBACK'])
#
MONTHLY_COST_DATES = generates_monthly_dates(MONTHSBACK)
#
# for year to date
MONTHSBACK_SELECTED = determinator(MONTHSBACK)
MONTHLY_COST_DATES_YTD = generates_monthly_dates(MONTHSBACK_SELECTED)
#
then = (datetime.now() - timedelta(days = MONTHSBACK*30))
today = datetime.now()
#
MONTHLY_START_DATE = (then.replace(day=1)).strftime('%Y-%m-%d')
MONTHLY_END_DATE = (today.replace(day=1)).strftime('%Y-%m-%d')
LASTMONTH = (today.replace(day=1) - relativedelta.relativedelta(months=1)).strftime('%Y-%m-%d')
##
MONTHLY_START_DATE_YTD = first_month_ytd(MONTHLY_COST_DATES_YTD)
#
COLUMNS = MONTHSBACK * 2 + 2
#
BODY_HTML = '<h2>AWS Monthly Cost Report for Accounts - Summary</h2>'
#
#--------------------------------------------------------------------------------------------------
# Tuple for all the accounts listed in MEDailySpendView settings
#
with open('accountMailDict.txt') as f:
    data_a = f.read()
accountMailDict = json.loads(data_a)
#
# Dictionary of named accounts
with open('accountDict.txt') as f:
    data_b = f.read()
accountDict = json.loads(data_b)
#
# Create an account list based on dictionary keys
accountList = []
for key in accountDict.keys():
    accountList.append(key)
#
# This list controls the number of accounts to have detailed report
# Accounts not listed here will be added to "Others". DO NOT remove 'Others' and 'dayTotal'
displayList_list = os.environ['displayList']
displayList = displayList_list.split()
#
aws_tag_filter_list = os.environ['aws_tag_filter'].split(",") if os.environ['aws_tag_filter'] else []
AWS_TAG_KEY = os.environ['AWS_TAG_KEY']
#
#--------------------------------------------------------------------------------------------------
# Compile HTML for E-mail Body

def create_report_html(emailDisplayDict, BODY_HTML):
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
        elif accountNum == 'monthTotal':
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
        #
        elif accountNum == 'monthTotal':
            BODY_HTML = BODY_HTML + "<td style='text-align: center; width: 95px;'> \
                        All Accounts</td><td style='text-align: center;'>&Delta; %</td>"

    BODY_HTML = BODY_HTML + "</tr>\n" # end row
    # Generate the table contents for report/e-mail:
    i_row=0 
    #
    for reportMonth in emailDisplayDict:
        # Use different style for the LAST ROW
        if reportMonth == MONTHLY_END_DATE : 
            BODY_HTML = BODY_HTML + row_color(i_row) + "<td style='text-align: center; color: Teal'><i>" + reportMonth + "*</i></td>"

            for accountNum in displayList:
                BODY_HTML = BODY_HTML + "<td style='text-align: right; padding: 4px; color: Teal'> \
                 <i>$ {:,.2f}</i></td>".format(round(emailDisplayDict[reportMonth]['monthTotal']['Cost'],2))

                if emailDisplayDict[reportMonth]['monthTotal']['percentDelta'] == None:
                    BODY_HTML = BODY_HTML + "<td style='text-align: right; padding: 4px; color: Teal'>0.00%</td>"
                    #arr_totals_percent.append("<td style='text-align: right; padding: 4px; color: Teal'>0.00%</td>")
                else:
                    BODY_HTML = BODY_HTML + "<td style='text-align: right; padding: 4px; color: Teal'> \
                    <i>{:.2%}</i></td>".format(emailDisplayDict[reportMonth]['monthTotal']['percentDelta'])
                    test="<td style='text-align: right; padding: 4px; color: Teal'> \
                    <i>{:.2%}</i></td>".format(emailDisplayDict[reportMonth]['monthTotal']['percentDelta'])
            BODY_HTML = BODY_HTML + "</tr>\n"
            continue
        
        BODY_HTML = BODY_HTML + row_color(i_row) + "<td style='text-align: center;'>" + reportMonth + "</td>"
        # Use normal format for MIDDLE ROWS
        for accountNum in displayList:
            BODY_HTML = BODY_HTML + "<td style='text-align: right; padding: 4px;'> \
            $ {:,.2f}</td>".format(round(emailDisplayDict[reportMonth]['monthTotal']['Cost'],2))
            
            if emailDisplayDict[reportMonth]['monthTotal']['percentDelta'] == None:
              BODY_HTML = BODY_HTML + "<td style='text-align: right; padding: 4px; color: Teal'>0.00%</td>"
            else:
              BODY_HTML = BODY_HTML + evaluate_change(emailDisplayDict[reportMonth]['monthTotal']['percentDelta'])

        BODY_HTML = BODY_HTML + "</tr>\n"
        i_row += 1

    BODY_HTML = BODY_HTML + "</table><br>\n"
    # * Note that total costs for this date are not reflected on this report.
    BODY_HTML = BODY_HTML + "<div style='color: Teal; font-size: 12px; font-style: italic;'> \
                * Note that total costs for this date are not reflected on this report.</div>\n"
    BODY_HTML = BODY_HTML + "<div style='color: Teal; font-size: 12px; font-style: italic;'> \
                *Color Legend : The color change is dynamically determined ranging from Red to Blue including Black.</div>\n"
    return BODY_HTML

#--------------------------------------------------------------------------------------------------
# Generate Table HTML Codes for e-mail formatting
def generate_html_table(cost_data_Dict, display_cost_data_Dict, emailDisplayDict):


  AWS_TAG_KEY = os.environ['AWS_TAG_KEY']
  AWS_FILTER = os.environ['AWS_FILTER']
  #
  aws_tag_filter_list = os.environ['aws_tag_filter'].split(",") if os.environ['aws_tag_filter'] else []
  #
  tag_key_len = len(AWS_TAG_KEY)
  tag_key_len += 1
  arguments = len(arr_totals)
  hide_column = 1
  #
  ytd_cola = 0
  column_p = 0
  column_pa = 0
  cost_last_colum_projected = 0

  # Start HTML table
  emailHTML = '<h2>AWS Monthly Cost Report for Accounts - Per ' + AWS_FILTER + ' Group</h2>' + \
        '<table border="1" style="border-collapse: collapse;">'

  for accounts in display_cost_data_Dict:
    #
    matrix_rows = len(display_cost_data_Dict[accounts])
    matrix_cols = arguments
    matrix_cols = len(cost_data_Dict)
    matrix = [([0]*matrix_cols) for i in range(matrix_rows)] 

    # table headers
    if hide_column == 0:
      global COLUMNS
      COLUMNS = COLUMNS + 2
    #
    emailHTML = emailHTML + '<tr style="background-color: SteelBlue;">' + '<td colspan="' + str(COLUMNS) + '" style="text-align: center; font-weight: bold">' + \
                    accountDict[accounts] + ' (' + accounts + ')</td></tr>'
    emailHTML = emailHTML + '<tr style="background-color: LightSteelBlue;">' + '<td style="text-align: center; font-weight: bold">' + AWS_TAG_KEY #+ '</td>'

    # timeperiod headers
    for timeperiods in cost_data_Dict:
      #high firts date
      date_now = convert_date(timeperiods['TimePeriod']['Start'])
      #
      if timeperiods['TimePeriod']['Start'] == MONTHLY_START_DATE and hide_column == 1:
        nada=0
      else:
        #
        emailHTML = emailHTML + '<td colspan="2" style="text-align: center; font-weight: bold">' + date_now
      if timeperiods['TimePeriod']['Start'] == MONTHLY_END_DATE or timeperiods['TimePeriod']['Start'] == LASTMONTH:
        emailHTML = emailHTML + '</td>'
        emailHTML = emailHTML + '<td style="text-align: center; font-weight: bold">Year to Date </td>'
        emailHTML = emailHTML + '<td style="text-align: center; font-weight: bold">Projected cost till end of the year'
      emailHTML = emailHTML + '</td>'
    emailHTML = emailHTML + '</tr>'
    #
    i_row = 0   # row counter for tracking row background color
    tag_key_length = len(display_cost_data_Dict[accounts])
    
    # services and costs per timeperiod
    for service in display_cost_data_Dict[accounts]:
      rsrcrowHTML = ''      # Resource row HTML code
      rsrcrowHTML = rsrcrowHTML + row_color(i_row)
      
      # Leading the row with Service Name
      if i_row > 0:
        rsrcrowHTML = rsrcrowHTML + '<td style="text-align: left;">' + service[tag_key_len:] + '</td>'
      else:
        new_service = service.replace(AWS_TAG_KEY, "Total Costs" )
        # remove extra characters
        new_service = new_service.replace("$", " " )
        rsrcrowHTML = rsrcrowHTML + '<td style="text-align: left;">' + new_service + '</td>'
      #
      # set in cero the provious day
      prevMonthCost = 0     # previous month cost
      currMonthCost = 0 # current month cost
      pctfrmprev = 0  # percentage delta from previous to curent day
      columna_v = 0
      column_p = 0
      matrix_column = 0
      ytd = 0
      pctey = 0
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
          columna_v += 1
          matrix[i_row][matrix_column] = clear(cost_td)
          #matrix[i_row][matrix_column] = 0
          matrix_column += 1
        else:
          if i_row > 0 :
            rsrcrowHTML = rsrcrowHTML + '<td style="text-align: right; padding: 4px;">'
            rsrcrowHTML = rsrcrowHTML + formating_cost(cost_td) + '</td>'
            #
            matrix[i_row][matrix_column] = clear(cost_td)
            matrix_column += 1
          else:
            #if columna_v >= arguments :
            #  rsrcrowHTML = rsrcrowHTML + '<td style="text-align: right; padding: 4px;"> $0.00 </td>'
            #  matrix[i_row][matrix_column] = 0
            #  matrix_column += 1
            #else:
            rsrcrowHTML = rsrcrowHTML + '<td style="text-align: right; padding: 4px;">' + '$' + str(arr_totals[columna_v]) + '</td>'
            matrix[i_row][matrix_column] = clear(arr_totals[columna_v])
            columna_v += 1
            matrix_column += 1
        #
        #ytd = ytd + ytd_cola
        ###########################
        # Calculate delta(s) after the first month <td>
        currMonthCost = cost_td
        #
        if cost_first_colum_count == 0 and hide_column == 1: # hide first column
          column_pa += 1
        else:
          if i_row > 0 :
            rsrcrowHTML = rsrcrowHTML + prevdaycost_table(prevMonthCost, currMonthCost)
          else:
            rsrcrowHTML = rsrcrowHTML + arr_totals_percent[column_pa]
            column_pa += 1
        prevMonthCost = cost_td
        cost_first_colum_count += 1
      ###########################    
      if timeperiods['TimePeriod']['Start'] == LASTMONTH:
        if i_row > 0 :
          cost_last_colum_projected = cost_td
        else:
          cost_last_colum_projected = arr_totals[arguments-2]
      #
      ##############################################################
      # year to date
      matrix_ytd = year_to_date_services_fix(accountList, MONTHLY_START_DATE_YTD, MONTHLY_END_DATE, accountDict, AWS_TAG_KEY, MONTHLY_COST_DATES_YTD, MONTHSBACK_SELECTED, displayList, aws_tag_filter_list)
      ytd = ytd + matrix_ytd[i_row]
      ytd = round(ytd,2)
      rsrcrowHTML = rsrcrowHTML + '<td style="text-align: right;">' + '$' + str(ytd) + '</td>'
      # 
      # proyjected cost
      proyjected_cost = projected_year(LASTMONTH, cost_last_colum_projected, ytd) 
      proyjected_cost = round(proyjected_cost,2)
      rsrcrowHTML = rsrcrowHTML + '<td style="text-align: right;">' +  '$' + str(proyjected_cost) + '</td>'
      emailHTML = emailHTML + rsrcrowHTML + '</tr>'       # Include row for displaying
      #
      i_row += 1                                # row counter
    #
    # last raw No tag key
    if not aws_tag_filter_list:
      # last row
      i_column = 0
      ytd_last_column = 0
      rsrcrowHTML = ''      # Resource row HTML code
      rsrcrowHTML = row_color(i_row)
      rsrcrowHTML = rsrcrowHTML + '<td style="text-align: left;"> No tag key: ' + AWS_TAG_KEY + '</td>'
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
          ytd_last_column = ytd_last_column + data
          #
          if i_column == 0:
            cost_first_colum_no_tag = curr_day_cost
          #
          if i_column != 0:
            # cost
            rsrcrowHTML = rsrcrowHTML + '<td>' + formating_cost(data) + '</td>'
            # percent calculation
            rsrcrowHTML = rsrcrowHTML + prevdaycost_table(prev_day_cost, curr_day_cost)
            #
            prev_day_cost = curr_day_cost
            cost_last_colum_projected = curr_day_cost
          else:
            prev_day_cost = curr_day_cost
            #prev_day_cost = curr_day_cost
            if hide_column == 0:
              rsrcrowHTML = rsrcrowHTML + '<td>' + formating_cost(data) + '</td>'
              rsrcrowHTML = rsrcrowHTML + prevdaycost_table(0, 0)
              #cost_last_colum_projected = 0
        #
        i_column += 1
      #
      #cost_last_colum_no_tag = curr_day_cost
      # year to date last column
      ytd_last_column = year_to_date_services_no_tag(matrix_ytd)
      rsrcrowHTML = rsrcrowHTML + '<td style="text-align: right;">' + '$' + str(ytd_last_column) + '</td>'
      #
      proyjected_cost = projected_year(LASTMONTH, cost_last_colum_projected,ytd_last_column)
      proyjected_cost = round(proyjected_cost,2)
      rsrcrowHTML = rsrcrowHTML + '<td style="text-align: right;">' +  '$' + str(proyjected_cost) + '</td>' + '</tr>'
      #
      emailHTML = emailHTML + rsrcrowHTML       # Include row for displaying
  #
  emailHTML = emailHTML + '</table><br>\n'

  # comments
  emailHTML = emailHTML + "<div style='color: Teal; font-size: 12px; font-style: italic;'> \
              **Color Legend : The color change is dynamically determined ranging from Red to Blue including Black.</div>\n"

  #print("emailHTML", emailHTML)

  return emailHTML

#--------------------------------------------------------------------------------------------------
# Lambda Handler

def lambda_handler(context=None, event=None):

    DISPLAY_BOTH_TABLES = os.environ['DISPLAY_BOTH_TABLES']

    # Using dictionary of 23 named accounts, get cost info from Cost Explorer
    # Result is dictionary keyed by account number
    mainCostDict = ce_get_costinfo_per_account(accountDict, MONTHLY_START_DATE, MONTHLY_END_DATE, aws_tag_filter_list, AWS_TAG_KEY)

    # Re-sort the mainCostDict; create a new dictionary keyed by reporting date
    mainDailyDict = process_costchanges_per_month(mainCostDict, MONTHLY_COST_DATES, MONTHSBACK)

    # Create a new dictionary (from mainDailyDict) with only big cost accounts labeled
    # Combine other accounts into "Others"
    mainDisplayDict = process_costchanges_for_display(mainDailyDict, displayList)

    # Update mainDisplayDict dictionary to include daily percent changes
    finalDisplayDict = process_percentchanges_per_day(mainDisplayDict,MONTHLY_COST_DATES)

    # for total cost
    global arr_totals
    arr_totals = create_report_total(finalDisplayDict,displayList)
    # 
    global arr_totals_percent
    arr_totals_percent = create_report_total_percent(finalDisplayDict,displayList)

    # Generate HTML code using finalDisplayDict and send HTML e-mail
    summary_html = create_report_html(finalDisplayDict, BODY_HTML)

    # =============================================================================================

    account_numbers = get_linked_accounts(accountList, MONTHLY_START_DATE, MONTHLY_END_DATE)
    #
    # Get cost data from the Master Payer Account
    cost_data_Dict = get_cost_data(account_numbers, MONTHLY_START_DATE, MONTHLY_END_DATE)
    
    # Restruction dictionary for email message display
    display_cost_data_Dict = restructure_cost_data(cost_data_Dict, account_numbers)

    # Put the restructured dictionary in HTML table
    html_for_email = generate_html_table(cost_data_Dict, display_cost_data_Dict, finalDisplayDict)
    #
    # to activate the first table
    if DISPLAY_BOTH_TABLES == 'true' :
      html_for_email = summary_html + '<br><br>' + html_for_email
    else :
      html_for_email = html_for_email

    # Send HTML e-mail
    send_report_email(html_for_email)
