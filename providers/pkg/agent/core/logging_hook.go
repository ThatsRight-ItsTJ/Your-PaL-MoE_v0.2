// ABOUTME: Provides logging hook for monitoring agent operations
// ABOUTME: Allows configurable levels of logging detail for debugging and monitoring

package core

import (
	"context"
	"encoding/json"
	"fmt"
	"log/slog"
	"strings"

	ldomain "github.com/lexlapax/go-llms/pkg/llm/domain"
)

// LoggingHook implements Hook for logging agent operations.
// It provides configurable logging levels to control the amount of detail
// logged during agent execution, from basic operation tracking to full debug output.
type LoggingHook struct {
	logger *slog.Logger
	level  LogLevel
}

// LogLevel represents the level of logging detail for agent operations.
// Higher levels include all information from lower levels.
type LogLevel int

const (
	// LogLevelBasic logs basic information
	LogLevelBasic LogLevel = iota
	// LogLevelDetailed logs detailed information including message content
	LogLevelDetailed
	// LogLevelDebug logs everything including full message content and tool data
	LogLevelDebug
)

// NewLoggingHook creates a new logging hook with the specified logger and level.
// If logger is nil, uses slog.Default(). The level controls how much detail
// is logged during agent operations.
func NewLoggingHook(logger *slog.Logger, level LogLevel) *LoggingHook {
	if logger == nil {
		logger = slog.Default()
	}
	return &LoggingHook{
		logger: logger,
		level:  level,
	}
}

// BeforeGenerate is called before generating a response.
// Logs the operation start and message details based on the configured log level.
func (h *LoggingHook) BeforeGenerate(ctx context.Context, messages []ldomain.Message) {
	h.logger.Info("Generating response", "emoji", "🤔")

	if h.level >= LogLevelDetailed {
		h.logger.Info("Message count", "count", len(messages))

		if h.level >= LogLevelDebug {
			for i, msg := range messages {
				h.logger.Debug("Message details",
					"index", i,
					"role", msg.Role,
					"content", getMessageContentText(msg.Content))
			}
		}
	}
}

// AfterGenerate is called after generating a response
func (h *LoggingHook) AfterGenerate(ctx context.Context, response ldomain.Response, err error) {
	if err != nil {
		h.logger.Error("Generation failed", "error", err, "emoji", "❌")
		return
	}

	h.logger.Info("Response generated", "emoji", "✅")

	if h.level >= LogLevelDetailed {
		contentLength := 50
		if h.level >= LogLevelDebug {
			contentLength = 200
		}
		h.logger.Info("Response content", "content", truncateString(response.Content, contentLength))
	}
}

// BeforeToolCall is called before executing a tool
func (h *LoggingHook) BeforeToolCall(ctx context.Context, tool string, params map[string]interface{}) {
	h.logger.Info("Calling tool", "tool", tool, "emoji", "🔧")

	if h.level >= LogLevelDetailed {
		paramsValue := getParamsSummary(params)
		if h.level >= LogLevelDebug {
			paramsJSON, _ := json.MarshalIndent(params, "  ", "  ")
			paramsValue = string(paramsJSON)
		}
		h.logger.Debug("Tool parameters", "params", paramsValue)
	}
}

// AfterToolCall is called after executing a tool
func (h *LoggingHook) AfterToolCall(ctx context.Context, tool string, result interface{}, err error) {
	if err != nil {
		h.logger.Error("Tool call failed", "tool", tool, "error", err, "emoji", "❌")
		return
	}

	h.logger.Info("Tool executed successfully", "tool", tool, "emoji", "✅")

	if h.level >= LogLevelDetailed {
		if result != nil {
			resultValue := truncateString(fmt.Sprintf("%v", result), 50)
			if h.level >= LogLevelDebug {
				resultJSON, _ := json.MarshalIndent(result, "  ", "  ")
				resultValue = truncateString(string(resultJSON), 300)
			}
			h.logger.Debug("Tool result", "result", resultValue)
		} else {
			h.logger.Debug("No result returned from tool")
		}
	}
}

// Helper functions

// truncateString truncates a string if it's too long
func truncateString(s string, maxLen int) string {
	if len(s) <= maxLen {
		return s
	}
	return s[:maxLen] + "..."
}

// getParamsSummary returns a summary of the parameters
func getParamsSummary(params map[string]interface{}) string {
	var parts []string
	for k, v := range params {
		parts = append(parts, fmt.Sprintf("%s: %v", k, truncateValue(v)))
	}
	return strings.Join(parts, ", ")
}

// truncateValue truncates a value for display
func truncateValue(v interface{}) string {
	switch val := v.(type) {
	case string:
		return truncateString(val, 20)
	case []interface{}:
		return fmt.Sprintf("[%d items]", len(val))
	case map[string]interface{}:
		return fmt.Sprintf("{%d keys}", len(val))
	default:
		return fmt.Sprintf("%v", v)
	}
}

// getMessageContentText extracts text from the ContentPart array and truncates it
func getMessageContentText(content []ldomain.ContentPart) string {
	if len(content) == 0 {
		return ""
	}

	var allText string
	for _, part := range content {
		if part.Type == ldomain.ContentTypeText {
			allText += part.Text + " "
		} else {
			allText += "[" + string(part.Type) + " content] "
		}
	}

	return truncateString(strings.TrimSpace(allText), 100)
}
