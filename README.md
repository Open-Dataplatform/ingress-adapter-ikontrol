# ingress-adapter-ikontrol

## Introduction
This adapter calls the iKontrol endpoints and ingest ZIP files in an "ingress" dataset in regard to their project ids.

### Usage
```sh
$ python -m ingress_adapter_ikontrol.adapter
```

## Configuration
The application needs two configuration files `conf.ini` (see `conf.example.ini`) and `credentials.ini` (see `credentials.example.ini`). 
The configuration file, `conf.ini`, must be placed in the root of the project or in the locations `/etc/osiris/conf.ini` or 
`/etc/ingress-adapter-ikontrol-conf.ini`. 

```
[Logging]
configuration_file = log.conf

[Azure Storage]
ingress_url = https://<storage_account>.dfs.core.windows.net

[Datasets]
source = <source_guid>

[iKontrol API]
api_url = https://publicapi.ikontrol.dk
api_version = <api_version>
```

The configuration file, `credentials.ini`, must be placed in the root of the project or in the location `/vault/secrets/credentials.ini`.

```
[Authorization]
tenant_id = <tenant_id>
client_id = <client_id>
client_secret = <client_secret>

[iKontrol Authorization]
api_key = <api_key>
username = <username>
password = <password>
```

### Logging
Logging can be controlled by defining handlers and formatters using [Logging Configuration](https://docs.python.org/3/library/logging.config.html) and specifically the [config fileformat](https://docs.python.org/3/library/logging.config.html#logging-config-fileformat). 
The location of the log configuration file (`Logging.configuration_file`) must be defined in the configuration file of the application as mentioned above.

Here is an example configuration:
```
[loggers]
keys=root

[handlers]
keys=consoleHandler,fileHandler

[formatters]
keys=fileFormatter,consoleFormatter

[logger_root]
level=ERROR
handlers=consoleHandler

[handler_consoleHandler]
class=StreamHandler
formatter=consoleFormatter
args=(sys.stdout,)

[handler_fileHandler]
class=FileHandler
formatter=fileFormatter
args=('logfile.log',)

[formatter_fileFormatter]
format=%(asctime)s - %(name)s - %(levelname)s - %(message)s
datefmt=

[formatter_consoleFormatter]
format=%(levelname)s: %(name)s - %(message)s
```

#### Grant access to the dataset
The application must be granted read access to the ingress dataset and write-access to the egress dataset on 
[the Data Platform](https://dataplatform.energinet.dk/).

Add the application you created earlier, using the `<YOUR APP NAME>` name, to the read- and write-access lists.


## Development

### tox

Development for this project relies on [tox](https://tox.readthedocs.io/).

Make sure to have it installed.

### Commands

If you want to run all commands in tox.ini

```sh
$ tox
```

#### Linting

You can also run a single linter specified in tox.ini. For example:

```sh
$ tox -e flake8
```


#### Tests

(No test at the moment)

Run unit tests.

```sh
$ tox -e py3
```

Run a specific testcase.

```sh
$ tox -e py3 -- -x tests/test_main.py