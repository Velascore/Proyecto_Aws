# Sistema de Gestión de Tareas - Proyecto final de  AWS

Camilo Andres Velasco
Bradley Campo
Santiago Barriga 
Manuel Luna 

##  Funcionalidades
- Crear tareas
- Editar y completar tareas
- Eliminar tareas
- Estadísticas de tareas
- Filtros por estado e importancia

##  Arquitectura AWS 
- EC2 Ubuntu (servidor Streamlit)
- RDS MySQL (almacenamiento)
- S3 (archivos)
- ALB + Auto Scaling
- VPC con subnets públicas y privadas

## Ejecutar en local
```bash
pip install -r requirements.txt
streamlit run app.py
