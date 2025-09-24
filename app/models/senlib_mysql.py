"""
Class for working with senlib as MySQL database.

"""

import mysql.connector
from sqlalchemy import create_engine

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


class SenLibMySql():

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

    def _getallsenotypejsons(self) -> List[dict]:
        """
        Obtains a list of all senotype jsons.
        """

        listjson = []
        rows = self._fetch(query='SELECT * FROM senotype')
        for row in rows:
            senotypejson = json.loads(row[1])
            listjson.append(senotypejson)

        return listjson

    def _getassertionvaluesets(self) -> pd.DataFrame:
        """
        Get the Senotype Editor assertion valuesets from the senlib database as a Pandas DataFrame.
        :return:
        """

        # Format: "mysql+pymysql://<username>:<password>@<host>/<database>"
        engine = create_engine(f"mysql+pymysql://{self.db_user}:{self.db_pwd}@{self.db_host}/{self.db_name}")

        df = pd.read_sql('SELECT * FROM senotype_editor_valuesets', engine)

        return df

    def getsenlibjson(self, id: str) -> dict:
        """
        Get a single senotype JSON.
        :param id: id of the senotype
        :return: the senotype json
        """

        rows = self._fetch(query=f'SELECT * FROM senotype where senotypeid="{id}"')
        for row in rows:
            return json.loads(row[1])

        return {}

    def __init__(self, cfg: AppConfig):
        """
        :param cfg: AppConfig, representing the app.cfg file.
        """

        # Get connect information for the MySQL instance from the configuration.
        self.db_user = cfg.getfield(key='SENOTYPE_DB_USER')
        self.db_pwd = cfg.getfield(key='SENOTYPE_DB_PWD')
        self.db_name = cfg.getfield(key='SENOTYPE_DB_NAME')
        self.db_host = cfg.getfield(key='SENOTYPE_DB_HOST')

        # Connect to the database.
        self.conn = mysql.connector.connect(
            user=self.db_user,
            password=self.db_pwd,
            host=self.db_host,
            database=self.db_name
        )

        # Get IDs for all senlib JSONs.
        self.senlibjsonids = self._getsenotypeids()

        # Get the Senotype Editor assertion valuesets.
        self.assertionvaluesets = self._getassertionvaluesets()

    def close(self):
        self.conn.close()