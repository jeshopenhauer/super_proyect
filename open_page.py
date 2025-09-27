from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import subprocess
import datetime

# Constantes globales
# Usar una ruta independiente del usuario
EDGE_USER_DATA_DIR = os.path.join(os.environ.get('LOCALAPPDATA', ''), "Microsoft", "Edge", "User Data")
# URL base para la plataforma SLIR
BASE_URL = "https://str.apps.valeo.com/slir/single-slir"

def cerrar_procesos_edge():
    """Cierra procesos de Edge en ejecución usando taskkill"""
    try:
        resultado = subprocess.run(["taskkill", "/F", "/IM", "msedge.exe"], 
                                   stdout=subprocess.DEVNULL, 
                                   stderr=subprocess.DEVNULL)        
        print("Procesos de Edge cerrados")
        
        return True
    except Exception as e:
        print(f"Error al intentar cerrar Edge: {e}")
        return False
        
def manejar_login(driver):
    """
    Detecta y maneja la pantalla de login si está presente
    
    Args:
        driver: Instancia del navegador Edge
        
    Returns:
        bool: True si se detectó y manejó el login, False en caso contrario
    """
    try:
        print("Verificando si se requiere inicio de sesión...")
        # Esperar un poco para que la página cargue completamente
        time.sleep(2)
        
        # Intentar varias estrategias para encontrar el botón de login
        login_button = None
        
        # 1. Buscar por texto exacto y clase
        try:
            login_button = driver.find_element(By.XPATH, "//button[contains(@class, 'p-button') and normalize-space(.)='Login']")
        except Exception:
            pass
            
        # 2. Buscar por clase específica
        if not login_button:
            try:
                login_button = driver.find_element(By.CSS_SELECTOR, "button.p-button.p-button-secondary")
            except Exception:
                pass
                
        # 3. Buscar por atributo _ngcontent y clase
        if not login_button:
            try:
                login_button = driver.find_element(By.CSS_SELECTOR, "button[_ngcontent-ng-c][class*='p-button'][class*='p-component']")
            except Exception:
                pass
        
        if login_button:
            print("Pantalla de login detectada. Intentando iniciar sesión automáticamente...")
            # Hacer clic en el botón de login
            driver.execute_script("arguments[0].click();", login_button)
            print("Se hizo clic en el botón de login")
            
            # Esperar a que se complete el proceso de login
            time.sleep(3)
            return True
        else:
            print("No se detectó pantalla de login, continuando...")
            return False
            
    except Exception as e:
        print(f"Error al intentar manejar el login: {e}")
        return False
    

def open_page(slir_code, cerrar_previo=True, mantener_abierto=True):
    """
    Abre Edge con el perfil del usuario y navega a la URL con el código SLIR proporcionado

    Args:
        slir_code (str): Código SLIR (ej: "SLIR1ST230476")
        cerrar_previo (bool): Si True, cierra cualquier instancia de Edge antes de abrir una nueva
        mantener_abierto (bool): Si True, mantiene el navegador abierto con detach=True

    Returns:
        tuple: (webdriver.Edge, float) - Instancia del navegador Edge y tiempo de carga en segundos,
               o (None, 0) si falla.
    """
    # Iniciar cronómetro de apertura del navegador
    tiempo_inicio_navegador = datetime.datetime.now()
    try:
        # Configurar opciones para Edge
        edge_options = Options()
        edge_options.add_argument(f"--user-data-dir={EDGE_USER_DATA_DIR}")
        

        # Evitar detección de automatización
        edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
       

        if mantener_abierto:
            edge_options.add_experimental_option("detach", True)

        # Si se solicita, cerrar cualquier instancia de Edge existente
        if cerrar_previo:
            cerrar_procesos_edge()

        print("Abriendo Edge...")

        try:
            # Configurar el servicio de Edge para redirigir logs
            log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs", "edge_driver.log")
            edge_service = EdgeService(log_output=log_path)
            
            # Opciones adicionales para silenciar mensajes
            edge_options.add_argument("--disable-logging")
            edge_options.add_argument("--log-level=3")  # FATAL = 3
            edge_options.add_argument("--silent")
            
            
            driver = webdriver.Edge(options=edge_options, service=edge_service)
        except Exception as e:
            if "user data directory is already in use" in str(e) or "crashed" in str(e):
                print("El perfil de usuario está en uso. Intentando cerrar instancias de Edge...")
                if cerrar_procesos_edge():
                    print("Intentando abrir Edge nuevamente después de cerrar procesos...")
                    time.sleep(0.5)
                    driver = webdriver.Edge(options=edge_options, service=edge_service)
                else:
                    print("No se pudo liberar el perfil de usuario.")
                    return None
            else:
                print(f"Error al iniciar Edge: {e}")
                return None

        # Construir la URL completa con el código SLIR y navegar a ella
        full_url = f"{BASE_URL}?code={slir_code}"
        driver.get(full_url)

        # Calcular tiempo de carga
        tiempo_fin_navegador = datetime.datetime.now()
        tiempo_carga_navegador = (tiempo_fin_navegador - tiempo_inicio_navegador).total_seconds()

        print(f"Ya estamos en: {full_url}")
        print(f"Tiempo de carga del navegador: {tiempo_carga_navegador:.2f} segundos")

        # Utilizar la función específica para manejar el login
        try:
            manejar_login(driver)
        except Exception as e:
            print(f"Error al manejar login, pero continuamos: {e}")
            # No interrumpimos la ejecución por un error en el login

        return driver, tiempo_carga_navegador

    except Exception as e:
        print(f"Error durante la automatización: {e}")
        return None, 0













# Ejemplo de uso si este script se ejecuta directamente
if __name__ == "__main__":
    print("Iniciando proceso de apertura de la pagina...")
    tiempo_inicio_total = datetime.datetime.now()

    # Código SLIR a procesar
    slir_code = "SLIR1ST230476"
    driver, tiempo_carga = open_page(slir_code)

    tiempo_fin_total = datetime.datetime.now()
    tiempo_total_proceso = (tiempo_fin_total - tiempo_inicio_total).total_seconds()

    if driver:
        print(f"- Tiempo total del proceso: {tiempo_total_proceso:.2f} segundos")
