from django.db import models
from django.contrib.auth.models import User

class Compra(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    ticker = models.CharField(max_length=20)
    cantidad = models.FloatField()
    precio_compra = models.FloatField()
    fecha = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.cantidad} de {self.ticker} a {self.precio_compra}"
    

class Movimiento(models.Model):
    TIPOS = [
        ("COMPRA", "Compra"),
        ("VENTA", "Venta"),
    ]
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=10, choices=TIPOS)
    ticker = models.CharField(max_length=20)
    cantidad = models.FloatField()
    precio = models.FloatField()              # precio por acción en el momento
    fecha = models.DateTimeField(auto_now_add=True)

    def total(self):
        return self.cantidad * self.precio

    def __str__(self):
        return f"{self.tipo} {self.cantidad} {self.ticker} a {self.precio}"
    
class Alerta(models.Model):
    CONDICIONES = [
        ("SUBE", "Sube por encima de"),
        ("BAJA", "Baja por debajo de"),
    ]
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    ticker = models.CharField(max_length=20)
    condicion = models.CharField(max_length=10, choices=CONDICIONES)
    precio_objetivo = models.FloatField()
    activa = models.BooleanField(default=True)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.ticker} {self.condicion} {self.precio_objetivo}"
    

class Perfil(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    saldo = models.FloatField(default=0)

    def __str__(self):
        return f"{self.usuario.username}: {self.saldo} €"