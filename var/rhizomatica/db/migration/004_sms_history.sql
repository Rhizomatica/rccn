BEGIN;
create table sms (
        id                      serial primary key,
        source_addr             varchar not null,
        destination_addr        varchar not null,
        context                 varchar,
        send_stamp              timestamp default current_timestamp
)
COMMIT;
