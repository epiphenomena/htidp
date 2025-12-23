package main

import (
	"sync"
	"testing"
)

func TestConnectionStore(t *testing.T) {
	store := NewConnectionStore()
	connID := "test-id"
	conn := Connection{
		ID:           connID,
		RequesterID:  "https://example.com",
		Status:       StatusPending,
	}

	// Test Save
	store.Save(conn)

	// Test Get
	retrieved, ok := store.Get(connID)
	if !ok {
		t.Fatalf("expected connection to be found")
	}
	if retrieved.ID != conn.ID {
		t.Errorf("expected ID %s, got %s", conn.ID, retrieved.ID)
	}

	// Test Concurrent Access
	var wg sync.WaitGroup
	for i := 0; i < 100; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			store.Save(conn)
			store.Get(connID)
		}()
	}
	wg.Wait()
}

func TestGenerateToken(t *testing.T) {
	token, err := GenerateToken()
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(token) == 0 {
		t.Error("expected token to be non-empty")
	}
	// Check length for 24 bytes input (should be 32 chars base64)
	if len(token) != 32 {
		t.Errorf("expected token length 32, got %d", len(token))
	}
}
