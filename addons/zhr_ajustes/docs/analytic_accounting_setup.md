# Plan de contabilidad analítica y centros de costo (Odoo 18 Community)

## Objetivo
Definir una estructura de centros de costo basada en **Contabilidad Analítica** para luego asignar personas (empleados) a dicha estructura, usando una jerarquía de **Gerencias → Departamentos** como base organizacional.

## Pasos previos recomendados en Odoo
1. **Activar la contabilidad analítica**  
   Asegúrate de que el módulo de **Contabilidad** esté instalado y habilita la opción de **Contabilidad Analítica** en la configuración contable.

2. **Definir el plan analítico (centros de costo)**  
   Crea las **Cuentas Analíticas** que representarán tus centros de costo.  
   - Estructura sugerida:  
     - Gerencia A  
       - Departamento A1  
       - Departamento A2  
     - Gerencia B  
       - Departamento B1  
       - Departamento B2

3. **Alinear la estructura organizacional**  
   En **Empleados → Departamentos**, crea los departamentos alineados a la estructura anterior.  
   - Usa el departamento padre como **Gerencia**.  
   - Usa el departamento hijo como **Departamento**.

4. **Vincular el centro de costo al departamento**  
   En cada **Departamento**, asigna la **Cuenta Analítica** correspondiente (centro de costo).  
   - Esto centraliza la asignación del centro de costo y evita duplicidad al nivel de empleado.

5. **Validar en transacciones**  
   Verifica que las transacciones que deban llevar centro de costo (por ejemplo, gastos, compras o asientos analíticos) puedan tomar la cuenta analítica desde el departamento o desde la entidad que lo consuma.

## Resultado esperado
Con esta configuración:
- La empresa queda organizada jerárquicamente por **Gerencias → Departamentos**.
- Cada **Departamento** tiene un **Centro de Costo** (Cuenta Analítica).
- Los empleados pueden heredar el centro de costo del departamento sin crear campos nuevos.
