BEGIN;

ALTER TABLE providers RENAME TO temp_prov;
CREATE TABLE providers (
        id                      serial primary key,
        provider_name           varchar not null,
        prefix                  varchar not null,
        username                varchar not null,
        fromuser                varchar,
        password                varchar not null,
        proxy                   varchar not null,
        active                  smallint not null default 0
);

INSERT INTO providers(id,provider_name,prefix,username,fromuser,password,proxy,active) SELECT id,provider_name,'',username,fromuser,password,proxy,active FROM temp_prov;
DROP TABLE temp_prov;
SELECT pg_catalog.setval(pg_get_serial_sequence('providers','id'), (SELECT MAX(id) FROM providers)+1);

CREATE TABLE user_location (
        id                      serial primary key,
        user_id                 integer not null,
        location_id             integer not null
);

UPDATE meta SET value='13' WHERE key='db_revision';

COMMIT;
