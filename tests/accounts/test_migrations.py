from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase

from accounts.migrations.rename_groups import forwards_func


class RenameGroupsMigrationTestCase(TestCase):
    def setUp(self):
        User = get_user_model()
        
        self.user1 = User.objects.create_user(username="user1", email="user1@test.com")
        self.user2 = User.objects.create_user(username="user2", email="user2@test.com")
        
        self.student_group = Group.objects.create(name='student')
        self.staff_group = Group.objects.create(name='staff')
        self.member_group = Group.objects.create(name='member')
        
        self.user1.groups.add(self.student_group, self.member_group)
        self.user2.groups.add(self.staff_group)
    
    def test_migration_function_renames_groups_correctly(self):
        class MockSchemaEditor:
            pass
        
        forwards_func(apps, MockSchemaEditor())
        
        # old groups should be gone
        self.assertFalse(Group.objects.filter(name='student').exists())
        self.assertFalse(Group.objects.filter(name='staff').exists())
        self.assertFalse(Group.objects.filter(name='member').exists())
        
        # new platform_ groups should exist
        self.assertTrue(Group.objects.filter(name='platform_student').exists())
        self.assertTrue(Group.objects.filter(name='platform_staff').exists())
        self.assertTrue(Group.objects.filter(name='platform_member').exists())
    
    def test_migration_updates_user_group_memberships(self):
        class MockSchemaEditor:
            pass
        
        forwards_func(apps, MockSchemaEditor())
        
        self.user1.refresh_from_db()
        self.user2.refresh_from_db()
        
        user1_groups = set(self.user1.groups.values_list('name', flat=True))
        user2_groups = set(self.user2.groups.values_list('name', flat=True))
        
        # users should have new platform_ groups
        self.assertIn('platform_student', user1_groups)
        self.assertIn('platform_member', user1_groups)
        self.assertIn('platform_staff', user2_groups)
        
        # old groups should be removed
        self.assertNotIn('student', user1_groups)
        self.assertNotIn('member', user1_groups)
        self.assertNotIn('staff', user2_groups)
    
    def test_migration_creates_all_required_platform_groups(self):
        platform_groups = ["alum", "employee", "faculty", "member", "staff", "student"]
        
        class MockSchemaEditor:
            pass
        
        forwards_func(apps, MockSchemaEditor())
        
        for group_name in platform_groups:
            self.assertTrue(
                Group.objects.filter(name=f'platform_{group_name}').exists(),
                f'platform_{group_name} group should exist after migration'
            )
    
    def test_migration_uses_auth_user_model_setting(self):
        # migration should use AUTH_USER_MODEL instead of hardcoded auth.User
        User = apps.get_model(settings.AUTH_USER_MODEL)
        
        self.assertIsNotNone(User)
        self.assertTrue(hasattr(User, 'username'))
        self.assertTrue(hasattr(User, 'email'))
        self.assertTrue(hasattr(User, 'groups'))
    
    def test_migration_handles_users_without_platform_groups(self):
        User = get_user_model()
        
        user3 = User.objects.create_user(username="user3", email="user3@test.com")
        other_group = Group.objects.create(name='other_group')
        user3.groups.add(other_group)
        
        class MockSchemaEditor:
            pass
        
        forwards_func(apps, MockSchemaEditor())
        
        user3.refresh_from_db()
        user3_groups = set(user3.groups.values_list('name', flat=True))
        self.assertIn('other_group', user3_groups)
    
    def test_migration_is_idempotent(self):
        # running migration multiple times shouldn't break things
        class MockSchemaEditor:
            pass
        
        forwards_func(apps, MockSchemaEditor())
        forwards_func(apps, MockSchemaEditor())
        
        platform_groups = ["alum", "employee", "faculty", "member", "staff", "student"]
        for group_name in platform_groups:
            count = Group.objects.filter(name=f'platform_{group_name}').count()
            self.assertEqual(count, 1)
    
    def test_migration_with_empty_database(self):
        User = get_user_model()
        User.objects.all().delete()
        Group.objects.all().delete()
        
        class MockSchemaEditor:
            pass
        
        forwards_func(apps, MockSchemaEditor())
        
        platform_groups = ["alum", "employee", "faculty", "member", "staff", "student"]
        for group_name in platform_groups:
            self.assertTrue(Group.objects.filter(name=f'platform_{group_name}').exists())


class CustomUserModelCompatibilityTest(TestCase):
    def test_get_model_with_auth_user_model_setting(self):
        # checks if apps.get_model works with AUTH_USER_MODEL
        User = apps.get_model(settings.AUTH_USER_MODEL)
        
        self.assertIsNotNone(User)
        self.assertTrue(hasattr(User, 'objects'))
        self.assertEqual(User, get_user_model())
    
    def test_get_model_accepts_dotted_string(self):
        # both formats should give us the same model
        User1 = apps.get_model(settings.AUTH_USER_MODEL)
        
        app_label, model_name = settings.AUTH_USER_MODEL.split('.')
        User2 = apps.get_model(app_label, model_name)
        
        self.assertEqual(User1, User2)