package com.jobautomator.security;

import com.jobautomator.exception.SecurityValidationException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.IOException;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.regex.Pattern;

/**
 * Security sanitizer and input validator for ProcessBuilder and CLI executions.
 * Prevents command injection, directory traversal, shell metacharacter attacks,
 * and malicious environment variable poisoning.
 */
public class ProcessSanitizer {
    private static final Logger log = LoggerFactory.getLogger(ProcessSanitizer.class);

    // Whitelist of allowed python scripts within the project
    private static final Set<String> ALLOWED_SCRIPTS = Set.of(
            "browsergym_service.py",
            "gmail_monitor.py",
            "read_5_latest_emails.py",
            "pdf_generator.py",
            "ai_service.py",
            "ats_audit_service.py",
            "authenticate_gmail.py",
            "industry_taxonomy.py",
            "role_research_service.py",
            "supabase_client.py",
            "telegram_notifier.py",
            "universal_resume_builder.py"
    );

    // Whitelist of safe environment variables allowed to be passed to sub-processes
    private static final Set<String> ALLOWED_ENV_VARS = Set.of(
            "PATH",
            "PYTHONPATH",
            "SYSTEMROOT",
            "COMSPEC",
            "PATHEXT",
            "TEMP",
            "TMP",
            "OPENAI_API_KEY",
            "SUPABASE_URL",
            "SUPABASE_KEY",
            "TELEGRAM_BOT_TOKEN",
            "TELEGRAM_CHAT_ID"
    );

    // Dangerous characters pattern that could lead to command injection or shell escapes
    private static final Pattern DANGEROUS_CHARS = Pattern.compile("[;&|`$><\\r\\n\\u0000\"']");

    // Safe argument pattern: letters, numbers, hyphens, underscores, dots, colons, slashes, query params
    private static final Pattern SAFE_ARGUMENT = Pattern.compile("^[a-zA-Z0-9_\\-./:=?&%#+@~]*$");

    // Safe Job ID pattern (e.g. linkedin-102938, job_48291)
    private static final Pattern SAFE_ID = Pattern.compile("^[a-zA-Z0-9_\\-]{1,100}$");

    private final Path projectRoot;

    public ProcessSanitizer() {
        this(Paths.get(".").toAbsolutePath().normalize());
    }

    public ProcessSanitizer(Path projectRoot) {
        this.projectRoot = projectRoot.normalize();
    }

    /**
     * Resolves and verifies the Python executable path.
     * Checks .venv virtual environment first, falling back to system python.
     */
    public String resolvePythonExecutable() {
        boolean isWindows = System.getProperty("os.name", "").toLowerCase().contains("win");
        Path venvPython = isWindows
                ? projectRoot.resolve(".venv").resolve("Scripts").resolve("python.exe")
                : projectRoot.resolve(".venv").resolve("bin").resolve("python");

        if (venvPython.toFile().exists()) {
            return venvPython.normalize().toString();
        }

        // Fallback to standard python command
        return isWindows ? "python.exe" : "python3";
    }

    /**
     * Validates and sanitizes a script path, enforcing:
     * 1. Path must not contain directory traversal sequences (..).
     * 2. Canonical path must reside inside the project directory.
     * 3. Script must end with .py.
     * 4. Script filename must be in the whitelist of trusted project scripts.
     */
    public String validateAndSanitizeScriptPath(String rawScriptPath) {
        if (rawScriptPath == null || rawScriptPath.isBlank()) {
            throw new SecurityValidationException("Script path cannot be null or empty");
        }

        // Check for basic injection or control characters
        if (DANGEROUS_CHARS.matcher(rawScriptPath).find()) {
            throw new SecurityValidationException("Script path contains illegal characters: " + rawScriptPath);
        }

        // Check for directory traversal
        if (rawScriptPath.contains("..")) {
            throw new SecurityValidationException("Directory traversal attempt detected in script path: " + rawScriptPath);
        }

        Path scriptPath = Paths.get(rawScriptPath);
        String fileName = scriptPath.getFileName().toString();

        if (!fileName.endsWith(".py")) {
            throw new SecurityValidationException("Only Python (.py) scripts are permitted for execution: " + rawScriptPath);
        }

        if (!ALLOWED_SCRIPTS.contains(fileName)) {
            throw new SecurityValidationException("Script '" + fileName + "' is not in the whitelist of approved scripts");
        }

        Path resolvedPath = projectRoot.resolve(scriptPath).normalize();
        
        // Ensure path stays within project root
        if (!resolvedPath.startsWith(projectRoot)) {
            throw new SecurityValidationException("Script path traverses outside project root: " + rawScriptPath);
        }

        return scriptPath.toString().replace('\\', '/');
    }

    /**
     * Sanitizes a single CLI argument.
     */
    public String sanitizeArgument(String arg) {
        if (arg == null) {
            throw new SecurityValidationException("Argument cannot be null");
        }
        if (DANGEROUS_CHARS.matcher(arg).find()) {
            throw new SecurityValidationException("Argument contains illegal characters: " + arg);
        }
        if (!SAFE_ARGUMENT.matcher(arg).matches()) {
            throw new SecurityValidationException("Argument does not match safe character policy: " + arg);
        }
        if (arg.length() > 2048) {
            throw new SecurityValidationException("Argument exceeds maximum allowable length (2048 chars)");
        }
        return arg;
    }

    /**
     * Validates and sanitizes a list of CLI arguments.
     */
    public List<String> sanitizeArguments(List<String> args) {
        if (args == null) {
            return Collections.emptyList();
        }
        return args.stream()
                .map(this::sanitizeArgument)
                .toList();
    }

    /**
     * Validates a Job ID string.
     */
    public String validateJobId(String jobId) {
        if (jobId == null || !SAFE_ID.matcher(jobId).matches()) {
            throw new SecurityValidationException("Invalid Job ID format: " + jobId);
        }
        return jobId;
    }

    /**
     * Builds a sanitized environment map for ProcessBuilder, stripping out unapproved or tainted variables.
     */
    public Map<String, String> buildSanitizedEnvironment(Map<String, String> currentEnv) {
        Map<String, String> safeEnv = new HashMap<>();
        if (currentEnv == null) {
            currentEnv = System.getenv();
        }

        for (Map.Entry<String, String> entry : currentEnv.entrySet()) {
            String key = entry.getKey();
            if (ALLOWED_ENV_VARS.contains(key.toUpperCase())) {
                safeEnv.put(key, entry.getValue());
            }
        }

        return Collections.unmodifiableMap(safeEnv);
    }
}
