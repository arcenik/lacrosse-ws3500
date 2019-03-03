FROM python:3.7-stretch

RUN mkdir -vp /opt/app
WORKDIR /opt/app

COPY ./requirement.txt /opt/app
RUN pip install -r requirement.txt

ENV HOST 127.0.0.1
ENV PORT 5000

COPY . /opt/app

CMD ["bash", "-cx", "python2 daemon.py --host ${HOST} --port ${PORT}"]
