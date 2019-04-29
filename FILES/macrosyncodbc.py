#!/opt/zabbix/virtualenv/bin/python

import os
import logging
from zabbix_api import ZabbixAPI
from configobj import ConfigObj


class MacroSyncODBCforMySQL(object):
	macros_list = {'{$ODBC_DSN}': 'DSN', '{$ODBC_DESCRIPTION}': 'Description', '{$ODBC_DRIVER}': 'Driver',
				   '{$ODBC_SERVER}': 'Server', '{$ODBC_DATABASE}': 'Database', '{$ODBC_USER}': 'User',
				   '{$ODBC_PASSWORD}': 'Password', '{$ODBC_PORT}': 'Port', '{$ODBC_SSLCA}': 'sslca'}
	inv_macros_list = {j: i for i, j in macros_list.items()}
	
	def __init__(self):
		self.confodbcMySQL = ConfigObj(os.getenv("ODBC_TEMP_MYSQL"))
		self.logger = logging.getLogger("macrosyncodbc")
		self.zabbix = ZabbixAPI(server=os.getenv("ZABBIX_ENDPOINT"))
		
		try:
			self.zabbix.login(os.getenv("ZABBIX_USER"), os.getenv("ZABBIX_PASS"))
		except:
			self.logger.error("Cant login into Zabbix API")
			raise
	
	def get_macros(self, group_name):
		if group_name:
			group_id = self.zabbix.hostgroup.get({"filter": {"name": [group_name]}})
			if group_id:
				group_id = group_id[0]['groupid']
			else:
				self.logger.error("No group found with name: {}".format(group_name))
				return None
			hosts = self.zabbix.host.get(
				{'groupids': group_id, 'selectMacros': 'extend', 'output': ['host'], 'filter': {'status': '0'}})
			self.logger.info("Found %d MySQL hosts.." % hosts.__len__())
			self.logger.debug('Hosts:')
			self.logger.debug(hosts)
			hosts_macros = {i['host']: {j['macro']: j['value'] for j in i['macros']} for i in hosts}
			hostids = {i['host']: i['hostid'] for i in hosts}
			self.logger.debug("%s found on %s" % (hosts_macros, group_name))
			return hosts_macros, hostids
	
	def sync(self):
		try:
			(hosts_macros, hostids) = self.get_macros(group_name=os.getenv("ODBC_HG_MYSQL"))
		except:
			exit(1)
		
		write = False
		list_dsn_sections = []
		for host, macros in hosts_macros.items():
			try:
				host_dsn = macros['{$ODBC_DSN}']
				list_dsn_sections.append(host_dsn)
			except:
				continue
			try:
				host_dsn
			except KeyError:
				self.logger.info("%s in %s doesnt have ODBC macros" % (host, os.getenv("ODBC_HG_MYSQL")))
				if host_dsn in self.confodbcMySQL.sections and os.getenv("CREATE_MACROS"):
					new_macros = [{"macro": i, "value": macros[i]} for i in
								  macros.keys()]
					for key in self.confodbcMySQL[host_dsn].keys():
						if key in self.inv_macros_list.keys():
							new_macros.append(
								{"macro": self.inv_macros_list[key], "value": self.confodbcMySQL[host_dsn][key]})
					
					new_macros.append({"macro": "{$ODBC_DSN}", "value": host_dsn})
					self.zabbix.host.update({"hostid": hostids[host_dsn], "macros": new_macros})
					self.logger.info("Macros %s created in %s" % (new_macros, host))
				else:
					self.logger.info("Macros wont be created in %s" % host)
					continue
			
			if host_dsn not in self.confodbcMySQL.sections:
				self.confodbcMySQL[host_dsn] = {}
				self.logger.info("Host %s found in Zabbix and will be included in odbc.ini" % host)
			else:
				self.logger.info("Host %s already in ODBC Configuration" % host)
			
			for key, value in macros.items():
				if key in self.macros_list.keys():
					try:
						if value != self.confodbcMySQL[host_dsn][self.macros_list[key]]:
							if self.macros_list[key] != "DSN":
								self.confodbcMySQL[host_dsn][self.macros_list[key]] = value
								write = True
								self.logger.debug(
									"key " + self.macros_list[key] + " altered to:  " + value + " in " + host)
						else:
							pass
					except KeyError:
						if self.macros_list[key] != "DSN":
							self.confodbcMySQL[host_dsn][self.macros_list[key]] = value
							write = True
							if self.macros_list[key] == "Password":
								self.logger.debug(
									"new key " + self.macros_list[key] + " created and assigned value: " + len(
										value) * "*" + " in " + host)
							else:
								self.logger.debug("new key " + self.macros_list[
									key] + " created and assigned value: " + value + " in " + host)
		
		for dsn in self.confodbcMySQL.sections:
			if dsn not in list_dsn_sections:
				try:
					self.confodbcMySQL.sections.remove(dsn)
					self.logger.info("Host %s was removed from ODBC configuration" % self.confodbcMySQL[dsn]['Server'])
					write = True
				
				except:
					pass
		
		if write:
			self.confodbcMySQL.write()
			self.logger.info("ODBC configuration for MySQL is set, the changes will be valid by now.")
			self.confodbcMySQL.reload()


class MacroSyncODBCforOracle(object):
	macros_list = {'{$ODBC_DSN}': 'DSN', '{$ODBC_DRIVER}': 'Driver', '{$ODBC_SERVER}': 'ServerName',
				   '{$ODBC_URL}': 'URL', '{$ODBC_URL2}': 'URL2'}
	inv_macros_list = {j: i for i, j in macros_list.items()}
	
	def __init__(self):
		self.confodbcOracle = ConfigObj(os.getenv("ODBC_TEMP_ORACLE"))
		self.conftns = ConfigObj(os.getenv("CONF_FILE_TNS_ORACLE"))
		self.logger = logging.getLogger("macrosyncodbc")
		self.zabbix = ZabbixAPI(server=os.getenv("ZABBIX_ENDPOINT"))
		
		try:
			self.zabbix.login(os.getenv("ZABBIX_USER"), os.getenv("ZABBIX_PASS"))
		except:
			self.logger.error("Cant login into Zabbix API")
			raise
	
	def get_macros(self, group_name):
		if group_name:
			group_id = self.zabbix.hostgroup.get({"filter": {"name": [group_name]}})
			if group_id:
				group_id = group_id[0]['groupid']
			else:
				self.logger.error("No group found with name: {}".format(group_name))
				return None
			hosts = self.zabbix.host.get(
				{'groupids': group_id, 'selectMacros': 'extend', 'output': ['host'], 'filter': {'status': '0'}})
			self.logger.info("Found %d Oracle hosts.." % hosts.__len__())
			self.logger.debug('Hosts:')
			self.logger.debug(hosts)
			hosts_macros = {i['host']: {j['macro']: j['value'] for j in i['macros']} for i in hosts}
			hostids = {i['host']: i['hostid'] for i in hosts}
			self.logger.debug("%s found on %s" % (hosts_macros, group_name))
			return hosts_macros, hostids
	
	def sync(self):
		try:
			(hosts_macros, hostids) = self.get_macros(group_name=os.getenv("ODBC_HG_ORACLE"))
		except:
			exit(1)
		
		write = False
		list_dsn_sections = []
		for host, macros in hosts_macros.items():
			try:
				host_dsn = macros['{$ODBC_DSN}']
				list_dsn_sections.append(host_dsn)
			except:
				continue
			try:
				macros['{$ODBC_URL2}']
				macros['{$ODBC_URL}'] = macros['{$ODBC_URL}'] + macros['{$ODBC_URL2}']
			except KeyError:
				pass
			try:
				macros['{$ODBC_URL}']
			except KeyError:
				self.logger.info("%s in %s doesnt have ODBC macros for Oracle" % (host, os.getenv("ODBC_HG_ORACLE")))
				if host_dsn in self.confodbcOracle.sections and os.getenv("CREATE_MACROS"):
					new_macros = [{"macro": i, "value": macros[i]} for i in
								  macros.keys()]
					for key in self.confodbcOracle[host_dsn].keys():
						if key in self.inv_macros_list.keys():
							new_macros.append(
								{"macro": self.inv_macros_list[key], "value": self.confodbcOracle[host_dsn][key]})
					
					new_macros.append({"macro": "{$ODBC_DSN}", "value": host_dsn})
					self.zabbix.host.update({"hostid": self.confodbcOracle[host_dsn], "macros": new_macros})
					self.logger.info("Macros %s created in %s" % (new_macros, host))
				else:
					self.logger.info("Macros wont be created in %s" % host)
					continue
			
			if host_dsn not in self.confodbcOracle.sections:
				self.confodbcOracle[host_dsn] = {}
				self.logger.info("Host %s found in Zabbix and will be included in odbc.ini" % host)
			else:
				self.logger.info("Host %s already in ODBC Configuration" % host)
			
			try:
				if macros['{$ODBC_SERVER}'] not in self.conftns.keys():
					self.conftns[macros['{$ODBC_SERVER}']] = ""
					self.logger.info("Host %s found in Zabbix and will be included in tnsnames.ora" % host)
				else:
					self.logger.info("Host %s already in tnsnames.ora" % host)
			except:
				self.logger.info("Host %s does not have ODBC_SERVER macro and will not be included in odbc.ini" % host)
				continue
			
			for key, value in macros.items():
				if key in self.macros_list.keys():
					try:
						if value != self.confodbcOracle[host_dsn][self.macros_list[key]]:
							if self.macros_list[key] == "ServerName":
								self.confodbcOracle[host_dsn][self.macros_list[key]] = value
								write = True
							elif self.macros_list[key] != "DSN" and self.macros_list[key] != "URL" and self.macros_list[
								key] != "URL2":
								self.confodbcOracle[host_dsn][self.macros_list[key]] = value
								write = True
								self.logger.debug(
									"key " + self.macros_list[key] + " altered to:  " + value + " in " + host)
						else:
							pass
					except KeyError:
						if self.macros_list[key] == "ServerName":
							self.confodbcOracle[host_dsn][self.macros_list[key]] = value
							write = True
						elif self.macros_list[key] != "DSN" and self.macros_list[key] != "URL" and self.macros_list[
							key] != "URL2":
							self.confodbcOracle[host_dsn][self.macros_list[key]] = value
							write = True
							self.logger.debug("new key " + self.macros_list[
								key] + " created and assigned value: " + value + " in " + host)
						elif self.macros_list[key] == "URL":
							if 'SERVICE_NAME' in value:
								service_name = value.split("@")[1]
								self.conftns[macros['{$ODBC_SERVER}']] = service_name
								write = True
							else:
								if "/" in value.split("@")[1]:
									separa_valores = value.split("@")[1]
									host_value = separa_valores.split("/")[0].split(":")[0]
									port_value = separa_valores.split("/")[0].split(":")[1]
									
									service_name = separa_valores.split("/")[1]
									
									monta_valor = "(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=" + host_value + ")(PORT=" + port_value + "))(CONNECT_DATA=(SERVICE_NAME=" + service_name + ")))"
									valor_tratado = monta_valor
									self.conftns[macros['{$ODBC_SERVER}']] = valor_tratado
								else:
									separa_valores = value.split("@")[1]
									host_value = separa_valores.split(":")[0]
									port_value = separa_valores.split(":")[1]
									
									sid_name = separa_valores.split(":")[2]
									
									monta_valor = "(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=" + host_value + ")(PORT=" + port_value + "))(CONNECT_DATA=(SID=" + sid_name + ")))"
									valor_tratado = monta_valor
									self.conftns[macros['{$ODBC_SERVER}']] = valor_tratado
								
								write = True
		
		for dsn in self.confodbcOracle.sections:
			if dsn not in list_dsn_sections:
				try:
					self.confodbcOracle.sections.remove(dsn)
					
					del self.conftns[self.confodbcOracle[dsn]['ServerName']]
					self.logger.info(
						"Instance %s was removed from ODBC configuration" % self.confodbcOracle[dsn]['ServerName'])
					write = True
				except:
					pass
		
		if write:
			self.confodbcOracle.write()
			self.logger.info("ODBC configuration for Oracle is set, the changes will be valid by now.")
			self.confodbcOracle.reload()
			self.conftns.write()
			self.conftns.reload()


class MacroSync(object):
	
	def __init__(self):
		self.configODBC = ConfigObj(os.getenv("CONF_FILE_ODBC"))
		self.configMySQL = ConfigObj(os.getenv("ODBC_TEMP_MYSQL"))
		self.configOracle = ConfigObj(os.getenv("ODBC_TEMP_ORACLE"))
		self.logger = logging.getLogger("macrosyncodbc")
	
	def merge(self):
		self.configODBC.clear()
		
		self.configODBC.merge(self.configMySQL)
		
		self.configODBC.merge(self.configOracle)
		self.configODBC.write()
		self.configODBC.reload()
		
		self.logger.info("MySQL and Oracle configuration was merged in odbc.ini, the changes will be valid by now.")
