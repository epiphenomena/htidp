package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestOrganizationMode_Enabled(t *testing.T) {
	config := &Config{
		Hostname:       "http://test.host",
		IsOrganization: true,
	}

	// Test /api/v1 for directory link
	req, _ := http.NewRequest("GET", "/api/v1", nil)
	rr := httptest.NewRecorder()
	
	// We need to wrap apiV1Handler to pass config
	handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		apiV1Handler(w, r, config)
	})
	
	handler.ServeHTTP(rr, req)

	if status := rr.Code; status != http.StatusOK {
		t.Errorf("handler returned wrong status code: got %v want %v",
			status, http.StatusOK)
	}

	var rootResp ApiRootResponse
	if err := json.NewDecoder(rr.Body).Decode(&rootResp); err != nil {
		t.Errorf("failed to decode response: %v", err)
	}

	found := false
	for _, link := range rootResp.Links {
		if link.Rel == "https://htidp.org/rel/directory" {
			found = true
			if link.Href != "http://test.host/api/v1/directory" {
				t.Errorf("unexpected href: got %v want %v", link.Href, "http://test.host/api/v1/directory")
			}
		}
	}

	if !found {
		t.Error("directory link not found in organization mode")
	}

	// Test /api/v1/directory
	reqDir, _ := http.NewRequest("GET", "/api/v1/directory", nil)
	rrDir := httptest.NewRecorder()

	handlerDir := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		directoryHandler(w, r, config)
	})

	handlerDir.ServeHTTP(rrDir, reqDir)

	if status := rrDir.Code; status != http.StatusOK {
		t.Errorf("directory handler returned wrong status code: got %v want %v",
			status, http.StatusOK)
	}

	var departments []Department
	if err := json.NewDecoder(rrDir.Body).Decode(&departments); err != nil {
		t.Errorf("failed to decode departments: %v", err)
	}

	if len(departments) == 0 {
		t.Error("expected departments, got none")
	}
}

func TestOrganizationMode_Disabled(t *testing.T) {
	config := &Config{
		Hostname:       "http://test.host",
		IsOrganization: false,
	}

	req, _ := http.NewRequest("GET", "/api/v1", nil)
	rr := httptest.NewRecorder()

	handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		apiV1Handler(w, r, config)
	})

	handler.ServeHTTP(rr, req)

	var rootResp ApiRootResponse
	json.NewDecoder(rr.Body).Decode(&rootResp)

	for _, link := range rootResp.Links {
		if link.Rel == "https://htidp.org/rel/directory" {
			t.Error("found directory link when organization mode is disabled")
		}
	}
}
