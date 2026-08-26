# Hipótesis de trabajo - Proyecto Endocarditis Infecciosa

Fase CRISP-DM: 2 (Data Understanding), como insumo para la Fase 4 (Modeling)
Grupo 1 - Cardiología e infectología

## Contexto

Con 152 pacientes y solo 30 desenlaces de mortalidad intrahospitalaria (30 eventos
frente a 216 variables candidatas en la base), la regla practica de "eventos por
variable" (EPV >= 10) limita a un maximo de ~3 predictores para un modelo
confirmatorio interpretable (regresion logistica clasica). Por eso, en lugar de
evaluar las 216 variables, se priorizaron 3 con criterio clinico, cubriendo tres
dominios distintos y no redundantes entre si.

Nota de limitacion: la literatura de referencia (estudio 2025, n=1705) identifica la
bilirrubina total como el predictor mas relevante de mortalidad en endocarditis.
Esa variable no esta disponible en esta base de 216 columnas, por lo que el modelo
debe apoyarse en variables proxy.

## Hipotesis general (alineada con la pregunta SMART del grupo)

Un modelo de clasificacion multivariado (regresion logistica regularizada o Random
Forest), entrenado con variables clinicas priorizadas por criterio clinico, permite
predecir la mortalidad intrahospitalaria (Vivo vs. Muerto) de pacientes con
endocarditis infecciosa, e identificar el peso relativo de cada variable en ese
desenlace, ajustando por las demas.

## Hipotesis especificas

| # | Dominio clinico | Variable(s) en la base | H0 (hipotesis nula) | H1 (hipotesis alterna) |
|---|---|---|---|---|
| H1 | Disfuncion cardiaca estructural | `Falla cardiaca`, `FEVI` | La presencia de falla cardiaca / FEVI reducida al ingreso no se asocia con la mortalidad intrahospitalaria | La presencia de falla cardiaca / FEVI reducida al ingreso se asocia con mayor mortalidad intrahospitalaria |
| H2 | Virulencia microbiologica | `Staphylococcus aureus` | La infeccion por *S. aureus* no se asocia con la mortalidad intrahospitalaria | La infeccion por *S. aureus* se asocia con mayor mortalidad intrahospitalaria, en comparacion con otros germenes |
| H3 | Reserva fisiologica del paciente | `Edad` | La edad del paciente no se asocia con la mortalidad intrahospitalaria | A mayor edad, mayor probabilidad de mortalidad intrahospitalaria |

## Variables excluidas del modelo confirmatorio (justificacion)

- **Shock septico / Sepsis Shock Septico**: descartada del set confirmatorio por
  posible circularidad temporal -- suele presentarse muy cerca del desenlace, lo
  que limita su utilidad como predictor temprano y accionable (el objetivo del
  proyecto es anticipar la decision de UCI/cirugia, no confirmar gravedad ya
  instaurada).
- **Complicaciones embolicas/neurologicas, marcadores inflamatorios/renales,
  tipo de endocarditis**: quedan como candidatas para un ejercicio exploratorio
  posterior (Random Forest / LASSO con mayor numero de variables), no como parte
  de la hipotesis confirmatoria de 3 variables.

## Nota de metodo (sesgo por indicacion)

La variable `Intervencion quirurgica` se considero y se dejo fuera intencionalmente
del set confirmatorio: en la practica clinica, van a cirugia los pacientes que ya
fallaron a manejo medico, por lo que una asociacion cruda entre cirugia y
mortalidad puede reflejar la gravedad basal del paciente (variable de confusion),
no un efecto causal de la cirugia en si. Si se incluye en analisis futuros, debe
ajustarse explicitamente por gravedad al ingreso.

## Referencia cruzada con el diccionario de datos

Las 3 variables de las hipotesis especificas y su tipo propuesto, segun
`diccionario_datos.csv`:

| variable | tipo_propuesto | pct_nulos |
|---|---|---|
| Falla cardiaca | categorica binaria | 0.0 |
| FEVI | categorica nominal | 73.0 (revisar imputacion en Fase 3) |
| Staphylococcus aureus | categorica nominal | 0.7 |
| Edad | numerica | 0.0 |
