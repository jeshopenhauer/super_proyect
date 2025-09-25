from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import subprocess
import datetime

# Constantes globales
EDGE_USER_DATA_DIR = "C:\\Users\\jmoralar\\AppData\\Local\\Microsoft\\Edge\\User Data"
PROFILE_DIRECTORY = "Default"
PAGE_URL = "https://str.apps.valeo.com/slir/single-slir?code=SLIR1ST230476"

def cerrar_procesos_edge():
    """Cierra procesos de Edge en ejecución usando taskkill"""
    try:
        # Luego cierra los procesos de Edge
        resultado = subprocess.run(["taskkill", "/F", "/IM", "msedge.exe"], 
                                  capture_output=True, text=True)
        
        print("Procesos de Edge cerrados")
        
        return True
    except Exception as e:
        print(f"Error al intentar cerrar Edge: {e}")
        return False
    

def open_page(cerrar_previo=True, mantener_abierto=True):
    """
    Abre Edge con el perfil del usuario y navega a la URL
    
    Args:
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
        edge_options.add_argument(f"--profile-directory={PROFILE_DIRECTORY}")
        edge_options.add_argument("--start-maximized")

        # Evitar detección de automatización
        edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        edge_options.add_experimental_option("useAutomationExtension", False)


        # Añade estas opciones para mejorar el rendimiento
        edge_options.add_argument("--disable-extensions")
        edge_options.add_argument("--disable-gpu")
        edge_options.add_argument("--disable-dev-shm-usage")
        edge_options.add_argument("--no-sandbox")
        edge_options.add_argument("--disable-features=TranslateUI")
        edge_options.add_argument("--disable-blink-features=AutomationControlled")


        # # Desactivar imágenes y otros recursos para cargar más rápido
        # prefs = {
        # "profile.default_content_setting_values": {
        # "images": 2,  # No cargar imágenes
        # "plugins": 2,  # No cargar plugins
        # "popups": 2,  # Bloquear popups
        # "geolocation": 2,  # No compartir ubicación
        # "notifications": 2  # Bloquear notificaciones
        # },
        # "profile.managed_default_content_settings": {"javascript": 1}  # Permitir JavaScript
        # }
        # edge_options.add_experimental_option("prefs", prefs)

        if mantener_abierto:
            edge_options.add_experimental_option("detach", True)

        # Si se solicita, cerrar cualquier instancia de Edge existente
        if cerrar_previo:
            cerrar_procesos_edge()
            
        print("Abriendo Edge...")
            
        try:
            driver = webdriver.Edge(options=edge_options)
        except Exception as e:
            if "user data directory is already in use" in str(e) or "crashed" in str(e):
                print("El perfil de usuario está en uso. Intentando cerrar instancias de Edge...")
                if cerrar_procesos_edge():
                    print("Intentando abrir Edge nuevamente después de cerrar procesos...")
                    time.sleep(0.5)
                    driver = webdriver.Edge(options=edge_options)
                else:
                    print("No se pudo liberar el perfil de usuario.")
                    return None
            else:
                print(f"Error al iniciar Edge: {e}")
                return None

        # Navegar a la URL definida globalmente
        driver.get(PAGE_URL)
        
        # Calcular tiempo de carga
        tiempo_fin_navegador = datetime.datetime.now()
        tiempo_carga_navegador = (tiempo_fin_navegador - tiempo_inicio_navegador).total_seconds()

        print(f"Ya estamos en: {PAGE_URL}")
        print(f"Tiempo de carga del navegador: {tiempo_carga_navegador:.2f} segundos")
        
        return driver, tiempo_carga_navegador

    except Exception as e:
        print(f"Error durante la automatización: {e}")
        return None, 0

# Ejemplo de uso si este script se ejecuta directamente
if __name__ == "__main__":
    print("Iniciando proceso de apertura de la pagina...")
    tiempo_inicio_total = datetime.datetime.now()

    driver, tiempo_carga = open_page()

    tiempo_fin_total = datetime.datetime.now()
    tiempo_total_proceso = (tiempo_fin_total - tiempo_inicio_total).total_seconds()
    
    if driver:
        
        print(f"- Tiempo total del proceso: {tiempo_total_proceso:.2f} segundos")
        