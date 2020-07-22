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


def test_content_object_attachment_downloads(client, monkeypatch):
    """
    Test that a file downloads correctly.

    Currently this test is tightly coupled to the actual
    contents of the Production S3 bucket. Less assumptive
    tests will replace these shortly.  # TODO
    """
    monkeypatch.setattr(
        'authbroker_client.is_authenticated',
        lambda: True,
    )
    response = client.get('/storage/kbarticle/Forms/AllItems.aspx')

    assert response.status_code == 200
    assert len(response.data) == 3370
    for header, value in (
            ('Content-Type', 'application/xml; charset=utf-8'),
            ('Content-Disposition', 'attachment; filename=AllItems.aspx'),
    ):
        assert response.headers[header] == value, f'{header} != {value}'


# TODO: Set the 'authenticated' status as a pytest fixture
