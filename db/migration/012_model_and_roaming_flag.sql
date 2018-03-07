BEGIN;

ALTER TABLE subscribers RENAME TO sub;
create table subscribers (
        id              serial primary key,
        msisdn          varchar,
        name            varchar,
        authorized      smallint not null default 0,
        balance         decimal not null default 0.00,
        subscription_status     smallint not null default 0,
        subscription_date       timestamp default current_timestamp,
	location	varchar,
	roaming		smallint not null default 0,
	equipment	varchar,
        created         timestamp default current_timestamp
);
INSERT INTO subscribers(id,msisdn,name,authorized,balance,subscription_status,subscription_date,location,created) SELECT id,msisdn,name,authorized,balance,subscription_status,subscription_date,location,created FROM sub;
DROP TABLE sub;
UPDATE meta SET value='12' WHERE key='db_revision';

COMMIT;
