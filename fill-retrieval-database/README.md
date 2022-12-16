# Fill retrieval database

# Description
To use the application, one needs to configure the database connection properties first. Here is an example.
```json
{
    "ip": "localhost",
    "port": "5432",
    "username": "admin",
    "password": "pwd",
    "retrieval_version": "1.0",
    "database_name": "m27",
    "csv_locations": ["output-tables"],
    "cache_folder_location": "cache"
}
```
The script to create the tables is located in scripts/init_db.sql file.

## Usage
python3 main.py will ask you to either create a new database(1) or update the data(2). If no database exists, one needs to create one first. The script will automatically create a new database and create all necessary database objects.
The second option will check available cached processed data to find new, deleted and modified records.