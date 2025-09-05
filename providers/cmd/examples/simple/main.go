package main

// ABOUTME: Simple example demonstrating basic structured output extraction from LLMs
// ABOUTME: Shows how to use schemas to validate and extract JSON data from LLM responses

import (
	"context"
	"encoding/json"
	"log"

	"github.com/lexlapax/go-llms/pkg/llm/provider"
	"github.com/lexlapax/go-llms/pkg/schema/domain"
	"github.com/lexlapax/go-llms/pkg/schema/validation"
	structuredProcessor "github.com/lexlapax/go-llms/pkg/structured/processor"
)

// Person defines a struct for our schema
type Person struct {
	Name  string `json:"name" validate:"required" description:"Person's name"`
	Age   int    `json:"age" validate:"min=0,max=120" description:"Age in years"`
	Email string `json:"email" validate:"required,email" description:"Email address"`
}

func main() {
	// Create a schema manually
	schema := &domain.Schema{
		Type: "object",
		Properties: map[string]domain.Property{
			"name":  {Type: "string", Description: "Person's name"},
			"age":   {Type: "integer", Minimum: float64Ptr(0), Maximum: float64Ptr(120)},
			"email": {Type: "string", Format: "email", Description: "Email address"},
		},
		Required: []string{"name", "email"},
	}

	// Create a mock LLM provider
	llmProvider := provider.NewMockProvider()

	// Create a validator and structured processor
	validator := validation.NewValidator()
	processor := structuredProcessor.NewStructuredProcessor(validator)
	promptEnhancer := structuredProcessor.NewPromptEnhancer()

	log.Println("Go-LLMs Simple Example")
	log.Println("======================")

	// Example 1: Using the mock provider with a simple prompt
	log.Println("\nExample 1: Simple generation")
	response, err := llmProvider.Generate(context.Background(), "Tell me about Go")
	if err != nil {
		log.Fatalf("Generation error: %v", err)
	}
	log.Printf("Response: %s\n", response)

	// Example 2: Using the mock provider with schema
	log.Println("\nExample 2: Structured generation with schema")
	result, err := llmProvider.GenerateWithSchema(
		context.Background(),
		"Generate information about a person",
		schema,
	)
	if err != nil {
		log.Fatalf("Structured generation error: %v", err)
	}

	// Pretty print the result
	resultJSON, _ := json.MarshalIndent(result, "", "  ")
	log.Printf("Structured Response:\n%s\n", string(resultJSON))

	// Example 3: Streaming responses
	log.Println("\nExample 3: Streaming response")
	stream, err := llmProvider.Stream(context.Background(), "Tell me about Go")
	if err != nil {
		log.Fatalf("Stream error: %v", err)
	}

	log.Print("Streamed Response: ")
	for token := range stream {
		log.Print(token.Text)
		if token.Finished {
			log.Println()
		}
	}

	// Example a raw LLM response with the structured processor
	log.Println("\nExample 4: Processing raw outputs with the structured processor")

	// Simulate a raw LLM response that contains JSON with some extra text
	rawResponse := `Here's the information about the person:
	
	{
		"name": "Jane Smith",
		"age": 35,
		"email": "jane.smith@example.com"
	}
	
	The above information was generated based on your request.`

	// Process the raw response
	processedResult, err := processor.Process(schema, rawResponse)
	if err != nil {
		log.Fatalf("Processing error: %v", err)
	}

	// Pretty print the processed result
	processedJSON, _ := json.MarshalIndent(processedResult, "", "  ")
	log.Printf("Processed Response:\n%s\n", string(processedJSON))

	// Example 5: Processing raw outputs into a typed struct
	log.Println("\nExample 5: Processing raw outputs into a typed struct")
	var person Person
	err = processor.ProcessTyped(schema, rawResponse, &person)
	if err != nil {
		log.Fatalf("Typed processing error: %v", err)
	}

	log.Printf("Person struct: Name=%s, Age=%d, Email=%s\n",
		person.Name, person.Age, person.Email)

	// Example 6: Enhancing prompts with schema information
	log.Println("\nExample 6: Enhancing prompts with schema information")
	prompt := "Generate information about a person"

	enhancedPrompt, err := promptEnhancer.Enhance(prompt, schema)
	if err != nil {
		log.Fatalf("Prompt enhancement error: %v", err)
	}

	log.Println("Original prompt:", prompt)
	log.Println("Enhanced prompt snippet (first 100 chars):", truncate(enhancedPrompt, 100))

	// Example 7: Enhancing prompts with additional options
	log.Println("\nExample 7: Enhancing prompts with examples")
	options := map[string]interface{}{
		"instructions": "Make sure the person has a realistic name and email",
		"examples": []map[string]interface{}{
			{
				"name":  "John Doe",
				"age":   30,
				"email": "john.doe@example.com",
			},
		},
	}

	enhancedPromptWithOptions, err := promptEnhancer.EnhanceWithOptions(prompt, schema, options)
	if err != nil {
		log.Fatalf("Prompt enhancement with options error: %v", err)
	}

	log.Println("Enhanced prompt with options snippet (first 100 chars):",
		truncate(enhancedPromptWithOptions, 100))
}

// Helper function for creating float pointers
func float64Ptr(v float64) *float64 {
	return &v
}

// Helper function to truncate strings
func truncate(s string, maxLen int) string {
	if len(s) <= maxLen {
		return s
	}
	return s[:maxLen] + "..."
}
