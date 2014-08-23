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
