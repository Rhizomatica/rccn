BEGIN;
CREATE TABLE meta (
        id  serial primary key,
        key varchar not null,
        value varchar not null
);
INSERT INTO meta(key,value) VALUES ('db_revision','9');
COMMIT;

CREATE INDEX caller_id_number_index ON cdr(caller_id_number);
CREATE INDEX destination_number_index ON cdr(destination_number);
CREATE INDEX start_stamp_index ON cdr(start_stamp);
CREATE INDEX context_index ON cdr(context);
CREATE INDEX destination_name_index ON cdr(destination_name);

CREATE INDEX source_addr_index ON sms(source_addr);
CREATE INDEX destination_addr ON sms(destination_addr);
CREATE INDEX context_sms_index ON sms(context);
CREATE INDEX send_stamp_index ON sms(send_stamp);

CREATE INDEX msidn_credit_history_index ON credit_history(msisdn);
CREATE INDEX created_index ON credit_history(created);

CREATE UNIQUE INDEX reseller_msisdn_index ON resellers(msisdn);

CREATE INDEX created_res_hist_index ON resellers_credit_history(created);
CREATE INDEX msisdn_res_index ON resellers_credit_history(msisdn);

CREATE INDEX created_res_tran_index ON resellers_transactions(created);
CREATE INDEX msisdn_res_tran_index ON resellers_transactions(reseller_msisdn);
CREATE INDEX subscriber_res_tran_index ON resellers_transactions(subscriber_msisdn);
