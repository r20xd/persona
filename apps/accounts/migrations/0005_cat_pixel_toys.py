from django.db import migrations, models

MAPPING = {"scarf": "yarn", "glasses": "ball", "gown": "mouse", "mug": "fish"}


def forward(apps, schema_editor):
    cat = apps.get_model("accounts", "StudentCat")
    for old, new in MAPPING.items():
        cat.objects.using(schema_editor.connection.alias).filter(accessory=old).update(
            accessory=new
        )


def backward(apps, schema_editor):
    cat = apps.get_model("accounts", "StudentCat")
    for old, new in MAPPING.items():
        cat.objects.using(schema_editor.connection.alias).filter(accessory=new).update(
            accessory=old
        )


class Migration(migrations.Migration):
    dependencies = [("accounts", "0004_studentcat")]
    operations = [
        migrations.RemoveConstraint(model_name="studentcat", name="cat_accessory_valid"),
        migrations.RunPython(forward, backward),
        migrations.AddConstraint(
            model_name="studentcat",
            constraint=models.CheckConstraint(
                condition=models.Q(accessory__in=["none", "yarn", "ball", "mouse", "fish"]),
                name="cat_accessory_valid",
            ),
        ),
    ]
