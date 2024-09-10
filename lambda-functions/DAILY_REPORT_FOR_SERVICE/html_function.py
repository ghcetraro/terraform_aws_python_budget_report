#
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
  #
  return text_out
########################################################################
# Function to color rows
def row_color(i_row):
  if (i_row % 2) == 0:
    return "<tr style='background-color: WhiteSmoke;'>"
  else:
    return "<tr>"
######################################################################
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