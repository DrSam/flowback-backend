import pytest
from flowback.group.tests import factories as group_factories
from django.core.files.uploadedfile import SimpleUploadedFile

pytestmark = pytest.mark.django_db


def test_create_decidable(api_client):
    group_user = group_factories.GroupUserFactory()
    api_client.force_login(group_user.user)
    
    data = {
        'group':group_user.group.id,
        'decidable_type':'poll'
    }
    
    url = f'/decidable-management/decidable/'
    response = api_client.post(
        url,
        data,
        format='multipart'
    )
    print(response.json())