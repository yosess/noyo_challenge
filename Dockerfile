FROM python:3.9.2

RUN pip install --upgrade pip

COPY requirements.txt .
RUN pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r ./requirements.txt --no-user

CMD ["flask", "run"]
