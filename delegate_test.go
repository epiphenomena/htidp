package main

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestDelegatedAccess(t *testing.T) {
	store := NewConnectionStore()
	parentToken := "parent-token-123"
	parentID := "https://bob.org/profile"

	// 1. Setup Parent Connection
	store.Save(Connection{
		ID:          "conn-parent",
		RequesterID: parentID,
		AccessToken: parentToken,
		Status:      StatusActive,
	})

	// 2. Request Delegate Token
	delegateReqPayload := map[string]string{
		"parent_token": parentToken,
		"employee_id":  "employee-456",
	}
	body, _ := json.Marshal(delegateReqPayload)
	reqDelegate, _ := http.NewRequest("POST", "/api/delegate", bytes.NewBuffer(body))
	rrDelegate := httptest.NewRecorder()

	// Use the handler directly
	delegateHandler(rrDelegate, reqDelegate, store)

	if status := rrDelegate.Code; status != http.StatusOK {
		t.Fatalf("delegateHandler returned wrong status code: got %v want %v",
			status, http.StatusOK)
	}

	var delegateResp map[string]string
	if err := json.NewDecoder(rrDelegate.Body).Decode(&delegateResp); err != nil {
		t.Fatalf("failed to decode delegate response: %v", err)
	}

	childToken := delegateResp["child_token"]
	if childToken == "" {
		t.Fatal("child_token is empty")
	}
	if delegateResp["linked_to"] != parentToken {
		t.Errorf("linked_to mismatch: got %v want %v", delegateResp["linked_to"], parentToken)
	}

	// 3. Access Protected Resource with Child Token
	handlerMe := RequireToken(meHandler, store)
	reqMe, _ := http.NewRequest("GET", "/api/me", nil)
	reqMe.Header.Set("Authorization", "Bearer "+childToken)
	rrMe := httptest.NewRecorder()

	handlerMe.ServeHTTP(rrMe, reqMe)

	if status := rrMe.Code; status != http.StatusOK {
		t.Errorf("meHandler with child token returned wrong status code: got %v want %v",
			status, http.StatusOK)
	}

	// 4. Verify LinkedTo logic in Store (Implementation Detail Check)
	childConn, ok := store.GetByToken(childToken)
	if !ok {
		t.Fatal("child connection not found in store")
	}
	if childConn.LinkedTo != parentToken {
		t.Errorf("child connection LinkedTo mismatch: got %v want %v", childConn.LinkedTo, parentToken)
	}
	
	// 5. Test with Invalid Parent Token
	invalidDelegateReqPayload := map[string]string{
		"parent_token": "invalid-token",
		"employee_id":  "employee-999",
	}
	bodyInvalid, _ := json.Marshal(invalidDelegateReqPayload)
	reqInvalid, _ := http.NewRequest("POST", "/api/delegate", bytes.NewBuffer(bodyInvalid))
	rrInvalid := httptest.NewRecorder()

	delegateHandler(rrInvalid, reqInvalid, store)

	if status := rrInvalid.Code; status != http.StatusBadRequest {
		t.Errorf("delegateHandler with invalid parent token returned wrong status code: got %v want %v",
			status, http.StatusBadRequest)
	}
}
