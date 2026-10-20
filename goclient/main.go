package main

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"time"

	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"

	pb "didverifier/goclient/pb"
)

type sampleFile struct {
	Credentials struct {
		ValidEmployment struct {
			JWT string `json:"jwt"`
		} `json:"valid_employment"`
		ValidDegree struct {
			JWT string `json:"jwt"`
		} `json:"valid_degree"`
		TamperedEmployment struct {
			JWT string `json:"jwt"`
		} `json:"tampered_employment"`
		ExpiredBadge struct {
			JWT string `json:"jwt"`
		} `json:"expired_badge"`
	} `json:"credentials"`
}

func main() {
	addr := os.Getenv("DID_VERIFIER_GRPC_ADDR")
	if addr == "" {
		addr = "localhost:50051"
	}

	samples, err := loadSamples()
	if err != nil {
		fmt.Fprintf(os.Stderr, "load samples: %v\n", err)
		os.Exit(1)
	}

	fmt.Println("============================================================")
	fmt.Printf("Go client connecting to gRPC DidVerifier at %s\n", addr)
	fmt.Println("============================================================")

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	conn, err := grpc.NewClient(addr, grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		fmt.Fprintf(os.Stderr, "dial: %v\n", err)
		os.Exit(1)
	}
	defer conn.Close()

	client := pb.NewDidVerifierClient(conn)

	health, err := client.HealthCheck(ctx, &pb.HealthCheckRequest{})
	if err != nil {
		fmt.Fprintf(os.Stderr, "HealthCheck failed: %v\n", err)
		os.Exit(1)
	}
	fmt.Printf("[ok] HealthCheck: status=%s version=%s ts=%s\n", health.Status, health.Version, health.Timestamp)
	if health.Status != "SERVING" {
		fmt.Fprintf(os.Stderr, "expected status SERVING, got %s\n", health.Status)
		os.Exit(1)
	}

	if err := checkValid(ctx, client, "Valid Employment Credential", "EmploymentCredential", samples.Credentials.ValidEmployment.JWT); err != nil {
		fail(err)
	}
	if err := checkValid(ctx, client, "Valid University Degree Credential", "UniversityDegreeCredential", samples.Credentials.ValidDegree.JWT); err != nil {
		fail(err)
	}
	if err := checkTampered(ctx, client, samples.Credentials.TamperedEmployment.JWT); err != nil {
		fail(err)
	}
	if err := checkExpired(ctx, client, samples.Credentials.ExpiredBadge.JWT); err != nil {
		fail(err)
	}

	fmt.Println("============================================================")
	fmt.Println("ALL GO gRPC VERIFICATION CHECKS COMPLETED SUCCESSFULLY")
	fmt.Println("============================================================")
}

func checkValid(ctx context.Context, client pb.DidVerifierClient, label, credentialType, jwt string) error {
	fmt.Printf("\n--- %s ---\n", label)
	res, err := client.VerifyCredential(ctx, &pb.VerifyCredentialRequest{CredentialData: jwt})
	if err != nil {
		return fmt.Errorf("%s rpc: %w", label, err)
	}
	fmt.Printf("Valid: %v\nType: %s\nIssuer: %s\nHolder: %s\nRecord ID: %s\n", res.Valid, res.CredentialType, res.IssuerDid, res.HolderDid, res.RecordId)
	if !res.Valid {
		return fmt.Errorf("%s: expected valid=true, errors=%v", label, res.Errors)
	}
	if res.CredentialType != credentialType {
		return fmt.Errorf("%s: expected type %s, got %s", label, credentialType, res.CredentialType)
	}
	if res.IssuerDid == "" || res.HolderDid == "" {
		return fmt.Errorf("%s: missing issuer or holder DID", label)
	}
	fmt.Println("[ok] passed")
	return nil
}

func checkTampered(ctx context.Context, client pb.DidVerifierClient, jwt string) error {
	fmt.Println("\n--- Tampered Employment Credential ---")
	res, err := client.VerifyCredential(ctx, &pb.VerifyCredentialRequest{CredentialData: jwt})
	if err != nil {
		return fmt.Errorf("tampered rpc: %w", err)
	}
	fmt.Printf("Valid: %v\nErrors: %v\n", res.Valid, res.Errors)
	if res.Valid {
		return fmt.Errorf("tampered credential was accepted")
	}
	if len(res.Errors) == 0 {
		return fmt.Errorf("tampered credential returned no errors")
	}
	fmt.Println("[ok] rejected tampered credential")
	return nil
}

func checkExpired(ctx context.Context, client pb.DidVerifierClient, jwt string) error {
	fmt.Println("\n--- Expired Visitor Badge ---")
	res, err := client.VerifyCredential(ctx, &pb.VerifyCredentialRequest{CredentialData: jwt})
	if err != nil {
		return fmt.Errorf("expired rpc: %w", err)
	}
	fmt.Printf("Valid: %v\nExpired: %v\nErrors: %v\n", res.Valid, res.Expired, res.Errors)
	if res.Valid && !res.Expired {
		return fmt.Errorf("expired credential was accepted as valid")
	}
	fmt.Println("[ok] flagged expired credential")
	return nil
}

func loadSamples() (*sampleFile, error) {
	path := os.Getenv("DID_VERIFIER_SAMPLES")
	if path == "" {
		path = filepath.Join("data", "sample_credentials.json")
	}
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("%s: %w (run from the project root after scripts/issue_test_credentials.py)", path, err)
	}
	var samples sampleFile
	if err := json.Unmarshal(raw, &samples); err != nil {
		return nil, err
	}
	return &samples, nil
}

func fail(err error) {
	fmt.Fprintf(os.Stderr, "[fail] %v\n", err)
	os.Exit(1)
}
