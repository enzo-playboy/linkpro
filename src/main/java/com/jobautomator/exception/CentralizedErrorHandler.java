package com.jobautomator.exception;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import reactor.core.publisher.Mono;

import java.time.Instant;
import java.util.HashMap;
import java.util.Map;
import java.util.regex.Pattern;

/**
 * Centralized exception handler and error categorizer for JobAutomator AI.
 * Handles reactive error wrapping, security message sanitization, and fallback orchestration.
 */
public class CentralizedErrorHandler {
    private static final Logger log = LoggerFactory.getLogger(CentralizedErrorHandler.class);

    private static final Pattern OPENAI_KEY_PATTERN = Pattern.compile("sk-[a-zA-Z0-9_\\-]{15,}");
    private static final Pattern BEARER_JWT_PATTERN = Pattern.compile("eyJ[a-zA-Z0-9_\\-\\.]+");
    private static final Pattern GENERIC_SECRET_PATTERN = Pattern.compile("(?i)(password|secret|key|token)=([^\\s&]+)");

    /**
     * Sanitizes sensitive information (API keys, JWTs, credentials) from error messages.
     */
    public static String sanitizeErrorMessage(String rawMessage) {
        if (rawMessage == null || rawMessage.isBlank()) {
            return "Unknown error occurred";
        }
        String clean = OPENAI_KEY_PATTERN.matcher(rawMessage).replaceAll("sk-***[REDACTED]");
        clean = BEARER_JWT_PATTERN.matcher(clean).replaceAll("[JWT-TOKEN-REDACTED]");
        clean = GENERIC_SECRET_PATTERN.matcher(clean).replaceAll("$1=[REDACTED]");
        return clean;
    }

    /**
     * Categorizes a Throwable into a machine-readable failure category.
     */
    public static String classifyError(Throwable t) {
        if (t instanceof SecurityValidationException) {
            return "SECURITY_VIOLATION";
        } else if (t instanceof RateLimitExceededException) {
            return "RATE_LIMIT_EXCEEDED";
        } else if (t instanceof ProcessExecutionException) {
            return "PROCESS_EXECUTION_FAILURE";
        } else if (t instanceof AgentExecutionException) {
            return "AGENT_REASONING_FAILURE";
        } else if (t instanceof java.util.concurrent.TimeoutException) {
            return "TIMEOUT";
        } else if (t instanceof IllegalArgumentException) {
            return "INVALID_INPUT";
        }
        return "INTERNAL_SYSTEM_ERROR";
    }

    /**
     * Converts an unhandled exception into a sanitized, standardized result map.
     */
    public static Map<String, Object> formatErrorResponse(Throwable t, String operationContext, Map<String, Object> basePayload) {
        String category = classifyError(t);
        String sanitizedMessage = sanitizeErrorMessage(t.getMessage());

        log.error("[CentralizedErrorHandler] Handled failure in operation='{}' | Category='{}' | Reason: {}",
                operationContext, category, sanitizedMessage);

        Map<String, Object> result = new HashMap<>();
        if (basePayload != null) {
            result.putAll(basePayload);
        }
        result.put("status", "FAILED");
        result.put("errorCategory", category);
        result.put("error", sanitizedMessage);
        result.put("operation", operationContext);
        result.put("timestamp", Instant.now().toString());
        return result;
    }

    /**
     * Reactive onErrorResume handler that logs and wraps failures into a standardized Mono payload.
     */
    public static <T extends Map<String, Object>> Mono<Map<String, Object>> handleReactiveError(
            Throwable t, String operationContext, Map<String, Object> fallbackPayload) {
        return Mono.just(formatErrorResponse(t, operationContext, fallbackPayload));
    }
}
