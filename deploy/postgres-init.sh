#!/bin/sh
# Only executed by the official entrypoint on an empty, explicitly owned data volume.
set -eu
: "${DB_NAME:?}" "${DB_USER:?}" "${DB_PASSWORD:?}"
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
  --set=app_user="$DB_USER" --set=app_password="$DB_PASSWORD" --set=app_db="$DB_NAME" <<'SQL'
CREATE ROLE :"app_user" LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION PASSWORD :'app_password';
CREATE DATABASE :"app_db" OWNER :"app_user";
\connect :app_db
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
SQL
