FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update -y
RUN apt-get install -y software-properties-common curl git

RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt-get install -y python3.9 python3.9-dev python3.9-distutils
RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
RUN python3.9 get-pip.py
RUN ln -s /usr/bin/python3.9 /usr/bin/python

RUN git clone https://github.com/staar21/llm-test-generation.git
WORKDIR /llm-test-generation

RUN pip install -r requirements.txt
CMD ["bash"]