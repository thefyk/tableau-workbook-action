import os
from tableauserverclient import ConnectionCredentials, ConnectionItem

def get_tableau_connection(connection_name):
    host = os.environ[f'CONNECTIONS_{connection_name}_HOST']
    user = os.environ.get(f'CONNECTIONS_{connection_name}_USER')
    password = os.environ.get(f'CONNECTIONS_{connection_name}_PASSWORD')

    if connection_name.lower() == 'snowflake':
        connection = ConnectionItem()
        connection.server_address = host
        connection.connection_credentials = ConnectionCredentials(user, password, True)

    if connection_name.lower() == 'databricks':
        http_path = os.environ[f'CONNECTIONS_{connection_name}_HTTP_PATH']

        connection = ConnectionItem()
        connection.server_address = host
        connection.port = 443
        connection.username = 'token'
        connection.password = password

    return connection
