BEGIN;
ALTER TABLE dids RENAME TO dids_temp;
create table dids (
	id			serial primary key,
	provider_id		int not null,
	subscriber_number	varchar,
	phonenumber		varchar not null,
	callerid		varchar
);
INSERT INTO dids(id,provider_id,subscriber_number,phonenumber) SELECT id,provider_id,subscriber_number,phonenumber FROM dids_temp;
DROP TABLE dids_temp;
COMMIT;
