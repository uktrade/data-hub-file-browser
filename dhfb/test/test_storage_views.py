import pytest


@pytest.mark.parametrize(
    ('url', 'listed_filename'),
    (
            (
                    '/storage/',
                    b'default.aspx',
            ),
            (
                    '/storage/kbarticle/Forms/',
                    b'AllItems.aspx',
            ),
    )
)
def test_list_view_renders(client, monkeypatch, url, listed_filename):
    """
    Test that the list views render as expected.

    Currently this test is tightly coupled to the actual
    contents of the Production S3 bucket. Less assumptive
    tests will replace these shortly.  # TODO
    """
    monkeypatch.setattr(
        'authbroker_client.is_authenticated',
        lambda: True,
    )
    response = client.get(url)

    assert response.status_code == 200
    assert b'These are documents moved from CDMS' in response.data
    assert listed_filename in response.data
