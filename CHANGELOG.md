# Cambios

El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y las versiones, [versionado semántico](https://semver.org/lang/es/).

## [Sin publicar]

### Cambiado
- **Cambio de esquema:** `sections` se llama ahora `other_products`, y las patentes (antes `sections["Patentes"]`) pasan a la lista `patents` del nivel superior, siempre presente. `counts` tiene `patents` en lugar de `Patentes`. Las cuatro secciones de apropiación social del conocimiento (Fortalecimiento o solución de asuntos de interés social, Generación de insumos de política pública y normatividad, Fortalecimiento de cadenas productivas, Trabajo conjunto entre un Centro de Ciencia y un grupo de investigación) van juntas en `other_products["Apropiación social del conocimiento"]`; cada ítem conserva su `type`. En `scienti.not_on_page` (o `added_from_scienti`), el conteo `sections` se divide igual en `patents` y `other_products`. En JSON-LD los ítems de `patents` tienen `@type` `Patent` y `@id` `…#/patents/n`; los de `other_products`, `…#/other_products/<sección>/n`. §4 y §13 del esquema.

### Agregado
- `authors[]` en todos los ítems de `patents` y `other_products`: las personas listadas en la página o, si no hay ninguna, el dueño solo. Cada autor tiene `affiliations`; las del dueño son, como en las obras, las instituciones de su experiencia cuyo periodo contiene el año del ítem (`year`, o el de `date`), salvo en las tesis, que siguen con la institución de la tesis. Nuevo conteo `products_with_affiliation` en `counts` y en `affiliations_from_experience`.
- `source` en las patentes, con los datos que siguen a "Gaceta Industrial de Publicación:", separados por rótulo: la parte inicial sin rótulo en `publisher` (número de gaceta, oficina, URL o número de publicación) y cada parte con rótulo en su clave (`gazette`, `publication_date`, `international_publication`, `application_number`…). El número de `Gaceta:` también va a `identifiers` como `gazette`.

- `scope` ("Ámbito") y `review_of` ("Par evaluador de") en los ítems de Par evaluador.

### Corregido
- Número de patente: es el texto antes del primer " - ", con sus espacios (`AU 2014313817 B2`, `US 10,085,948 B2`). Antes solo se reconocía sin espacios, y en esos casos el número quedaba dentro del título.

## [0.6.0] - 2026-11-01

### Agregado
- Campos estructurados en los ítems de las demás secciones (`sections`, §13 del esquema): `title`, `authors[]` (el dueño con su COD_RH, los coautores por nombre; jurados y orientados en Jurado en comités de evaluación), `country`, `city`, `institution`, `publisher`, `venue`, `program`, `date` (ISO), `duration`, `pages`, `role`, `purpose`, `holder`, `database`, `platform`, `environment`, `identifiers[]` (contrato/registro, patente, gaceta, NIT, registro, número de concepto, secreto empresarial, derechos de autor, número de acceso, DOI, ISBN, ISSN) y `links[]` con las URL escritas en el texto. Los coautores se separan del título por la línea de la página en que va cada persona. En los 4.596 CvLAC de la UdeA hay unos 39.000 coautores y 6.700 ítems con URL en estas secciones, antes sin separar.

### Corregido
- Valores de `fields` que seguían hasta el final del ítem: `contrato/registro`, `Finalidad`, `Vía de solicitud`, `Institución solicitante` y `Medio de divulgación` se cortan donde empieza la parte sin rótulo (". En: Colombia, ,2017, 0 meses p."); los vacíos o "n/a" se quitan. En Signos distintivos ya no queda el año como etiqueta.

## [0.5.0] - 2026-10-31

### Agregado
- Salida JSON-LD: `to_jsonld(data, base=None)` y la opción `--format jsonld` (con `--base` para el prefijo del IRI). Es el mismo documento con `@context`, `@id` y `@type`; obras, proyectos, eventos e ítems de sección son nodos con un JSON Pointer como `@id`. `pyld` se agrega a las dependencias de desarrollo para probar la conversión a RDF.

### Corregido
- DOI de las obras: se reconoce también escrito como enlace (`DOI: https://doi.org/10…`, `dx.doi.org`) o con texto antes, y se busca en el resto de la cita y en sus enlaces si no está después de "DOI:". Se quitan la puntuación y la barra finales. En una muestra de 1.000 CvLAC, las obras con DOI pasan de 2.421 a 2.611.
- Año de las obras en formatos etiquetados (libros de divulgación, de formación…): se toma de "Fecha de presentación" antes que del texto libre, que incluye el título (`Plan… al año 2050` daba 2050).

### Cambiado
- Documentación: las opciones `--format` y `--base` en el README y en el esquema, y una sección JSON-LD en el esquema (§20) con el contexto, los tipos y los `@id`.
- CI y publicación usan `actions/checkout@v7`, `actions/setup-python@v7`, `actions/upload-artifact@v7` y `actions/download-artifact@v8`.

## [0.4.0] - 2026-10-28

### Agregado
- Código de SIIU (UdeA) en los proyectos: `projects[].siiu` y `projects[].external_ids` con `source: "siiu"`, cuando el título es igual y el año compatible; resumen en el objeto `siiu` y opción `--siiu auto|off` (`siiu=` en `extract()`). Los proyectos de SIIU se buscan con el documento del registro de autor de Scienti, que no se imprime ni se guarda.
- `projects[].external_ids` también con el id de Scienti, como en las obras.

## [0.3.0] - 2026-10-28

### Agregado
- `profile.full_name`, `profile.first_names` y `profile.last_names`, como en ImpactU, separados con las partes del nombre de la página, el nombre en citaciones o la nacionalidad (`profile.name_split_by`).

## [0.2.0] - 2026-10-28

### Agregado
- Barra de progreso en la terminal (etapa, porcentaje, tiempo transcurrido), con `--no-progress` para ocultarla, y parámetro `progress` en `extract()`.

## [0.1.0] - 2026-10-28

### Agregado
- Comando `cvlac-json` y función `cvlac_json.extract()`, para Python 3.10 o superior, sin dependencias.
- Perfil, identificadores, formación, experiencia (con años y ROR), áreas, idiomas, líneas, reconocimientos, proyectos, eventos y todas las demás secciones.
- Producción bibliográfica en el esquema de obras de ImpactU, con las afiliaciones del dueño del CV según el año.
- Tesis dirigidas con título, director, codirectores, estudiantes, institución con ROR, estado y programa.
- Identificadores Scienti por DOI o título (`--scienti auto|full|off`, `--apikey`).

[Sin publicar]: https://github.com/restrepo/cvlac-json/compare/v0.6.0...HEAD
[0.6.0]: https://github.com/restrepo/cvlac-json/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/restrepo/cvlac-json/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/restrepo/cvlac-json/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/restrepo/cvlac-json/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/restrepo/cvlac-json/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/restrepo/cvlac-json/releases/tag/v0.1.0
