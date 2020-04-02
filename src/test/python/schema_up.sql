DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO postgres;

CREATE TABLE account (
    id serial primary key, --integer primary key autoincrement,
    name text not null,
    created_at timestamp without time zone default (now() at time zone 'utc')
);

INSERT INTO account (name) VALUES
('oliver'),
('rachel'),
('buddy');


