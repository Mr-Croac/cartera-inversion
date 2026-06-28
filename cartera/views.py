from django.shortcuts import render
from django.http import JsonResponse
from django.contrib import messages
import yfinance as yf
import json
import urllib.request
import urllib.parse
from .models import Compra, Movimiento, Alerta
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
import csv
from django.http import HttpResponse
from .models import Perfil
def obtener_perfil(usuario):
    perfil, creado = Perfil.objects.get_or_create(usuario=usuario)
    return perfil

def calcular_posiciones(usuario):
    # Agrupar movimientos por ticker
    tickers = Movimiento.objects.filter(usuario=usuario).values_list("ticker", flat=True).distinct()
    

    posiciones = []
    total_invertido = 0
    total_actual = 0

    for ticker in tickers:
        compras = Movimiento.objects.filter(usuario=usuario, ticker=ticker, tipo="COMPRA")
        ventas = Movimiento.objects.filter(usuario=usuario, ticker=ticker, tipo="VENTA")

        acciones_compradas = sum(c.cantidad for c in compras)
        acciones_vendidas = sum(v.cantidad for v in ventas)
        acciones_netas = acciones_compradas - acciones_vendidas
        
        # Si ya no tienes acciones de este ticker, lo saltamos
        if acciones_netas <= 0.0001:
            continue

        # Coste medio de compra
        coste_total_compras = sum(c.cantidad * c.precio for c in compras)
        precio_medio = coste_total_compras / acciones_compradas if acciones_compradas else 0
        invertido = acciones_netas * precio_medio

        # Precio actual
        try:
            precio_actual = yf.Ticker(ticker).info.get("currentPrice")
        except Exception:
            precio_actual = None

        if precio_actual:
            valor_actual = acciones_netas * precio_actual
            ganancia = valor_actual - invertido
            rentabilidad = (ganancia / invertido * 100) if invertido else 0
        else:
            precio_actual = "N/D"
            valor_actual = invertido
            ganancia = 0
            rentabilidad = 0

        posiciones.append({
            "ticker": ticker,
            "acciones": round(acciones_netas, 4),
            "precio_medio": round(precio_medio, 2),
            "precio_actual": precio_actual,
            "invertido": round(invertido, 2),
            "valor_actual": round(valor_actual, 2),
            "ganancia": round(ganancia, 2),
            "rentabilidad": round(rentabilidad, 2),
        })

        total_invertido += invertido
        total_actual += valor_actual if isinstance(valor_actual, (int, float)) else 0

    resumen = {
        "total_invertido": round(total_invertido, 2),
        "total_actual": round(total_actual, 2),
        "ganancia_total": round(total_actual - total_invertido, 2),
        "rentabilidad_total": round((total_actual - total_invertido) / total_invertido * 100, 2) if total_invertido else 0,
    }

    return posiciones, resumen

def inicio(request):
    # ───── PARTE 1: PRECIOS (igual que antes) ─────
    posiciones = []
    resumen_cartera = {"total_invertido": 0, "total_actual": 0, "ganancia_total": 0, "rentabilidad_total": 0}
    columnas_disponibles = {
        "precio":   ("Precio",     "currentPrice"),
        "apertura": ("Apertura",   "open"),
        "maximo":   ("Máximo día", "dayHigh"),
        "minimo":   ("Mínimo día", "dayLow"),
        "volumen":  ("Volumen",    "volume"),
        "per":      ("PER",        "trailingPE"),
    }

    texto_tickers = request.GET.get("tickers", "")
    if texto_tickers.strip():
        tickers = [t.strip().upper() for t in texto_tickers.split(",") if t.strip()]
    else:
        tickers = ["AAPL", "TSLA", "MSFT"]

    seleccionadas = request.GET.getlist("columnas")
    if not seleccionadas:
        seleccionadas = ["precio"]

    acciones = []
    for ticker in tickers:
        try:
            info = yf.Ticker(ticker).info
            nombre = info.get("longName")
            if not nombre:
                acciones.append({"ticker": ticker, "nombre": "❌ No encontrado", "datos": []})
                continue
            fila = {"ticker": ticker, "nombre": nombre, "datos": []}
            for clave in seleccionadas:
                _, campo = columnas_disponibles[clave]
                fila["datos"].append(info.get(campo, "N/D"))
            acciones.append(fila)
        except Exception:
            acciones.append({"ticker": ticker, "nombre": "⚠️ Error", "datos": []})

    cabeceras = [columnas_disponibles[c][0] for c in seleccionadas]

    # ───── PARTE 2: MOVIMIENTOS (compras y ventas) ─────
    movimientos = []
    saldo = 0
    if request.user.is_authenticated:
        posiciones, resumen_cartera = calcular_posiciones(request.user)
        saldo = round(obtener_perfil(request.user).saldo, 2)
        for mov in Movimiento.objects.filter(usuario=request.user).order_by("-fecha"):
            movimientos.append({
                "tipo": mov.tipo,
                "ticker": mov.ticker,
                "cantidad": round(mov.cantidad, 4),
                "precio": round(mov.precio, 2),
                "total": round(mov.total(), 2),
                "fecha": mov.fecha,
            })

    alertas = []
    if request.user.is_authenticated:
        for alerta in Alerta.objects.filter(usuario=request.user, activa=True):
            try:
                precio_actual = yf.Ticker(alerta.ticker).info.get("currentPrice")
            except Exception:
                precio_actual = None

            cumplida = False
            if precio_actual:
                if alerta.condicion == "SUBE" and precio_actual >= alerta.precio_objetivo:
                    cumplida = True
                elif alerta.condicion == "BAJA" and precio_actual <= alerta.precio_objetivo:
                    cumplida = True

            alertas.append({
                "id": alerta.id,
                "ticker": alerta.ticker,
                "condicion": alerta.condicion,
                "precio_objetivo": alerta.precio_objetivo,
                "precio_actual": precio_actual if precio_actual else "N/D",
                "cumplida": cumplida,
            })        

    contexto = {
        "acciones": acciones,
        "cabeceras": cabeceras,
        "columnas_disponibles": columnas_disponibles,
        "seleccionadas": seleccionadas,
        "texto_tickers": texto_tickers,
        "movimientos": movimientos,
         "alertas": alertas,
        "saldo": saldo,
        "posiciones": posiciones,
        "resumen_cartera": resumen_cartera,
    } 
    
    return render(request, 'cartera/inicio.html', contexto)

def buscar_tickers(request):
    consulta = request.GET.get("q", "").strip()

    if not consulta:
        return JsonResponse({"resultados": []})

    url = f"https://query2.finance.yahoo.com/v1/finance/search?q={urllib.parse.quote(consulta)}"

    try:
        peticion = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(peticion, timeout=5) as respuesta:
            datos = json.loads(respuesta.read().decode())

        resultados = []
        for item in datos.get("quotes", []):
            simbolo = item.get("symbol")
            nombre = item.get("shortname") or item.get("longname") or ""
            if simbolo:
                resultados.append({"simbolo": simbolo, "nombre": nombre})

        return JsonResponse({"resultados": resultados[:10]})

    except Exception:
        return JsonResponse({"resultados": []})


def historial_precios(request):
    ticker = request.GET.get("ticker", "").strip().upper()
    periodo = request.GET.get("periodo", "1y")  # por defecto 1 año

    # Periodos válidos de yfinance
    validos = ["1mo", "6mo", "1y", "5y", "max"]
    if periodo not in validos:
        periodo = "1y"

    if not ticker:
        return JsonResponse({"fechas": [], "precios": []})

    try:
        datos = yf.Ticker(ticker).history(period=periodo)
        if datos.empty:
            return JsonResponse({"fechas": [], "precios": []})

        import math
        fechas = []
        precios = []
        for fecha, precio in zip(datos.index, datos["Close"]):
            valor = float(precio)
            if not math.isnan(valor):  # solo añadir si es un número válido
                fechas.append(fecha.strftime("%Y-%m-%d"))
                precios.append(round(valor, 2))

        return JsonResponse({
            "ticker": ticker,
            "fechas": fechas,
            "precios": precios,
        })
    except Exception:
        return JsonResponse({"fechas": [], "precios": []})
    

def precio_actual(request):
    ticker = request.GET.get("ticker", "").strip().upper()
    if not ticker:
        return JsonResponse({"precio": None})
    try:
        precio = yf.Ticker(ticker).info.get("currentPrice")
        return JsonResponse({"precio": precio})
    except Exception:
        return JsonResponse({"precio": None})
    

from django.db.models import Sum

@login_required
def descargar_registro(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="registro_movimientos.csv"'

    writer = csv.writer(response)
    writer.writerow(["Tipo", "Ticker", "Cantidad", "Precio", "Total", "Fecha"])

    for mov in Movimiento.objects.filter(usuario=request.user).order_by("-fecha"):
        writer.writerow([
            mov.tipo, mov.ticker, mov.cantidad, mov.precio,
            round(mov.total(), 2), mov.fecha.strftime("%Y-%m-%d %H:%M"),
        ])

    return response
@login_required
def crear_alerta(request):
    if request.method == "POST":
        ticker = request.POST.get("ticker", "").strip().upper()
        condicion = request.POST.get("condicion")
        precio_objetivo = request.POST.get("precio_objetivo")

        if ticker and condicion and precio_objetivo:
            Alerta.objects.create(
                usuario=request.user,
                ticker=ticker,
                condicion=condicion,
                precio_objetivo=float(precio_objetivo),
            )
    return redirect("inicio")


@login_required
def borrar_alerta(request, alerta_id):
    Alerta.objects.filter(id=alerta_id, usuario=request.user).delete()
    return redirect("inicio")

@login_required
def alertas_ticker(request):
    ticker = request.GET.get("ticker", "").strip().upper()
    alertas = Alerta.objects.filter(usuario=request.user, ticker=ticker, activa=True)
    datos = [
        {"condicion": a.condicion, "precio": a.precio_objetivo}
        for a in alertas
    ]
    
    return JsonResponse({"alertas": datos})

@login_required
def registrar_compra(request):
    if request.method == "POST":
        ticker = request.POST.get("ticker", "").strip().upper()
        cantidad = request.POST.get("cantidad")
        precio = request.POST.get("precio")

        if ticker and cantidad and precio:
            cantidad = float(cantidad)
            precio = float(precio)
            coste = cantidad * precio
            perfil = obtener_perfil(request.user)

            if coste <= perfil.saldo:
                perfil.saldo -= coste
                perfil.save()
                Movimiento.objects.create(
                    usuario=request.user, tipo="COMPRA",
                    ticker=ticker, cantidad=cantidad, precio=precio,
                )
                messages.success(request, f"Compra realizada: {cantidad:.4f} de {ticker} por {coste:.2f} €")
            else:
                messages.error(request, f"Saldo insuficiente. Necesitas {coste:.2f} € y tienes {perfil.saldo:.2f} €")
    return redirect("inicio")

@login_required
def vender(request):
    if request.method == "POST":
        ticker = request.POST.get("ticker", "").strip().upper()
        cantidad = request.POST.get("cantidad")
        precio = request.POST.get("precio")

        if ticker and cantidad and precio:
            cantidad = float(cantidad)
            precio = float(precio)

            compras = Movimiento.objects.filter(
                usuario=request.user, ticker=ticker, tipo="COMPRA"
            ).aggregate(total=Sum("cantidad"))["total"] or 0
            ventas = Movimiento.objects.filter(
                usuario=request.user, ticker=ticker, tipo="VENTA"
            ).aggregate(total=Sum("cantidad"))["total"] or 0
            disponibles = compras - ventas

            if cantidad <= disponibles:
                ingreso = cantidad * precio
                perfil = obtener_perfil(request.user)
                perfil.saldo += ingreso
                perfil.save()
                Movimiento.objects.create(
                    usuario=request.user, tipo="VENTA",
                    ticker=ticker, cantidad=cantidad, precio=precio,
                )
                messages.success(request, f"Venta realizada: {cantidad:.4f} de {ticker} por {ingreso:.2f} €")
            else:
                messages.error(request, f"No tienes suficientes acciones. Disponibles: {disponibles:.4f}")
    return redirect("inicio")

@login_required
def ingresar_fondos(request):
    if request.method == "POST":
        cantidad = request.POST.get("cantidad")
        if cantidad:
            perfil = obtener_perfil(request.user)
            perfil.saldo += float(cantidad)
            perfil.save()
            messages.success(request, f"Has ingresado {float(cantidad):.2f} €")
    return redirect("inicio")

@login_required
def noticias_ticker(request):
    ticker = request.GET.get("ticker", "").strip().upper()
    if not ticker:
        return JsonResponse({"noticias": []})

    try:
        noticias_raw = yf.Ticker(ticker).news
        noticias = []
        for n in noticias_raw[:6]:  # máximo 6 titulares
            contenido = n.get("content", n)
            titulo = contenido.get("title", "Sin título")
            # El enlace puede venir en distintos sitios según la versión
            enlace = ""
            if contenido.get("canonicalUrl"):
                enlace = contenido["canonicalUrl"].get("url", "")
            elif contenido.get("clickThroughUrl"):
                enlace = contenido["clickThroughUrl"].get("url", "")
            editor = contenido.get("provider", {}).get("displayName", "")

            noticias.append({
                "titulo": titulo,
                "enlace": enlace,
                "editor": editor,
            })

        return JsonResponse({"noticias": noticias})
    except Exception:
        return JsonResponse({"noticias": []})
    
  
def calcular_rsi(precios, periodo=14):
    if len(precios) < periodo + 1:
        return []

    rsi = [None] * periodo  # los primeros días no tienen RSI

    # Calcular cambios día a día
    ganancias = []
    perdidas = []
    for i in range(1, len(precios)):
        cambio = precios[i] - precios[i - 1]
        ganancias.append(max(cambio, 0))
        perdidas.append(max(-cambio, 0))

    # Primera media (simple)
    media_ganancia = sum(ganancias[:periodo]) / periodo
    media_perdida = sum(perdidas[:periodo]) / periodo

    for i in range(periodo, len(precios) - 1):
        if media_perdida == 0:
            rsi.append(100)
        else:
            rs = media_ganancia / media_perdida
            rsi.append(round(100 - (100 / (1 + rs)), 2))

        # Media suavizada (estilo Wilder)
        media_ganancia = (media_ganancia * (periodo - 1) + ganancias[i]) / periodo
        media_perdida = (media_perdida * (periodo - 1) + perdidas[i]) / periodo

    return rsi

def indicador_rsi(request):
    ticker = request.GET.get("ticker", "").strip().upper()
    periodo = request.GET.get("periodo", "1y")
    validos = ["1mo", "6mo", "1y", "5y", "max"]
    if periodo not in validos:
        periodo = "1y"

    if not ticker:
        return JsonResponse({"fechas": [], "rsi": []})

    try:
        import math
        datos = yf.Ticker(ticker).history(period=periodo)
        if datos.empty:
            return JsonResponse({"fechas": [], "rsi": []})

        fechas = []
        precios = []
        for fecha, precio in zip(datos.index, datos["Close"]):
            valor = float(precio)
            if not math.isnan(valor):
                fechas.append(fecha.strftime("%Y-%m-%d"))
                precios.append(round(valor, 2))

        rsi = calcular_rsi(precios)
        return JsonResponse({"fechas": fechas, "rsi": rsi})
    except Exception:
        return JsonResponse({"fechas": [], "rsi": []})
    
def calcular_ema(precios, periodo):
    if len(precios) < periodo:
        return []
    ema = []
    mult = 2 / (periodo + 1)
    media_inicial = sum(precios[:periodo]) / periodo
    for i in range(periodo - 1):
        ema.append(None)
    ema.append(round(media_inicial, 4))
    for i in range(periodo, len(precios)):
        valor = (precios[i] - ema[-1]) * mult + ema[-1]
        ema.append(round(valor, 4))
    return ema


def calcular_macd(precios):
    ema12 = calcular_ema(precios, 12)
    ema26 = calcular_ema(precios, 26)
    macd = []
    for i in range(len(precios)):
        if i < len(ema12) and i < len(ema26) and ema12[i] is not None and ema26[i] is not None:
            macd.append(round(ema12[i] - ema26[i], 4))
        else:
            macd.append(None)
    macd_validos = [m for m in macd if m is not None]
    signal_validos = calcular_ema(macd_validos, 9)
    signal = [None] * (len(macd) - len(signal_validos)) + signal_validos
    histograma = []
    for i in range(len(macd)):
        if macd[i] is not None and i < len(signal) and signal[i] is not None:
            histograma.append(round(macd[i] - signal[i], 4))
        else:
            histograma.append(None)
    return macd, signal, histograma


def indicador_macd(request):
    ticker = request.GET.get("ticker", "").strip().upper()
    periodo = request.GET.get("periodo", "1y")
    if periodo not in ["1mo", "6mo", "1y", "5y", "max"]:
        periodo = "1y"
    if not ticker:
        return JsonResponse({"fechas": [], "macd": [], "senal": [], "histograma": []})
    try:
        import math
        datos = yf.Ticker(ticker).history(period=periodo)
        if datos.empty:
            return JsonResponse({"fechas": [], "macd": [], "senal": [], "histograma": []})
        fechas = []
        precios = []
        for fecha, precio in zip(datos.index, datos["Close"]):
            valor = float(precio)
            if not math.isnan(valor):
                fechas.append(fecha.strftime("%Y-%m-%d"))
                precios.append(round(valor, 2))
        macd, signal, histograma = calcular_macd(precios)
        return JsonResponse({"fechas": fechas, "macd": macd, "senal": signal, "histograma": histograma})
    except Exception:
        return JsonResponse({"fechas": [], "macd": [], "senal": [], "histograma": []})
    
def calcular_bollinger(precios, periodo=20, num_desv=2):
    import math
    banda_media = []
    banda_sup = []
    banda_inf = []

    for i in range(len(precios)):
        if i < periodo - 1:
            banda_media.append(None)
            banda_sup.append(None)
            banda_inf.append(None)
        else:
            ventana = precios[i - periodo + 1 : i + 1]
            media = sum(ventana) / periodo
            # Desviación típica
            varianza = sum((p - media) ** 2 for p in ventana) / periodo
            desv = math.sqrt(varianza)
            banda_media.append(round(media, 2))
            banda_sup.append(round(media + num_desv * desv, 2))
            banda_inf.append(round(media - num_desv * desv, 2))

    return banda_media, banda_sup, banda_inf


def indicador_bollinger(request):
    ticker = request.GET.get("ticker", "").strip().upper()
    periodo = request.GET.get("periodo", "1y")
    if periodo not in ["1mo", "6mo", "1y", "5y", "max"]:
        periodo = "1y"
    if not ticker:
        return JsonResponse({"fechas": [], "media": [], "superior": [], "inferior": []})
    try:
        import math
        datos = yf.Ticker(ticker).history(period=periodo)
        if datos.empty:
            return JsonResponse({"fechas": [], "media": [], "superior": [], "inferior": []})
        fechas = []
        precios = []
        for fecha, precio in zip(datos.index, datos["Close"]):
            valor = float(precio)
            if not math.isnan(valor):
                fechas.append(fecha.strftime("%Y-%m-%d"))
                precios.append(round(valor, 2))
        media, sup, inf = calcular_bollinger(precios)
        return JsonResponse({"fechas": fechas, "media": media, "superior": sup, "inferior": inf})
    except Exception:
        return JsonResponse({"fechas": [], "media": [], "superior": [], "inferior": []})