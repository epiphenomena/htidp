package main

import (
	"bytes"
	"crypto/ed25519"
	"crypto/sha256"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

func TestHandshakeHandler(t *testing.T) {
	config := &Config{Hostname: "http://localhost:8080"}
	store := NewConnectionStore()

	// Generate keys for the requester (Bob)
	pubKey, privKey, err := ed25519.GenerateKey(nil)
	if err != nil {
		t.Fatalf("Failed to generate keys: %v", err)
	}

	pubKeyStr := FormatKey(pubKey)

	// Prepare payload data
	requesterID := "https://bob.org/profile"
	timestamp := "2025-12-09T10:00:00Z"
	introText := "Hi Alice, I'd like to connect."

	// Reconstruct message as server expects (Canonical JSON)
	payloadMap := map[string]string{
		"requester_id": requesterID,
		"timestamp":    timestamp,
		"intro_text":   introText,
		"public_key":   pubKeyStr,
	}
	var buf bytes.Buffer
	enc := json.NewEncoder(&buf)
	enc.SetEscapeHTML(false)
	enc.Encode(payloadMap)
	message := strings.TrimSuffix(buf.String(), "\n")

	// Sign the hash of the message
	hashed := sha256.Sum256([]byte(message))
	signatureBytes := ed25519.Sign(privKey, hashed[:])
	signatureStr := FormatKey(signatureBytes)

	// Test case 1: Valid request
	payload := map[string]string{
		"requester_id": requesterID,
		"timestamp":    timestamp,
		"intro_text":   introText,
		"public_key":   pubKeyStr,
		"signature":    signatureStr,
	}
	body, _ := json.Marshal(payload)
	req := httptest.NewRequest("POST", "/api/v1/handshake", bytes.NewBuffer(body))
	w := httptest.NewRecorder()

	handshakeHandler(w, req, config, store)

	resp := w.Result()
	if resp.StatusCode != http.StatusAccepted {
		t.Errorf("Expected status 202 Accepted, got %d. Body: %s", resp.StatusCode, w.Body.String())
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

	// Test case 2: Invalid signature
	badSigBytes := make([]byte, len(signatureBytes))
	copy(badSigBytes, signatureBytes)
	badSigBytes[0] ^= 0xFF // Flip bits

	payloadBad := map[string]string{
		"requester_id": requesterID,
		"timestamp":    timestamp,
		"intro_text":   introText,
		"public_key":   pubKeyStr,
		"signature":    FormatKey(badSigBytes),
	}
	bodyBad, _ := json.Marshal(payloadBad)
	reqBad := httptest.NewRequest("POST", "/api/v1/handshake", bytes.NewBuffer(bodyBad))
	wBad := httptest.NewRecorder()

	handshakeHandler(wBad, reqBad, config, store)

	if wBad.Result().StatusCode != http.StatusBadRequest {
		t.Errorf("Expected status 400 Bad Request for invalid signature, got %d", wBad.Result().StatusCode)
	}

	// Test case 3: Intro text too long
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