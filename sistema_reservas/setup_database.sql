CREATE DATABASE IF NOT EXISTS sistema_reservas;
CREATE USER IF NOT EXISTS 'sistema_reservas_user'@'localhost' IDENTIFIED BY 'masterpassword123';
GRANT ALL PRIVILEGES ON sistema_reservas.* TO 'sistema_reservas_user'@'localhost';
FLUSH PRIVILEGES;
