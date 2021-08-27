# Flask_BE
Example project for Flask APP.


Python Setup
------------
1. Python: v3.6 or above
2. Install required python packages: `pip install -r requirements.txt`
3. Migrate database schema / Create admin user: `python admin.py`
4. Run flask server: `python run.py`


PostgreSQL Setup
----------------
      1. Install PostgreSQL
      2. Login as the default user: `sudo -u postgres psql`
      3. Create a database: `create database <dbname>;`
      4. Create an user account: `create user <username> with encrypted password '<password>';`
      5. Grant database access to the user: `grant all privileges on database <dbname> to <username>;`

                                    (Alternative way)
      1. `sudo -u postgres createuser <username>`
      2. `sudo -u postgres createdb <dbname>`
      3. `sudo -u postgres psql`
      4. `alter user <username> with encrypted password '<password>';`
      5. `grant all privileges on database <dbname> to <username> ;`


PostgreSQL commands
-------------------
1. `\?` list all the commands
2. `\l` list databases
3. `\conninfo` display information about current connection
4. `\c [DBNAME]` connect to new database, e.g., \c template1
5. `\dt` list tables of the public schema
6. `\dt` <schema-name>.* list tables of certain schema, e.g., \dt public.*
7. `\dt *.*` list tables of all schemas. Then you can run SQL statements, e.g., SELECT * FROM my_table;
(Note: a statement must be terminated with semicolon ;)
8. `\q` quit psql


Help
-----
PostgreSQL setup: https://medium.com/coding-blocks/creating-user-database-and-adding-access-on-postgresql-8bfcd2f4a91e
