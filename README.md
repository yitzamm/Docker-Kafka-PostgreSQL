# Docker-Kafka-PostgreSQL

## Objetivo
Este proyecto tiene como objetivo implementar una arquitectura basada en microservicios utilizando contenedores Docker y mensajería distribuida con Apache Kafka.

La aplicación simula un sistema simple donde una API expone datos, un productor envía eventos a Kafka, un consumidor procesa esos eventos y una interfaz web permite visualizar e interactuar con la información.

El propósito principal es demostrar el diseño, comunicación y escalabilidad de microservicios desacoplados en un entorno contenerizado.

## Tecnologías

- **Docker -** Contenerización de todos los servicios
- **Docker Compose -** Orquestación de múltiples contenedores
- **Python -** Lógica de API, productor y consumidor
- **Apache Kafka -** Sistema de mensajería distribuida
- **PostgreSQL -** Base de datos relacional
- **pgAdmin -** Administración visual de la base de datos
- **HTML / CSS / Javascript -** Interfaz de usuario
- **Arquitecture de microservicios -** Separación de responsabilidades por servicio

## Estructura del proyecto

```
microservices-lab/
│
├── api/
│   ├── Dockerfile
│   └── main.py
│
├── consumer/
│   ├── Dockerfile
│   └── consumer.py
│
├── producer/
│   ├── Dockerfile
│   └── producer.py
│
├── ui/
│   ├── index.html
│   ├── style.css
│   └── app.js
│
└── docker-compose.yml
```

## Flujo de trabajo del sistema

Luego de investigar un poco acerca de las configuraciones básicas de Apache Kafka dentro de Docker Compose, empecé por hacerle modificaciones iniciales al archivo original y así evitar  complicaciones más adelante. Estos cambios incluyeron agregarle broker ID y Kafka listeners para listener mapping, start up y conexiones de red. Adicional, agregué la dependencia faltante en la sección de Kafka UI. Las dependencias juegan un papel importante en el proyecto, por lo que es importante entender bien la relación entre cada componente. En concreto, Kafka depende de Zookeeper, Kafka UI depende de Kafka, Consumer depende de Kafka y Postgres, y API depende de Postgres.

El siguiente paso fue crear el servidor de Postgres desde pgAdmin y desde ahí agregar una tabla. Para la tabla seguí el siguiente steps list: Servers > Databases > clientesdb > public > Tables. Una vez en Tables, click derecho Create > Table. Inicié con únicamente 3 valores, ID, nombre y correo, más adelante le agregué varias columnas más. ID es el que lleva primary key, entonces habilité el PK y dentro del Constraints tab, cambié el Identity de ALWAYS a BY DEFAULT, y setié incrementos de 1 con start 1.

A continuación, configuré Kafka, creé main.py, producer.py, consumer.py y el UI (html, css y js). La API respondió sin problema desde http://localhost:8000/clientes, sin embargo el UI (http://localhost:8083/) me devolvió un error de CORS. Este ocurre cuando un navegador bloquea una solicitud HTTP a un dominio diferente por motivos de seguridad y es una restricción propia del navegador, en mi caso, http://localhost:8000/clientes != http://localhost:8083 y por tanto detecta un conflicto de origen. Para arreglarlo, habilité cross-origin requests desde main.py.

La primer mejora que le quería implementar al proyecto era permitir que el usuario pudiera agregar un cliente desde el UI, dejar que Kafka producer detectara el evento, creara el tópico, y que por último Kafka consumer actualizara la base de datos con el evento recibido. Para que funcionara necesitaba que la API pudiera leer desde la base de datos y enviarle eventos a producer.py. El problema era que el contenedor de producer hacía exit casi inmediatamente después de correr docker compose up. Ahora que producer no le estaba enviando data preescrita a consumer, ocupaba a los 2 siempre arriba y en "listening state". Producer debía escuchar a API y Consumer escuchar a Producer. Con eso en mente, reinventé la conexión a Kafka y reconfiguré el API endpoint.

Esto solucionó el auto-exit, pero estaba teniendo errores de backend cuando hacía un insert. Desde inspect, revisé los API responses, status codes y los logs de cada contenedor. Tras revisar más detenidamente los files, logré identificar y reinstalar las dependencias faltantes. Aproveché para agregar una función que permitiera editar y eliminar clientes, estas usan una lógica muy similar y básicamente el mismo recorrido (UI -> API -> Kafka Producer -> Kafka Consumer -> DB). Llegado a este punto edit y delete reflejaban de inmediato los cambios, pero agregar clientes tenía un delay significativo y para visualizarlo tenía que refrescar la ventana del navegador. Lo anterior ocurre porque las mutaciones de información (agregar, editar, eliminar) recorren un Kafka-based pipeline que usa procesamiento asíncrono, para contrarrestarlo, le agregué un delay directamente a la interfaz, suficiente para que el consumer pueda terminar de procesar el evento antes de que el UI pida actualizarse.

El otro agregado está sugerido dentro del proyecto que es justamente incluir logs centralizados. Mi idea era poder visualizar los logs de Kafka en tiempo real desde la pantalla por medio de WebSockets sin necesidad de polling. En este sentido, La API actúa como puente, recibiendo los mensajes del consumidor para luego retransmitirlos. Para esto agregué 3 secciones importantes en main.py, una tipo LogEvents que usa BaseModel, otra para el WebSocket tanto la parte del endpoint como el broadcast function y un HTTP bridge que reciba los logs desde LogEvent y espere el broadcast_log.

Los cambios en el consumer y el UI fueron bastante más concretos. Consumer.py incluye la parte de reformatting para estandarizar los mensajes de salida, donde format_log define el estilo del formato y requests.post aplica el nuevo formato dentro de cada función. De aquí me moví para el index file, en el index metí un panel para los logs con su respectivo header y body, js por otra parte, contiene el EventListener que básicamente carga los logSockets y muestra el conection state del Websocket en los logs de la consola, así como los eventos de Kafka en el panel de mensajes, también mantiene un estado inicial de "No hay logs para mostrar" que se reemplaza dinámicamente apenas llega el primer mensaje.
