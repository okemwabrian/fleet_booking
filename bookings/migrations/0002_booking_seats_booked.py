from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='seats_booked',
            field=models.PositiveIntegerField(default=1),
        ),
    ]