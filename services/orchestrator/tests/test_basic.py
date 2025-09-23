"""Basic tests to validate testing framework setup."""


def test_basic_assertion():
    """Test that basic assertions work."""
    assert True


def test_math_operations():
    """Test basic math operations."""
    assert 1 + 1 == 2
    assert 10 / 2 == 5


def test_string_operations():
    """Test string operations."""
    assert "HELIOS" + " Orchestrator" == "HELIOS Orchestrator"
    assert "test".upper() == "TEST"


class TestBasicClass:
    """Test basic class functionality."""

    def test_instance_creation(self):
        """Test creating class instances."""
        test_dict = {"key": "value"}
        assert test_dict["key"] == "value"

    def test_list_operations(self):
        """Test list operations."""
        test_list = [1, 2, 3]
        test_list.append(4)
        assert len(test_list) == 4
        assert test_list[-1] == 4
