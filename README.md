# 📈 Cartera de Inversión

Simulador de cartera de inversión construido con Django. Permite buscar acciones en tiempo real, simular compras y ventas, seguir la evolución de tus posiciones y analizar el mercado con indicadores técnicos profesionales.

> ⚠️ **Nota:** Es un simulador con fines educativos. No utiliza dinero real ni constituye asesoramiento financiero.

---

## ✨ Funcionalidades

- 🔍 **Buscador de mercado en tiempo real** con autocompletado (acciones, índices) y vista previa del precio al pasar el ratón.
- 📊 **Gráficas interactivas** de evolución del precio con distintos periodos (1M, 6M, 1A, 5A, Máx) y comparación entre varias empresas.
- 📈 **Indicadores técnicos** calculados desde cero:
  - **Media móvil** de 20 sesiones
  - **RSI** (Índice de Fuerza Relativa) con bandas de sobrecompra/sobreventa
  - **MACD** con línea de señal e histograma
  - **Bandas de Bollinger**
- 💰 **Simulación de compras y ventas** con gestión de saldo por usuario.
- 📂 **Cartera personal** con resumen global (invertido, valor actual, ganancia, rentabilidad), tabla de posiciones y gráfico de distribución.
- 🔔 **Alertas de precio** (avisa cuando una acción sube o baja de un valor objetivo).
- 📰 **Noticias financieras** de cada empresa.
- 📥 **Exportación** del registro de movimientos a CSV.
- 🌙 **Modo oscuro / claro**.
- 👤 **Sistema de usuarios** (registro, inicio y cierre de sesión).

---

## 🛠️ Tecnologías

- **Backend:** Python, Django
- **Datos de mercado:** yfinance (API de Yahoo Finance)
- **Frontend:** HTML, CSS, JavaScript
- **Gráficas:** Chart.js
- **Base de datos:** SQLite

---

## 🚀 Instalación y uso

Sigue estos pasos para ejecutar el proyecto en tu ordenador.

### 1. Clonar el repositorio

```bash
git clone https://github.com/Mr-Croac/cartera-inversion.git
cd cartera-inversion
```

### 2. Crear y activar un entorno virtual

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Mac / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar las dependencias

```bash
pip install -r requirements.txt
```

### 4. Aplicar las migraciones de la base de datos

```bash
python manage.py migrate
```

### 5. Arrancar el servidor

```bash
python manage.py runserver
```

### 6. Abrir en el navegador

Visita 👉 `http://127.0.0.1:8000/`

---

## 📸 Capturas

> _Añade aquí tus capturas de pantalla._

<!--
Para añadir una captura:
1. Sube la imagen al repositorio (por ejemplo en una carpeta "capturas").
2. Enlázala así:

![Pantalla principal](capturas/principal.png)
![Gráfica con indicadores](capturas/indicadores.png)
![Mi cartera](capturas/cartera.png)
-->

---

## 🗺️ Próximas mejoras

- [ ] Informe diario automático por email
- [ ] Más indicadores técnicos (volatilidad)
- [ ] Despliegue online

---

## 👤 Autor

Desarrollado por [Mr-Croac](https://github.com/Mr-Croac) como proyecto de aprendizaje.
