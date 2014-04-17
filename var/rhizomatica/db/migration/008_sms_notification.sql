BEGIN;
ALTER TABLE configuration RENAME TO config;
create table configuration (
        limit_local_calls               smallint not null default 0,
        limit_local_minutes             integer,
        charge_local_calls              smallint not null default 0,
        charge_local_rate               decimal,
        charge_local_rate_type          varchar,
        charge_internal_calls           smallint not null default 0,
        charge_internal_rate            decimal,
        charge_internal_rate_type       varchar,
        charge_inbound_calls            smallint not null default 0,
        charge_inbound_rate             decimal,
        charge_inbound_rate_type        varchar,
        smsc_shortcode                  varchar not null default '10000',
	sms_sender_unauthorized		varchar,
	sms_destination_unauthorized	varchar
);
INSERT INTO configuration SELECT * FROM config;
DROP TABLE config;
COMMIT;
