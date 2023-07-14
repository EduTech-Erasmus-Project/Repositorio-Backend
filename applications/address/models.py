from django.db import models
from model_utils.models import TimeStampedModel


# Create your models here.
class Country(TimeStampedModel):
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return str(self.name)


class Province(TimeStampedModel):
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name="province")

    def __str__(self):
        return str(self.name)


class City(TimeStampedModel):
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    province = models.ForeignKey(Province, on_delete=models.CASCADE, related_name="city")

    def __str__(self):
        return str(self.name)


class University(TimeStampedModel):
    name = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name="university", null=True)

    def __str__(self):
        return str(self.name)


class Campus(TimeStampedModel):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=300)
    is_active = models.BooleanField(default=True)
    university = models.ForeignKey(University, on_delete=models.CASCADE, related_name="campus")
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name="campus_city", null=True)

    def __str__(self):
        return str(self.name)
