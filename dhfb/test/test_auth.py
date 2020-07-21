import pytest


@pytest.mark.parametrize(
    'url',
    (
        '/',
        '/storage/',
        '/storage/folder/',
        '/storage/document.pdf',
    )
)
def test_login_required_for_content(client, url):
    """Test that app views redirect to /login for Anonymous user."""
    response = client.get(url)

    assert response.status_code == 302
    assert response.headers['Location'].startswith('http://localhost/login')
