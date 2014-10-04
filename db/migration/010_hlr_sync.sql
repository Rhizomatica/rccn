BEGIN;
UPDATE meta SET value='10' WHERE key='db_revision';
INSERT INTO meta(key,value) VALUES ('hlr_sync', '0');
CREATE TABLE hlr (
        id              serial primary key,
        created         timestamp default current_timestamp,
        msisdn          varchar not null,
        home_bts        varchar not null,
        current_bts     varchar not null,
        authorized      integer not null default 1,
        updated         timestamp default current_timestamp
);
CREATE INDEX updated_hlr_index ON hlr(updated);
CREATE INDEX homebts_hlr_index ON hlr(home_bts);
CREATE INDEX currentbts_hlr_index ON hlr(current_bts);
CREATE UNIQUE INDEX msisdn_hlr_index ON hlr(msisdn);
CREATE INDEX authorized_hlr_index ON hlr(authorized);
COMMIT;
