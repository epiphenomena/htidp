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

// HandshakeRequest defines the payload for a handshake request.
type HandshakeRequest struct {
	RequesterID string `json:"requester_id"`
	Timestamp   string `json:"timestamp"`
	IntroText   string `json:"intro_text"`
	PublicKey   string `json:"public_key"`
	Signature   string `json:"signature"`
}

// HandshakeResponsePending defines the response for a pending handshake.
type HandshakeResponsePending struct {
	Status string  `json:"status"`
	Token  *string `json:"token"`
	Links  []Link  `json:"links"`
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
	// If the request path is exactly /api/v1 or /api/v1/, serve the root.
	// Otherwise, it might be a sub-resource handled elsewhere (though http.HandleFunc handles prefix matching, 
	// specific matches should take precedence or we need to check path here if we use one handler for prefix).
	// Since we register /api/v1/handshake separately, this handler catches others.
	// Ideally, exact match for root resource.
	if r.URL.Path != "/api/v1" && r.URL.Path != "/api/v1/" {
		http.NotFound(w, r)
		return
	}

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

// handshakeHandler handles POST requests to /api/v1/handshake.
func handshakeHandler(w http.ResponseWriter, r *http.Request, config *Config, store *ConnectionStore) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req HandshakeRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	// Validate intro_text length
	if len(req.IntroText) >= 280 {
		http.Error(w, "intro_text must be less than 280 characters", http.StatusBadRequest)
		return
	}

	// TODO: Verify signature.
	// Crucial: Ignore the signature verification for this step.

	// Save the request to the store with status Pending.
	// We generate a unique ID for the handshake.
	connID, err := GenerateToken()
	if err != nil {
		http.Error(w, "Internal server error", http.StatusInternalServerError)
		return
	}

	conn := Connection{
		ID:          connID,
		RequesterID: req.RequesterID,
		Timestamp:   req.Timestamp,
		IntroText:   req.IntroText,
		PublicKey:   req.PublicKey,
		Signature:   req.Signature,
		Status:      StatusPending,
	}
	store.Save(conn)

	response := HandshakeResponsePending{
		Status: "pending",
		Token:  nil,
		Links: []Link{
			{
				Rel:  "self",
				Href: fmt.Sprintf("%s/handshakes/%s", config.Hostname, connID), // Example in schema says /handshakes/12345. Assuming root relative or api relative? Schema example: "https://alice.com/handshakes/12345". I will stick to schema example structure.
			},
		},
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusAccepted)
	json.NewEncoder(w).Encode(response)
}

func main() {
	config := &Config{
		Hostname: "http://localhost:8080",
	}
	store := NewConnectionStore()

	http.HandleFunc("/.well-known/htidp", func(w http.ResponseWriter, r *http.Request) {
		wellKnownHandler(w, r, config)
	})

	// Register specific handler for handshake first (longest match usually wins in some routers, but ServeMux matches patterns)
	// In ServeMux, "/api/v1/" matches everything under it.
	// We need to be careful. If we register "/api/v1/handshake", it takes precedence over "/api/v1/".
	http.HandleFunc("/api/v1/handshake", func(w http.ResponseWriter, r *http.Request) {
		handshakeHandler(w, r, config, store)
	})

	http.HandleFunc("/api/v1/", func(w http.ResponseWriter, r *http.Request) {
		apiV1Handler(w, r, config)
	})

	// Also map /handshakes/ for the check_status link if we want it to work (though not strictly required by this task, good to have placeholders or just let it 404 for now).
	// The prompt only asks to implement the POST [handshake_url].

	log.Println("Starting server on localhost:8080")
	if err := http.ListenAndServe(":8080", nil); err != nil {
		log.Fatalf("could not start server: %s\n", err)
	}
}