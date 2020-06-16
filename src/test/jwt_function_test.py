import json

CREATE_FUNCTION = """
create type public.jwt_token as (
  role text,
  exp integer,
  email text
);

create function public.authenticate(email text, password text)
returns public.jwt_token
as $$
	begin
		return ('user', 100, email)::public.jwt_token;
	end;
$$
language plpgsql
strict
security definer;
"""


def test_jwt_function(client_builder):
    client = client_builder(CREATE_FUNCTION, jwt_identifier="public.jwt_token", jwt_secret="secret")

    query = """
    mutation {
        authenticate(input: {password: "super_secret", email: "o@r.com", clientMutationId: "some_client_id"}) {
            result
            clientMutationId
        }
    }
    """

    with client:
        resp = client.post("/", json={"query": query})
    result = json.loads(resp.text)
    assert resp.status_code == 200
    assert result["errors"] == []
    token = result["data"]["authenticate"]["result"]
    assert isinstance(token, str)
    assert len(token) > 10
