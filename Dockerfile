FROM ubuntu:22.04
WORKDIR /app
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get -qq update && apt-get upgrade -y
RUN apt-get install -y apt-utils
RUN apt-get install -y tzdata
RUN apt-get install -y curl
RUN apt-get -qq install --no-install-recommends -y python3-pip
RUN apt remove ffmpeg -y
RUN apt update
RUN apt-get install software-properties-common -y
RUN add-apt-repository ppa:ubuntuhandbook1/ffmpeg6 -y
RUN apt update
RUN apt install ffmpeg --no-install-recommends -y
RUN apt-get -y install net-tools

RUN pip3 install docker
RUN pip3 install ffmpeg-python
RUN pip3 install numpy
RUN pip3 install Pillow
RUN pip3 install psutil
RUN pip3 install redis
RUN pip3 install requests
RUN pip3 install rq
RUN pip3 install schedule
RUN pip3 install shortuuid
RUN pip3 install getmac
RUN pip3 install pybase64

COPY . .

CMD ["python3", "main.py"]