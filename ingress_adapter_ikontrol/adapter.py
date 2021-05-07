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

    def __get_all_projects(self):
        """
        Returns all the details of a project.
        """
        response = requests.get(
            url=f'{self.api_url}/{self.api_version}/{self.api_key}/Project/GetAll',
            auth=HTTPBasicAuth(self.username, self.password)
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

    def get_all_project_ids(self) -> list:
        """
        Returns a list of all project IDs.
        """
        all_projects = self.__get_all_projects()
        project_ids = []

        for project in all_projects:
            project_ids.append(project['Id'])

        return project_ids


class IKontrolAdapter(IngressAdapter):
    """
    The iKontrol Adapter.
    Implements the retrieve_data method.
    """
    # pylint: disable=too-many-arguments
    def __init__(self, ingress_url, tenant_id, client_id, client_secret, dataset_guid,
                 api_url, api_version, api_key, username, password):
        super().__init__(ingress_url, tenant_id, client_id, client_secret, dataset_guid)

        self.client = IKontrolClient(api_url, api_version, api_key, username, password)
        self.project_ids = self.client.get_all_project_ids()
        self.current_index = 0
        self.current_projectid = None

    def retrieve_data(self) -> bytes:
        """
        Retrieves the data from iKontrol and returns it.
        """
        self.current_projectid = self.project_ids[self.current_index]
        logger.debug('Recieving ZIP of ProjectId: %s', self.current_projectid)

        self.current_index += 1
        project_zip = self.client.get_project_zip(self.current_projectid)
        logger.debug('Successfully recieved ZIP of ProjectId: %s', self.current_projectid)

        return project_zip

    def get_filename(self) -> str:
        return f'{self.current_projectid}.zip'

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
    username = credentials_config['iKontrol Authorization']['username']
    password = credentials_config['iKontrol Authorization']['password']

    ingress_url = config['Azure Storage']['ingress_url']
    dataset_guid = config['Datasets']['source']
    api_url = config['iKontrol API']['api_url']
    api_version = config['iKontrol API']['api_version']
    api_key = config['iKontrol API']['api_key']

    adapter = IKontrolAdapter(ingress_url, tenant_id, client_id, client_secret, dataset_guid,
                              api_url, api_version, api_key, username, password)

    # print(adapter.retrieve_data())
    logger.info('Running the iKontrol Ingress Adapter')
    while adapter.has_more_projects():
        adapter.upload_data()

    logger.info('Successfully finished the iKontrol Ingress Adapter')


if __name__ == '__main__':
    main()
