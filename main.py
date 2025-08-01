# -*- coding: utf-8 -*-
"""
@author: jayaharyonomanik
Edited By: thefyk
"""

import os
import sys
import yaml
import json
import logging
import argparse
from datetime import datetime
from pathlib import Path
from github import Github

from tableau_api import TableauApi
import authentication


logger = logging.getLogger()
logger.setLevel(logging.INFO)
logging.basicConfig(format='%(asctime)s %(message)s')

class TableauWorkbookError(Exception):
    """Exception raised for errors in tableau workbook.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f'{self.message}'

def get_full_schema(project_dir):
    logging.info(project_dir)
    from mergedeep import merge, Strategy
    full_schema = None
    for schema_file in Path(project_dir).glob("**/*.yml"):
        schema = yaml.full_load(schema_file.open())
        full_schema = merge(full_schema, schema, strategy=Strategy.ADDITIVE) if full_schema is not None else schema

    new_schema = dict({'workbooks':dict()})
    for value in full_schema['workbooks']:
        new_schema['workbooks'][value['file_path']] = value

    return new_schema

def comment_pr(repo_token, message):
    g = Github(repo_token)
    repo = g.get_repo(os.environ['GITHUB_REPOSITORY'])
    event_payload = open(os.environ['GITHUB_EVENT_PATH']).read()
    json_payload =  json.loads(event_payload)
    pr = repo.get_pull(json_payload['number'])
    pr.create_issue_comment(message)
    return True

def get_addmodified_files(repo_token):
    g = Github(repo_token)
    repo = g.get_repo(os.environ['GITHUB_REPOSITORY'])
    event_payload = open(os.environ['GITHUB_EVENT_PATH']).read()
    json_payload =  json.loads(event_payload)
    pr = repo.get_pull(json_payload['number'])
    list_files = [file.filename for file in pr.get_files() if os.path.exists(file.filename)]
    logging.info(repo)
    logging.info(f'File List: {list_files}')

    list_files_escaped = []
    for filename in list_files:
        if filename[:1] == '/':
            list_files_escaped.append(filename[1:])
        else:
            list_files_escaped.append(filename)

    logging.info(f'File List: {list_files}')
    logging.info(f'File List Escaped: {list_files_escaped}')
    return list_files_escaped

def submit_workbook(workbook_schema, file_path, env):
    environment = os.environ['ENVIRONMENT']
    user = os.environ['USER']

    logging.info(f'User: {user}')
    environment_projects = {'stage': 'Stage','prod': 'Prod'}
    environment_project = environment_projects.get(environment, f'Dev/{user}') 

    base_project = os.environ['BASE_PROJECT']
    project_path = f'{base_project}/{environment_project}'
    sub_path = workbook_schema.get('project_path')
    if sub_path:
        project_path = f'{project_path}/{sub_path}'

    logging.info('Setting Tableau API')
    token = os.environ['PAT']
    logging.error(token)
    tableau_api = TableauApi(os.environ['PATNAME'],
                            os.environ['PAT'],
                            os.environ['TABLEAU_URL'] + '/api/',
                            os.environ['TABLEAU_URL'],
                            os.environ['SITE_ID'],
                            os.environ['SITE_NAME'])

    logging.info('Getting Tableau Project ID')
    project_id = tableau_api.get_project_id_by_path_with_tree(project_path)
    if project_id is None:
            logging.info("Existing project on a given path doesn't exist, creating new project")
            project_id = tableau_api.create_project_by_path(project_path)

    logging.info(f'Project ID: {project_id}')

    hidden_views = None
    show_tabs = False
    tags = None
    description = None

    logging.info(f'Setting Options')
    if 'option' in workbook_schema:
        hidden_views = workbook_schema['option']['hidden_views'] if 'hidden_views' in workbook_schema['option'] else None
        show_tabs = workbook_schema['option']['show_tabs'] if 'show_tabs' in workbook_schema['option'] else False
        tags = workbook_schema['option']['tags'] if 'tags' in workbook_schema['option'] else None
        description = workbook_schema['option']['description'] if 'description' in workbook_schema['option'] else None

    logging.info(f'Publishing Workbook')
    
    connections = []
    for connection_name in workbook_schema.get('connections'):
        connections.append(authentication.get_tableau_connection(connection_name))

    new_workbook = tableau_api.publish_workbook(name =  workbook_schema['name'],
                                                project_id = project_id,
                                                file_path = file_path,
                                                hidden_views = hidden_views,
                                                show_tabs = show_tabs,
                                                tags = tags,
                                                description = description,
                                                connections = connections)

    return project_path, new_workbook

def refresh_workbooks(full_schema_config):
    environment = os.environ['ENVIRONMENT']
    user = os.environ['USER']

    environment_projects = {'stage': 'Stage','prod': 'Prod'}
    environment_project = environment_projects.get(environment, f'Dev/{user}') 

    base_project = os.environ['BASE_PROJECT']
    project_path = f'{base_project}/Dev'

    tableau_api = TableauApi(os.environ['PATNAME'],
                            os.environ['PAT'],
                            os.environ['TABLEAU_URL'] + '/api/',
                            os.environ['TABLEAU_URL'],
                            os.environ['SITE_ID'],
                            os.environ['SITE_NAME'])


    current_hour = datetime.now().hour
    logging.info(f'REFRESHING WORKBOOKS FOR HOUR {current_hour}')
    for workbook_name, workbook_config in full_schema_config['workbooks'].items():
        for schedule in workbook_config.get('schedules', []):
            logging.info(f'{workbook_name}: {schedule}')
            if schedule.startswith('DAILY'):
                hour = int(schedule[-2:])
                if hour == current_hour:
                    logging.info(f"Refreshing Workbook {workbook_name}")
                    project_id = tableau_api.get_project_id_by_path_with_tree(project_path)
                    tableau_api.refresh_workbook(workbook_name, project_id)

def main(args):
    logging.info(f"Workbook Dir : { args.workbook_dir }")
    logging.info(f"Environments : { args.env }")

    full_schema_config = get_full_schema(args.workbook_dir)
    logging.info(str(full_schema_config))

    if os.environ.get('ACTION') == 'REFRESH_WORKBOOKS':
        logging.info('REFRESHING WORKBOOKS WITH REFRESH SCHEDULES')
        refresh_workbooks(full_schema_config)
        return

    addmodified_files = get_addmodified_files(args.repo_token)
    addmodified_files = [file.lstrip(args.workbook_dir) for file in addmodified_files if args.workbook_dir in file and ".twb" in file]

    if len(addmodified_files) > 0:
        logging.info("Add & Modified Files:")
        logging.info(addmodified_files)

        addmodified_stripped_files = []
        for filename in addmodified_files:
            if filename[:1] == '/':
                addmodified_stripped_files.append(filename[1:])
            else:
                addmodified_stripped_files.append(filename)

        addmodified_files = addmodified_stripped_files

        status = True
        list_message = list()
        for file in addmodified_files:
            if file in full_schema_config['workbooks'].keys():
                workbook_schema = full_schema_config['workbooks'][file]
                logging.info(f"Publishing workbook : { workbook_schema['project_path'] + '/' + workbook_schema['name'] } to Tableau")
                project_path, new_workbook = submit_workbook(workbook_schema,
                                                                args.workbook_dir + "/" + file,
                                                                args.env)
                logging.info(f"Workbook : { project_path } Published to Tableau")
                list_message.append(f"Workbook : { project_path } published to Tableau  :heavy_check_mark:")

            else:
                logging.info(f"Skip publishing workbook { file } not listed in config files")

        comment_pr(args.repo_token, "\n".join(list_message))
        if status is False:
            #raise TableauWorkbookError("\n".join(list_message))
            sys.exit(1)
    else:
        logging.info("No file changes detected")
    sys.exit(0)


if __name__=='__main__':
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument('--workbook_dir', action='store', type=str, required=False)
    parser.add_argument('--env', action = 'store', type = str, required = True)
    parser.add_argument('--repo_token', action = 'store', type=str, required = True)

    args = parser.parse_args()
    main(args)
