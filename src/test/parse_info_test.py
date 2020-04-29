import pytest
from nebulo.gql.parse_info import ASTNode


def test_astnode_get_subfield_alias_exception():
    with pytest.raises(Exception):
        # Calling instance method on class
        # No instance variables used before the thing
        # we're trying to test
        ASTNode.get_subfield_alias(None, path=[])  # type: ignore
