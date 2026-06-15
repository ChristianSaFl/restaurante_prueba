# Laboratorio 05 — Pruebas Funcionales con Selenium
**Curso:** Ingeniería de Software II | **Docente:** DSc. Edgar Sarmiento

---

## Estructura agregada al proyecto

```
Proyecto-software2-desarrollo/
├── requirements.txt                          ← dependencias
├── src/main/python/web/
│   ├── app.py                                ← servidor Flask
│   └── templates/
│       ├── base.html
│       └── products/
│           ├── create.html                   ← formulario Create Product
│           ├── list.html
│           └── detail.html
└── tests/lab05/
    ├── test_create_product_funcional.py      ← pruebas unitarias (sin Selenium)
    └── test_selenium_create_product.py       ← pruebas funcionales con Selenium
```

---

## Instalación

```bash
pip install -r requirements.txt
```

---

## Ejecutar el servidor web

```bash
# Desde la raíz del proyecto
cd src
PYTHONPATH=. python main/python/web/app.py
# → http://localhost:8083
```

---

## Ejecutar las pruebas Selenium (Lab 05)

> El servidor Flask se levanta automáticamente dentro de los tests
> en el puerto **8084**, separado del servidor de desarrollo.

```bash
# Desde la raíz del proyecto
PYTHONPATH=src python -m pytest tests/lab05/test_selenium_create_product.py -v
```

Con reporte HTML:
```bash
PYTHONPATH=src python -m pytest tests/lab05/test_selenium_create_product.py -v \
    --html=reporte_selenium_lab05.html --self-contained-html
```

---

## Ejecutar TODAS las pruebas

```bash
PYTHONPATH=src python -m pytest tests/ -v --html=reporte_completo.html --self-contained-html
```

---

## Requisitos previos para Selenium

- **Google Chrome** instalado en tu PC
- `webdriver-manager` descarga ChromeDriver automáticamente

Si tienes Firefox en lugar de Chrome, cambia en `test_selenium_create_product.py`:
```python
# En vez de _chrome_driver(), usa:
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager
driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()))
```

---

## Tabla de Casos de Prueba (Caja Negra)

| ID   | Escenario                           | Valores de Prueba               | Resultado Esperado                   |
|------|-------------------------------------|---------------------------------|--------------------------------------|
| CP01 | Producto válido                     | name="Pizza", price="20.00"     | Aparece en lista de productos        |
| CP02 | Precio mínimo (valor límite)        | name="Agua", price="0.01"       | Creado exitosamente                  |
| CP03 | Precio alto                         | name="Langosta", price="999.99" | Creado exitosamente                  |
| CP04 | Nombre vacío                        | name="", price="10"             | Error en formulario                  |
| CP05 | Nombre solo espacios                | name="   ", price="10"          | Error en formulario                  |
| CP06 | Precio = 0 (valor límite inválido)  | name="Pizza", price="0"         | Error en formulario                  |
| CP07 | Precio negativo                     | name="Pizza", price="-5"        | Error en formulario                  |
| CP08 | Precio vacío                        | name="Pizza", price=""          | Error en formulario                  |
| CP09 | Precio no numérico                  | name="Pizza", price="abc"       | Error en formulario                  |
| CP10 | Caracteres especiales en nombre     | name="Café & Té", price="15.50" | Guardado correctamente               |
| CP11 | Precio decimal                      | name="Jugo", price="3.75"       | Precio mostrado como 3.75            |
| CP12 | Verificar página de detalle         | name="Sopa", price="12.00"      | Detalle muestra nombre y precio      |
| CP13 | Cancelar formulario                 | clic en "Cancelar"              | Vuelve a lista sin crear producto    |
| CP14 | Título de página correcto           | GET /products/new               | Título contiene "Crear Producto"     |
| CP15 | Campos del formulario presentes     | GET /products/new               | Inputs name, price y botón visibles  |
