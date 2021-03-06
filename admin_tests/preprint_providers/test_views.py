import json

from nose import tools as nt
from django.test import RequestFactory

from tests.base import AdminTestCase
from osf_tests.factories import (
    AuthUserFactory,
    PreprintProviderFactory,
    PreprintFactory,
    SubjectFactory,
)
from osf.models import PreprintProvider
from admin_tests.utilities import setup_form_view, setup_user_view
from admin.preprint_providers import views
from admin.preprint_providers.forms import PreprintProviderForm
from admin.base.forms import ImportFileForm


class TestPreprintProviderList(AdminTestCase):
    def setUp(self):
        super(TestPreprintProviderList, self).setUp()

        self.provider1 = PreprintProviderFactory()
        self.provider2 = PreprintProviderFactory()

        self.user = AuthUserFactory()

        self.request = RequestFactory().get('/fake_path')
        self.view = views.PreprintProviderList()
        self.view = setup_user_view(self.view, self.request, user=self.user)

    def test_get_list(self, *args, **kwargs):
        res = self.view.get(self.request, *args, **kwargs)
        nt.assert_equal(res.status_code, 200)

    def test_get_queryset(self):
        providers_returned = list(self.view.get_queryset())
        provider_list = [self.provider1, self.provider2]
        nt.assert_items_equal(providers_returned, provider_list)
        nt.assert_is_instance(providers_returned[0], PreprintProvider)

    def test_context_data(self):
        self.view.object_list = self.view.get_queryset()
        res = self.view.get_context_data()
        nt.assert_is_instance(res, dict)
        nt.assert_equal(len(res['preprint_providers']), 2)
        nt.assert_is_instance(res['preprint_providers'][0], PreprintProvider)


class TestPreprintProviderDisplay(AdminTestCase):
    def setUp(self):
        super(TestPreprintProviderDisplay, self).setUp()

        self.user = AuthUserFactory()

        self.preprint_provider = PreprintProviderFactory()

        self.request = RequestFactory().get('/fake_path')
        self.view = views.PreprintProviderDisplay()
        self.view = setup_user_view(self.view, self.request, user=self.user)

        self.view.kwargs = {'preprint_provider_id': self.preprint_provider.id}

    def test_get_object(self):
        obj = self.view.get_object()
        nt.assert_is_instance(obj, PreprintProvider)
        nt.assert_equal(obj.name, self.preprint_provider.name)

    def test_context_data(self):
        res = self.view.get_context_data()
        nt.assert_is_instance(res, dict)
        nt.assert_is_instance(res['preprint_provider'], dict)
        nt.assert_equal(res['preprint_provider']['name'], self.preprint_provider.name)
        nt.assert_is_instance(res['form'], PreprintProviderForm)
        nt.assert_is_instance(res['import_form'], ImportFileForm)

    def test_get(self, *args, **kwargs):
        res = self.view.get(self.request, *args, **kwargs)
        nt.assert_equal(res.status_code, 200)


class TestDeletePreprintProvider(AdminTestCase):
    def setUp(self):
        super(TestDeletePreprintProvider, self).setUp()

        self.user = AuthUserFactory()
        self.preprint_provider = PreprintProviderFactory()

        self.request = RequestFactory().get('/fake_path')
        self.view = views.DeletePreprintProvider()
        self.view = setup_user_view(self.view, self.request, user=self.user)

        self.view.kwargs = {'preprint_provider_id': self.preprint_provider.id}

    def test_cannot_delete_if_preprints_present(self):
        preprint = PreprintFactory()
        self.preprint_provider.preprint_services.add(preprint)
        self.preprint_provider.save()

        redirect = self.view.delete(self.request)
        nt.assert_equal(redirect.url, '/preprint_providers/{}/cannot_delete/'.format(self.preprint_provider.id))
        nt.assert_equal(redirect.status_code, 302)

    def test_delete_provider_with_no_preprints(self):
        redirect = self.view.delete(self.request)
        nt.assert_equal(redirect.url, '/preprint_providers/')
        nt.assert_equal(redirect.status_code, 302)

    def test_get_with_no_preprints(self):
        res = self.view.get(self.request)
        nt.assert_equal(res.status_code, 200)

    def test_cannot_get_if_preprints_present(self):
        preprint = PreprintFactory()
        self.preprint_provider.preprint_services.add(preprint)
        self.preprint_provider.save()

        redirect = self.view.get(self.request)
        nt.assert_equal(redirect.url, '/preprint_providers/{}/cannot_delete/'.format(self.preprint_provider.id))
        nt.assert_equal(redirect.status_code, 302)


class TestPreprintProviderChangeForm(AdminTestCase):
    def setUp(self):
        super(TestPreprintProviderChangeForm, self).setUp()

        self.user = AuthUserFactory()
        self.preprint_provider = PreprintProviderFactory()

        self.request = RequestFactory().get('/fake_path')
        self.request.user = self.user
        self.view = views.PreprintProviderChangeForm()
        self.view = setup_form_view(self.view, self.request, form=PreprintProviderForm())

        self.parent_1 = SubjectFactory()
        self.child_1 = SubjectFactory(parent=self.parent_1)
        self.child_2 = SubjectFactory(parent=self.parent_1)
        self.grandchild_1 = SubjectFactory(parent=self.child_1)

        self.view.kwargs = {'preprint_provider_id': self.preprint_provider.id}

    def test_get_context_data(self):
        self.view.object = self.preprint_provider
        res = self.view.get_context_data()
        nt.assert_is_instance(res, dict)
        nt.assert_is_instance(res['import_form'], ImportFileForm)

    def test_preprint_provider_form(self):
        formatted_rule = [[[self.parent_1._id], True]]

        new_data = {
            'name': 'New Name',
            'subjects_chosen': '{}, {}, {}, {}'.format(
                self.parent_1.id, self.child_1.id, self.child_2.id, self.grandchild_1.id
            ),
            'toplevel_subjects': [self.parent_1.id],
            'subjects_acceptable': '[]',
            '_id': 'newname'
        }
        form = PreprintProviderForm(data=new_data)
        nt.assert_true(form.is_valid())

        new_provider = form.save()
        nt.assert_equal(new_provider.name, new_data['name'])
        nt.assert_equal(new_provider.subjects_acceptable, formatted_rule)


class TestPreprintProviderExport(AdminTestCase):
    def setUp(self):
        super(TestPreprintProviderExport, self).setUp()

        self.user = AuthUserFactory()
        self.preprint_provider = PreprintProviderFactory()

        self.request = RequestFactory().get('/fake_path')
        self.view = views.ExportPreprintProvider()
        self.view = setup_user_view(self.view, self.request, user=self.user)

        self.view.kwargs = {'preprint_provider_id': self.preprint_provider.id}

    def test_post(self):
        res = self.view.get(self.request)
        content_dict = json.loads(res.content)
        nt.assert_equal(content_dict['model'], 'osf.preprintprovider')
        nt.assert_equal(content_dict['fields']['name'], self.preprint_provider.name)
        nt.assert_equal(res.__getitem__('content-type'), 'text/json')

    def test_certain_fields_not_included(self):
        res = self.view.get(self.request)
        content_dict = json.loads(res.content)
        for field in views.FIELDS_TO_NOT_IMPORT_EXPORT:
            nt.assert_not_in(field, content_dict['fields'].keys())


class TestCreatePreprintProvider(AdminTestCase):
    def setUp(self):
        super(TestCreatePreprintProvider, self).setUp()

        self.user = AuthUserFactory()
        self.preprint_provider = PreprintProviderFactory()

        self.request = RequestFactory().get('/fake_path')
        self.request.user = self.user
        self.view = views.CreatePreprintProvider()
        self.view = setup_form_view(self.view, self.request, form=PreprintProviderForm())

        self.view.kwargs = {'preprint_provider_id': self.preprint_provider.id}

    def test_get_context_data(self):
        self.view.object = self.preprint_provider
        res = self.view.get_context_data()
        nt.assert_is_instance(res, dict)
        nt.assert_is_instance(res['import_form'], ImportFileForm)

    def test_get_view(self):
        res = self.view.get(self.request)
        nt.assert_equal(res.status_code, 200)


class TestGetSubjectDescendants(AdminTestCase):
    def setUp(self):
        super(TestGetSubjectDescendants, self).setUp()

        self.user = AuthUserFactory()
        self.preprint_provider = PreprintProviderFactory()

        self.parent_1 = SubjectFactory()
        self.child_1 = SubjectFactory(parent=self.parent_1)
        self.child_2 = SubjectFactory(parent=self.parent_1)
        self.grandchild_1 = SubjectFactory(parent=self.child_1)

        self.request = RequestFactory().get('/?parent_id={}'.format(self.parent_1.id))
        self.view = views.GetSubjectDescendants()
        self.view = setup_user_view(self.view, self.request, user=self.user)

    def test_get_subject_descendants(self):
        res = self.view.get(self.request)
        nt.assert_equal(res.status_code, 200)
        nt.assert_equal(res.__getitem__('content-type'), 'application/json')

        content_dict = json.loads(res.content)
        nt.assert_items_equal(
            content_dict['all_descendants'],
            [self.child_1.id, self.child_2.id, self.grandchild_1.id]
        )
