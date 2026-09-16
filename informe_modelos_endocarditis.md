# Comparacion de modelos de mortalidad en endocarditis

## Definición del problema



## Objetivo

Estimar la mortalidad intrahospitalaria con variables disponibles al ingreso o al diagnostico. La cohorte principal contiene 139 pacientes y 30 muertes; los pacientes `Remitido` fueron excluidos porque su desenlace posterior no esta completamente observado.

## Datos

# Enfoque analítico

## Selección de categorias

se usaron estregioas X, Y, Z para acotar variables y con criterio clinico se seleccionaron las que mejor pueden definir el modelo

## Modelos evaluados

1. **Nucleo con neutrofilos:** `Edad`, `Falla cardiaca`, `Enfermedad renal`, `Tipo de endocarditis`, `Staphylococcus aureus` y `Neutrofilos`.
2. **Nucleo con leucocitos:** mismas variables, reemplazando `Neutrofilos` por `Leucocitos`.
3. **Reducido de cinco variables con neutrofilos:** `Edad`, `Falla cardiaca`, `Enfermedad renal`, `Staphylococcus aureus` y `Neutrofilos`.
4. **Reducido de cinco variables con leucocitos:** mismas cinco variables, reemplazando `Neutrofilos` por `Leucocitos`.
5. **Ampliado con neutrofilos:** nucleo clinico mas `Creatinina`, `Plaquetas`, `Hemoglobina`, `Fiebre`, `Sintomas neurologicos` y `Aneurisma micotico`.

Todos los modelos usaron imputacion, codificacion, escalado, Elastic Net, `class_weight='balanced'` y validacion cruzada estratificada.

## Resultados

### F2 promedio en validacion cruzada

| Modelo | F2 |
|---|---:|
| Nucleo con neutrofilos | 0.531 |
| Nucleo con leucocitos | 0.546 |
| Reducido 5 con neutrofilos | 0.549 |
| Reducido 5 con leucocitos | 0.537 |
| Ampliado con neutrofilos | 0.570 |

### Test con umbral 0.50

| Modelo | Accuracy | Recall muerte | Precision muerte | F2 |
|---|---:|---:|---:|---:|
| Nucleo con neutrofilos | 0.64 | 0.67 | 0.33 | 0.556 |
| Nucleo con leucocitos | 0.57 | 0.50 | 0.25 | 0.417 |
| Reducido 5 con neutrofilos | 0.57 | 0.67 | 0.29 | 0.526 |
| Reducido 5 con leucocitos | 0.46 | 0.83 | 0.26 | 0.581 |
| Ampliado con neutrofilos | 0.71 | 0.83 | 0.42 | 0.694 |

En el modelo ampliado, el umbral `0.60` mantuvo el recall en `0.83`, aumento la precision a `0.50` y redujo los falsos positivos de 7 a 5. Esta comparacion es exploratoria porque el umbral definitivo debe seleccionarse con predicciones fuera de fold.

## Recomendacion provisional

El candidato principal es el **modelo ampliado con neutrofilos**, porque obtuvo el mejor F2 en validacion cruzada y el mejor equilibrio observado en el test. El modelo reducido de cinco variables con neutrofilos queda como alternativa parsimoniosa y mas facil de implementar.

No se incluyen simultaneamente leucocitos y neutrofilos por su alta colinealidad. `Neutrofilos` se mantiene como representacion principal por su especificidad biologica y por el mejor comportamiento del modelo ampliado.

## Limitaciones y siguientes pasos

Solo hay 30 eventos y el test contiene 6 muertes. Una sola observacion cambia sustancialmente las metricas. Antes de cualquier uso clinico se requiere validacion cruzada repetida, bootstrap, calibracion, seleccion del umbral con predicciones fuera de fold y validacion externa.

Los OR del modelo Elastic Net son exploratorios y no equivalen a OR inferenciales definitivos. La recomendacion final debe considerar rendimiento, parsimonia, carga de falsas alertas y factibilidad clinica.