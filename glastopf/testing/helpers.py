from sqlalchemy import Table, Column, Integer, String, MetaData
from sqlalchemy import create_engine
import bson
import warnings
import os
import uuid
import json
from subprocess import call

file_dir = os.path.dirname(os.path.abspath(__file__))


def create_mongo_database(fill=True):
    from pymongo import MongoClient, uri_parser
    db_name = 'glastopf-test-{0}'.format(str(uuid.uuid4())[0:10])
    conn_string = "mongodb://localhost/{0}".format(db_name)

    with warnings.catch_warnings(record=True):
        c = MongoClient(conn_string)

    #read and insert test data into mongodb instance
    if fill:
        data = open(os.path.join(file_dir, 'data/events_500.bson'), 'r').read()
        for item in bson.decode_all(data):
            del item['_id']
            c[db_name].events.insert(item)
    return conn_string


def delete_mongo_testdata(conn_string):
    from pymongo import MongoClient, uri_parser
    db_name = uri_parser.parse_uri(conn_string)['database']
    with warnings.catch_warnings(record=True):
        client = MongoClient(conn_string)
    client.drop_database(db_name)


def populate_main_sql_testdatabase(engine):
    meta = MetaData()

    table = Table('events', meta,
                  Column('id', Integer, primary_key=True, ),
                  Column('time', String(30)),
                  Column('source', String(30)),
                  Column('request_url', String(500)),
                  Column('request_raw', String(65536)),
                  Column('pattern', String(20)),
                  Column('filename', String(500)),
    )

    meta.create_all(engine)

    insert_dicts = []
    data = open(os.path.join(file_dir, 'data/events_500.bson'), 'r').read()
    for item in bson.decode_all(data):
        new_item = {"source": "{0}:{1}".format(item["source"][0], item["source"][1]),
                    "request_url": item["request"]["url"],
                    "pattern": item["pattern"]}


        insert_dicts.append(new_item)

    conn = engine.connect()
    print "Inserted: {0}".format(len(insert_dicts))
    conn.execute(table.insert(), insert_dicts)


def create_empty_main_db_sqla(engine):
    meta = MetaData()

    Table('events', meta,
          Column('id', Integer, primary_key=True, ),
          Column('time', String(30)),
          Column('source', String(30)),
          Column('request_url', String(500)),
          Column('request_raw', String(65536)),
          Column('pattern', String(20)),
          Column('filename', String(500)),
    )

    meta.create_all(engine)


def create_sandbox(dest_dir):
    sandbox_dir = os.path.join(file_dir, '../sandbox')

    #preserve old working dir
    old_cwd = os.getcwd()

    os.chdir(sandbox_dir)

    #execute makefile and output to self.workdir/data/apd_sandbox.php
    sandbox_out = os.path.join(dest_dir, 'apd_sandbox.php')
    call(['make', 'out={0}'.format(sandbox_out)])
    print sandbox_out
    #restore state of original working dir
    os.chdir(old_cwd)


def gen_config(conn_string):
    """
    Generates configuration for testing purposes.
    """
    return [
        "[dork-db]\n",
        "enabled = True\n",
        "pattern = rfi\n",
        "token_pattern = /\w+\n",
        "n_clusters = 10\n",
        "max_iter = 10\n",
        "n_init = 2\n",
        "[surfcertids]\n",
        "enabled = False\n",
        "host = localhost\n",
        "port = 5432\n",
        "user =\n",
        "password =\n",
        "database = idsserver\n",
        "[syslog]\n",
        "enabled = False\n",
        "socket = /dev/log\n",
        "[mail]\n",
        "enabled = False\n",
        "patterns = rfi,lfi\n",
        "user =\n",
        "pwd =\n",
        "mail_from =\n",
        "mail_to =\n",
        "smtp_host = smtp.gmail.com\n",
        "smtp_port = 587\n",
        "[hpfeed]\n",
        "enabled = True\n",
        "host = hpfeeds.honeycloud.net\n",
        "port = 10000\n",
        "secret = 3wis3l2u5l7r3cew\n",
        "chan = glastopf.events,glastopf.files\n",
        "ident = x8yer@hp1\n",
        "[webserver]\n",
        "host = 0.0.0.0\n",
        "port = 8080\n",
        "uid = nobody\n",
        "gid = nogroup\n",
        "proxy_enabled = False\n",
        "[main-database]\n",
        "enabled = True\n",
        "connection_string = {0}\n".format(conn_string),
    ]


if __name__ == '__main__':
    engine = create_engine('sqlite:///')
    populate_main_sql_testdatabase(engine)
