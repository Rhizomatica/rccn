BEGIN;
UPDATE meta SET value='11' WHERE key='db_revision';

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
        created         timestamp default current_timestamp
);
INSERT INTO subscribers(id,msisdn,name,authorized,balance,subscription_status,subscription_date,created) SELECT id,msisdn,name,authorized,balance,subscription_status,subscription_date,created FROM sub;
DROP TABLE sub;
CREATE TABLE locations (
	id		serial primary key,
	name		varchar not null
);
COMMIT;
