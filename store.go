package main

import (
	"crypto/rand"
	"encoding/base64"
	"sync"
)

// ConnectionStatus represents the state of a connection.
type ConnectionStatus string

const (
	StatusPending ConnectionStatus = "Pending"
	StatusActive  ConnectionStatus = "Active"
)

// Connection represents a relationship between this server and a requester.
type Connection struct {
	ID          string
	RequesterID string
	Timestamp   string
	IntroText   string
	PublicKey   string
	Signature   string
	Status      ConnectionStatus
	AccessToken string
}

// ConnectionStore is a thread-safe in-memory storage for connections.
type ConnectionStore struct {
	mu          sync.RWMutex
	connections map[string]Connection
}

// NewConnectionStore initializes a new ConnectionStore.
func NewConnectionStore() *ConnectionStore {
	return &ConnectionStore{
		connections: make(map[string]Connection),
	}
}

// Save adds or updates a connection in the store.
func (s *ConnectionStore) Save(conn Connection) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.connections[conn.ID] = conn
}

// Get retrieves a connection by its ID.
func (s *ConnectionStore) Get(id string) (Connection, bool) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	conn, ok := s.connections[id]
	return conn, ok
}

// GenerateToken returns a secure random string (URL-safe base64).
func GenerateToken() (string, error) {
	b := make([]byte, 24) // 24 bytes becomes 32 chars in base64
	_, err := rand.Read(b)
	if err != nil {
		return "", err
	}
	return base64.RawURLEncoding.EncodeToString(b), nil
}
