# postgresql.conf compare

Compares parameters defined and their default values between PostgreSQL major versions.  [Hosted by RustProof Labs](https://pgconfig.rustprooflabs.com/).


## Deployment Instructions

> Note:  Need to update the sub-version of Python over time.  Can use simply
`python3` but that can lead to using older unsupported versions based on distro-defaults.


```bash
cd ~/venv
python3.8 -m venv pgconfig
source ~/venv/pgconfig/bin/activate
```

Install requirements

```bash
source ~/venv/pgconfig/bin/activate
cd ~/git/pgconfig-ce
pip install -r requirements.txt
```

Run web server w/ uWSGI.

```bash
source ~/venv/pgconfig/bin/activate
cd ~/git/pgconfig-ce
python run_server.py
```

## Add new config files

To add a new configuration version you need a Postgres database instance running
that you can connect to.  Activate the Python venv and start `ipython`.

```bash
source ~/venv/pgconfig/bin/activate
cd ~/git/pgconfig-ce/config_from_pg
ipython
```

Import
```python
import generate
```

You'll be prompted for the database connection parameters.  Ideally you are using
a `~/.pgpass` file, but the option is there to enter your password. 

```
Database host [127.0.0.1]: 
Database port [5432]: 
Database name: postgres 
Enter PgSQL username: your_username
Enter password (empty for pgpass): 
```

Run the generation.  Will create a file in the appropriate spot for the webapp.
When adding a new version you need to add it to `webapp/pgconfig.py` as well
as generating this file.

```python
generate.run()
```

Preparing database objects...
Database objects ready.
Pickled config data saved to: ../webapp/config/pg15.pkl



## Unit tests

Run unit tests.

```
python -m unittest tests/*.py
```

Or run unit tests with coverage.

```
coverage run -m unittest tests/*.py
```

Generate report.

```
coverage report -m webapp/*.py

Name                 Stmts   Miss  Cover   Missing
--------------------------------------------------
webapp/__init__.py      15      0   100%
webapp/config.py        25      0   100%
webapp/forms.py          6      0   100%
webapp/pgconfig.py     150     37    75%   26-27, 53, 71-73, 87-94, 115-122, 140-145, 162-170, 222-223, 300, 393, 417
webapp/routes.py        83     58    30%   20, 24, 30, 35, 40-43, 51, 56-75, 87, 92-119, 127-140, 143-155
--------------------------------------------------
TOTAL                  279     95    66%
```

## Pylint

Run pylint.

```
pylint --rcfile=./.pylintrc -f parseable ./webapp/*.py ./config_from_pg/*.py
```

## History

The open source (Community Edition) version of this project started as a manual fork
of RustProof Labs' internal project, commit `fcc0619`.  The original internal project will
be retired as this project evolves. 

