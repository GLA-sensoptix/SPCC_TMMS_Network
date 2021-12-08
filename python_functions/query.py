from python_functions.database import Database
import json
import psycopg2
import os

tempFolder = 'tmp/'


class Query:
    def __init__(self, host, db_name, user, port, password):
        self.db = Database(
            host=host, database=db_name, user=user, port=port, password=password
        )

    # get parsing by id
    def getParsingById(self, id):
        query = """
        SELECT p.name, p.specific, p.configs FROM parsings p WHERE id = {0}
        """.format(id)
        res = self.db.select(query)
        if (len(res) > 0):
            return res[0]
        else:
            raise psycopg2.DatabaseError()

    # retrieve config by id
    def getConfigById(self, id):
        query = """
        SELECT c.id, c.file_name, c.last_treatment::timestamp, c.ftp, c.ftp_ip, c.ftp_user, c.ftp_password, c.ftp_directory,
        c.config, c.to_move, c.regex_variables, COALESCE(g.time_zone,f.time_zone) , p.name, p.specific , p.configs
        from configs c
        INNER JOIN parsings p on c.parsing_id = p.id
        LEFT JOIN gateways g on c.gateway_id = g.id
        LEFT JOIN files f on c.file_id = f.id
        where c.id = {0}
        """.format(id)
        res = self.db.select(query)
        if (len(res) > 0):
            return res[0]
        else:
            raise psycopg2.DatabaseError()

    # retrieve all configs from database"
    def getConfigs(self):
        query = """
        SELECT c.id, c.file_name, c.last_treatment::timestamp, c.ftp, c.ftp_ip, c.ftp_user, c.ftp_password, c.ftp_directory,
        c.config, c.to_move, c.regex_variables, COALESCE(g.time_zone,f.time_zone) , p.name, p.specific , p.configs 
        from configs c
        INNER JOIN parsings p on c.parsing_id = p.id
        LEFT JOIN gateways g on c.gateway_id = g.id
        LEFT JOIN files f on c.file_id = f.id
        """
        res = self.db.select(query)
        if (len(res) > 0):
            return res
        else:
            raise psycopg2.DatabaseError()

    # function to insert new values and set last timestamp
    def insertValues(self, data, confId, timezone='UTC', lastTreatment = None):
        if timezone is None:
            timezone = 'UTC'
        conn = None
        try:
            conn = self.db.getConnection()
            data.to_csv('{}/insert'.format(tempFolder), header=False, index=True)
            cur = conn.cursor()
            cur.execute("SET TIME ZONE '{0}'".format(timezone))
            cur.copy_from(open('{}/insert'.format(tempFolder), 'r'), "raw_data", sep=",",
                          columns=("timestamp", "variable_id", "value"))
            if lastTreatment is not None:
                cur.execute(
                    """UPDATE configs SET last_treatment = '{0}' where id = {1}""".format(lastTreatment, confId))
            conn.commit()
            cur.close()
            conn.close()
        except psycopg2.DatabaseError as error:
            raise error
        finally:
            if conn is not None:
                conn.close()

    # functions to replace data between two dates , old data go last_data -> false
    def updateValues(self, data, timezone, configTable, minDate, maxDate):
        if timezone is None:
            timezone = 'UTC'
        condition = None
        if(minDate and maxDate):
            condition = """
            WHERE timestamp >= to_timestamp('{0}','DD-MM-YYYY HH24:MI:SS')
            AND timestamp <= to_timestamp('{1}','DD-MM-YYYY HH24:MI:SS')
            """.format(minDate, maxDate)
        elif(minDate):
            condition = """ WHERE timestamp >= to_timestamp('{0}','DD-MM-YYYY HH24:MI:SS')""".format(
                minDate)
        elif(maxDate):
            condition = """ WHERE timestamp <= to_timestamp('{0}','DD-MM-YYYY HH24:MI:SS')""".format(
                maxDate)
        allVariables = []
        for config in configTable:
            allVariables.append(config['variable_id'])
        allVariables = list(set(allVariables))
        if condition is not None:
            try:
                conn = self.db.getConnection()
                cur = conn.cursor()
                cur.execute("SET TIME ZONE '{0}'".format(timezone))
                update = """ update raw_data 
                set last_data = false""" + condition + """ and variable_id in {0}""".format(tuple(allVariables))
                cur.execute(update)
                data.to_csv('{}/insert'.format(tempFolder), header=False, index=True)
                cur.copy_from(open('{}/insert'.format(tempFolder)), "raw_data", sep=",",
                              columns=("timestamp", "variable_id", "value"))
                conn.commit()
                cur.close()
                conn.close()
            except psycopg2.DatabaseError as error:
                raise error
            finally:
                if conn is not None:
                    conn.close()
