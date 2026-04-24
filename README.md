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

**Docker Compose**
<img width="1019" height="494" alt="image" src="https://github.com/user-attachments/assets/5c25fefc-7a40-4d3c-979f-1d6029f56c7c" />

El siguiente paso fue crear el servidor de Postgres desde pgAdmin y desde ahí agregar una tabla. Para la tabla seguí el siguiente steps list: Servers > Databases > clientesdb > public > Tables. Una vez en Tables, click derecho Create > Table. Inicié con únicamente 3 valores, ID, nombre y correo, más adelante le agregué varias columnas más. ID es el que lleva primary key, entonces habilité el PK y dentro del Constraints tab, cambié el Identity de ALWAYS a BY DEFAULT, y setié incrementos de 1 con start 1.

**DB Table**
<img width="896" height="471" alt="image" src="https://github.com/user-attachments/assets/3de227c9-af47-4156-9085-c761f3f44891" />

A continuación, configuré Kafka, creé main.py, producer.py, consumer.py y el UI (html, css y js). La API respondió sin problema desde http://localhost:8000/clientes, sin embargo el UI (http://localhost:8083/) me devolvió un error de CORS. Este ocurre cuando un navegador bloquea una solicitud HTTP a un dominio diferente por motivos de seguridad y es una restricción propia del navegador, en mi caso, http://localhost:8000/clientes != http://localhost:8083 y por tanto detecta un conflicto de origen. Para arreglarlo, habilité cross-origin requests desde main.py.

**CORS error handling**
<img width="553" height="265" alt="CORS error" src="https://github.com/user-attachments/assets/7a8ea4f4-f762-469d-95b6-c98aea17c200" />
<img width="411" height="244" alt="image" src="https://github.com/user-attachments/assets/8ceacb80-fed0-489c-a2b6-d0b261c70d6c" />

La primer mejora que le quería implementar al proyecto era permitir que el usuario pudiera agregar un cliente desde el UI, dejar que Kafka producer detectara el evento, creara el tópico, y que por último Kafka consumer actualizara la base de datos con el evento recibido. Para que funcionara necesitaba que la API pudiera leer desde la base de datos y enviarle eventos a producer.py. El problema era que el contenedor de producer hacía exit casi inmediatamente después de correr docker compose up. Ahora que producer no le estaba enviando data preescrita a consumer, ocupaba a los 2 siempre arriba y en "listening state". Producer debía escuchar a API y Consumer escuchar a Producer. Con eso en mente, reinventé la conexión a Kafka (con time sleep y retries) y ahora producer también depende de Kafka en el Docker Compose.

**Docker Logs**
<img width="1385" height="292" alt="image" src="https://github.com/user-attachments/assets/96fdea23-465c-44ab-bd3e-69dbf7db6764" />
<img width="1349" height="162" alt="image" src="https://github.com/user-attachments/assets/53f5204f-473e-40bc-ad4c-dd2f6861c5e9" />

*NOTA:* Kafka Consumer usa la modalidad "silently listening" a diferencia de producer quien se encuentra activamente enviando mensajes. Para acceder a los logs de consumer existe la opción de cambiar CMD a unbuffered mode desde el Dockerfile o bien agregarle el -f flag de follow al docker logs command para mostrar los logs en tiempo real.

Esto solucionó el auto-exit, pero estaba teniendo errores de backend cuando hacía un insert. Desde inspect, revisé los API responses, status codes y los logs de cada contenedor. Tras revisar más detenidamente los files, logré identificar y reinstalar las dependencias faltantes. Aproveché para agregar una función que permitiera editar y eliminar clientes, estas usan una lógica muy similar y básicamente el mismo recorrido (UI -> API -> Kafka Producer -> Kafka Consumer -> DB). Llegado a este punto edit y delete reflejaban de inmediato los cambios, pero agregar clientes tenía un delay significativo y para visualizarlo tenía que refrescar la ventana del navegador. Lo anterior ocurre porque las mutaciones de información (agregar, editar, eliminar) recorren un Kafka-based pipeline que usa procesamiento asíncrono, para contrarrestarlo, le agregué un delay directamente a la interfaz, suficiente para que el consumer pueda terminar de procesar el evento antes de que el UI pida actualizarse.

<img width="437" height="100" alt="image" src="https://github.com/user-attachments/assets/66741d51-dcbe-4144-9868-44938f42ef9d" />

El otro agregado está sugerido dentro del proyecto que es justamente incluir logs centralizados. Mi idea era poder visualizar los logs de Kafka en tiempo real desde la pantalla por medio de WebSockets sin necesidad de polling. En este sentido, La API actúa como puente, recibiendo los mensajes del consumidor para luego retransmitirlos. Para esto agregué 3 secciones importantes en main.py, una tipo LogEvents que usa BaseModel, otra para el WebSocket tanto la parte del endpoint como el broadcast function y un HTTP bridge que reciba los logs desde LogEvent y espere el broadcast_log.

**Centralized Logs**
<img width="358" height="259" alt="image" src="https://github.com/user-attachments/assets/b34c808c-0e55-42a6-b984-a126ee77fb04" />

Los cambios en el consumer y el UI fueron bastante más concretos. Consumer.py incluye la parte de reformatting para estandarizar los mensajes de salida, donde format_log define el estilo del formato y requests.post aplica el nuevo formato dentro de cada función. De aquí me moví para el index file, en el index metí un panel para los logs con su respectivo header y body, js por otra parte, contiene el EventListener que básicamente carga los logSockets y muestra el conection state del Websocket en los logs de la consola, así como los eventos de Kafka en el panel de mensajes, también mantiene un estado inicial de "No hay logs para mostrar" que se reemplaza dinámicamente apenas llega el primer mensaje. Para el diseño del UI, opté por algo simple, un fondo oscuro y white cards con botones azules y rojos. La sección "Agregar cliente" utiliza un formulario o form-card, que permite el input de cada pieza de información y llama a la función "crearCliente()", el display de los clientes es directamente un table-card, y tanto el mensaje de confirmación de "Eliminar cliente" como "Editar cliente" usan un modal para mantenerse ocultos y aparecer en pantalla de acuerdo al modal-action seleccionado.

**User Interface**
<img width="1763" height="855" alt="image" src="https://github.com/user-attachments/assets/083cec07-7d54-4136-b6c6-cddd19cbd961" />

Para mantener la información de los clientes almacenada en la base de datos, los servicios de postgres y pgadmin llevan adjuntos volúmenes persistentes. Como nota adicional, me gustaría agregar que el comando <docker compose down -v> no solo se trae abajo todos los servicios de la infraestructura sino que también vacía la información almacenada dentro los volúmenes. Para dar los servicios de baja con los volúmenes intactos el comando es <docker compose down> sin el -v flag.

<img width="313" height="59" alt="image" src="https://github.com/user-attachments/assets/cbae4c5d-a1bf-4c01-a468-a4814d333200" />

Uno de los problemas que tuve cuando reinicié los servicios fue que ahora era Kafka Consumer estaba entrando en "exit mode" con error "NoBrokerAvailable", parecía que se trataba de un problema de inicio y red donde Kafka estaba usando el mismo listener para la comunicación interna entre contenedores y el acceso externo desde el host, y aunque ya le había agregado listener mapping anteriormente, el producer y el consumer estaban iniciando antes de que el broker estuviera disponible. Hasta este momento mi Kafka listener era 9092, para corregirlo, agregué un segundo listener 29092 para el tráfico interno de Docker y dejé 9092 para el acceso externo. Para puertos secundarios lo convencional es usar 29092, 19092, 39092... Esto además de minimizar confusiones en el tráfico hace que los contenedores se comuniquen de forma segura dentro de la red de Docker y mantiene los accesos por separado. Luego de reconfigurar el listener mapping, también cambié el bootstrap server de mi producer y mi consumer de <bootstrap_servers="kafka:9092"> a <bootstrap_servers="kafka:29092">.

**Kafka Listener Mapping**
<img width="712" height="352" alt="image" src="https://github.com/user-attachments/assets/ed506068-30fd-4c89-963d-4c4bb5c366c3" />

El otro inconveniente fue propiamente el arranque de Kafka tras reinicios abruptos, ERROR Exiting Kafka due to fatal exception during startup, KeeperErrorCode = NodeExists. Los registros residuales y metadata temporal de Zookeeper impedían que Kafka pudiera registrar nuevamente el broker durante el start-up, la solución que encontré fue implementar políticas de reinicio <restart: unless-stopped> y healthcheks a Zookeeper, Kafka 
 y Postgres, y cambiar el depends on de los otros servicios a depends on: condition: service_healthy. Esto me garantiza una mayor estabilidad y mejor tolerancia ante fallos.

**Healthcheck and Restart Policy**
<img width="1452" height="206" alt="image" src="https://github.com/user-attachments/assets/a8ad861e-8ca6-4aa4-aa81-78733da9e368" />
<img width="539" height="134" alt="image" src="https://github.com/user-attachments/assets/cfb1b776-fc93-407b-8836-66ae4b0463ff" />


