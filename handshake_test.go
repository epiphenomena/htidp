package main

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

func TestHandshakeHandler(t *testing.T) {
	config := &Config{Hostname: "http://localhost:8080"}
	store := NewConnectionStore()

	// Test case 1: Valid request
	payload := map[string]string{
		"requester_id": "https://bob.org/profile",
		"timestamp":    "2025-12-09T10:00:00Z",
		"intro_text":   "Hi Alice, I'd like to connect.",
		"public_key":   "Ed25519;base64;dummy",
		"signature":    "Ed25519;base64;dummy",
	}
	body, _ := json.Marshal(payload)
	req := httptest.NewRequest("POST", "/api/v1/handshake", bytes.NewBuffer(body))
	w := httptest.NewRecorder()

	handshakeHandler(w, req, config, store)

	resp := w.Result()
	if resp.StatusCode != http.StatusAccepted {
		t.Errorf("Expected status 202 Accepted, got %d", resp.StatusCode)
	}

	var respBody HandshakeResponsePending
	if err := json.NewDecoder(resp.Body).Decode(&respBody); err != nil {
		t.Fatalf("Failed to decode response: %v", err)
	}

	if respBody.Status != "pending" {
		t.Errorf("Expected status 'pending', got '%s'", respBody.Status)
	}
	if respBody.Token != nil {
		t.Errorf("Expected token to be nil, got %v", respBody.Token)
	}
	if len(respBody.Links) == 0 {
		t.Error("Expected links in response")
	}

	// Verify store
	// We don't have direct access to the ID generated inside the handler to check the store directly by key,
	// but we can check if count is 1 or iterate.
	// Since store.connections is unexported map, we can't iterate it from test easily unless we export a Len() method or similar, 
	// or use reflection, or just rely on the fact that we got a success response and the code calls Save.
	// Wait, Store methods are exported. Get(id) is exported.
	// We can extract ID from the link in response.
	// Response link href: "http://localhost:8080/handshakes/<ID>"
	href := respBody.Links[0].Href
	parts := strings.Split(href, "/")
	id := parts[len(parts)-1]

	conn, ok := store.Get(id)
	if !ok {
		t.Errorf("Connection not found in store with ID %s", id)
	}
	if conn.RequesterID != payload["requester_id"] {
		t.Errorf("Expected RequesterID %s, got %s", payload["requester_id"], conn.RequesterID)
	}

	// Test case 2: Intro text too long
	longIntro := strings.Repeat("a", 281)
	payloadInvalid := map[string]string{
		"requester_id": "https://bob.org/profile",
		"intro_text":   longIntro,
	}
	bodyInvalid, _ := json.Marshal(payloadInvalid)
	reqInvalid := httptest.NewRequest("POST", "/api/v1/handshake", bytes.NewBuffer(bodyInvalid))
	wInvalid := httptest.NewRecorder()

	handshakeHandler(wInvalid, reqInvalid, config, store)

	if wInvalid.Result().StatusCode != http.StatusBadRequest {
		t.Errorf("Expected status 400 Bad Request for long intro text, got %d", wInvalid.Result().StatusCode)
	}
}
