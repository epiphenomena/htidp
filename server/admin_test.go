package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestAdminApprovalFlow(t *testing.T) {
	config := &Config{Hostname: "http://localhost:8080"}
	store := NewConnectionStore()

	// 1. Create a pending request
	connID := "test-id-123"
	conn := Connection{
		ID:          connID,
		RequesterID: "https://bob.org/profile",
		Status:      StatusPending,
		IntroText:   "Hello",
	}
	store.Save(conn)

	// 2. List pending requests
	reqList := httptest.NewRequest("GET", "/admin/requests", nil)
	wList := httptest.NewRecorder()
	adminRequestsHandler(wList, reqList, store)

	if wList.Result().StatusCode != http.StatusOK {
		t.Errorf("Expected status 200 OK for list requests, got %d", wList.Result().StatusCode)
	}

	var list []Connection
	if err := json.NewDecoder(wList.Body).Decode(&list); err != nil {
		t.Fatalf("Failed to decode list response: %v", err)
	}
	if len(list) != 1 {
		t.Errorf("Expected 1 pending request, got %d", len(list))
	}
	if list[0].ID != connID {
		t.Errorf("Expected ID %s, got %s", connID, list[0].ID)
	}

	// 3. Approve the request
	reqApprove := httptest.NewRequest("POST", "/admin/approve/"+connID, nil)
	wApprove := httptest.NewRecorder()
	adminApproveHandler(wApprove, reqApprove, store)

	if wApprove.Result().StatusCode != http.StatusOK {
		t.Errorf("Expected status 200 OK for approve request, got %d", wApprove.Result().StatusCode)
	}

	var approveResp map[string]string
	if err := json.NewDecoder(wApprove.Body).Decode(&approveResp); err != nil {
		t.Fatalf("Failed to decode approve response: %v", err)
	}
	if approveResp["status"] != "approved" {
		t.Errorf("Expected status 'approved', got '%s'", approveResp["status"])
	}
	if approveResp["access_token"] == "" {
		t.Error("Expected access_token to be generated")
	}

	// 4. Verify status via handshake status endpoint
	reqStatus := httptest.NewRequest("GET", "/handshakes/"+connID, nil)
	wStatus := httptest.NewRecorder()
	handshakeStatusHandler(wStatus, reqStatus, config, store)

	if wStatus.Result().StatusCode != http.StatusOK {
		t.Errorf("Expected status 200 OK for status check, got %d", wStatus.Result().StatusCode)
	}

	var statusResp HandshakeResponseAccepted
	if err := json.NewDecoder(wStatus.Body).Decode(&statusResp); err != nil {
		t.Fatalf("Failed to decode status response: %v", err)
	}
	
	// Check if it looks like an accepted response
	if statusResp.Status != "accepted" {
		t.Errorf("Expected status 'accepted', got '%s'", statusResp.Status)
	}
	if statusResp.Token != approveResp["access_token"] {
		t.Errorf("Expected token %s, got %s", approveResp["access_token"], statusResp.Token)
	}
}
