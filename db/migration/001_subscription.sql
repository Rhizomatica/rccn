BEGIN;
ALTER TABLE subscribers RENAME TO sub;
create table subscribers (
        id              serial primary key,
        msisdn          varchar,
        name            varchar,
        authorized      smallint not null default 0,
        balance         decimal not null default 0.00,
        subscription_status     smallint not null default 0,
        subscription_date       timestamp default current_timestamp,
        created         timestamp default current_timestamp
);

INSERT INTO subscribers(id,msisdn,name,authorized,balance,created) SELECT id,msisdn,name,authorized,balance,created FROM sub;
DROP TABLE sub;
COMMIT;

CREATE LANGUAGE plpgsql;

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
