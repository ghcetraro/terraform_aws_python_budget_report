#
import boto3
# Create Cost Explorer service client using saved credentials
cost_explorer = boto3.client('ce')
#
#--------------------------------------------------------------------------------------------------
# Get Linked Account Dimension values from Master Payer Cost Explorer
def get_linked_accounts(accountList, START_DATE, END_DATE):
  #
  results = []    # holder for full linked account results
  token = None    # holder for NextPageToken
  #
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
  active_accounts = []    # holder for just linked account numbers
  defined_accounts = []   # holder for reporting accounts
  #
  for accountnumbers in results:
    active_accounts.append(accountnumbers['Value'])
  #
  # use account number for report if it exists in dimension values
  for accountnumbers in accountList:
    if accountnumbers in active_accounts:
      defined_accounts.append(accountnumbers)
  #
  return defined_accounts
#--------------------------------------------------------------------------------------------------
# Get Cost Data from Master Payer Cost Explorer

def get_cost_data(account_numbers, START_DATE, END_DATE):
  #
  results = []    # holder for service costs
  token = None    # holder for NextPageToken
  #
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
        {'Type': 'DIMENSION', 'Key': 'SERVICE'}
      ],
      # Filter using active accounts listed in MEDaily Spend View
      Filter = {'Dimensions': {'Key': 'LINKED_ACCOUNT', 'Values': account_numbers}},
      **kwargs)
    #
    results += data['ResultsByTime']
    token = data.get('NextPageToken')
    if not token:
      break
  #
  return results
#--------------------------------------------------------------------------------------------------
# Get cost information for accounts defined in accountDict
def ce_get_costinfo_per_account(accountDict_input, START_DATE, END_DATE):
    accountCostDict = {} # main dictionary of cost info for each account
    for key in accountDict_input:
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
        periodCost = 0      # holder for cost of the account in reporting period
        # Calculate cost of the account in reporting period
        for dayCost in response['ResultsByTime']:
            periodCost = periodCost + float(dayCost['Total']['UnblendedCost']['Amount'])
        print('Cost of account ', key, ' for the period is: ', periodCost )
        # Only include accounts that have non-zero cost in the dictionary
        if periodCost > 0:
            accountCostDict.update({key:response})
    return accountCostDict