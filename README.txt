Guía de Instalación y Ejecución del Proyecto de Gestión de Pagos

Requisitos Previos (Instalar solo una vez)
Antes de empezar, asegúrate de tener instalado lo siguiente en tu computadora. Si ya lo tienes, puedes saltar esta sección.

Python:

Descárgalo desde python.org.

MUY IMPORTANTE: Durante la instalación, asegúrate de marcar la casilla que dice "Add Python to PATH".

Node.js:

Descárgalo desde nodejs.org. Esto instalará Node.js y npm.

Visual Studio Code:

Descárgalo desde code.visualstudio.com.

Paso 1: Configurar el Proyecto (Se hace solo la primera vez)
Descomprime la carpeta del proyecto que te enviaron.

Abre VS Code y ve a File > Open Folder... para abrir la carpeta completa del proyecto (sistema-pagos).

Abre una terminal en VS Code (View > Terminal o Ctrl + Ñ).

Configurar el Backend (Python):

En la terminal, navega a la carpeta del backend:

cd backend

Crea el entorno virtual y activa las librerías. Escribe estos tres comandos, uno por uno:

python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt

Configurar el Frontend (React):

Haz clic en el icono + en la terminal para abrir una segunda terminal.

En esta nueva terminal, navega a la carpeta del frontend:

cd frontend

Instala todas las dependencias de React. Este comando puede tardar unos minutos:

npm install

¡La configuración está lista! No necesitas volver a hacer estos pasos.

Paso 2: Iniciar la Aplicación (Cada vez que quieras usarla)
Para ejecutar el proyecto, necesitas tener dos terminales abiertas en VS Code.

Iniciar el Backend:

En la primera terminal, asegúrate de estar en la carpeta backend.

Activa el entorno virtual:

.\venv\Scripts\activate

Inicia el servidor de Python:

flask run

Deja esta terminal corriendo.

Iniciar el Frontend:

En la segunda terminal, asegúrate de estar en la carpeta frontend.

Inicia el servidor de React:

npm start

Esto debería abrir automáticamente una pestaña en tu navegador. Si no lo hace, abre tu navegador y ve a la siguiente dirección: http://localhost:3000

Para detener la aplicación, simplemente ve a cada terminal y presiona Ctrl + C.