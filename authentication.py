import os
from tableauserverclient import ConnectionCredentials, ConnectionItem

host = 'nfa05164.snowflakecomputing.com'
user = 'TABLEAU_EXT_DA'
password = 'eyJraWQiOiIyNTg4NjkxNDY3NjU1MjMzOCIsImFsZyI6IkVTMjU2In0.eyJwIjoiMzk1MDAyOTc0ODE3OjM5NTAwMjk3MDUwMSIsImlzcyI6IlNGOjEwMDkiLCJleHAiOjE3Nzg2OTYzMjJ9.ThnGl_SOGMmBm-p_sRyX70HqH5xe5dgH4DfgrAXa2_uoaysbtCLRM9u_HQOzVGpY8xzh8pYcKpUEFAFcrDSoug'

def get_tableau_connection(connection_name):
    host = os.environ[f'{connection_name}_HOST']
    user = os.environ[f'{connection_name}_USER']
    password = os.environ[f'{connection_name}_PASSWORD']

    connection = ConnectionItem()
    connection.server_address = host
    connection.connection_credentials = ConnectionCredentials(user, password, True)

    return connection
