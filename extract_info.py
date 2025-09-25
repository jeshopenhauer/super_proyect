from open_page import open_page
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
import time
import csv
import os
import json
import datetime  # Importamos el módulo completo para usar datetime.datetime
from datetime import datetime as dt  # Alias para evitar conflictos

def extract_html(driver):
    """
    Extrae el HTML completo de la página actual
    
    Args:
        driver: Instancia del navegador Selenium
        
    Returns:
        str: HTML completo de la página o None si falla
    """
    try:
        # Esperar a que la página cargue completamente
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Extraer el HTML completo
        html_content = driver.page_source
        
        print(f"HTML conseguido ok. Tamaño: {len(html_content)} bytes")
        return html_content
    
    except Exception as e:
        print(f"Error al extraer HTML: {e}")
        return None
        
def extract_table_data(driver, wait_time=60):
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
            spinner = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, spinner_selector))
            )
            print("Spinner de carga detectado, esperando a que desaparezca...")
            WebDriverWait(driver, wait_time).until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, spinner_selector))
            )
        except TimeoutException:
            # Si no se encuentra el spinner o ya ha desaparecido, continuamos
            pass
        
        # Esperar a que aparezca la tabla o filas de la tabla
        print("Esperamos a que aparezca la tabla...")
        WebDriverWait(driver, wait_time).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr, tr td"))
        )
        
        # Esperamos un poco más para asegurar que todos los datos se han cargado
        time.sleep(2)
        
        # 1. Extraer información general del proyecto
        project_info = extract_project_info(driver)
        
        # 2. Extraer datos de la tabla
        table_data = extract_table_rows(driver)
        
        result = {
            "project_info": project_info,
            "table_data": table_data
        }
        
        print(f"Datos de la tabla extraídos exitosamente. {len(table_data)} filas encontradas.")
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

def extract_project_info(driver):
    """Extrae la información general del proyecto que aparece en la parte superior"""
    project_info = {}
    
    try:
        # Extraer código del proyecto
        project_code_elem = driver.find_element(By.CSS_SELECTOR, "div:contains('Project Code') + div, .project-code")
        project_info["project_code"] = project_code_elem.text.strip()
    except:
        project_info["project_code"] = "No encontrado"
    
    try:
        # Extraer nombre del proyecto
        project_name_elem = driver.find_element(By.CSS_SELECTOR, "div:contains('Project Name') + div, .project-name")
        project_info["project_name"] = project_name_elem.text.strip()
    except:
        project_info["project_name"] = "No encontrado"
    
    try:
        # Extraer tipo del proyecto
        project_type_elem = driver.find_element(By.CSS_SELECTOR, "div:contains('Project Type') + div, .project-type")
        project_info["project_type"] = project_type_elem.text.strip()
    except:
        project_info["project_type"] = "No encontrado"
    
    # Intentamos extraer más información si está disponible
    for field in ["Technical PRAC", "Launch Period", "Rol Launch", "Rol Request", "PRAC Last Update"]:
        try:
            field_elem = driver.find_element(By.XPATH, f"//div[contains(text(),'{field}')]/following-sibling::div[1]")
            project_info[field.lower().replace(" ", "_")] = field_elem.text.strip()
        except:
            project_info[field.lower().replace(" ", "_")] = "No encontrado"
    
    return project_info

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

def process_slir_code(code, max_pages=None):
    """
    Procesa un código SLIR específico
    
    Args:
        code (str): Código SLIR para procesar (ejemplo: SLIR1ST230476)
        max_pages (int, optional): Número máximo de páginas a procesar. None para todas.
        
    Returns:
        dict: Datos extraídos o None si falla
    """
    try:
        # Abrir la página con el código proporcionado
        driver, tiempo_carga = open_page()
        
        if not driver:
            print(f"No se pudo abrir la página para el código: {code}")
            return None
        
        # Extraer el HTML como prueba
        html_content = extract_html(driver)
        
        if not html_content:
            print(f"No se pudo extraer el HTML para el código: {code}")
            driver.quit()
            return None
        
        # Guardar el HTML en un archivo
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = dt.now().strftime("%Y%m%d_%H%M%S")
        html_filename = os.path.join(output_dir, f"slir_{code}_{timestamp}.html")
        
        with open(html_filename, "w", encoding="utf-8") as f:
            f.write(html_content)
            
        print(f"HTML guardado en: {html_filename}")
        
        # Extraer datos de la tabla dinámica de la primera página
        print("Extrayendo datos de la tabla dinámica (página 1)...")
        all_table_data = extract_table_data(driver)
        
        if not all_table_data:
            print(f"No se pudieron extraer datos de la tabla para el código: {code}")
            return {
                "code": code,
                "html_file": html_filename,
                "extraction_time": timestamp,
                "success": False,
                "message": "No se pudieron extraer datos de la tabla"
            }
        
        # Información del proyecto (se mantiene igual en todas las páginas)
        project_info = all_table_data.get("project_info", {})
        
        # Todos los datos de filas de todas las páginas
        all_rows = all_table_data.get("table_data", [])
        
        # Procesar páginas adicionales si se requiere
        current_page = 1
        while max_pages is None or current_page < max_pages:
            # Intentar hacer clic en el botón "Next Page"
            print(f"\nIntentando navegar a la página {current_page + 1}...")
            next_page_success = click_next_page(driver)
            
            if not next_page_success:
                print(f"No hay más páginas disponibles o no se pudo navegar a la siguiente página.")
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
            "project_info": project_info,
            "table_data": all_rows,
            "pages_processed": current_page
        }
        
        # Guardar los datos combinados en formato JSON
        json_filename = os.path.join(output_dir, f"slir_{code}_{timestamp}_data.json")
        with open(json_filename, "w", encoding="utf-8") as f:
            json.dump(combined_data, f, ensure_ascii=False, indent=2)
        
        print(f"\nDatos combinados guardados en: {json_filename}")
        
        # Guardar datos combinados en formato CSV
        csv_filename = os.path.join(output_dir, f"slir_{code}_{timestamp}_data.csv")
        save_to_csv(combined_data, csv_filename)
        
        print(f"Datos combinados guardados en CSV: {csv_filename}")
        
        return {
            "code": code,
            "html_file": html_filename,
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
        print("Navegador mantenido abierto para revisión manual.")
        # Descomentar las siguientes líneas cuando se quiera volver a cerrar automáticamente
        # if 'driver' in locals() and driver:
        #     try:
        #         driver.quit()
        #         print("Navegador cerrado correctamente.")
        #     except:
        #         pass

def click_next_page(driver, max_retries=3, wait_time=10):
    """
    Hace clic en el botón 'Next Page' para avanzar a la siguiente página de resultados
    
    Args:
        driver: WebDriver de Selenium
        max_retries: Número máximo de intentos de clic
        wait_time: Tiempo máximo de espera en segundos
        
    Returns:
        bool: True si el clic fue exitoso, False en caso contrario
    """
    # Iniciar cronómetro
    tiempo_inicio = datetime.datetime.now()
    
    print("Buscando el botón 'Next Page'...")
    
    # Intentar hacer clic con diferentes selectores
    selectors = [
        (By.CSS_SELECTOR, "button[aria-label='Next Page']"),
        (By.XPATH, "//button[@aria-label='Next Page']"),
        (By.XPATH, "//button[contains(@class, 'p-paginator-next')]"),
        (By.CSS_SELECTOR, ".p-paginator-next")
    ]
    
    for attempt in range(max_retries):
        for selector_type, selector in selectors:
            try:
                # Esperar a que el botón sea clickeable
                button = WebDriverWait(driver, wait_time).until(
                    EC.element_to_be_clickable((selector_type, selector))
                )
                
                print(f"Botón 'Next Page' encontrado con selector: {selector}")
                
                # Intentar hacer scroll hasta el botón para asegurarnos de que es visible
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                time.sleep(1)  # Pequeña pausa para permitir que se complete el scroll
                
                # Hacer clic en el botón
                print("Haciendo clic en el botón 'Next Page'")
                button.click()
                
                # Esperar a que la página se actualice (spinner o cambio en el contenido)
                print("Esperando a que la página se actualice...")
                
                # Esperar a que aparezca un spinner si existe
                try:
                    spinner_selector = ".spinner-container, .p-progress-spinner"
                    WebDriverWait(driver, 3).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, spinner_selector))
                    )
                    print("Spinner de carga detectado, esperando a que desaparezca...")
                    WebDriverWait(driver, wait_time).until(
                        EC.invisibility_of_element_located((By.CSS_SELECTOR, spinner_selector))
                    )
                except TimeoutException:
                    # Si no hay spinner, esperamos un momento para que se cargue la nueva página
                    time.sleep(2)
                
                # Calcular tiempo transcurrido
                tiempo_fin = datetime.datetime.now()
                tiempo_total = (tiempo_fin - tiempo_inicio).total_seconds()
                print(f"✓ Clic en 'Next Page' realizado correctamente (tiempo: {tiempo_total:.2f} segundos)")
                return True
                
            except TimeoutException:
                print(f"Timeout esperando el botón con selector: {selector}")
                continue
            except ElementClickInterceptedException:
                print(f"El botón está tapado por otro elemento. Intentando con JavaScript...")
                try:
                    driver.execute_script("arguments[0].click();", button)
                    tiempo_fin = datetime.datetime.now()
                    tiempo_total = (tiempo_fin - tiempo_inicio).total_seconds()
                    print(f"✓ Clic realizado con JavaScript (tiempo: {tiempo_total:.2f} segundos)")
                    time.sleep(2)  # Esperamos a que se procese el clic
                    return True
                except Exception as e:
                    print(f"Error al hacer clic con JavaScript: {e}")
                    continue
            except Exception as e:
                print(f"Error al hacer clic en el botón: {e}")
                continue
        
        print(f"Intento {attempt + 1} fallido. Esperando antes de reintentar...")
        time.sleep(2)
    
    print(f"❌ No se pudo hacer clic en el botón 'Next Page' después de {max_retries} intentos")
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
    
    # Procesar hasta 3 páginas como máximo (o todas si hay menos de 3)
    max_pages = 3
    print(f"Se procesarán hasta {max_pages} páginas")
    
    result = process_slir_code(test_code, max_pages=max_pages)
    
    if result and result.get("success", False):
        print(f"\nProcesamiento exitoso.")
        print(f"- HTML guardado en: {result['html_file']}")
        print(f"- JSON guardado en: {result['json_file']}")
        print(f"- CSV guardado en: {result['csv_file']}")
        
        # Mostrar un resumen de los datos extraídos
        if 'data' in result and 'table_data' in result['data']:
            print(f"- Se procesaron {result.get('pages_processed', 1)} páginas")
            print(f"- Se extrajeron {len(result['data']['table_data'])} filas en total")
    else:
        print(f"No se pudo procesar el código: {test_code}")
