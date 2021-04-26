FROM python:3.8

COPY ./ingress_adapter_ikontrol ./ingress_adapter_ikontrol
COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt