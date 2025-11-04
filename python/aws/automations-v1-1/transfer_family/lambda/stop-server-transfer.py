import boto3
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    transfer_client = boto3.client('transfer')
    server_id = event.get('ServerId')

    try:
        transfer_client.stop_server(
            ServerId=server_id
        )
        return {
            'statusCode': 200,
            'body': 'Server ´{}´ stopped successfully'.format(server_id)
        }
    except ClientError as e:
        return {
            'statusCode': 500,
            'body': f'Error stopping server: {str(e)}'
        }