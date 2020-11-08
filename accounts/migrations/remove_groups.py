from django.db import migrations


def forwards_func(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    User = apps.get_model("auth", "User")
    groups = ["alum", "employee", "faculty", "member", "staff", "student"]
    db_alias = schema_editor.connection.alias

    Group.objects.bulk_create(Group(name=f"platform_{group}") for group in groups)

    for user in User.objects.all():
        user_group = user.groups.all()
        for group in user_group:
            user.groups.add(f"platfrom_{group}")

    for group in groups:
        Group.objects.using(db_alias).filter(name=group).delete()


# create platfrom_group and go over all users to update their groups
class Migration(migrations.Migration):
    dependencies = [("accounts", "0001_initial")]
    operations = [
        migrations.RunPython(forwards_func, None),
    ]
