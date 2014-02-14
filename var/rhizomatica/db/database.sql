create table cdr (
    id                        serial primary key,
    local_ip_v4               inet not null,
    caller_id_name            varchar,
    caller_id_number          varchar,
    destination_number        varchar not null,
    context                   varchar not null,
    start_stamp               timestamp with time zone not null,
    answer_stamp              timestamp with time zone,
    end_stamp                 timestamp with time zone not null,
    duration                  int not null,
    billsec                   int not null,
    hangup_cause              varchar not null,
    uuid                      uuid not null,
    bleg_uuid                 uuid,
    accountcode               varchar,
    read_codec                varchar,
    write_codec               varchar,
    sip_hangup_disposition    varchar,
    ani                       varchar,
    destination_name          varchar,
    cost      		      decimal
);

create table sms (
	id			serial primary key,
	source_addr		varchar not null,
	destination_addr 	varchar not null,
	context			varchar,
	send_stamp		timestamp default current_timestamp
)

create table subscribers (
	id		serial primary key,
	msisdn 		varchar,
	name		varchar,
	authorized	smallint not null default 0,
	balance		decimal not null default 0.00,
	subscription_status	smallint not null default 0,
	created		timestamp default current_timestamp
);
CREATE UNIQUE INDEX msisdn_index ON subscribers(msisdn);

CREATE FUNCTION update_subscription_change_date()
  RETURNS TRIGGER
  LANGUAGE plpgsql
AS $$
BEGIN
  NEW.subscription_date := now();
  RETURN NEW;
END;
$$;

CREATE TRIGGER check_subscription_change
    BEFORE UPDATE ON subscribers
    FOR EACH ROW
    WHEN (OLD.subscription_status != NEW.subscription_status)
    EXECUTE PROCEDURE update_subscription_change_date();


--INSERT INTO subscribers(name,msisdn,authorized,balance) values('Test1','68820110010',1,4.0);
--INSERT INTO subscribers(name,msisdn,authorized,balance) values('Test2','68820123991',1,0.0);
--INSERT INTO subscribers(name,msisdn,authorized,balance) values('Test3','68820131755',1,4.0);


create table credit_history (
	id			serial primary key,
	receipt_id		varchar not null,
	msisdn			varchar not null,
	previous_balance	decimal not null,
	current_balance		decimal not null,
	amount			decimal not null,
	created	timestamp 	default current_timestamp
);

create table site (
	site_name		varchar not null,
	postcode		varchar not null,
	pbxcode 		varchar not null,
	network_name		varchar not null,
	ip_address		varchar not null
);

--insert into site(site_name,postcode,pbxcode,network_name,ip_address) values('Talea','68820','1','Talea Red Cellular','10.66.0.10');



create table providers (
	id			serial primary key,
	provider_name		varchar not null,
	username		varchar not null,
	fromuser		varchar,
	password		varchar not null,
	proxy			varchar not null,
	active			smallint not null default 0
);

--insert into providers(provider_name,username,fromuser,password,proxy,active) values('Clearcom','rhizo1','rhizo1','RRn1HyvQa91z','comunidad-clearcom.mx',1)

	
create table dids (
	id			serial primary key,
	provider_id		int not null,
	subscriber_number	varchar,
	phonenumber		varchar not null,
	callerid		varchar
);

--insert into dids(provider_id,phonenumber) values(1,'5547382004');
--insert into dids(provider_id,subscriber_number,phonenumber) values(1,'68820110010','rhizo1');


create table rates (
	id			serial primary key,
	destination		varchar not null,
	prefix			varchar not null,
	cost			decimal not null
);

create table configuration (
	limit_local_calls		smallint not null default 0,
	limit_local_minutes		integer,
	charge_local_calls		smallint not null default 0,
	charge_local_rate		decimal,
	charge_local_rate_type		varchar,
	charge_internal_calls		smallint not null default 0,
	charge_internal_rate		decimal,
	charge_internal_rate_type	varchar,
	charge_inbound_calls		smallint not null default 0,
	charge_inbound_rate		decimal,
	charge_inbound_rate_type	varchar
);


create table users (
	id		serial primary key,
	username	varchar not null,
	password	varchar not null,
	role		varchar,
	created 	timestamp default current_timestamp
);
