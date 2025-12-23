package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
)

// Config holds the server configuration.
type Config struct {
	Hostname string
}

// WellKnownResponse defines the structure for the /.well-known/htidp response.
type WellKnownResponse struct {
	ApiRoot string `json:"api_root"`
}

// Link defines the structure for HATEOAS links.
type Link struct {
	Rel     string   `json:"rel"`
	Href    string   `json:"href"`
	Methods []string `json:"methods,omitempty"`
}

// ApiRootResponse defines the structure for the /api/v1 response.
type ApiRootResponse struct {
	Links []Link `json:"links"`
}

// wellKnownHandler handles requests to /.well-known/htidp.
func wellKnownHandler(w http.ResponseWriter, r *http.Request, config *Config) {
	response := WellKnownResponse{
		ApiRoot: fmt.Sprintf("%s/api/v1", config.Hostname),
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// apiV1Handler handles requests to /api/v1.
func apiV1Handler(w http.ResponseWriter, r *http.Request, config *Config) {
	response := ApiRootResponse{
		Links: []Link{
			{
				Rel:  "self",
				Href: fmt.Sprintf("%s/api/v1", config.Hostname),
			},
			{
				Rel:     "https://htidp.org/rel/handshake",
				Href:    fmt.Sprintf("%s/api/v1/handshake", config.Hostname),
				Methods: []string{"POST"},
			},
		},
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

func main() {
	config := &Config{
		Hostname: "http://localhost:8080",
	}

	http.HandleFunc("/.well-known/htidp", func(w http.ResponseWriter, r *http.Request) {
		wellKnownHandler(w, r, config)
	})

	http.HandleFunc("/api/v1/", func(w http.ResponseWriter, r *http.Request) {
		apiV1Handler(w, r, config)
	})

	log.Println("Starting server on localhost:8080")
	if err := http.ListenAndServe(":8080", nil); err != nil {
		log.Fatalf("could not start server: %s\n", err)
	}
}
