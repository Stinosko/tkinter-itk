# Slim version of Python
FROM python:3.11

# Download Package Information
RUN apt-get update -y

# Install Tkinter
RUN apt-get install tk git libglib2.0-0 -y

COPY ./tkinter_itk/requirements.txt /app/requirements.txt
COPY ./tkinter_itk/requirements-SAM.txt /app/requirements-SAM.txt

# RUN pip install -r /app/requirements.txt


RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y

COPY ./tkinter_itk  /app/tkinter_itk
COPY ./example.ipynb /app/example.ipynb
COPY ./run_itk_tkinter.py /app/run_itk_tkinter.py
COPY ./setup.py /app/setup.py
COPY ./test-data /app/test-data
COPY ./models /app/models

WORKDIR /app

RUN mv /app/tkinter_itk/ /root/tkinter_itk
RUN mv /app/setup.py /root/setup.py

RUN pip install --upgrade pip
RUN pip install -e "/root[sam]"

# RUN pip install -r /app/requirements-SAM.txt

# Commands to run Tkinter application
CMD ["/app/run_itk_tkinter.py"]

ENTRYPOINT ["python3"]
# docker build -t tkinter_in_docker .
# docker run -u=$(id -u $USER):$(id -g $USER) -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix:rw --rm tkinter_in_docker
# https://towardsdatascience.com/empowering-docker-using-tkinter-gui-bf076d9e4974