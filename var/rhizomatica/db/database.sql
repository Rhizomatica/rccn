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
);

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


create table credit_history (
	id			serial primary key,
	receipt_id		varchar not null,
	msisdn			varchar not null,
	previous_balance	decimal not null,
	current_balance		decimal not null,
	amount			decimal not null,
	created	timestamp 	default current_timestamp
);

-- function to generate receipt number based on the table sequence
CREATE OR REPLACE FUNCTION gen_receipt_number() RETURNS TRIGGER AS $$
DECLARE
   receipt_num varchar;
BEGIN
   SELECT TG_ARGV[0]||lpad( (cast(currval(TG_ARGV[1]) as text)), 10, '0') INTO receipt_num;
   NEW.receipt_id := receipt_num;
   RETURN NEW;
END
$$ LANGUAGE plpgsql;

CREATE TRIGGER t_receipt_number
   BEFORE INSERT ON credit_history
   FOR EACH ROW
   EXECUTE PROCEDURE gen_receipt_number('INV','credit_history_id_seq');


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
	charge_inbound_rate_type	varchar,
	smsc_shortcode			varchar not null default 10000
);


create table users (
	id		serial primary key,
	username	varchar not null,
	password	varchar not null,
	role		varchar,
	created 	timestamp default current_timestamp
);

CREATE TABLE resellers (
        id              serial primary key,
        created         timestamp default current_timestamp,
        msisdn          varchar not null,
        pin             varchar not null,
        balance         decimal not null,
        total_sales     integer not null default 0
);
CREATE UNIQUE INDEX reseller_msisdn_index ON resellers(msisdn);

CREATE TABLE resellers_credit_history (
        id              serial primary key,
        created         timestamp default current_timestamp,
        receipt_id      varchar not null,
        msisdn 		varchar not null,
        previous_balance decimal,
        current_balance  decimal,
        amount           decimal
);


CREATE TRIGGER t_reseller_receipt_number
   BEFORE INSERT ON resellers_credit_history
   FOR EACH ROW
   EXECUTE PROCEDURE gen_receipt_number('RNV','resellers_credit_history_id_seq');


CREATE TABLE resellers_transactions(
        id                      serial primary key,
        created                 timestamp default current_timestamp,
        reseller_msisdn         varchar not null,
        subscriber_msisdn       varchar not null,
        amount                  decimal not null
);

CREATE TABLE resellers_configuration (
	message1		varchar,
	message2		varchar,
	message3		varchar,
	message4		varchar,
	message5		varchar,
	message6 		varchar
);
INSERT INTO resellers_configuration VALUES('Invalid data','Reseller does not have enough funds to add credit to your account',
'Not enough funds to add the credit requested','Amount of [var1] pesos successfully added to your account. New balance: [var2]','[var1] pesos successfully transferred to [var3]. Your current balance is: [var4]', 'General error credit could not be added');
