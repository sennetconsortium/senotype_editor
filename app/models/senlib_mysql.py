"""
Class for working with senlib as MySQL database.

"""

import mysql.connector
from mysql.connector import errors
from sqlalchemy import create_engine
from flask import abort

import pandas as pd
import json
from typing import List, Tuple, Any

from models.appconfig import AppConfig

import logging
# Configure consistent logging. This is done at the beginning of each module instead of with a superclass of
# logger to avoid the need to overload function calls to logger.
logging.basicConfig(format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
                    level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)


class SenLibMySql:

    def _fetch(self, query: str) -> List[Tuple[Any, ...]]:
        """
        Simple fetch from table.
        :param query: SQL string
        """

        cursor = self.conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()
        return results

    def _getsenotypeids(self) -> list:
        """
        Obtains the ids of all Senotype submissions in the senlib repo.
        :return: list of Senotype ids with descriptions
        """

        listids = []

        logger.info('Fetching senotype ids')

        rows = self._fetch(query='SELECT * FROM senotype')
        for row in rows:
            senotypeid = row[0]
            senotypejson = json.loads(row[1])  # Converts JSON string to dict
            senotype = senotypejson.get('senotype')
            provenance = senotype.get('provenance')
            successor = provenance.get('successor')
            name = senotype.get('name', '')
            if len(name) >= 40:
                name = f'{name[0:37]}...'

            listids.append(f'{senotypeid} ({name})')

        return listids

    def getallsenotypejsons(self) -> List[dict]:
        """
        Obtains a list of all senotype jsons.
        """

        listjson = []

        logger.info('Fetching senotypes')

        rows = self._fetch(query='SELECT * FROM senotype')
        for row in rows:
            senotypejson = json.loads(row[1])
            listjson.append(senotypejson)

        return listjson

    def _gettable(self, tablename: str) -> pd.DataFrame:

        """
        Fetches a table from the senlib database.

        """

        # Format: "mysql+pymysql://<username>:<password>@<host>/<database>"
        engine = create_engine(f"mysql+pymysql://{self.db_user}:{self.db_pwd}@{self.db_host}/{self.db_name}")

        df = pd.read_sql(f'SELECT * FROM {tablename}', engine)
        return df

    def getsenotypejson(self, id: str) -> dict:
        """
        Get a single senotype JSON.
        :param id: id of the senotype
        :return: the senotype json
        """

        logger.info(f'Fetching senotype for {id}')
        rows = self._fetch(query=f'SELECT * FROM senotype where senotypeid="{id}"')
        for row in rows:
            return json.loads(row[1])

        return {}

    def writesenotype(self, senotypeid: str, senotypejson: dict):
        """
        Upsert to the senlib database.
        :param senotypeid: id to add or update
        :param senotypejson: new or revised senotype json
        """

        # Convert the dict into a string.
        senotypejson = json.dumps(senotypejson)

        cursor = self.conn.cursor()
        sql = (
            "INSERT INTO senotype (senotypeid, senotypejson) "
            "VALUES (%s, CAST(%s AS JSON)) "
            "ON DUPLICATE KEY UPDATE senotypejson = VALUES(senotypejson);"
        )

        params = (senotypeid, senotypejson)

        try:
            logger.info(f'Updating senotype for {senotypeid}')
            cursor.execute(sql, params)
            # Commit the transaction
            self.conn.commit()
        except errors.DatabaseError as db_err:
            logger.error(f"Error writing to the senlib database: {db_err}")
            abort(500, f"Error writing to the senlib database: {db_err}")
        finally:
            cursor.close()

    def __init__(self, cfg: AppConfig):
        """
        :param cfg: AppConfig, representing the app.cfg file.
        """

        # Get connect information for the MySQL instance from the configuration.
        self.db_user = cfg.getfield(key='SENOTYPE_DB_USER')
        self.db_pwd = cfg.getfield(key='SENOTYPE_DB_PWD')
        self.db_name = cfg.getfield(key='SENOTYPE_DB_NAME')
        self.db_host = cfg.getfield(key='SENOTYPE_DB_HOST')

        self.error = ''
        # Connect to the database.
        try:
            self.conn = mysql.connector.connect(
                user=self.db_user,
                password=self.db_pwd,
                host=self.db_host,
                database=self.db_name
            )

            logger.info(f'Connected to {self.db_name} as {self.db_user}')

            # Get IDs for all senlib JSONs.
            self.senlibjsonids = self._getsenotypeids()

            # Get the Senotype Editor assertion valuesets.
            self.assertionvaluesets = self._gettable(tablename='senotype_editor_valuesets')

            # Get the Senotype Editor assertion-object maps.
            self.assertion_predicate_object = self._gettable(tablename='assertion_predicate_object')

            # Get the Senotype Editor context assertion maps.
            self.context_assertion_code = self._gettable(tablename='context_assertion_code')

        except errors.DatabaseError as db_err:
            logger.error(f"Error connecting to the senlib database: {db_err}")
            abort(500, f"Error connecting to the senlib database: {db_err}")

    def close(self):
        self.conn.close()
