package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestApiMe_NoToken(t *testing.T) {
	store := NewConnectionStore()
	handler := RequireToken(meHandler, store)

	req, _ := http.NewRequest("GET", "/api/me", nil)
	rr := httptest.NewRecorder()

	handler.ServeHTTP(rr, req)

	if status := rr.Code; status != http.StatusUnauthorized {
		t.Errorf("handler returned wrong status code: got %v want %v",
			status, http.StatusUnauthorized)
	}
}

func TestApiMe_InvalidToken(t *testing.T) {
	store := NewConnectionStore()
	handler := RequireToken(meHandler, store)

	req, _ := http.NewRequest("GET", "/api/me", nil)
	req.Header.Set("Authorization", "Bearer invalid-token")
	rr := httptest.NewRecorder()

	handler.ServeHTTP(rr, req)

	if status := rr.Code; status != http.StatusUnauthorized {
		t.Errorf("handler returned wrong status code: got %v want %v",
			status, http.StatusUnauthorized)
	}
}

func TestApiMe_ValidToken(t *testing.T) {
	store := NewConnectionStore()
	token := "valid-token-123"
	
	// manually add a connection with a token
	store.Save(Connection{
		ID:          "conn-1",
		AccessToken: token,
		Status:      StatusActive,
	})

	handler := RequireToken(meHandler, store)

	req, _ := http.NewRequest("GET", "/api/me", nil)
	req.Header.Set("Authorization", "Bearer "+token)
	rr := httptest.NewRecorder()

	handler.ServeHTTP(rr, req)

	if status := rr.Code; status != http.StatusOK {
		t.Errorf("handler returned wrong status code: got %v want %v",
			status, http.StatusOK)
	}

	var response map[string]string
	if err := json.NewDecoder(rr.Body).Decode(&response); err != nil {
		t.Errorf("failed to decode response: %v", err)
	}

	expectedName := "Alice Smith"
	if response["https://htidp.org/core/vcard#fn"] != expectedName {
		t.Errorf("handler returned unexpected name: got %v want %v",
			response["https://htidp.org/core/vcard#fn"], expectedName)
	}
}
