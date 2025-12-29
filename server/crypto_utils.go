package main

import (
	"crypto/ed25519"
	"crypto/sha256"
	"encoding/base64"
	"errors"
	"strings"
)

// ParseKey extracts the base64 part from "Ed25519;base64;<data>"
func ParseKey(input string) ([]byte, error) {
	parts := strings.Split(input, ";")
	if len(parts) != 3 {
		return nil, errors.New("invalid format: expected 'Ed25519;base64;<data>'")
	}
	if parts[0] != "Ed25519" || parts[1] != "base64" {
		return nil, errors.New("unsupported algorithm or encoding")
	}
	return base64.StdEncoding.DecodeString(parts[2])
}

// FormatKey formats the key as "Ed25519;base64;<data>"
func FormatKey(data []byte) string {
	return "Ed25519;base64;" + base64.StdEncoding.EncodeToString(data)
}

// VerifySignature verifies the Ed25519 signature.
// It assumes the signature was created on the SHA256 hash of the message.
func VerifySignature(pubKeyStr, message, signatureStr string) error {
	pubKeyBytes, err := ParseKey(pubKeyStr)
	if err != nil {
		return err
	}
	if len(pubKeyBytes) != ed25519.PublicKeySize {
		return errors.New("invalid public key size")
	}

	sigBytes, err := ParseKey(signatureStr)
	if err != nil {
		return err
	}

	hashed := sha256.Sum256([]byte(message))

	if !ed25519.Verify(pubKeyBytes, hashed[:], sigBytes) {
		return errors.New("signature verification failed")
	}
	return nil
}
