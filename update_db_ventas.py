import mysql.connector

def actualizar_bd():
    try:
        db = mysql.connector.connect(
            host="localhost",
            user="root",
            password="1323",
            database="ipera_db"
        )
        cursor = db.cursor()
        
        # Agregar columna cantidad a la tabla ventas si no existe
        try:
            cursor.execute("ALTER TABLE ventas ADD COLUMN cantidad INT DEFAULT 1")
            db.commit()
            print("Columna 'cantidad' agregada a tabla ventas.")
        except mysql.connector.Error as err:
            if err.errno == 1060: # Error 1060: Duplicate column name
                print("La columna 'cantidad' ya existe.")
            else:
                raise err
        
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        if 'db' in locals() and db.is_connected():
            cursor.close()
            db.close()

if __name__ == "__main__":
    actualizar_bd()
