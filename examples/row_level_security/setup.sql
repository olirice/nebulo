/*************************************************
Create Roles for Authenticated and Anonymous Users
**************************************************/

-- Authenticated users
create role api_user;
grant usage on schema public to api_user;
alter default privileges in schema public grant all on tables to api_user;
alter default privileges in schema public grant all on sequences to api_user;

-- Anonymous users
create role anon_api_user;
grant usage on schema public to anon_api_user;
alter default privileges in schema public grant all on sequences to anon_api_user;

/**************************************
Create "account" and "blog_post" tables
***************************************/
create table account (
	id bigserial primary key,
	username text not null unique,
	password_hash text not null,
	created_at timestamp without time zone default (now() at time zone 'utc')
);
-- Do not expose the "password_hash" column
comment on column account.password_hash is E'@exclude insert, update, delete, read';
-- Hide createAccount mutation, so we can provide our own to handle "password_hash"
comment on table account is E'@exclude insert';

-- Allow the anonymous user to create and read and account
grant insert on table public.account to anon_api_user;
grant select on table public.account to anon_api_user;


create table blog_post(
	id bigserial primary key,
	account_id bigint not null references account(id),
	title text not null,
	body text not null,
	created_at timestamp without time zone default (now() at time zone 'utc')
);

-- Enable extension for safe hashing and checking of passwords
create extension pgcrypto;

-- create our own createAccount mutation to create accounts and hash the password
create or replace function create_account(
	username text,
	password text
) returns account
as $$
	declare
		acct account;
	begin
		with new_account as (
			insert into account(username, password_hash) values
			-- Hash the password
			(username, crypt(password, gen_salt('bf', 8)))
			returning *
		)
		select * into acct from new_account;

		return acct;
	end;
$$ language plpgsql;


/*****************
JWT Authentication
******************/
create type jwt as (
	account_id bigint,
	username text,
	/* special field to sets the postgres
	role for the current transaction to
	anon_api_user or api_user */
	role text,
	exp integer
);


create or replace function authenticate(
	username text,
	password text
) returns jwt
as $$
	declare
		acct account;
	begin
		select a.* into acct
		from account as a
		where a.username = authenticate.username;

		if acct.password_hash = crypt(password, acct.password_hash) then
		return (
			acct.id,
			acct.username,
			'api_user',
			extract(epoch from now() + interval '7 days')
		)::jwt;

		else return null;

		end if;
	end;
$$ language plpgsql strict security definer;


/*************
Access Control
**************/
-- Opt in to row level security for
alter table account enable row level security;
alter table blog_post enable row level security;

-- An anonymous user may create an account
create policy rls_account_anon_insert on account for insert to anon_api_user with check (true);

-- Accounts can be seen by anyone
create policy rls_account_select on account for select using (true);

-- Accounts may be edited by their owner
create policy rls_account_all on account using (id = nullif(current_setting('jwt.claims.account_id', true), '')::bigint);

-- Blog posts can be seen by anyone
create policy rls_blog_post_select on blog_post for select using (true);

-- Blog posts are editable by their account owner
create policy rls_blog_post_mod on blog_post using (account_id = nullif(current_setting('jwt.claims.account_id', true), '')::bigint);
