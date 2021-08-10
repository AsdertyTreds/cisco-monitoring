FROM python:3.8
SHELL ["/bin/bash", "-c"]
RUN  mkdir - /usr/src/cisco-monitoring
WORKDIR /usr/src/cisco-monitoring
COPY . /usr/src/cisco-monitoring
EXPOSE 8080
ENV TZ Europe/Moscow
RUN python -m venv venv
RUN source venv/bin/activate
RUN pip install --no-cache-dir -r reqirement.txt
CMD ["python","main.py"]
