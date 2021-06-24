import zipfile
import tempfile
import os
from ingress_adapter_ikontrol.adapter import IKontrolClient


def get_ikontrolclient(mocker):
    """
    Make an instance of the class
    """
    with mocker.patch('ingress_adapter_ikontrol.adapter.IKontrolClient._IKontrolClient__get_all_tasks'):
        client = IKontrolClient(' http://url', '1', 'key', 'user', 'pass')

        return client


def test_get_all_project_ids(mocker):
    """
    Test if get_all_project_ids returns correct list
    """
    mocker.patch(
        'ingress_adapter_ikontrol.adapter.IKontrolClient._IKontrolClient__get_all_projects',
        return_value=[{"Id": 1, "test": "abc"}, {"Id": 2, "test": "bcd"}]
    )
    result = get_ikontrolclient(mocker).get_all_project_ids()

    assert result == [1, 2]


def test_write_to_zip(mocker):
    """
    Test write to zip.
    """
    project_id = 123
    mock_get_all_scheme_pdfs = mocker.patch(
        'ingress_adapter_ikontrol.adapter.IKontrolClient._IKontrolClient__get_all_scheme_pdfs'
    )
    mock_get_all_scheme_pdfs.return_value = [(1, b'abc'), (2, b'bcd')]
    mock_get_project_schemes_and_tasks = mocker.patch(
        'ingress_adapter_ikontrol.adapter.IKontrolClient._IKontrolClient__get_project_schemes_and_tasks'
    )
    mock_get_project_schemes_and_tasks.return_value = b'{"Id": 1, "test": "abc"}'

    try:
        with tempfile.TemporaryDirectory() as zip_dir:
            zip_path = f'{project_id}.zip'
            files_in_zip = os.listdir(zip_dir)
            with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zfd:
                get_ikontrolclient(mocker).write_to_zip(zfd, zip_dir, project_id)

        # with zipfile.ZipFile(zip_path, 'r') as zfd:
    finally:
        os.remove(zip_path)

    for file in files_in_zip:
        if '.json' in file:
            assert file == f'{project_id}.json'
        elif '.pdf' in file:
            for x, _ in mock_get_all_scheme_pdfs.return_value:
                if x == file[-5:-4]:  # Compare only the id from the file name
                    assert file == f'Schemeresponse-{x}.pdf'

    assert zip_path == zfd.filename
    assert mock_get_all_scheme_pdfs.call_count == 1
    assert mock_get_project_schemes_and_tasks.call_count == 1
