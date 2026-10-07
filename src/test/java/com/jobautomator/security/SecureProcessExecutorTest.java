package com.jobautomator.security;

import com.jobautomator.exception.SecurityValidationException;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import reactor.test.StepVerifier;

import java.time.Duration;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

class SecureProcessExecutorTest {

    @Test
    @DisplayName("Should immediately reject unapproved script path before spawning process")
    void shouldRejectUnapprovedScriptPath() {
        SecureProcessExecutor executor = new SecureProcessExecutor();

        StepVerifier.create(executor.executePythonScript("evil_script.py"))
                .expectError(SecurityValidationException.class)
                .verify();
    }

    @Test
    @DisplayName("Should reject script path with command injection characters")
    void shouldRejectScriptPathWithInjection() {
        SecureProcessExecutor executor = new SecureProcessExecutor();

        StepVerifier.create(executor.executePythonScript("src/browsergym_service.py; rm -rf /"))
                .expectError(SecurityValidationException.class)
                .verify();
    }

    @Test
    @DisplayName("Should reject malicious arguments containing shell injection")
    void shouldRejectMaliciousArguments() {
        SecureProcessExecutor executor = new SecureProcessExecutor();

        StepVerifier.create(executor.executePythonScript("src/browsergym_service.py", List.of("safeArg", "; cat /etc/passwd")))
                .expectError(SecurityValidationException.class)
                .verify();
    }

    @Test
    @DisplayName("Should reject directory traversal in script path")
    void shouldRejectDirectoryTraversalPath() {
        SecureProcessExecutor executor = new SecureProcessExecutor();

        StepVerifier.create(executor.executePythonScript("../../browsergym_service.py"))
                .expectError(SecurityValidationException.class)
                .verify();
    }
}
