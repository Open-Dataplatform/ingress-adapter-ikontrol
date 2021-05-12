"""
iKontrol Adapter for Ingress.
"""
import json
import requests

from requests.auth import HTTPBasicAuth
from osiris.adapters.ingress_adapter import IngressAdapter
from osiris.core.configuration import Configuration, ConfigurationWithCredentials

configuration = Configuration(__file__)
configuration_credentials = ConfigurationWithCredentials(__file__)
credentials_config = configuration_credentials.get_credentials_config()
config = configuration.get_config()
logger = configuration.get_logger()


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

    def get_project_schemes_and_tasks(self, project_id: int) -> bytes:
        """
        Returns project details, schemes, and tasks in the given project ID.
        """
        project = self.__get_project(project_id)
        schemes = self.__get_project_schemes(project_id)
        tasks = self.__get_all_project_tasks(project_id)

        schemes_and_tasks = {
            'project': project,
            'schemes': schemes,
            'tasks': tasks
        }

        return json.dumps(schemes_and_tasks).encode('UTF-8')


class IKontrolAdapter(IngressAdapter):
    """
    The iKontrol Adapter.
    Implements the retrieve_data method.
    """
    # pylint: disable=too-many-arguments
    def __init__(self, ingress_url, tenant_id, client_id, client_secret, dataset_guid, client):
        super().__init__(ingress_url, tenant_id, client_id, client_secret, dataset_guid)

        self.client = client
        self.project_ids = self.client.get_all_project_ids()
        self.current_index = 0
        self.current_projectid = None

    def retrieve_data(self) -> bytes:
        """
        Retrieves the data from iKontrol and returns it.
        """
        if self.current_index >= len(self.project_ids):
            logger.error('Current index out of range of project ids')
            raise IndexError('Current index out of range')

        self.current_projectid = self.project_ids[self.current_index]
        self.current_index += 1

        logger.debug('Receiving data of ProjectId: %s', self.current_projectid)
        project_schemes_and_tasks = self.client.get_project_schemes_and_tasks(self.current_projectid)
        logger.debug('Successfully received data of ProjectId: %s', self.current_projectid)

        return project_schemes_and_tasks

    def get_filename(self) -> str:
        return f'{self.current_projectid}.json'

    def has_more_projects(self) -> bool:
        """
        Return bool whether more projects exist in the list.
        """
        return self.current_index < len(self.project_ids)


def main():
    """
    Initialize class and upload ZIP file.
    """
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

    # print(adapter.retrieve_data())
    logger.info('Running the iKontrol Ingress Adapter')

    while adapter.has_more_projects():
        adapter.upload_data()

    logger.info('Successfully finished the iKontrol Ingress Adapter')


if __name__ == '__main__':
    main()
