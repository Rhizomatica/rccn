CREATE TABLE meta (
	id  serial primary key,
	key varchar not null,
	value varchar not null
);
INSERT INTO meta(key,value) VALUES ('db_revision','10');
INSERT INTO meta(key,value) VALUES ('hlr_sync', '0');

CREATE TABLE cdr (
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
CREATE INDEX caller_id_number_index ON cdr(caller_id_number);
CREATE INDEX destination_number_index ON cdr(destination_number);
CREATE INDEX start_stamp_index ON cdr(start_stamp);
CREATE INDEX context_index ON cdr(context);
CREATE INDEX destination_name_index ON cdr(destination_name);


CREATE TABLE sms (
	id			serial primary key,
	source_addr		varchar not null,
	destination_addr 	varchar not null,
	context			varchar,
	send_stamp		timestamp default current_timestamp
);
CREATE INDEX source_addr_index ON sms(source_addr);
CREATE INDEX destination_addr ON sms(destination_addr);
CREATE INDEX context_sms_index ON sms(context);
CREATE INDEX send_stamp_index ON sms(send_stamp);


CREATE TABLE subscribers (
	id		serial primary key,
	msisdn 		varchar,
	name		varchar,
	authorized	smallint not null default 0,
	balance		decimal not null default 0.00,
	subscription_status	smallint not null default 0,
        subscription_date       timestamp default current_timestamp,
	created		timestamp default current_timestamp
);
CREATE UNIQUE INDEX msisdn_index ON subscribers(msisdn);


CREATE OR REPLACE FUNCTION update_subscription_change_date()
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

CREATE TABLE credit_history (
	id			serial primary key,
	receipt_id		varchar not null,
	msisdn			varchar not null,
	previous_balance	decimal not null,
	current_balance		decimal not null,
	amount			decimal not null,
	created	timestamp 	default current_timestamp
);
CREATE INDEX msidn_credit_history_index ON credit_history(msisdn);
CREATE INDEX created_index ON credit_history(created);


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


CREATE TABLE site (
	site_name		varchar not null,
	postcode		varchar not null,
	pbxcode 		varchar not null,
	network_name		varchar not null,
	ip_address		varchar not null
);

CREATE TABLE providers (
	id			serial primary key,
	provider_name		varchar not null,
	username		varchar not null,
	fromuser		varchar,
	password		varchar not null,
	proxy			varchar not null,
	active			smallint not null default 0
);

CREATE TABLE dids (
	id			serial primary key,
	provider_id		int not null,
	subscriber_number	varchar,
	phonenumber		varchar not null,
	callerid		varchar
);

CREATE TABLE rates (
	id			serial primary key,
	destination		varchar not null,
	prefix			varchar not null,
	cost			decimal not null
);

CREATE TABLE configuration (
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
	smsc_shortcode			varchar not null default '10000',
        sms_sender_unauthorized         varchar,
        sms_destination_unauthorized    varchar
);


CREATE TABLE users (
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
CREATE INDEX created_res_hist_index ON resellers_credit_history(created);
CREATE INDEX msisdn_res_index ON resellers_credit_history(msisdn);


CREATE TRIGGER t_reseller_receipt_number
   BEFORE INSERT ON resellers_credit_history
   FOR EACH ROW
   EXECUTE PROCEDURE gen_receipt_number('RNV','resellers_credit_history_id_seq');


CREATE TABLE resellers_transactions (
        id                      serial primary key,
        created                 timestamp default current_timestamp,
        reseller_msisdn         varchar not null,
        subscriber_msisdn       varchar not null,
        amount                  decimal not null
);
CREATE INDEX created_res_tran_index ON resellers_transactions(created);
CREATE INDEX msisdn_res_tran_index ON resellers_transactions(reseller_msisdn);
CREATE INDEX subscriber_res_tran_index ON resellers_transactions(subscriber_msisdn);

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


CREATE TABLE hlr (
        id              serial primary key,
        created         timestamp default current_timestamp,
        msisdn          varchar not null,
	home_bts	varchar not null,
	current_bts	varchar not null,
	authorized	integer not null default 1,
	updated		timestamp default current_timestamp
);

CREATE INDEX updated_hlr_index ON hlr(updated);
CREATE INDEX homebts_hlr_index ON hlr(home_bts);
CREATE INDEX currentbts_hlr_index ON hlr(current_bts);
CREATE UNIQUE INDEX msisdn_hlr_index ON hlr(msisdn);
CREATE INDEX authorized_hlr_index ON hlr(authorized);
