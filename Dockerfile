FROM python:3.8

COPY ./ingress_adapter_ikontrol ./ingress_adapter_ikontrol
COPY requirements.in ./

RUN pip install pip-tools
RUN pip-compile --generate-hashes requirements.in

RUN pip install --no-cache-dir -r requirements.txt
