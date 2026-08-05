from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vehicles', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='vehicle',
            name='capacity',
            field=models.PositiveIntegerField(default=14, help_text='Total number of passenger seats'),
        ),
    ]