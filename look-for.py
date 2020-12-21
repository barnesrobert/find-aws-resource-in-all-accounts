#--------------------------------------------------------------------------------------------------
# Function: look-for
# Purpose:  Loops through all AWS accounts and regions within an Organization to find a specific resource
# Inputs:   
#
#  {
#    "view_only": "true|false",
#    "regions": ["us-east-1", ...]
#  }
#
#  Leave the regions sections blank to apply to all regions
#
#--------------------------------------------------------------------------------------------------

import json
import boto3
import botocore
from botocore.exceptions import ClientError
from botocore.exceptions import EndpointConnectionError

sts_client = boto3.client('sts')
organizations_client = boto3.client('organizations')

#--------------------------------------------------------------------------------------------------
# Function handler
#--------------------------------------------------------------------------------------------------
def lambda_handler(event, context):

  # Determine whether the user just wants to view the orphaned logs.
  view_only = ('view_only' in event and event['view_only'].lower() == 'true')

  regions = []

  #--------------------------------------------------
  # Determine which regions to include. Apply to all regions by default.
  #--------------------------------------------------
  if 'regions' in event and type(event['regions']) == list:
    regions = event['regions']

  # Get all regions if not otherwise specified.
  if not regions:
    region_response = boto3.client('ec2').describe_regions()
    regions = [region['RegionName'] for region in region_response['Regions']]


  # Loop through the accounts in the organization.
  response = organizations_client.list_accounts()
  
  for account in response['Accounts']:

    if account['Status'] == 'ACTIVE':

      member_account = sts_client.assume_role(
        RoleArn='arn:aws:iam::{}:role/AWSControlTowerExecution'.format(account['Id']),
        RoleSessionName='look_for'
      )
      
      loop_through_account(account['Id'], member_account, regions, view_only)

  return


#--------------------------------------------------
# function: loop_through_account
#--------------------------------------------------
def loop_through_account(account_id, assumed_role, regions, view_only):

  ACCESS_KEY = assumed_role['Credentials']['AccessKeyId']
  SECRET_KEY = assumed_role['Credentials']['SecretAccessKey']
  SESSION_TOKEN = assumed_role['Credentials']['SessionToken']
  
  #--------------------------------------------------
  # Iterate through the specified regions.
  #--------------------------------------------------
  for region in regions:

    print({
      "Account": account_id,
      "Region": region
      }
    )

    try:
      # Create service client using the assumed role credentials, e.g. S3
      client = boto3.client(
        'SERVICE_NAME',
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        aws_session_token=SESSION_TOKEN,
        region_name=region
        )
      
      for RESOURCE in client.METHOD()['RESOURCES']:
        print('DO SOMETHING HERE')

    except botocore.exceptions.SERVCICE_METHOD_ERROR as error:
      print(ValueError(error))
