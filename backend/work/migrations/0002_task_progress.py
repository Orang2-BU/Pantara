from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('work', '0001_initial')]

    operations = [
        migrations.AddField(
            model_name='task', name='progress',
            field=models.PositiveSmallIntegerField(default=0, help_text='Percent complete (0-100)')
        ),
    ]
