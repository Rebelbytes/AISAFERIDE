# Generated manually for Challan model

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0003_vehicleowner'),
    ]

    operations = [
        migrations.CreateModel(
            name='Challan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('vehicle_number', models.CharField(max_length=15)),
                ('violation_type', models.CharField(max_length=100)),
                ('fine_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('date_issued', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(default='Pending', max_length=20)),
                ('notes', models.TextField(blank=True)),
                ('owner', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='accounts.vehicleowner')),
            ],
        ),
    ]
