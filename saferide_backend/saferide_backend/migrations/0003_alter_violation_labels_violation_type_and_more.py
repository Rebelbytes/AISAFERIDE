
# Generated manually to fix schema mismatch

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('saferide_backend', '0002_rename_timestamp_violation_created_at_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='violation',
            old_name='labels',
            new_name='violation_type',
        ),
        migrations.AddField(
            model_name='violation',
            name='confidence',
            field=models.FloatField(default=0.0),
        ),
    ]
