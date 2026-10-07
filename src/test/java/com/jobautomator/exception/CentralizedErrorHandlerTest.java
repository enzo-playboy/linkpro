package com.jobautomator.exception;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import reactor.test.StepVerifier;

import java.util.Map;
import java.util.concurrent.TimeoutException;

import static org.assertj.core.api.Assertions.assertThat;

class CentralizedErrorHandlerTest {

    @Test
    @DisplayName("Should correctly categorize different exception types")
    void shouldCategorizeExceptions() {
        assertThat(CentralizedErrorHandler.classifyError(new SecurityValidationException("Forbidden")))
                .isEqualTo("SECURITY_VIOLATION");

        assertThat(CentralizedErrorHandler.classifyError(new RateLimitExceededException("OPENAI", 5000)))
                .isEqualTo("RATE_LIMIT_EXCEEDED");

        assertThat(CentralizedErrorHandler.classifyError(new ProcessExecutionException("Exit 1")))
                .isEqualTo("PROCESS_EXECUTION_FAILURE");

        assertThat(CentralizedErrorHandler.classifyError(new AgentExecutionException("AgentX", "Reasoning failure")))
                .isEqualTo("AGENT_REASONING_FAILURE");

        assertThat(CentralizedErrorHandler.classifyError(new TimeoutException("Timed out")))
                .isEqualTo("TIMEOUT");

        assertThat(CentralizedErrorHandler.classifyError(new IllegalArgumentException("Bad input")))
                .isEqualTo("INVALID_INPUT");

        assertThat(CentralizedErrorHandler.classifyError(new RuntimeException("Something broke")))
                .isEqualTo("INTERNAL_SYSTEM_ERROR");
    }

    @Test
    @DisplayName("Should mask OpenAI API keys from error messages")
    void shouldMaskOpenAiApiKeys() {
        String raw = "Call failed with API key: sk-proj-1234567890abcdef1234567890 when calling OpenAI";
        String clean = CentralizedErrorHandler.sanitizeErrorMessage(raw);

        assertThat(clean).doesNotContain("sk-proj-1234567890abcdef1234567890");
        assertThat(clean).contains("sk-***[REDACTED]");
    }

    @Test
    @DisplayName("Should mask Bearer JWT tokens from error messages")
    void shouldMaskBearerTokens() {
        String raw = "Auth header was Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.t-IDN failed";
        String clean = CentralizedErrorHandler.sanitizeErrorMessage(raw);

        assertThat(clean).doesNotContain("eyJhbGciOiJIUzI1Ni");
        assertThat(clean).contains("[JWT-TOKEN-REDACTED]");
    }

    @Test
    @DisplayName("Should mask sensitive parameter assignments (password, secret, token)")
    void shouldMaskGenericSecrets() {
        String raw = "Connection failed with secret=supersecret123 and password=myPass!456";
        String clean = CentralizedErrorHandler.sanitizeErrorMessage(raw);

        assertThat(clean).doesNotContain("supersecret123");
        assertThat(clean).doesNotContain("myPass!456");
        assertThat(clean).contains("secret=[REDACTED]");
        assertThat(clean).contains("password=[REDACTED]");
    }

    @Test
    @DisplayName("Should format structured error response map")
    void shouldFormatStructuredErrorResponse() {
        Throwable t = new SecurityValidationException("Invalid path ../etc/passwd");
        Map<String, Object> base = Map.of("jobId", "123", "candidate", "Enzo");

        Map<String, Object> response = CentralizedErrorHandler.formatErrorResponse(t, "JobSearch", base);

        assertThat(response).containsEntry("status", "FAILED");
        assertThat(response).containsEntry("errorCategory", "SECURITY_VIOLATION");
        assertThat(response).containsEntry("operation", "JobSearch");
        assertThat(response).containsEntry("jobId", "123");
        assertThat(response).containsEntry("candidate", "Enzo");
        assertThat(response).containsKey("timestamp");
        assertThat((String) response.get("error")).contains("Invalid path ../etc/passwd");
    }

    @Test
    @DisplayName("Should produce a non-blocking reactive error fallback Mono")
    void shouldProduceReactiveErrorFallback() {
        Throwable t = new RateLimitExceededException("LINKEDIN", 1000);
        Map<String, Object> fallback = Map.of("fallbackKey", "fallbackValue");

        StepVerifier.create(CentralizedErrorHandler.handleReactiveError(t, "RateLimitedOp", fallback))
                .assertNext(res -> {
                    assertThat(res).containsEntry("status", "FAILED");
                    assertThat(res).containsEntry("errorCategory", "RATE_LIMIT_EXCEEDED");
                    assertThat(res).containsEntry("fallbackKey", "fallbackValue");
                })
                .verifyComplete();
    }
}
