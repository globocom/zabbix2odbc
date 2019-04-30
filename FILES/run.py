#!/opt/zabbix/virtualenv/bin/python

import sys
import os
import logging
import time
from macrosyncodbc import MacroSyncODBCforMySQL, MacroSyncODBCforOracle, MacroSync

stdout_handler = logging.StreamHandler(sys.stdout)
handlers = [stdout_handler]
log_format = '[%(asctime)s] %(name)s - %(levelname)s: %(message)s'
logging.basicConfig(format=log_format, handlers=handlers)
logger = logging.getLogger('macrosyncodbc')
logger.setLevel(getattr(logging, os.getenv("LOG_LEVEL")))

confMySQL = MacroSyncODBCforMySQL()
confOracle = MacroSyncODBCforOracle()
logger.info("Zabbix2ODBC was started")
while True:
    try:
        confMySQL.sync()
        confOracle.sync()
        time.sleep(5)
        MacroSync().merge()
        logger.info("ODBC synced with Zabbix macros")
        time.sleep(float(os.getenv("INTERVAL_TIME")))

    except (KeyboardInterrupt, SystemExit), e:
        logger.info("Zabbix2ODBC interrupted by %s" % e.__class__.__name__)
        confMySQL.zabbix.user.logout([])
        confOracle.zabbix.user.logout([])
        break
