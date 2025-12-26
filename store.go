package main

import (
	"crypto/ed25519"
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

// ConnectionStore is a thread-safe in-memory storage for connections and server identity.
type ConnectionStore struct {
	mu              sync.RWMutex
	connections     map[string]Connection
	ServerPublicKey ed25519.PublicKey
	ServerPrivateKey ed25519.PrivateKey
}

// NewConnectionStore initializes a new ConnectionStore and generates server keys.
func NewConnectionStore() *ConnectionStore {
	pub, priv, err := ed25519.GenerateKey(nil)
	if err != nil {
		// In a real app, we might handle this better, but panic is acceptable for startup failure here
		panic("failed to generate server keys: " + err.Error())
	}

	return &ConnectionStore{
		connections:      make(map[string]Connection),
		ServerPublicKey:  pub,
		ServerPrivateKey: priv,
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

// ListPending returns all connections with status Pending.
func (s *ConnectionStore) ListPending() []Connection {
	s.mu.RLock()
	defer s.mu.RUnlock()
	var pending []Connection
	for _, conn := range s.connections {
		if conn.Status == StatusPending {
			pending = append(pending, conn)
		}
	}
	return pending
}

// GetByToken retrieves a connection by its access token.
func (s *ConnectionStore) GetByToken(token string) (Connection, bool) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	for _, conn := range s.connections {
		if conn.AccessToken == token {
			return conn, true
		}
	}
	return Connection{}, false
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
