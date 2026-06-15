"""
==============================================================
Laboratorio 05 - Pruebas Funcionales
Docente : DSc. Edgar Sarmiento Calisaya
Curso   : Ingeniería de Software II
Alumno  : [Tu nombre]
==============================================================

Objeto de Prueba : Funcionalidad "Create Product"
Estrategia       : Clases de Equivalencia + Valores Límite

TABLA DE CASOS DE PRUEBA
========================
| ID  | Objeto / Funcionalidad | Escenario / Acciones                          | Valores de Prueba               | Resultado Esperado                          |
|-----|------------------------|-----------------------------------------------|---------------------------------|---------------------------------------------|
| CP01| Create Product         | Crear producto con nombre y precio válidos    | name="Pizza", price=20.0        | Producto creado; name="Pizza", price=20.0   |
| CP02| Create Product         | Crear producto con precio de 1 centavo (mín.) | name="Agua", price=0.01         | Producto creado correctamente               |
| CP03| Create Product         | Crear producto con precio muy alto            | name="Langosta", price=9999.99  | Producto creado correctamente               |
| CP04| Create Product         | Crear producto con nombre largo (frontera)    | name="A"*100, price=10          | Producto creado correctamente               |
| CP05| Create Product         | Nombre vacío → clase inválida                 | name="", price=10               | ValueError: "Product name cannot be empty"  |
| CP06| Create Product         | Nombre solo espacios → clase inválida         | name="   ", price=10            | ValueError: "Product name cannot be empty"  |
| CP07| Create Product         | Nombre None → clase inválida                  | name=None, price=10             | ValueError: "Product name cannot be empty"  |
| CP08| Create Product         | Precio cero → valor límite inválido           | name="Pizza", price=0           | ValueError: "Product price must be positive"|
| CP09| Create Product         | Precio negativo → clase inválida              | name="Pizza", price=-5          | ValueError: "Product price must be positive"|
| CP10| Create Product         | Precio None → clase inválida                  | name="Pizza", price=None        | ValueError: "Product price must be positive"|
| CP11| Create Product         | Nombre con caracteres especiales              | name="Café & Té", price=15.5    | Producto creado correctamente               |
| CP12| Create Product         | Precio decimal válido                         | name="Jugo", price=3.75         | Producto creado; price=3.75                 |
| CP13| Create Product         | Precio muy cercano a cero (frontera positiva) | name="Caramelo", price=0.001    | Producto creado correctamente               |
| CP14| Create Product         | Nombre con solo un carácter                   | name="X", price=5               | Producto creado correctamente               |
| CP15| Create Product         | Precio exactamente igual al máximo conocido   | name="Joya", price=50           | Producto creado; price=50.0                 |
"""

import unittest
from main.python.domain.entities.product import Product


class TestCreateProduct(unittest.TestCase):
    """
    Suite de pruebas funcionales para la funcionalidad 'Create Product'.
    Utiliza Clases de Equivalencia y Valores Límite (caja negra).
    Sigue la estructura xUnit: setUp, @Test, tearDown.
    """

    # ------------------------------------------------------------------ #
    # SetUp / TearDown  (equivalente @BeforeEach / @AfterEach en JUnit)   #
    # ------------------------------------------------------------------ #

    def setUp(self):
        """Inicialización antes de cada caso de prueba."""
        self.product = None

    def tearDown(self):
        """Limpieza después de cada caso de prueba."""
        self.product = None

    # ------------------------------------------------------------------ #
    # CP01 – CP04: Clase válida                                            #
    # ------------------------------------------------------------------ #

    def test_CP01_crear_producto_valido(self):
        """CP01: Nombre y precio válidos → producto creado correctamente."""
        self.product = Product("Pizza", 20.0)
        self.assertEqual(self.product.name, "Pizza")
        self.assertEqual(self.product.price, 20.0)

    def test_CP02_precio_minimo_valido(self):
        """CP02: Precio en valor límite inferior válido (0.01)."""
        self.product = Product("Agua", 0.01)
        self.assertEqual(self.product.name, "Agua")
        self.assertAlmostEqual(self.product.price, 0.01)

    def test_CP03_precio_muy_alto(self):
        """CP03: Precio elevado → sigue siendo válido."""
        self.product = Product("Langosta", 9999.99)
        self.assertEqual(self.product.name, "Langosta")
        self.assertAlmostEqual(self.product.price, 9999.99)

    def test_CP04_nombre_largo(self):
        """CP04: Nombre largo de 100 caracteres → válido."""
        nombre_largo = "A" * 100
        self.product = Product(nombre_largo, 10)
        self.assertEqual(len(self.product.name), 100)
        self.assertEqual(self.product.price, 10)

    # ------------------------------------------------------------------ #
    # CP05 – CP07: Clase inválida – nombre                                 #
    # ------------------------------------------------------------------ #

    def test_CP05_nombre_vacio(self):
        """CP05: Nombre vacío → ValueError."""
        with self.assertRaises(ValueError) as ctx:
            Product("", 10)
        self.assertIn("empty", str(ctx.exception).lower())

    def test_CP06_nombre_solo_espacios(self):
        """CP06: Nombre con solo espacios → ValueError."""
        with self.assertRaises(ValueError) as ctx:
            Product("   ", 10)
        self.assertIn("empty", str(ctx.exception).lower())

    def test_CP07_nombre_none(self):
        """CP07: Nombre None → ValueError."""
        with self.assertRaises(ValueError) as ctx:
            Product(None, 10)
        self.assertIn("empty", str(ctx.exception).lower())

    # ------------------------------------------------------------------ #
    # CP08 – CP10: Clase inválida – precio                                 #
    # ------------------------------------------------------------------ #

    def test_CP08_precio_cero(self):
        """CP08: Precio = 0 (valor límite inválido) → ValueError."""
        with self.assertRaises(ValueError) as ctx:
            Product("Pizza", 0)
        self.assertIn("positive", str(ctx.exception).lower())

    def test_CP09_precio_negativo(self):
        """CP09: Precio negativo → ValueError."""
        with self.assertRaises(ValueError) as ctx:
            Product("Pizza", -5)
        self.assertIn("positive", str(ctx.exception).lower())

    def test_CP10_precio_none(self):
        """CP10: Precio None → ValueError."""
        with self.assertRaises(ValueError) as ctx:
            Product("Pizza", None)
        self.assertIn("positive", str(ctx.exception).lower())

    # ------------------------------------------------------------------ #
    # CP11 – CP15: Casos adicionales / frontera                            #
    # ------------------------------------------------------------------ #

    def test_CP11_nombre_con_caracteres_especiales(self):
        """CP11: Nombre con caracteres especiales → válido."""
        self.product = Product("Café & Té", 15.5)
        self.assertEqual(self.product.name, "Café & Té")
        self.assertAlmostEqual(self.product.price, 15.5)

    def test_CP12_precio_decimal_valido(self):
        """CP12: Precio decimal → creado y almacenado correctamente."""
        self.product = Product("Jugo", 3.75)
        self.assertAlmostEqual(self.product.price, 3.75)

    def test_CP13_precio_frontera_positiva(self):
        """CP13: Precio muy cercano a cero pero positivo → válido."""
        self.product = Product("Caramelo", 0.001)
        self.assertGreater(self.product.price, 0)

    def test_CP14_nombre_un_caracter(self):
        """CP14: Nombre de un solo carácter → válido."""
        self.product = Product("X", 5)
        self.assertEqual(self.product.name, "X")

    def test_CP15_precio_entero_redondo(self):
        """CP15: Precio entero exacto → almacenado como número."""
        self.product = Product("Joya", 50)
        self.assertEqual(self.product.price, 50)


if __name__ == "__main__":
    unittest.main(verbosity=2)
