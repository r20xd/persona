from django.db import migrations, models


def copy_selected_toy(apps, schema_editor):
    cat = apps.get_model("accounts", "StudentCat")
    for code in ("yarn", "ball", "mouse", "fish"):
        cat.objects.using(schema_editor.connection.alias).filter(accessory=code).update(toys=[code])


class Migration(migrations.Migration):
    dependencies = [("accounts", "0005_cat_pixel_toys")]
    operations = [
        migrations.AddField(
            model_name="studentcat",
            name="toys",
            field=models.JSONField(default=list),
        ),
        # Legacy accessory remains synchronized by the service for reverse compatibility.
        migrations.RunPython(copy_selected_toy, migrations.RunPython.noop),
    ]
