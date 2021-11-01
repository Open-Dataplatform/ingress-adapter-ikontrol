"""
iKontrol Adapter for Ingress.
"""
import json
import os
import shutil
import tempfile
import zipfile
import logging
import logging.config
from configparser import ConfigParser

import requests

from requests.auth import HTTPBasicAuth
from osiris.core.azure_client_authorization import ClientAuthorization
from osiris.adapters.ingress_adapter import IngressAdapter


logger = logging.getLogger(__file__)


class IKontrolClient:
    """
    iKontrol Client - Connects to the iKontrol API and provides the calls.
    """
    # pylint: disable=too-many-arguments
    def __init__(self, api_url, api_version, api_key, username, password):
        self.api_url = api_url
        self.api_version = api_version
        self.api_key = api_key
        self.username = username
        self.password = password
        self.tasks = self.__get_all_tasks()

    def __get_all_projects(self):
        """
        Returns all the details of all projects.
        """
        response = requests.get(
            url=f'{self.api_url}/{self.api_version}/{self.api_key}/Project/GetAll',
            auth=HTTPBasicAuth(self.username, self.password)
        )

        return json.loads(response.content)

    def __get_project(self, project_id: int):
        """
        Returns all the details of a project.
        """
        response = requests.get(
            url=f'{self.api_url}/{self.api_version}/{self.api_key}/Project/Get',
            auth=HTTPBasicAuth(self.username, self.password),
            params={'id': project_id}
        )

        return json.loads(response.content)

    def get_project_zip(self, project_id: int):
        """
        Returns a ZIP-file containing every PDF possible as set up in iKontrol.
        """
        response = requests.get(
            url=f'{self.api_url}/{self.api_version}/{self.api_key}/Documentation/GetProjectZip',
            auth=HTTPBasicAuth(self.username, self.password),
            params={'projectId': project_id}
        )

        return response.content

    def __get_project_schemes(self, project_id: int, from_date='1970-01-01'):
        """
        Returns every scheme in a project.
        """
        response = requests.get(
            url=f'{self.api_url}/{self.api_version}/{self.api_key}/Scheme/GetByProjectId',
            auth=HTTPBasicAuth(self.username, self.password),
            params={'projectId': project_id, 'from': from_date}
        )

        return json.loads(response.content)

    def __get_tasks(self, task_type_id: int, from_date='1970-01-01'):
        """
        Returns every task with the given task type id.
        """
        response = requests.get(
            url=f'{self.api_url}/{self.api_version}/{self.api_key}/Task/Get',
            auth=HTTPBasicAuth(self.username, self.password),
            params={'taskTypeId': task_type_id, 'from': from_date}
        )

        return json.loads(response.content)

    def __get_menuitems(self):
        """
        Returns all active menuitems.
        """
        response = requests.get(
            url=f'{self.api_url}/{self.api_version}/{self.api_key}/MenuItem/GetAll',
            auth=HTTPBasicAuth(self.username, self.password),
        )

        return json.loads(response.content)

    def __get_scheme_pdf(self, response_id):
        """
        Returns scheme PDF
        """
        response = requests.get(
            url=f'{self.api_url}/{self.api_version}/{self.api_key}/Scheme/DownloadSchemeResponse',
            auth=HTTPBasicAuth(self.username, self.password),
            params={'responseId': response_id}
        )

        return response.content

    def get_all_project_ids(self) -> list:
        """
        Returns a list of all project IDs.
        """
        all_projects = self.__get_all_projects()
        project_ids = []

        for project in all_projects:
            project_ids.append(project['Id'])

        return project_ids

    def __get_all_tasktype_ids(self) -> list:
        """
        Returns a list of all tasktype IDs.
        """
        all_menuitems = self.__get_menuitems()
        task_type_ids = []

        # The task menu item type id 4, so all task ids are returned
        for menuitem in all_menuitems:
            if ('MasterTypeId', 4) in menuitem.items():
                task_type_ids.append(menuitem['Id'])

        return task_type_ids

    def __get_all_tasks(self):
        task_type_ids = self.__get_all_tasktype_ids()
        tasks = []

        for task_type_id in task_type_ids:
            tasks.extend(self.__get_tasks(task_type_id))

        return tasks

    def __get_all_project_tasks(self, project_id: int) -> list:
        """
        Returns a list of all tasks in the given project ID.
        """
        project_tasks = []

        for task in self.tasks:
            if ('ProjectId', project_id) in task.items():
                project_tasks.append(task)

        return project_tasks

    def __get_all_scheme_pdfs(self, project_id: int) -> list:
        """
        Returns a list of all scheme responses in the given project ID.
        """
        schemes = self.__get_project_schemes(project_id)
        pdf_responses = []

        for scheme in schemes:
            if 'Id' in scheme:
                pdf_responses.append((scheme['Id'], self.__get_scheme_pdf(scheme['Id'])))

        return pdf_responses

    def __get_project_schemes_and_tasks(self, project_id: int) -> bytes:
        """
        Returns project details, schemes, and tasks in the given project ID.
        """
        project = self.__get_project(project_id)
        schemes = self.__get_project_schemes(project_id)
        tasks = self.__get_all_project_tasks(project_id)

        data = {
            'project': project,
            'schemes': schemes,
            'tasks': tasks
        }

        return json.dumps(data).encode('UTF-8')

    def write_to_zip(self, zfd, zip_dir: str, project_id: int):
        """
        Writes JSON file and PDF(s) to ZIP-file.
        """
        for response_id, scheme_pdf in self.__get_all_scheme_pdfs(project_id):
            file_path = os.path.join(zip_dir, f'Schemeresponse-{response_id}.pdf')

            with open(file_path, 'bw') as file:
                file.write(scheme_pdf)

            zfd.write(file_path, f'Schemeresponse-{response_id}.pdf')

        file_path = os.path.join(zip_dir, f'{project_id}.json')

        with open(file_path, 'bw') as file:
            file.write(self.__get_project_schemes_and_tasks(project_id))

        zfd.write(file_path, f'{project_id}.json')

    def create_zip_file(self, project_id):
        """
        Returns ZIP containing project details, schemes, and tasks in JSON and scheme PDFs from the given project ID.
        """
        work_dir = "."
        zip_path = os.path.join(work_dir, f'{project_id}.zip')
        zip_dir = tempfile.mkdtemp()

        try:
            with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zfd:
                self.write_to_zip(zfd, zip_dir, project_id)

            with open(zip_path, 'rb') as zip_file:
                return zip_file.read()

        finally:
            shutil.rmtree(zip_dir)
            os.remove(zip_path)


class IKontrolAdapter(IngressAdapter):
    """
    The iKontrol Adapter.
    Implements the retrieve_data method.
    """
    # pylint: disable=too-many-arguments
    def __init__(self, ingress_url, tenant_id, client_id, client_secret, dataset_guid, client):
        client_auth = ClientAuthorization(tenant_id, client_id, client_secret)
        super().__init__(client_auth=client_auth, ingress_url=ingress_url, dataset_guid=dataset_guid)

        self.client = client
        self.project_ids = self.client.get_all_project_ids()
        self.current_index = 0
        self.current_projectid = None

    def retrieve_data(self) -> bytes:
        """
        Retrieves the data from iKontrol and returns it.
        """
        if self.current_index >= len(self.project_ids):
            raise IndexError('Current index out of range')

        self.current_projectid = self.project_ids[self.current_index]
        self.current_index += 1

        logger.debug('Receiving data of ProjectId: %s', self.current_projectid)
        project_zip = self.client.create_zip_file(self.current_projectid)
        logger.debug('Successfully received data of ProjectId: %s', self.current_projectid)

        return project_zip

    def get_filename(self) -> str:
        """
        Get the name of a project ZIP
        """
        return f'{self.current_projectid}.zip'

    def has_more_projects(self) -> bool:
        """
        Return bool whether more projects exist in the list.
        """
        return self.current_index < len(self.project_ids)

    def get_event_time(self):
        pass

    def save_state(self):
        pass


def main():
    """
    Initialize class and upload ZIP file.
    """
    config = ConfigParser()
    config.read(['conf.ini', '/etc/osiris/conf.ini'])
    credentials_config = ConfigParser()
    credentials_config.read(['credentials.ini', '/vault/secrets/credentials.ini'])

    logging.config.fileConfig(fname=config['Logging']['configuration_file'],  # type: ignore
                              disable_existing_loggers=False)

    tenant_id = credentials_config['Authorization']['tenant_id']
    client_id = credentials_config['Authorization']['client_id']
    client_secret = credentials_config['Authorization']['client_secret']
    api_key = credentials_config['iKontrol Authorization']['api_key']
    username = credentials_config['iKontrol Authorization']['username']
    password = credentials_config['iKontrol Authorization']['password']

    ingress_url = config['Azure Storage']['ingress_url']
    dataset_guid = config['Datasets']['source']
    api_url = config['iKontrol API']['api_url']
    api_version = config['iKontrol API']['api_version']

    client = IKontrolClient(api_url, api_version, api_key, username, password)
    adapter = IKontrolAdapter(ingress_url, tenant_id, client_id, client_secret, dataset_guid, client)

    # adapter.retrieve_data()
    logger.info('Running the iKontrol Ingress Adapter')
    while adapter.has_more_projects():
        adapter.upload_data()

    logger.info('Successfully finished the iKontrol Ingress Adapter')


if __name__ == '__main__':
    main()
