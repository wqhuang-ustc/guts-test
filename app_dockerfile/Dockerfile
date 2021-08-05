FROM ubuntu:18.04
LABEL MAINTAINER="Weiqing Huang <wqhuang.ustc@gmail.com>"

RUN apt-get update -y && apt-get install -y python-pip python-dev

COPY ./requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt
COPY ./api.py /app/api.py

WORKDIR /app
EXPOSE 5000
ENTRYPOINT ["python"]

CMD ["api.py"]