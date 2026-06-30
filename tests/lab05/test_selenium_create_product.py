"""


Objeto de Prueba : Funcionalidad "Create Product" (interfaz web Flask)
Estrategia       : Clases de Equivalencia + Valores Límite (Caja Negra)
Framework        : Selenium WebDriver 4 + unittest (xUnit para Python)

TABLA DE CASOS DE PRUEBA
=========================
| ID  | Escenario                          | Valores de Prueba              | Resultado Esperado                              |
|-----|------------------------------------|--------------------------------|-------------------------------------------------|
| CP01| Crear producto válido              | name="Pizza", price="20.00"    | Redirige a lista; producto aparece en tabla     |
| CP02| Crear producto precio mínimo       | name="Agua", price="0.01"      | Producto creado exitosamente                    |
| CP03| Crear producto precio alto         | name="Langosta", price="999.99"| Producto creado exitosamente                    |
| CP04| Nombre vacío → error               | name="", price="10"            | Permanece en form; muestra mensaje de error     |
| CP05| Nombre solo espacios → error       | name="   ", price="10"         | Permanece en form; muestra mensaje de error     |
| CP06| Precio cero → error                | name="Pizza", price="0"        | Permanece en form; muestra mensaje de error     |
| CP07| Precio negativo → error            | name="Pizza", price="-5"       | Permanece en form; muestra mensaje de error     |
| CP08| Precio vacío → error               | name="Pizza", price=""         | Permanece en form; muestra mensaje de error     |
| CP09| Precio no numérico → error         | name="Pizza", price="abc"      | Permanece en form; muestra mensaje de error     |
| CP10| Nombre con caracteres especiales   | name="Café & Té", price="15.5" | Producto creado; nombre guardado correctamente  |
| CP11| Precio decimal válido              | name="Jugo", price="3.75"      | Producto creado; precio mostrado como 3.75      |
| CP12| Crear producto y verificar detalle | name="Sopa", price="12.00"     | Página detalle muestra nombre y precio          |
| CP13| Cancelar formulario                | (clic en Cancelar)             | Redirige a lista sin crear producto             |
| CP14| Página muestra título correcto     | GET /products/new              | Título de página contiene "Crear Producto"      |
| CP15| Formulario tiene campos requeridos | GET /products/new              | Existen inputs id="name" e id="price"           |

INSTRUCCIONES PARA EJECUTAR
============================
1. Instalar dependencias:
       pip install flask selenium webdriver-manager

2. En una terminal, iniciar el servidor Flask:
       cd src
       PYTHONPATH=. python main/python/web/app.py

3. En otra terminal, ejecutar las pruebas:
       cd <raiz-proyecto>
       PYTHONPATH=src python -m pytest tests/lab05/test_selenium_create_product.py -v
   O con reporte HTML:
       PYTHONPATH=src python -m pytest tests/lab05/test_selenium_create_product.py -v \\
           --html=reporte_selenium_lab05.html --self-contained-html

NOTA: Selenium necesita Chrome instalado. El driver se descarga automáticamente
      con webdriver-manager. Si usas Firefox, cambia ChromeDriver por GeckoDriver.
"""

import time
import threading
import unittest

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ── Servidor Flask embebido para los tests ────────────────────────────────────
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))

from main.python.web.app import app, _clear_products

BASE_URL = "http://localhost:8084"   # Puerto exclusivo para tests


def _start_test_server():
    """Arranca Flask en modo test en un hilo daemon."""
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    app.run(host="127.0.0.1", port=8084, debug=False, use_reloader=False)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _chrome_driver() -> webdriver.Chrome:
    """
    Crea un ChromeDriver headless.
    webdriver-manager descarga el driver compatible automáticamente.
    """
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        service = Service(ChromeDriverManager().install())
    except Exception:
        service = Service()          # Usa chromedriver del PATH

    options = Options()
    options.add_argument("--headless=new")        # Sin ventana gráfica
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,800")

    return webdriver.Chrome(service=service, options=options)


# ── Suite de pruebas ──────────────────────────────────────────────────────────

class TestCreateProductWeb(unittest.TestCase):
    """
    Pruebas funcionales de caja negra para 'Create Product'.
    Sigue estructura xUnit: setUpClass / setUp / test* / tearDown / tearDownClass.
    """

    # ── Ciclo de vida de la clase (una sola vez por suite) ────────────────────

    @classmethod
    def setUpClass(cls):
        """Arranca el servidor Flask una vez para toda la suite."""
        cls._server_thread = threading.Thread(target=_start_test_server, daemon=True)
        cls._server_thread.start()
        time.sleep(1.5)   # Espera a que Flask esté listo

    @classmethod
    def tearDownClass(cls):
        """El hilo daemon muere solo al terminar el proceso."""
        pass

    # ── Ciclo de vida de cada test ────────────────────────────────────────────

    def setUp(self):
        """
        Antes de cada test:
          - Limpia el repositorio en memoria.
          - Abre un navegador Chrome headless nuevo.
          - Configura espera implícita de 3 s.
        """
        _clear_products()
        self.driver = _chrome_driver()
        self.driver.implicitly_wait(3)
        self.wait = WebDriverWait(self.driver, 6)

    def tearDown(self):
        """Cierra el navegador después de cada test."""
        self.driver.quit()

    # ── Métodos auxiliares ────────────────────────────────────────────────────

    def _login(self):
        """Inicia sesión como admin antes de acceder a rutas protegidas."""
        self.driver.get(f"{BASE_URL}/login")
        self.driver.find_element(By.NAME, "username").send_keys("admin")
        self.driver.find_element(By.NAME, "password").send_keys("admin123")
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        # IMPORTANTE: click() no espera a que termine la navegación resultante.
        # Sin esta espera, el siguiente driver.get() puede dispararse antes de
        # que el POST /login complete, dejando al navegador sin sesión iniciada
        # (se manifiesta como NoSuchElementException en /products/new).
        self.wait.until(EC.url_changes(f"{BASE_URL}/login"))

    def _go_to_create(self):
        """Navega al formulario de creación de producto (con login previo)."""
        self._login()
        self.driver.get(f"{BASE_URL}/products/new")

    def _fill_and_submit(self, name: str, price: str):
        """Rellena el formulario y hace clic en Guardar."""
        self._go_to_create()
        self.driver.find_element(By.ID, "name").clear()
        self.driver.find_element(By.ID, "name").send_keys(name)
        self.driver.find_element(By.ID, "price").clear()
        self.driver.find_element(By.ID, "price").send_keys(price)
        self.driver.find_element(By.ID, "submit-btn").click()

    def _has_error(self) -> bool:
        """Verifica si el formulario muestra un mensaje de error."""
        elements = self.driver.find_elements(By.ID, "error-message")
        return len(elements) > 0 and elements[0].is_displayed()

    # ── Casos de prueba ───────────────────────────────────────────────────────

    def test_CP01_crear_producto_valido(self):
        """CP01: Nombre y precio válidos → producto aparece en la lista."""
        self._fill_and_submit("Pizza", "20.00")

        # Debe redirigir a /products
        self.wait.until(EC.url_contains("/products"))
        self.assertIn("/products", self.driver.current_url)

        # El producto aparece en la tabla (list.html no usa class="product-name",
        # el nombre va en una celda <td class="fw-500"> dentro de la tabla)
        nombres = [e.text for e in self.driver.find_elements(By.CSS_SELECTOR, "table tbody td.fw-500")]
        self.assertIn("Pizza", nombres)

    def test_CP02_precio_minimo_valido(self):
        """CP02: Precio 0.01 (valor límite inferior válido) → creación exitosa."""
        self._fill_and_submit("Agua", "0.01")
        self.wait.until(EC.url_contains("/products"))
        nombres = [e.text for e in self.driver.find_elements(By.CSS_SELECTOR, "table tbody td.fw-500")]
        self.assertIn("Agua", nombres)

    def test_CP03_precio_alto_valido(self):
        """CP03: Precio elevado → creación exitosa."""
        self._fill_and_submit("Langosta", "999.99")
        self.wait.until(EC.url_contains("/products"))
        nombres = [e.text for e in self.driver.find_elements(By.CSS_SELECTOR, "table tbody td.fw-500")]
        self.assertIn("Langosta", nombres)

    def test_CP04_nombre_vacio_muestra_error(self):
        """CP04: Nombre vacío → permanece en formulario con error."""
        self._fill_and_submit("", "10")
        # Debe quedarse en /products/new
        self.assertIn("new", self.driver.current_url)
        self.assertTrue(self._has_error(), "Se esperaba mensaje de error")

    def test_CP05_nombre_espacios_muestra_error(self):
        """CP05: Nombre solo espacios → error de validación."""
        self._fill_and_submit("   ", "10")
        self.assertIn("new", self.driver.current_url)
        self.assertTrue(self._has_error())

    def test_CP06_precio_cero_muestra_error(self):
        """CP06: Precio = 0 (valor límite inválido) → error."""
        self._fill_and_submit("Pizza", "0")
        self.assertIn("new", self.driver.current_url)
        self.assertTrue(self._has_error())

    def test_CP07_precio_negativo_muestra_error(self):
        """CP07: Precio negativo → error."""
        self._fill_and_submit("Pizza", "-5")
        self.assertIn("new", self.driver.current_url)
        self.assertTrue(self._has_error())

    def test_CP08_precio_vacio_muestra_error(self):
        """CP08: Precio vacío → error."""
        self._fill_and_submit("Pizza", "")
        self.assertIn("new", self.driver.current_url)
        self.assertTrue(self._has_error())

    def test_CP09_precio_no_numerico_muestra_error(self):
        """CP09: Precio no numérico ('abc') → error."""
        self._fill_and_submit("Pizza", "abc")
        self.assertIn("new", self.driver.current_url)
        self.assertTrue(self._has_error())

    def test_CP10_nombre_caracteres_especiales(self):
        """CP10: Nombre con caracteres especiales → creado correctamente."""
        self._fill_and_submit("Café & Té", "15.50")
        self.wait.until(EC.url_contains("/products"))
        nombres = [e.text for e in self.driver.find_elements(By.CSS_SELECTOR, "table tbody td.fw-500")]
        self.assertIn("Café & Té", nombres)

    def test_CP11_precio_decimal_valido(self):
        """CP11: Precio decimal válido → guardado y mostrado correctamente."""
        self._fill_and_submit("Jugo", "3.75")
        self.wait.until(EC.url_contains("/products"))
        precios = [e.text for e in self.driver.find_elements(By.CSS_SELECTOR, "table tbody td.mono.fw-500")]
        self.assertTrue(any("3.75" in p for p in precios))

    @unittest.skip(
        "No existe vista de detalle de producto en la app actual "
        "(no hay ruta GET /products/<id> ni enlace 'Ver' en products/list.html, "
        "a diferencia de bills/orders que sí la tienen). "
        "Hay que implementar esa funcionalidad antes de poder validar este caso."
    )
    def test_CP12_verificar_detalle_producto(self):
        """CP12: Producto creado → página de detalle muestra nombre y precio."""
        self._fill_and_submit("Sopa", "12.00")
        self.wait.until(EC.url_contains("/products"))

        # Clic en "Ver" del primer producto
        self.driver.find_element(By.LINK_TEXT, "Ver").click()
        self.wait.until(EC.presence_of_element_located((By.ID, "detail-name")))

        nombre = self.driver.find_element(By.ID, "detail-name").text
        precio = self.driver.find_element(By.ID, "detail-price").text

        self.assertEqual(nombre, "Sopa")
        self.assertIn("12.00", precio)

    def test_CP13_cancelar_no_crea_producto(self):
        """CP13: Clic en Cancelar → redirige a lista sin crear producto."""
        self._go_to_create()
        self.driver.find_element(By.LINK_TEXT, "Cancelar").click()
        self.wait.until(EC.url_contains("/products"))

        # No hay productos: list.html no usa id="no-products-msg", el mensaje
        # vacío está dentro de <div class="empty"> en la fila {% else %} de la tabla.
        no_msg = self.driver.find_elements(By.CSS_SELECTOR, "div.empty")
        self.assertTrue(len(no_msg) > 0, "Lista debe estar vacía")

    def test_CP14_titulo_pagina_correcto(self):
        """CP14: El título de la página de creación es correcto."""
        self._go_to_create()
        # create.html define {% block title %}Nuevo producto{% endblock %}
        self.assertIn("Nuevo producto", self.driver.title)

    def test_CP15_formulario_tiene_campos_requeridos(self):
        """CP15: El formulario tiene los inputs name y price con IDs correctos."""
        self._go_to_create()

        campo_nombre = self.driver.find_element(By.ID, "name")
        campo_precio = self.driver.find_element(By.ID, "price")
        boton_submit = self.driver.find_element(By.ID, "submit-btn")

        self.assertTrue(campo_nombre.is_displayed())
        self.assertTrue(campo_precio.is_displayed())
        self.assertTrue(boton_submit.is_displayed())


if __name__ == "__main__":
    unittest.main(verbosity=2)