BEGIN;
DROP TABLE sites;
create table site (
	site_name		varchar not null,
	postcode		varchar not null,
	pbxcode 		varchar not null,
	network_name		varchar not null
	ip_address		varchar not null
);
insert into site(site_name,postcode,pbxcode,network_name,ip_address) values('Talea','68820','1','TaleaGSM','10.66.0.10');
COMMIT;
