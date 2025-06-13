from multi_db_connector.factory import get_connector

def test_invalid_type():
    config = {"type": "unknown"}
    try:
        get_connector(config)
    except ValueError as e:
        assert "Unsupported DB type" in str(e)