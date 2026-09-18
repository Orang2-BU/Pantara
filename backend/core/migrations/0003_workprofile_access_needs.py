from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('core', '0002_workspace_access_support')]

    operations = [
        migrations.AddField(
            model_name='workprofile', name='access_needs', field=models.JSONField(default=list)
        ),
    ]
