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
        msisdn          varchar not null,
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
        message1                varchar,
        message2                varchar,
        message3                varchar,
        message4                varchar,
        message5                varchar,
        message6                varchar
);
INSERT INTO resellers_configuration VALUES('Invalid data','Reseller does not have enough funds to add credit to your account',
'Not enough funds to add the credit requested','Amount of [var1] pesos successfully added to your account. New balance: [var2]','[var1] pesos successfully transferred to [var3]. Your current balance is: [var4]', 'General error credit could not be added');
