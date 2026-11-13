-- Dev utility: wipe everything and start fresh
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO bbms_app;
GRANT ALL ON SCHEMA public TO public;

