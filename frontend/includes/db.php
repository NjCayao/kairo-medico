<?php

/**
 * Clase Database - Conexión y operaciones BD
 */

class Database
{
    private $conn;
    private $host;
    private $user;
    private $pass;
    private $dbname;
    private $port;

    public function __construct()
    {
        $this->host = DB_HOST;
        $this->user = DB_USER;
        $this->pass = DB_PASS;
        $this->dbname = DB_NAME;
        $this->port = DB_PORT;
    }

    /**
     * Conectar a la base de datos
     */
    public function connect()
    {
        $this->conn = null;

        try {
            $dsn = "mysql:host={$this->host};port={$this->port};dbname={$this->dbname};charset=utf8mb4";

            $this->conn = new PDO($dsn, $this->user, $this->pass);
            $this->conn->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
            $this->conn->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);
        } catch (PDOException $e) {
            die("Error de conexión: " . $e->getMessage());
        }

        return $this->conn;
    }

    /**
     * Ejecutar query SELECT
     */
    public function query($sql, $params = [])
    {
        try {
            $stmt = $this->conn->prepare($sql);
            $stmt->execute($params);
            return $stmt->fetchAll();
        } catch (PDOException $e) {
            error_log("Error query: " . $e->getMessage());
            return []; 
        }
    }

    /**
     * Ejecutar INSERT/UPDATE/DELETE
     */
    public function execute($sql, $params = [])
    {
        try {
            $stmt = $this->conn->prepare($sql);
            return $stmt->execute($params);
        } catch (PDOException $e) {
            error_log("Error execute: " . $e->getMessage());
            return false;
        }
    }

    /**
     * Obtener último ID insertado
     */
    public function lastInsertId()
    {
        return $this->conn->lastInsertId();
    }

    /**
     * Contar filas
     */
    public function count($sql, $params = [])
    {
        try {
            $stmt = $this->conn->prepare($sql);
            $stmt->execute($params);
            return $stmt->rowCount();
        } catch (PDOException $e) {
            return 0;
        }
    }
}
