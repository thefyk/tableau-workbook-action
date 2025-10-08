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
        connection.username = user
        connection.password = password
        connection.set_attribute('httpPath', http_path)

        if hasattr(connection, '_connectionXML'):
            connection._connectionXML.set('_.fcp.DatabricksCatalog.true...v-http-path', http_path)


    return connection
