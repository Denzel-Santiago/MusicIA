# Arquitectura del backend

## Capas

```text
routes → bootstrap → application (use cases + ports)
                           ↑              ↓
                         domain        adapters
```

- `app/domain/` contiene reglas independientes de FastAPI, SQLAlchemy, disco y servicios externos.
- `app/application/ports/` declara las capacidades que necesitan los casos de uso; `use_cases/` coordina esas capacidades.
- `app/adapters/` implementa filesystem, persistencia SQLAlchemy, clientes HTTP para MusicBrainz/AcoustID y fingerprinting Chromaprint.
- `app/bootstrap/dependencies.py` construye adaptadores y casos de uso para inyección en rutas.
- `app/routes/` traduce solicitudes y respuestas HTTP; `app/main.py` configura FastAPI y crea el esquema SQLite actual.

Regla de dependencias: dominio no depende de las demás capas; aplicación puede depender del dominio y de sus puertos; adaptadores implementan puertos; rutas reciben casos de uso desde bootstrap.
Las pruebas automatizadas de arquitectura revisan que dominio/aplicación no importen FastAPI, SQLAlchemy o clientes concretos y que no haya ciclos entre las capas internas.

## Ubicación de componentes

| Componente | Ubicación |
| --- | --- |
| Normalización, parser y resolución de metadata | `app/domain/metadata/` |
| Comparación de identidad acústica | `app/domain/identity/` |
| Entidad musical | `app/domain/music/` |
| Escaneo y acceso a archivos | `app/adapters/filesystem/` |
| Fingerprints | `app/adapters/audio/chromaprint/` |
| MusicBrainz y AcoustID | `app/adapters/external_services/` |
| SQLite, modelo ORM y repositorio | `app/adapters/persistence/sqlalchemy/` |
| Casos de uso y contratos | `app/application/` |
| Ensamblado para FastAPI | `app/bootstrap/` |
| Rutas API | `app/routes/` |

## Compatibilidad y pendientes

Los módulos conservados en `app/services/`, además de `app/database/connection.py` y `app/models/song.py`, funcionan como fachadas de compatibilidad para imports antiguos y diagnósticos existentes. Algunos diagnósticos de `app/services/test/` también usan la base SQLite configurada o servicios externos; no se deben considerar pruebas unitarias aisladas.

`app/services/audio_analyzer.py` sigue en diseño y no se migró: todavía reúne decodificación, orquestación y extractores no implementados, y requiere NumPy, que no figura en `backend/requirements.txt`. La fase de análisis musical sigue pendiente. El cambio de capas no requiere ni incluye migración de esquema o datos.

## Pruebas

Desde `backend/`:

```powershell
python -m unittest discover -s tests -v
```

Esto ejecuta las pruebas unitarias de casos de uso con SQLite en memoria y las comprobaciones de arquitectura. Para diagnósticos heredados, primero inspeccionar el archivo: varios tienen nombre `test_` pero hacen consultas contra la base de datos configurada, requieren audio local o consultan servicios HTTP.

FastAPI se inicia desde `backend/` con el entorno configurado:

```powershell
uvicorn app.main:app --reload
```
