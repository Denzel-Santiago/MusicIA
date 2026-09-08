import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
DATABASE_PATH = BASE_DIR / "data" / "music.db"


NEW_COLUMNS = {
    "normalized_title": "TEXT",
    "normalized_artist": "TEXT",
    "metadata_source": "TEXT",
    "metadata_confidence": "REAL",
}


def get_existing_columns(connection):
    cursor = connection.execute("PRAGMA table_info(songs)")
    return {row[1] for row in cursor.fetchall()}


def migrate_database():
    if not DATABASE_PATH.exists():
        print(f"No se encontró la base de datos: {DATABASE_PATH}")
        return

    connection = sqlite3.connect(DATABASE_PATH)

    try:
        existing_columns = get_existing_columns(connection)

        added_columns = []

        for column_name, column_type in NEW_COLUMNS.items():

            if column_name not in existing_columns:

                sql = (
                    f"ALTER TABLE songs "
                    f"ADD COLUMN {column_name} {column_type}"
                )

                connection.execute(sql)
                added_columns.append(column_name)

        connection.commit()

        if added_columns:
            print("Migración completada.")
            print("Columnas agregadas:")

            for column in added_columns:
                print(f"  + {column}")

        else:
            print("La base de datos ya contiene todas las columnas.")
            print("No fue necesario realizar cambios.")

    finally:
        connection.close()


if __name__ == "__main__":
    migrate_database()