@echo off
echo Checking for CRM database file...
if exist crm.db (
    echo Deleting existing database file: crm.db
    del crm.db
    echo Database reset complete.
) else (
    echo No database file found. Nothing to reset.
)
