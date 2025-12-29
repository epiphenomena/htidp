package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"strings"
)

// Config holds the server configuration.
type Config struct {
	Hostname       string
	IsOrganization bool
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

// HandshakeResponseAccepted defines the response for an accepted handshake.
type HandshakeResponseAccepted struct {
	Status string `json:"status"`
	Token  string `json:"token"`
	Links  []Link `json:"links"`
}

// wellKnownHandler handles requests to /.well-known/htidp.
func wellKnownHandler(w http.ResponseWriter, r *http.Request, config *Config) {
	response := WellKnownResponse{
		ApiRoot: fmt.Sprintf("%s/api/v1", config.Hostname),
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// identityHandler returns the public identity of the server owner.
func identityHandler(w http.ResponseWriter, r *http.Request) {
	log.Printf("GET /api/v1/identity")
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	identity := map[string]string{
		"https://htidp.org/core/vcard#fn":    "Alice Smith",
		"https://htidp.org/core/vcard#photo": "https://alice.com/photos/profile.jpg",
		"https://htidp.org/core/vcard#note":  "Building decentralized identity systems.",
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(identity)
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

	links := []Link{
		{
			Rel:  "self",
			Href: fmt.Sprintf("%s/api/v1", config.Hostname),
		},
		{
			Rel:     "identity",
			Href:    fmt.Sprintf("%s/api/v1/identity", config.Hostname),
			Methods: []string{"GET"},
		},
		{
			Rel:     "handshake",
			Href:    fmt.Sprintf("%s/api/v1/handshake", config.Hostname),
			Methods: []string{"POST"},
		},
	}

	if config.IsOrganization {
		links = append(links, Link{
			Rel:     "https://htidp.org/rel/directory",
			Href:    fmt.Sprintf("%s/api/v1/directory", config.Hostname),
			Methods: []string{"GET"},
		})
	}

	response := ApiRootResponse{
		Links: links,
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

	// Reconstruct the signed message (Canonical JSON)
	// We must match the client's canonicalization (sorted keys, no whitespace, no HTML escaping)
	payload := map[string]string{
		"requester_id": req.RequesterID,
		"timestamp":    req.Timestamp,
		"intro_text":   req.IntroText,
		"public_key":   req.PublicKey,
	}

	var buf bytes.Buffer
	enc := json.NewEncoder(&buf)
	enc.SetEscapeHTML(false)
	if err := enc.Encode(payload); err != nil {
		http.Error(w, "Error reconstructing message", http.StatusInternalServerError)
		return
	}
	// json.Encoder.Encode appends a newline. JSON.stringify does not.
	// We trim the trailing newline.
	message := strings.TrimSuffix(buf.String(), "\n")

	// Verify signature
	if err := VerifySignature(req.PublicKey, message, req.Signature); err != nil {
		http.Error(w, "Invalid signature: "+err.Error(), http.StatusBadRequest)
		return
	}

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

// adminRequestsHandler lists pending connections.
func adminRequestsHandler(w http.ResponseWriter, r *http.Request, store *ConnectionStore) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	pending := store.ListPending()
	if pending == nil {
		pending = []Connection{}
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(pending)
}

// adminApproveHandler approves a connection request.
func adminApproveHandler(w http.ResponseWriter, r *http.Request, store *ConnectionStore) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Extract ID from path /admin/approve/{id}
	parts := strings.Split(r.URL.Path, "/")
	if len(parts) < 4 {
		http.Error(w, "Invalid ID", http.StatusBadRequest)
		return
	}
	id := parts[3]

	conn, ok := store.Get(id)
	if !ok {
		http.Error(w, "Connection not found", http.StatusNotFound)
		return
	}

	if conn.Status != StatusPending {
		http.Error(w, "Connection is not pending", http.StatusBadRequest)
		return
	}

	token, err := GenerateToken()
	if err != nil {
		http.Error(w, "Internal server error", http.StatusInternalServerError)
		return
	}

	conn.Status = StatusActive
	conn.AccessToken = token
	store.Save(conn)

	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]string{"status": "approved", "access_token": token})
}

// handshakeStatusHandler handles polling of the handshake status.
func handshakeStatusHandler(w http.ResponseWriter, r *http.Request, config *Config, store *ConnectionStore) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Extract ID from path /handshakes/{id}
	parts := strings.Split(r.URL.Path, "/")
	if len(parts) < 3 {
		http.Error(w, "Invalid ID", http.StatusBadRequest)
		return
	}
	id := parts[2]

	conn, ok := store.Get(id)
	if !ok {
		http.Error(w, "Connection not found", http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")

	if conn.Status == StatusActive {
		response := HandshakeResponseAccepted{
			Status: "accepted",
			Token:  conn.AccessToken,
			Links: []Link{
				{
					Rel:  "profile",
					Href: fmt.Sprintf("%s/api/me", config.Hostname),
				},
			},
		}
		json.NewEncoder(w).Encode(response)
	} else {
		response := HandshakeResponsePending{
			Status: "pending",
			Token:  nil,
			Links: []Link{
				{
					Rel:  "self",
					Href: fmt.Sprintf("%s/handshakes/%s", config.Hostname, conn.ID),
				},
			},
		}
		json.NewEncoder(w).Encode(response)
	}
}

// DelegateRequest defines the payload for creating a delegated token.
type DelegateRequest struct {
	ParentToken string `json:"parent_token"`
	EmployeeID  string `json:"employee_id"`
}

// delegateHandler handles the creation of delegated tokens.
func delegateHandler(w http.ResponseWriter, r *http.Request, store *ConnectionStore) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req DelegateRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	// Validate parent token
	_, ok := store.GetByToken(req.ParentToken)
	if !ok {
		http.Error(w, "Invalid parent token", http.StatusBadRequest)
		return
	}

	// Generate child token
	childToken, err := GenerateToken()
	if err != nil {
		http.Error(w, "Internal server error", http.StatusInternalServerError)
		return
	}

	// Create new connection for the delegate
	connID, err := GenerateToken()
	if err != nil {
		http.Error(w, "Internal server error", http.StatusInternalServerError)
		return
	}

	delegateConn := Connection{
		ID:          connID,
		RequesterID: req.EmployeeID,
		IntroText:   "Delegated Access",
		Status:      StatusActive,
		AccessToken: childToken,
		LinkedTo:    req.ParentToken,
	}

	store.Save(delegateConn)

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{
		"child_token": childToken,
		"linked_to":   req.ParentToken,
	})
}

// RequireToken is a middleware that checks for a valid Bearer token.
func RequireToken(next http.HandlerFunc, store *ConnectionStore) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		authHeader := r.Header.Get("Authorization")
		if authHeader == "" {
			http.Error(w, "Missing Authorization header", http.StatusUnauthorized)
			return
		}

		parts := strings.Split(authHeader, " ")
		if len(parts) != 2 || parts[0] != "Bearer" {
			http.Error(w, "Invalid Authorization header format", http.StatusUnauthorized)
			return
		}

		token := parts[1]
		conn, ok := store.GetByToken(token)
		if !ok {
			http.Error(w, "Invalid token", http.StatusUnauthorized)
			return
		}

		if conn.LinkedTo != "" {
			parentConn, parentOk := store.GetByToken(conn.LinkedTo)
			parentID := "Unknown"
			if parentOk {
				parentID = parentConn.RequesterID
			}
			log.Printf("Access Delegated by [%s]", parentID)
		}

		next(w, r)
	}
}

// meHandler handles requests to /api/me.
func meHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	identity := map[string]string{
		"https://htidp.org/core/vcard#fn":    "Alice Smith",
		"https://htidp.org/core/vcard#photo": "https://alice.com/photos/profile.jpg",
		"https://htidp.org/core/vcard#note":  "Building decentralized identity systems.",
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(identity)
}

// Department represents an organizational unit.
type Department struct {
	Name        string `json:"name"`
	IdentityURL string `json:"identity_url"`
}

// directoryHandler handles requests to /api/v1/directory.
func directoryHandler(w http.ResponseWriter, r *http.Request, config *Config) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Hardcoded departments for demonstration
	departments := []Department{
		{
			Name:        "Engineering",
			IdentityURL: fmt.Sprintf("%s/api/departments/engineering", config.Hostname),
		},
		{
			Name:        "HR",
			IdentityURL: fmt.Sprintf("%s/api/departments/hr", config.Hostname),
		},
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(departments)
}

// adminActiveHandler lists active connections.
func adminActiveHandler(w http.ResponseWriter, r *http.Request, store *ConnectionStore) {
	log.Printf("GET /admin/active")
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	active := store.ListActive()
	if active == nil {
		active = []Connection{}
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(active)
}

// CORS is a simple middleware to allow cross-origin requests.
func CORS(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")
		if r.Method == "OPTIONS" {
			w.WriteHeader(http.StatusOK)
			return
		}
		next.ServeHTTP(w, r)
	})
}

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}
	
	hostname := os.Getenv("HOSTNAME")
	if hostname == "" {
		hostname = "http://localhost:" + port
	}

	isOrg := os.Getenv("IS_ORGANIZATION") == "true"

	config := &Config{
		Hostname:       hostname,
		IsOrganization: isOrg,
	}
	store := NewConnectionStore()

	http.HandleFunc("/.well-known/htidp", func(w http.ResponseWriter, r *http.Request) {
		wellKnownHandler(w, r, config)
	})

	// Register specific handler for handshake first
	http.HandleFunc("/api/v1/handshake", func(w http.ResponseWriter, r *http.Request) {
		handshakeHandler(w, r, config, store)
	})

	http.HandleFunc("/api/v1/identity", func(w http.ResponseWriter, r *http.Request) {
		identityHandler(w, r)
	})

	http.HandleFunc("/api/v1/directory", func(w http.ResponseWriter, r *http.Request) {
		directoryHandler(w, r, config)
	})

	http.HandleFunc("/admin/requests", func(w http.ResponseWriter, r *http.Request) {
		adminRequestsHandler(w, r, store)
	})

	http.HandleFunc("/admin/active", func(w http.ResponseWriter, r *http.Request) {
		adminActiveHandler(w, r, store)
	})

	http.HandleFunc("/admin/approve/", func(w http.ResponseWriter, r *http.Request) {
		adminApproveHandler(w, r, store)
	})

	http.HandleFunc("/api/delegate", func(w http.ResponseWriter, r *http.Request) {
		delegateHandler(w, r, store)
	})

	http.HandleFunc("/handshakes/", func(w http.ResponseWriter, r *http.Request) {
		handshakeStatusHandler(w, r, config, store)
	})

	http.HandleFunc("/api/me", RequireToken(meHandler, store))

	http.HandleFunc("/api/v1/", func(w http.ResponseWriter, r *http.Request) {
		apiV1Handler(w, r, config)
	})

	log.Printf("Starting server on port %s\n", port)
	if err := http.ListenAndServe(":"+port, CORS(http.DefaultServeMux)); err != nil {
		log.Fatalf("could not start server: %s\n", err)
	}
}