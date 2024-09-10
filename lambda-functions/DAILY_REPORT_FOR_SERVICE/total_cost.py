from html_function import *
#
#------------------------------------------------------------
def total_cost(emailDisplayDict_input, displayList_input, hide_column):
  #
  i_row=0
  i_data=0
  rsrcrowHTML = '<td style="text-align: left;"> Total Costs </td>'
  arguments = len(emailDisplayDict_input)
  arguments = arguments * 2 -1
  account = 0
  #
  for reportDate in emailDisplayDict_input:
    #
    for accountNum in displayList_input:
      if i_row == 0:
        arr_totals = "$ {:,.2f} ".format(round(emailDisplayDict_input[reportDate][accountNum]['Cost'],2))
        cost_last_colum = round(emailDisplayDict_input[reportDate][accountNum]['Cost'],2)
        # hide first colum
        if i_data == 0 and hide_column == 1:
          nada = 0
        else:
          rsrcrowHTML = rsrcrowHTML + '<td style="text-align: right;">' + arr_totals + '</td>'
        #
        if i_data == 0 and hide_column == 1:
          nada = 0
        else:
          if emailDisplayDict_input[reportDate][accountNum]['percentDelta'] == None:
            #arr_totals_percent = '<td style="text-align: right;">0.00%</td>'
            arr_totals_percent = evaluate_change('0')
            rsrcrowHTML = rsrcrowHTML + arr_totals_percent
          else:
            arr_totals_percent = evaluate_change(emailDisplayDict_input[reportDate][accountNum]['percentDelta'])
            rsrcrowHTML = rsrcrowHTML + arr_totals_percent 
        #
        # obtain first colum data
        if i_data == 0 :
          i_data = 1
          cost_first_colum = round(emailDisplayDict_input[reportDate][accountNum]['Cost'],2)
        #
        i_row += 1
        #
      else:
        i_row = 0
      #
  ######
  value = evaluate_change(overall_percent_delta_calculation(cost_first_colum,cost_last_colum))
  rsrcrowHTML = rsrcrowHTML + value 
  #
  #
  return rsrcrowHTML
#------------------------------------------------------------
def total_cost_first_column(emailDisplayDict_input, displayList_input):
  #
  i_row=0
  #
  for reportDate in emailDisplayDict_input:
    #
    for accountNum in displayList_input:
      if i_row == 0:
        value = round(emailDisplayDict_input[reportDate][accountNum]['Cost'],2)
        #
      i_row += 1
      #
  return value
#------------------------------------------------------------
def total_cost_last_column(emailDisplayDict_input, displayList_input):
  #
  i_row=0
  #
  for reportDate in emailDisplayDict_input:
    #
    for accountNum in displayList_input:
      value = round(emailDisplayDict_input[reportDate][accountNum]['Cost'],2)
      #
  return value
#------------------------------------------------------------
def overall_percent_delta_calculation(cost_first_colum,cost_last_colum):
  #
  #print("cost_first_colum", cost_first_colum)
  #print("cost_last_colum", cost_last_colum)
  #
  if cost_last_colum == 0 and cost_first_colum == 0:
    pctfrmprev = 0
  elif cost_last_colum != 0 and cost_first_colum != 0:
    pctfrmprev = (cost_last_colum /cost_first_colum) - 1
  elif cost_last_colum != 0 and cost_first_colum == 0:
    cost_first_colum = 0.01
    pctfrmprev = (cost_last_colum /cost_first_colum) - 1
  else:
    cost_last_colum = 0.01
    pctfrmprev = (cost_last_colum /cost_first_colum) - 1
  #
  return round(pctfrmprev,2)
