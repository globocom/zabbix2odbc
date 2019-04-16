FROM python:2.7-slim

LABEL maintainer=zabbix@corp.globo.com

ENV APP_HOME /home/app/

ADD requirements.txt $APP_HOME/requirements.txt
RUN pip install -r $APP_HOME/requirements.txt

ENV ZABBIX_ENDPOINT ""
ENV ZABBIX_USER ""
ENV ZABBIX_PASS ""
ENV INTERVAL_TIME ""
ENV CREATE_MACROS ""
ENV ODBC_HG_MYSQL ""
ENV ODBC_HG_ORACLE ""
ENV CONF_FILE_ODBC ""
ENV CONF_FILE_TNS_ORACLE ""
ENV ODBC_TEMP_MYSQL ""
ENV ODBC_TEMP_ORACLE ""
ENV LOG_LEVEL ""

ADD ./FILES/ $APP_HOME

WORKDIR $APP_HOME

CMD ["python","run.py"]