import socket
import threading

class Server:
    def __init__(self, host, port):
        # Inicio puerto y host
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Crear socket TCP
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Reutilizar la dirección
        self.clients = {} # Clientes
        self.lock = threading.Lock() # Bloqueo para manejar el acceso a clientes

    def start(self):
        """Inicio servidor, y aceptar conexiones de clientes."""
        try:
            # Asignar servidor a la dirección y puerto especificados
            self.server_socket.bind((self.host, self.port))
            # Escuchar conexiones entrantes en el socket
            self.server_socket.listen(5)
            print(f"Servidor iniciado en {self.host}:{self.port}")
            print("Esperando clientes...")
            
            # Bucle infinito para aceptar conexiones de clientes
            while True:
                # Aceptar conexión de un cliente
                client_socket, addr = self.server_socket.accept()
                # Agregar cliente para manejarlo en un hilo separado
                client_thread = threading.Thread(target=self.handle_client, args=(client_socket, addr))
                # Convertir el hilo en un hilo daemon para que se cierre al cerrar el programa
                client_thread.daemon = True # Un hilo daemo es un hilo que se ejecuta en segundo plano y se cierra automáticamente cuando el programa principal termina.
                # Iniciar el hilo para manejar al cliente
                client_thread.start()
        except KeyboardInterrupt:
            print("El servidor se está apagando...")
        except Exception as e:
            print(f"Error: {str(e)}")
        finally:
            # Cerrar el socket del servidor al salir
            self.server_socket.close()
            print("Servidor cerrado")
    
    def handle_client(self, client_socket, addr):
        """Manejar la conexión de un cliente"""
        username = None
        try:
            # Solicitar nombre de usuario al cliente
            username_data = client_socket.recv(1024).decode('utf-8')
            username = username_data.strip()
            
            # Verificar si el nombre de usuario ya está en uso
            with self.lock:
                self.clients[username] = client_socket # Agregar cliente al diccionario de clientes
            
            # Anunciar a todos que un nuevo usuario se ha unido
            self.broadcast(f"--- {username} se ha unido al chat ---", sender=None)
            print(f"Nueva conexión desde {addr[0]}:{addr[1]} como {username}")
            
            # Espera mensajes del cliente
            while True:
                # Recibir datos del cliente
                data = client_socket.recv(1024).decode('utf-8')
                if not data:
                    # Si no se recibe datos, salir del bucle
                    break
                
                # Verificar si el cliente quiere salir
                if data.lower() == "exit":
                    break
                
                # Enviar el mensaje a todos los clientes conectados
                self.broadcast(f"{username}: {data}", sender=username)
                print(f"{username}: {data}")
        
        except ConnectionResetError:
            print(f"La conexión con {addr[0]}:{addr[1]} fue restablecida")
        except Exception as e:
            print(f"Error al manejar cliente {addr[0]}:{addr[1]}: {str(e)}")
        finally:
            # Cerrar la conexión del cliente
            if username and username in self.clients:
                with self.lock:
                    # Eliminar cliente del diccionario
                    self.clients.pop(username, None)
                # Anunciar que el usuario ha salido
                self.broadcast(f"--- {username} ha salido del chat ---", sender=None)
                print(f"{username} desconectado")
            
            try:
                # Cerrar el socket del cliente
                client_socket.close()
            except:
                # Ignorar errores al cerrar el socket
                pass
            
    def broadcast(self, message, sender=None):
        """Enviar mensaje a todos los clientes conectados"""
        with self.lock:
            # Usar lock para evitar modificaciones concurrentes al diccionario de clientes
            for username, client in list(self.clients.items()):
                # Evitar enviar el mensaje al remitente
                if username == sender:
                    continue
                
                try:
                    # Enviar el mensaje al cliente
                    client.send(message.encode('utf-8'))
                except:
                    # Si hay un error al enviar el mensaje, eliminar el cliente del diccionario en metodo handle_client
                    pass


if __name__ == "__main__":
    HOST = "127.0.0.1"  # localhost
    PORT = 9999
    
    # custom ip
    custom_host = input("Ingrese IP del servidor (deje en blanco para usar 127.0.0.1): ")
    if custom_host:
        HOST = custom_host
    
    # crear servidor
    server = Server(HOST, PORT)
    server.start()
