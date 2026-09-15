# **MusicAI**

MusicAI es un proyecto personal de asistente musical local orientado a construir una experiencia similar a una radio inteligente/DJ.

La biblioteca musical pertenece al usuario y las recomendaciones futuras deberán salir exclusivamente de los archivos locales disponibles.

---

## **Estado actual**

| Fase                                        | Estado                 |
| ------------------------------------------- | ---------------------- |
| 0. Arquitectura / configuración             | Completada             |
| 1. Biblioteca local                         | Completada             |
| 2. Metadata e identificación                | Completada             |
| 2.1 Normalización                           | Completada             |
| 2.1.2 Extracción inteligente desde filename | Completada             |
| 2.1.3 Resolver de metadata                  | Completada y ajustada  |
| 2.1.4 Limpieza inteligente de metadata      | Completada             |
| 2.2 MusicBrainz                             | Implementada y probada |
| 2.3 Fingerprinting acústico / AcoustID      | Completada             |
| 2.3 Comparación de identidad acústica       | Completada             |
| 3. Análisis musical                         | Pendiente              |
| 4. Player                                   | Pendiente              |
| 5. Recomendaciones                          | Pendiente              |
| 6. Aprendizaje                              | Pendiente              |
| 7. Radio                                    | Pendiente              |
| 8. DJ / mixing                              | Pendiente              |
| 9. Locutor IA                               | Pendiente              |

---

## **Objetivo**

MusicAI deberá:

* analizar archivos MP3/FLAC y otros formatos locales;
* detectar duplicados exactos;
* limpiar y resolver metadata;
* identificar canciones aunque la metadata esté ausente o sea incorrecta;
* usar MusicBrainz y AcoustID como fuentes externas de verificación;
* utilizar fingerprinting acústico para comprobar la identidad real del audio;
* analizar BPM, tonalidad, energía, estructura, intro y outro;
* aprender preferencias de escucha;
* recomendar únicamente música de la biblioteca local;
* funcionar como una radio/DJ estilo GTA;
* crear posteriormente transiciones y crossfades naturales;
* incorporar un futuro locutor de IA.

---

## **Arquitectura**

```text
MusicAI/

├── backend/
│   ├── app/
│   │   ├── database/connection.py
│   │   ├── models/song.py
│   │   └── services/
│   │       ├── scanner.py
│   │       ├── library.py
│   │       ├── metadata_normalizer.py
│   │       ├── filename_parser.py
│   │       ├── metadata_resolver.py
│   │       ├── metadata_cleaner.py
│   │       ├── metadata_identifier.py
│   │       ├── musicbrainz_client.py
│   │       ├── metadata_matcher.py
│   │       ├── metadata_quality.py
│   │       ├── acoustic_fingerprint.py
│   │       ├── acoustic_fingerprint_store.py
│   │       ├── acoustic_library.py
│   │       ├── acoustic_identifier.py
│   │       ├── acoustid_client.py
│   │       ├── acoustic_metadata_resolver.py
│   │       ├── acoustic_identity_comparator.py
│   │       └── archivos de prueba
│   └── .venv/
│
├── frontend/
├── data/music.db
├── music/
├── .env
├── .gitignore
└── README.md
```

### Stack actual

* Python
* FastAPI
* Uvicorn
* SQLAlchemy
* SQLite
* Mutagen
* Requests
* python-dotenv
* FFmpeg
* Chromaprint / fpcalc
* MusicBrainz
* AcoustID

El frontend previsto utiliza React + TypeScript y Tauri será considerado posteriormente para la aplicación de escritorio.

---

# **Fase 1 — Biblioteca local**

MusicAI analiza recursivamente la carpeta:

```text
music/
```

Actualmente se soportan:

```text
.mp3
.flac
.wav
.m4a
.ogg
```

Los archivos se identifican mediante SHA-256.

Los duplicados exactos se detectan por hash y se descartan lógicamente. Las pruebas de deduplicación no deben borrar físicamente archivos del usuario.

También se mantiene el estado de disponibilidad de cada canción mediante `is_available`, permitiendo detectar archivos que hayan sido eliminados o movidos.

---

# **Fase 2 — Metadata e identificación**

La fase 2 tiene como objetivo obtener una identidad musical confiable incluso cuando la metadata original sea incorrecta, incompleta o contaminada.

El sistema mantiene separadas:

1. metadata original;
2. metadata interpretada por MusicAI;
3. identificación externa;
4. identidad acústica;
5. decisión final.

La metadata original no se sobrescribe durante los procesos de resolución.

---

## **2.1 Normalización**

La metadata se normaliza antes de utilizarla para comparación o identificación.

Se eliminan diferencias irrelevantes de formato, mayúsculas, acentos y otros elementos que puedan afectar una comparación textual.

---

## **2.1.2 Filename parser**

El parser interpreta nombres de archivo que contienen artista y título.

Ejemplo:

```text
Avicii - The Nights.mp3
```

Resultado:

```text
artist = Avicii
title  = The Nights
confidence = 0.90
```

También reconoce formatos invertidos o provenientes de archivos de letras:

```text
(Letra) Hablame De Ti - Banda MS (Completa).mp3
```

Resultado:

```text
artist = Banda MS
title  = Hablame De Ti
confidence = 0.90
```

También evita interpretar etiquetas puramente relacionadas con versiones como si fueran artistas.

Ejemplo:

```text
Song Title - Original Mix.mp3
```

se mantiene de forma conservadora como un título versionado.

---

## **2.1.3 Metadata resolver**

El resolver combina la metadata original con la información extraída del filename.

La prioridad depende de la calidad de la metadata.

Si la metadata es confiable, se conserva.

Si está incompleta, el filename puede completar campos.

Si la metadata es sospechosa y el filename tiene suficiente confianza, el filename puede tener prioridad.

Ejemplo problemático:

```text
Metadata:

artist = (Letra) Hablame De Ti
title  = Banda MS (Completa)

Filename:

(Letra) Hablame De Ti - Banda MS (Completa).mp3
```

Resultado:

```text
artist = Banda MS
title  = Hablame De Ti
source = filename
confidence = 0.90
```

La metadata original permanece intacta.

---

## **2.1.4 Limpieza inteligente de metadata**

Se implementó una limpieza conservadora de títulos.

Detecta y elimina ruido relacionado con:

* lyric video;
* lyrics;
* letra;
* subtitulado;
* music video;
* official video;
* YouTube;
* etiquetas de subida;
* atribuciones de uploader.

Se preservan deliberadamente descriptores musicales como:

* Remix;
* Radio Edit;
* Original Mix;
* Acoustic Version;
* Live Version;
* feat.;
* ft.

La limpieza no intenta adivinar información musical que no esté respaldada por los datos.

La limpieza fue aplicada sobre la biblioteca existente y validada sin crear registros nuevos ni alterar campos no relacionados.

---

# **2.2 MusicBrainz**

El cliente se encuentra en:

```text
backend/app/services/musicbrainz_client.py
```

Implementa:

* búsquedas de recordings;
* consultas por MBID;
* extracción de artistas;
* releases;
* release groups;
* User-Agent;
* rate limiting;
* reintentos ante HTTP 429;
* reintentos ante HTTP 503.

Un HTTP 503 se considera indisponibilidad temporal del servicio y **no constituye evidencia de una identidad incorrecta**.

### Matcher de metadata

El matcher utiliza actualmente:

```text
Título      50%
Artista     35%
Duración    15%
```

Clasificación:

```text
>= 0.95  confirmed
>= 0.80  probable
>= 0.60  review
<  0.60  rejected
```

El resultado de MusicBrainz no reemplaza automáticamente la metadata local cuando la evidencia es insuficiente.

---

# **2.3 Fingerprinting acústico / AcoustID**

## **Objetivo**

El fingerprinting acústico permite identificar el audio real independientemente de que su metadata sea correcta.

El pipeline implementado es:

```text
Archivo de audio
       ↓
FFmpeg / audio real
       ↓
Chromaprint / fpcalc
       ↓
Fingerprint acústico
       ↓
AcoustID
       ↓
Múltiples candidatos
       ↓
MusicBrainz por MBID
       ↓
Ranking de candidatos
       ↓
Comparación de identidad
       ↓
Decisión
```

---

## **Generación del fingerprint**

`acoustic_fingerprint.py` ejecuta `fpcalc` sobre el archivo de audio.

La huella generada es estable para el mismo contenido de audio y se almacena en:

```text
songs.acoustic_fingerprint
```

La duración obtenida durante el fingerprinting también se utiliza para comparar candidatos.

---

## **Almacenamiento**

`acoustic_fingerprint_store.py` permite generar y almacenar el fingerprint de una canción sin modificar el resto de su información.

`acoustic_library.py` procesa únicamente canciones disponibles que todavía no poseen fingerprint.

Por lo tanto, el proceso puede ejecutarse nuevamente sin recalcular innecesariamente las canciones ya procesadas:

```powershell
python -m app.services.acoustic_library
```

En el estado actual:

```text
Canciones disponibles: 41
Fingerprints generados: 41
Errores: 0
```

---

# **AcoustID**

MusicAI utiliza una API key de AcoustID almacenada mediante `.env`.

Ejemplo:

```env
ACOUSTID_API_KEY=TU_API_KEY
```

La API key nunca debe almacenarse directamente en el código ni subirse a Git.

El cliente se encuentra en:

```text
backend/app/services/acoustid_client.py
```

La consulta utiliza:

* fingerprint;
* duración;
* API key;
* información adicional de recording IDs.

AcoustID puede devolver múltiples candidatos para un mismo audio. Por esta razón, MusicAI **no acepta automáticamente el primer resultado**.

---

# **Ranking acústico**

El ranking combina la similitud de metadata con la confianza proporcionada por AcoustID:

```text
metadata_score * 0.80
+
acoustid_score * 0.20
```

La metadata utilizada para el ranking debe corresponder a la identidad local ya resuelta por MusicAI.

Esto es importante porque una identificación acústica puede devolver múltiples recordings compatibles.

El sistema:

1. obtiene todos los candidatos disponibles;
2. elimina MBIDs duplicados;
3. consulta MusicBrainz;
4. compara título, artista y duración;
5. calcula el `metadata_score`;
6. combina metadata y AcoustID;
7. ordena los candidatos;
8. selecciona el mejor candidato analizado.

Los candidatos cuyo MusicBrainz no pudo consultarse se conservan como información de diagnóstico y no se interpretan automáticamente como identidades incorrectas.

---

# **Resolver acústico**

El resolver se encuentra en:

```text
backend/app/services/acoustic_metadata_resolver.py
```

Estados principales:

```text
not_found
musicbrainz_lookup_failed
identified
```

El resolver acústico:

* recibe el fingerprint;
* recibe la duración;
* recibe la metadata local resuelta;
* obtiene candidatos de AcoustID;
* obtiene información de MusicBrainz;
* ejecuta el ranking;
* devuelve la identidad acústica mejor evaluada.

No modifica SQLite.

La separación entre resolución y persistencia permite probar el sistema sin alterar la biblioteca.

---

# **Comparador de identidad acústica**

El comparador se encuentra en:

```text
backend/app/services/acoustic_identity_comparator.py
```

Su responsabilidad es diferente a la del resolver.

El resolver responde:

> ¿Qué canción parece corresponder al fingerprint?

El comparador responde:

> ¿La identidad acústica encontrada es compatible con la identidad local que ya tenemos?

Esta separación es deliberada para evitar que una fuente externa pueda reemplazar automáticamente información local sin suficiente evidencia.

---

## **Comparación de artistas**

El comparador normaliza los créditos de artistas y reconoce relaciones como:

```text
Avicii
```

frente a:

```text
Avicii, Billy Raffoul
```

o:

```text
Avicii Feat. Sandro Cavazza
```

También reconoce equivalencias de crédito como:

```text
Banda MS
```

frente a:

```text
Banda MS de Sergio Lizárraga
```

cuando la estructura del nombre proporciona evidencia suficiente.

Las pruebas aisladas de créditos de artistas alcanzaron:

```text
6/6 PASS
```

---

## **Clasificaciones**

El comparador puede producir:

```text
confirmed
probable
review
conflict
```

Las decisiones correspondientes pueden ser:

```text
identity_confirmed
acoustic_identity_preferred
review_recommended
review_required
strong_acoustic_conflict
no_action
```

Política:

```text
confirmed → aceptar automáticamente

probable  → evaluar según confianza acústica

review    → recomendar revisión

conflict  → no reemplazar automáticamente
```

La política es deliberadamente conservadora.

---

# **Validación de la Fase 2.3**

La fase completa fue probada mediante diferentes niveles de pruebas:

### Fingerprint

Se comprobó que el mismo archivo genera fingerprints estables.

### AcoustID

Se comprobó la comunicación con AcoustID y la recuperación de candidatos y MBIDs.

### MusicBrainz por MBID

Se comprobó la recuperación de recordings identificados mediante AcoustID.

### Ranking

Se comprobó la selección del mejor candidato cuando existen múltiples resultados acústicos.

### Créditos de artistas

Se probaron equivalencias y colaboraciones:

```text
6/6 PASS
```

### Política de identidad

Se probaron casos de:

* coincidencia exacta;
* diferencias de versión;
* artistas diferentes;
* títulos diferentes;
* colaboraciones;
* créditos abreviados;
* conflictos fuertes;
* ausencia de resultados;
* indisponibilidad de MusicBrainz.

La prueba extendida obtuvo:

```text
8/8 PASS
```

---

# **Prueba de integración acústica completa**

La prueba principal:

```powershell
python -m app.services.test_acoustic_integration
```

valida el flujo completo:

```text
SQLite
 ↓
Metadata local
 ↓
Fingerprint
 ↓
AcoustID
 ↓
MusicBrainz
 ↓
Ranking
 ↓
Comparador
 ↓
Decisión final
```

Resultado más reciente:

```text
==============================================
RESULTADO FINAL: 5/5 canciones confirmadas
==============================================
```

Canciones utilizadas:

| ID | Canción          | Clasificación | Decisión           |
| -: | ---------------- | ------------- | ------------------ |
|  1 | Hablame De Ti    | confirmed     | identity_confirmed |
| 32 | The Nights       | confirmed     | identity_confirmed |
| 35 | Waiting For Love | confirmed     | identity_confirmed |
| 39 | Without You      | confirmed     | identity_confirmed |
| 40 | You Be Love      | confirmed     | identity_confirmed |

### Casos importantes validados

**ID 1 — Hablame De Ti**

```text
Local:
Banda MS / Hablame De Ti

Acústico:
Banda MS de Sergio Lizárraga / Háblame de ti

AcoustID:
0.9823312

Resultado:
confirmed
```

El comparador reconoce que los créditos corresponden al mismo artista.

---

**ID 32 — The Nights**

```text
Local:
Avicii / The Nights

Acústico:
Avicii / The Nights

Resultado:
confirmed
```

Incluso con indisponibilidad temporal de MusicBrainz durante la consulta, el proceso mantuvo una identificación correcta.

---

**ID 35 — Waiting For Love**

```text
Local:
Avicii / Waiting For Love

Acústico:
Avicii / Waiting for Love

AcoustID:
0.9843091

MBID:
b40a9429-47a3-4f71-b3d8-611bf6b4b0c5

Resultado:
confirmed
```

Este caso fue especialmente importante porque AcoustID devolvía múltiples candidatos. Al proporcionar la metadata local al ranking, MusicAI seleccionó correctamente la grabación correspondiente de Avicii.

---

**ID 39 — Without You**

```text
Local:
Avicii Feat. Sandro Cavazza / Without You

Acústico:
Avicii, Sandro Cavazza / Without You

AcoustID:
0.99222046

Resultado:
confirmed
```

Se confirmó correctamente la colaboración.

---

**ID 40 — You Be Love**

```text
Local:
Avicii / You Be Love

Acústico:
Avicii, Billy Raffoul / You Be Love

AcoustID:
0.96486026

Resultado:
confirmed
```

También se reconoció correctamente el crédito adicional del artista colaborador.

---

# **Conclusión de la Fase 2.3**

La Fase 2.3 se considera **completada**.

MusicAI ya cuenta con un pipeline funcional de identificación acústica:

```text
Audio
 ↓
Fingerprint
 ↓
AcoustID
 ↓
Candidatos
 ↓
MusicBrainz
 ↓
Ranking
 ↓
Comparación
 ↓
Decisión
```

La prueba de integración actual confirma:

```text
5/5 canciones confirmadas
```

La identificación acústica permanece separada de la modificación de SQLite.

Por lo tanto, el sistema todavía **no sobrescribe automáticamente la metadata local basándose únicamente en la identificación acústica**. Esa decisión deberá diseñarse posteriormente con una política explícita de persistencia y confianza.

---

# **Pruebas**

### Filename parser

```powershell
python -m app.services.test_filename_parser_problematic
```

### Metadata resolver

```powershell
python -m app.services.test_metadata_resolver_problematic
```

Esta prueba cubre metadata correcta, sospechosa, incompleta, filenames ambiguos, fallback y formatos invertidos.

No modifica SQLite.

### Ranking acústico

```powershell
python -m app.services.test_acoustic_candidate_ranking
```

Comprueba fingerprint, AcoustID, múltiples candidatos, MusicBrainz y ranking.

### Comparador de artistas

```powershell
python -m app.services.test_artist_credit_similarity
```

Comprueba créditos equivalentes y colaboraciones.

### Política del comparador

```powershell
python -m app.services.test_acoustic_identity_policy_extended
```

Comprueba coincidencias, conflictos, versiones, colaboraciones y ausencia de resultados.

### Comparador multi-canción

```powershell
python -m app.services.test_acoustic_identity_comparator_multi
```

Prueba cinco canciones y compara identidad local contra identidad acústica.

### Integración acústica completa

```powershell
python -m app.services.test_acoustic_integration
```

Prueba el pipeline completo de cinco canciones.

Resultado actual:

```text
5/5 PASS
```

Las pruebas de comparación e integración no modifican SQLite.

---

# **Levantar FastAPI**

Desde `MusicAI/backend` con `.venv` activo:

```powershell
uvicorn app.main:app --reload
```

Abrir:

```text
http://127.0.0.1:8000
http://127.0.0.1:8000/docs
```

---

# **AcoustID**

Crear `.env` en la raíz de MusicAI:

```env
ACOUSTID_API_KEY=TU_API_KEY
```

La API key se obtiene al registrar la aplicación en AcoustID.

No debe subirse a Git ni escribirse directamente en el código.

Verificar que se carga sin imprimirla:

```powershell
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(bool(os.getenv('ACOUSTID_API_KEY')))"
```

Debe aparecer:

```text
True
```

---

# **Base de datos**

La base de datos es:

```text
data/music.db
```

La tabla principal es:

```text
songs
```

Actualmente contiene:

### Metadata original

```text
title
artist
album
genre
year
duration
```

### Metadata interpretada

```text
normalized_title
normalized_artist
metadata_source
metadata_confidence
```

### Identificación del archivo

```text
file_path
file_hash
acoustic_fingerprint
```

### Disponibilidad

```text
is_available
```

El fingerprint acústico se almacena independientemente de la metadata original.

---

# **Requisitos**

Instalar:

* Python
* Node.js LTS
* Git
* FFmpeg
* Chromaprint

Comprobar:

```powershell
python --version
node --version
npm --version
git --version
ffmpeg -version
fpcalc -version
```

Después de modificar el PATH de Windows para FFmpeg o Chromaprint, reiniciar VS Code.

---

# **Preparar Python**

Desde la raíz del proyecto:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Instalar las dependencias actuales:

```powershell
pip install fastapi uvicorn sqlalchemy mutagen requests python-dotenv
```

---

# **Orden recomendado en una instalación nueva**

1. Instalar Python, Node.js LTS, Git, FFmpeg y Chromaprint.
2. Clonar/copiar MusicAI.
3. Crear y activar `backend/.venv`.
4. Instalar dependencias Python.
5. Crear `.env` y configurar `ACOUSTID_API_KEY`.
6. Comprobar `ffmpeg -version` y `fpcalc -version`.
7. Colocar la biblioteca musical en `music/`.
8. Ejecutar las pruebas de filename y metadata.
9. Ejecutar el procesamiento de fingerprints.
10. Ejecutar las pruebas de AcoustID.
11. Ejecutar el ranking acústico.
12. Ejecutar el comparador de identidad.
13. Ejecutar la integración acústica completa.
14. Levantar FastAPI.

---

# **Reglas para continuar el desarrollo**

* No confiar solamente en metadata.
* No confiar solamente en AcoustID.
* No interpretar un HTTP 503 de MusicBrainz como identidad incorrecta.
* No borrar físicamente archivos durante pruebas de deduplicación.
* No sobrescribir metadata automáticamente hasta estabilizar la política de identidad.
* Mantener separadas identificación, comparación y modificación de datos.
* Preferir decisiones conservadoras ante conflictos.
* Mantener las pruebas sin efectos secundarios sobre SQLite cuando sea posible.
* No asumir que el primer resultado de AcoustID es necesariamente el correcto.
* Utilizar la metadata local resuelta como contexto para el ranking acústico.
* Mantener las API keys fuera del código fuente y fuera del repositorio.

---

# **Próximo objetivo técnico**

La **Fase 2.3 está cerrada**.

El siguiente objetivo es comenzar:

```text
Fase 3 — Análisis musical
```

El primer bloque de análisis deberá estudiar las características musicales reales de cada archivo, comenzando por:

* BPM;
* tonalidad/key;
* energía;
* loudness;
* danceability;
* estructura;
* intro;
* outro.

La información obtenida deberá prepararse para alimentar posteriormente:

```text
Análisis musical
       ↓
Base de características
       ↓
Recommendation Engine
       ↓
DJ Engine
       ↓
Radio
```

La Fase 3 deberá mantenerse separada de las decisiones de identidad implementadas en la Fase 2.

---

# **Filosofía**

MusicAI debe recopilar evidencia, comparar fuentes, medir confianza y tomar decisiones conservadoras.

La IA futura debe complementar el razonamiento técnico, no sustituirlo.

El proyecto se está construyendo incrementalmente:

```text
Componente
    ↓
Pruebas aisladas
    ↓
Validación
    ↓
Integración
    ↓
Siguiente componente
```

Cada componente debe poder probarse antes de integrarlo con el siguiente.
