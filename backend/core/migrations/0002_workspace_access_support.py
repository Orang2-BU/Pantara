from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('core', '0001_initial')]

    operations = [
        migrations.AddField(
            model_name='workspace', name='access_support', field=models.JSONField(default=list)
        ),
    ]
