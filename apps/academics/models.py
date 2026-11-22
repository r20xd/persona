from django.db import models


class Faculty(models.Model):
    code = models.SlugField(unique=True)
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Program(models.Model):
    code = models.SlugField(unique=True)
    name = models.CharField(max_length=200)
    faculty = models.ForeignKey(Faculty, on_delete=models.PROTECT)

    def __str__(self):
        return self.name


class StudyGroup(models.Model):
    code = models.CharField(max_length=30, unique=True)
    program = models.ForeignKey(Program, on_delete=models.PROTECT)

    def __str__(self):
        return self.code


class Term(models.Model):
    code = models.SlugField(unique=True)
    title = models.CharField(max_length=160)
    starts_on = models.DateField()
    ends_on = models.DateField()

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(ends_on__gte=models.F("starts_on")), name="term_dates_valid"
            )
        ]


class Subject(models.Model):
    code = models.SlugField(unique=True)
    name = models.CharField(max_length=200)


class Teacher(models.Model):
    code = models.SlugField(unique=True)
    full_name = models.CharField(max_length=200)


class Room(models.Model):
    code = models.SlugField(unique=True)
    building = models.CharField(max_length=120)
    number = models.CharField(max_length=30)


class CourseOffering(models.Model):
    class ControlType(models.TextChoices):
        EXAM = "exam", "Экзамен"
        CREDIT = "credit", "Зачёт"

    subject = models.ForeignKey(Subject, on_delete=models.PROTECT)
    group = models.ForeignKey(StudyGroup, on_delete=models.PROTECT)
    term = models.ForeignKey(Term, on_delete=models.PROTECT)
    control_type = models.CharField(max_length=6, choices=ControlType.choices)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["subject", "group", "term"], name="offering_unique"),
            models.CheckConstraint(
                condition=models.Q(control_type__in=["exam", "credit"]),
                name="offering_control_valid",
            ),
        ]


class Enrollment(models.Model):
    student = models.ForeignKey("accounts.StudentProfile", on_delete=models.PROTECT)
    offering = models.ForeignKey(CourseOffering, on_delete=models.PROTECT)

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.student_id and self.offering_id and self.student.group_id != self.offering.group_id:
            raise ValidationError("Курс должен принадлежать группе студента.")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["student", "offering"], name="enrollment_unique")
        ]
