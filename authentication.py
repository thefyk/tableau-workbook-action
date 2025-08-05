import os
from tableauserverclient import ConnectionCredentials, ConnectionItem

def get_tableau_connection(connection_name):
    host = os.environ[f'CONNECTIONS_{connection_name}_HOST']
    user = os.environ[f'CONNECTIONS_{connection_name}_USER']
    password = os.environ[f'CONNECTIONS_{connection_name}_PASSWORD']

    connection = ConnectionItem()
    connection.server_address = host
    connection.connection_credentials = ConnectionCredentials(user, password, True)

    return connection
