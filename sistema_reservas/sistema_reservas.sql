CREATE DATABASE sistema_reservas CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'sistema_reservas_user'@'localhost' IDENTIFIED BY 'masterpassword';
GRANT ALL PRIVILEGES ON sistema_reservas.* TO 'sistema_reservas_user'@'localhost';
FLUSH PRIVILEGES;