from open_page import open_page
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import csv
import os
import sys
import json
from datetime import datetime

# Función extract_html eliminada
        
def extract_table_data(driver, wait_time=30):
    """
    Extrae datos de la tabla de la página SLIR después de que cargue dinámicamente
    
    Args:
        driver: Instancia del navegador Selenium
        wait_time: Tiempo máximo de espera para la carga de la tabla en segundos
        
    Returns:
        dict: Diccionario con los datos extraídos de la tabla y headers
    """
    try:
        print("Esperamos a que la tabla cargue ...")
        
        # Esperar a que desaparezca el spinner de carga si existe
        try:
            spinner_selector = ".spinner-container, .p-progress-spinner"
            spinner = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, spinner_selector))
            )
            print("Spinner de carga detectado...")
            WebDriverWait(driver, wait_time).until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, spinner_selector))
            )
        except TimeoutException:
            # Si no se encuentra el spinner o ya ha desaparecido, continuamos
            pass
        
        # Esperar a que aparezca la tabla o filas de la tabla
        print("Esperando a la tabla...")
        WebDriverWait(driver, wait_time).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr, tr td"))
        )
        
        
        # Extraer solo datos de la tabla
        table_data = extract_table_rows(driver)
        
        result = {
            "project_info": {},  # Proyecto info vacío ya que se eliminó esa función
            "table_data": table_data
        }
        
        print(f"Datos de la tabla conseguidos: {len(table_data)} filas ")
        return result
        
    except TimeoutException as e:
        print(f"Timeout esperando a que la tabla cargue: {e}")
        return None
    except NoSuchElementException as e:
        print(f"No se encontró el elemento en la página: {e}")
        return None
    except Exception as e:
        print(f"Error al extraer datos de la tabla: {e}")
        return None

# Función extract_project_info eliminada

def extract_table_rows(driver):
    """Extrae todas las filas de la tabla principal"""
    table_data = []
    
    try:
        # Identificar las filas de la tabla (intenta con diferentes selectores)
        selectors = [
            "table tbody tr",
            "tr[role='row']",
            ".p-datatable-tbody tr",
            "div[role='grid'] div[role='row']"
        ]
        
        rows = None
        for selector in selectors:
            try:
                rows = driver.find_elements(By.CSS_SELECTOR, selector)
                if rows and len(rows) > 0:
                    print(f"Filas encontradas con selector: {selector}")
                    break
            except:
                continue
        
        if not rows or len(rows) == 0:
            print("No se encontraron filas en la tabla.")
            return table_data
        
        print(f"Encontradas {len(rows)} filas en la tabla.")
        
        # Obtener encabezados de columna si están disponibles
        headers = []
        try:
            header_elements = driver.find_elements(By.CSS_SELECTOR, "th, [role='columnheader']")
            for header in header_elements:
                header_text = header.text.strip()
                if header_text:  # Solo añadir si no está vacío
                    headers.append(header_text)
        except:
            headers = []  # Si falla, dejamos la lista vacía
        
        # Extraer datos de cada fila
        for row in rows:
            row_data = {}
            
            # Si tenemos encabezados, los usamos como claves
            if headers:
                cells = row.find_elements(By.CSS_SELECTOR, "td, [role='cell']")
                for i, cell in enumerate(cells):
                    if i < len(headers):
                        row_data[headers[i]] = cell.text.strip()
                    else:
                        row_data[f"column_{i}"] = cell.text.strip()
            else:
                # Si no tenemos encabezados, usamos índices
                cells = row.find_elements(By.CSS_SELECTOR, "td, [role='cell']")
                for i, cell in enumerate(cells):
                    row_data[f"column_{i}"] = cell.text.strip()
            
            # Solo añadir la fila si tiene datos
            if any(row_data.values()):
                table_data.append(row_data)
    
    except Exception as e:
        print(f"Error al extraer filas de la tabla: {e}")
    
    return table_data

def process_slir_code(code):
    """
    Procesa un código SLIR específico
    
    Args:
        code (str): Código SLIR para procesar (ejemplo: SLIR1ST230476)
        
    Returns:
        dict: Datos extraídos o None si falla
    """
    try:
        # Abrir la página con el código proporcionado
        driver, tiempo_carga = open_page()
        
        if not driver:
            print(f"No se pudo abrir la página para el código: {code}")
            return None
        
        # Detectar si estamos en un entorno PyInstaller
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            # Estamos en el ejecutable - usar rutas relativas al ejecutable
            base_path = os.path.dirname(sys.executable)
            output_dir = os.path.join(base_path, "output")
        else:
            # Estamos en el script normal
            output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
            
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Ya no guardamos el HTML
        html_filename = None
        
        # Detectar el número total de páginas
        total_pages = get_total_pages(driver)
        if total_pages:
            print(f"Número total de páginas detectado: {total_pages}")
        else:
            print("No se pudo detectar el número total de páginas, se procesarán todas las disponibles")
            
        # Extraer datos de la tabla dinámica de la primera página
        print("Extrayendo datos de la tabla dinámica (página 1)...")
        all_table_data = extract_table_data(driver)
        
        if not all_table_data:
            print(f"No se pudieron extraer datos de la tabla para el código: {code}")
            return {
                "code": code,
                "extraction_time": timestamp,
                "success": False,
                "message": "No se pudieron extraer datos de la tabla"
            }
        
        # Solo necesitamos los datos de la tabla
        all_rows = all_table_data.get("table_data", [])
        
        # Procesar páginas adicionales si existen
        current_page = 1
        max_page = total_pages if total_pages else float('inf')  # Infinito si no se conoce el total
        
        while current_page < max_page:
            # Intentar hacer clic en el botón "Next Page"
            print(f"\nIntentando navegar a la página {current_page + 1}...")
            next_page_success = click_next_page(driver)
            
            if not next_page_success:
                print("No hay más páginas disponibles.")
                break
                
            # Si el clic fue exitoso, extraer datos de la nueva página
            current_page += 1
            print(f"Extrayendo datos de la tabla dinámica (página {current_page})...")
            
            # Extraer los datos de la nueva página
            page_data = extract_table_data(driver)
            
            if page_data and "table_data" in page_data and page_data["table_data"]:
                # Añadir las filas de esta página a la lista principal
                new_rows = page_data["table_data"]
                all_rows.extend(new_rows)
                print(f"Se añadieron {len(new_rows)} filas de la página {current_page}. Total: {len(all_rows)}")
            else:
                print(f"No se encontraron datos en la página {current_page}.")
                break
        
        # Actualizar el diccionario con todos los datos combinados
        combined_data = {
            "project_info": {},  # Ya no tenemos info del proyecto
            "table_data": all_rows,
            "pages_processed": current_page,
            "total_pages": total_pages if total_pages else current_page,
            "total_rows": len(all_rows)
        }
        
        # Guardar los datos combinados en formato JSON
        json_filename = os.path.join(output_dir, f"slir_{code}_{timestamp}_data.json")
        with open(json_filename, "w", encoding="utf-8") as f:
            json.dump(combined_data, f, ensure_ascii=False, indent=2)
        
        print(f"Datos combinados guardados en: {json_filename}")
        
        # Guardar datos combinados en formato CSV
        csv_filename = os.path.join(output_dir, f"slir_{code}_{timestamp}_data.csv")
        save_to_csv(combined_data, csv_filename)
        
        print(f"Datos combinados guardados en CSV: {csv_filename}")
        
        return {
            "code": code,
            "json_file": json_filename,
            "csv_file": csv_filename,
            "extraction_time": timestamp,
            "pages_processed": current_page,
            "data": combined_data,
            "success": True
        }
    
    except Exception as e:
        print(f"Error en process_slir_code: {e}")
        return None
    
    finally:
        # No cerramos el driver automáticamente para permitir revisar la página
        print("Dejamos el navegador abierto.")
        # Descomentar las siguientes líneas cuando se quiera volver a cerrar automáticamente
        # if 'driver' in locals() and driver:
        #     try:
        #         driver.quit()
        #         print("Navegador cerrado correctamente.")
        #     except:
        #         pass

def get_total_pages(driver, wait_time=5):
    """
    Obtiene el número total de páginas disponibles al cargar la página
    
    Args:
        driver: WebDriver de Selenium
        wait_time: Tiempo máximo de espera en segundos
        
    Returns:
        int: Número total de páginas o None si no se puede determinar
    """
    try:
        print("Detectando número total de páginas...")
        
        # Esperar a que el paginador cargue
        WebDriverWait(driver, wait_time).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "span.p-paginator-pages, .p-paginator"))
        )
        
        # Método 1: Buscar botones de página con aria-label
        page_buttons = driver.find_elements(By.CSS_SELECTOR, "button[aria-label]")
        page_numbers = []
        
        for button in page_buttons:
            aria_label = button.get_attribute("aria-label")
            if aria_label and aria_label.isdigit():
                page_numbers.append(int(aria_label))
        
        if page_numbers:
            total = max(page_numbers)
            print(f"Total de páginas detectado: {total}")
            return total
            
       
        
    except Exception as e:
        print(f"Error al detectar el número de páginas: {e}")
        return None

def click_next_page(driver, wait_time=5):
    """
    Hace clic en el botón 'Next Page' para avanzar a la siguiente página de resultados
    utilizando JavaScript (más confiable para este caso)
    
    Args:
        driver: WebDriver de Selenium
        wait_time: Tiempo máximo de espera en segundos
        
    Returns:
        bool: True si el clic fue exitoso, False en caso contrario
    """
    try:
        print("Buscando el botón 'Next Page'...")
        
        # Verificar primero si el botón está deshabilitado (última página)
        disabled_buttons = driver.find_elements(By.CSS_SELECTOR, 
            "button.p-paginator-next.p-disabled, button.p-paginator-next[disabled]")
        
        if disabled_buttons and len(disabled_buttons) > 0:
            print("El botón 'Next Page' está deshabilitado. No se puede avanzar más.")
            return False
            
        # Buscar el botón Next Page
        next_button = WebDriverWait(driver, wait_time).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "button.p-paginator-next"))
        )
        
        # Comprobar explícitamente si está deshabilitado
        is_disabled = next_button.get_attribute("disabled") == "true" or "p-disabled" in next_button.get_attribute("class")
        if is_disabled:
            print("El botón 'Next Page' está deshabilitado. No se puede avanzar más.")
            return False
        
        # Hacer scroll hasta el botón para asegurarnos de que es visible
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
        time.sleep(0.5)
        
        # Hacer clic usando JavaScript (más confiable)
        print("Haciendo clic en el botón 'Next Page'")
        driver.execute_script("arguments[0].click();", next_button)
        
        # Esperar a que la página se actualice
        try:
            # Esperar a que aparezca el spinner si existe
            spinner_selector = ".spinner-container, .p-progress-spinner"
            WebDriverWait(driver, 2).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, spinner_selector))
            )
            # Esperar a que desaparezca
            WebDriverWait(driver, wait_time).until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, spinner_selector))
            )
        except TimeoutException:
            # Si no hay spinner, esperamos un momento
            time.sleep(1)
        
        print("✓ Clic realizado con JavaScript")
        return True
        
    except Exception as e:
        print(f"Error al hacer clic en el botón Next Page: {e}")
        return False

def save_to_csv(table_data, csv_filename):
    """
    Guarda los datos de la tabla en un archivo CSV
    
    Args:
        table_data (dict): Diccionario con los datos de la tabla
        csv_filename (str): Ruta del archivo CSV a crear
    """
    try:
        # Comprobar si tenemos datos de tabla
        if not table_data or 'table_data' not in table_data or not table_data['table_data']:
            print("No hay datos de tabla para guardar en CSV")
            return
        
        rows = table_data['table_data']
        
        # Si hay al menos una fila, extraer las claves como encabezados
        if rows:
            headers = rows[0].keys()
            
            with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=headers)
                writer.writeheader()
                writer.writerows(rows)
                
            print(f"CSV creado exitosamente con {len(rows)} filas")
        else:
            print("No se encontraron filas para guardar en CSV")
            
    except Exception as e:
        print(f"Error al guardar CSV: {e}")

if __name__ == "__main__":
    # Código de prueba para un solo SLIR
    test_code = "SLIR1ST230476"
    print(f"Procesando código SLIR de prueba: {test_code}")
    
    result = process_slir_code(test_code)
    
    if result and result.get("success", False):
        print(f"\nProcesamiento exitoso.")
        print(f"- JSON guardado en: {result['json_file']}")
        print(f"- CSV guardado en: {result['csv_file']}")
        print(f"- Filas extraídas: {result['data']['total_rows']}")
        print(f"- Páginas procesadas: {result['pages_processed']}")
    else:
        print(f"No se pudo procesar el código: {test_code}")
