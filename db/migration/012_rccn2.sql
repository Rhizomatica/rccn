BEGIN;
UPDATE meta SET value='12' WHERE key='db_revision';

DROP TABLE site;
DROP TABLE providers;
DROP TABLE dids;
DROP TABLE configuration;
DROP TABLE resellers_configuration;

COMMIT;
