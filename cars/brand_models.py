from django.db import models


class CarBrand(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class CarModel(models.Model):
    brand = models.ForeignKey(CarBrand, on_delete=models.CASCADE, related_name="models")
    name = models.CharField(max_length=50)

    class Meta:
        unique_together = ("brand", "name")

    def __str__(self):
        return f"{self.brand.name} - {self.name}"
