package com.jobautomator.security;

import com.jobautomator.exception.ProcessExecutionException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import reactor.core.publisher.Mono;
import reactor.core.scheduler.Schedulers;

import java.io.BufferedReader;
import java.io.File;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.CompletableFuture;
import java.util.stream.Collectors;

/**
 * Secure, non-blocking process execution service for invoking Python automation scripts
 * (e.g. BrowserGym, Gmail Monitor, PDF Generator) safely.
 *
 * Implements non-blocking execution via process.onExit() and reactive pipelines,
 * strict argument/path sanitization, timeout management, and buffer drainers.
 */
public class SecureProcessExecutor {
    private static final Logger log = LoggerFactory.getLogger(SecureProcessExecutor.class);
    private static final Duration DEFAULT_TIMEOUT = Duration.ofSeconds(60);

    private final ProcessSanitizer sanitizer;
    private final File workingDirectory;

    public SecureProcessExecutor() {
        this(new ProcessSanitizer(), new File("."));
    }

    public SecureProcessExecutor(ProcessSanitizer sanitizer, File workingDirectory) {
        this.sanitizer = sanitizer;
        this.workingDirectory = workingDirectory;
    }

    /**
     * Non-blockingly executes a Python script with sanitized arguments.
     *
     * @param scriptPath Relative path to script (e.g. "src/browsergym_service.py")
     * @param arguments  List of string arguments to pass
     * @param timeout    Execution timeout duration
     * @return Mono of ProcessExecutionResult
     */
    public Mono<ProcessExecutionResult> executePythonScript(String scriptPath, List<String> arguments, Duration timeout) {
        return Mono.defer(() -> {
            long startTime = System.currentTimeMillis();

            // 1. Sanitize executable, script path, and arguments
            String pythonExe = sanitizer.resolvePythonExecutable();
            String safeScript = sanitizer.validateAndSanitizeScriptPath(scriptPath);
            List<String> safeArgs = sanitizer.sanitizeArguments(arguments);

            List<String> command = new ArrayList<>();
            command.add(pythonExe);
            command.add(safeScript);
            command.addAll(safeArgs);

            log.info("[SecureProcessExecutor] Launching sanitized command: {} in dir: {}",
                    command, workingDirectory.getAbsolutePath());

            ProcessBuilder pb = new ProcessBuilder(command);
            pb.directory(workingDirectory);

            // 2. Set sanitized environment
            Map<String, String> currentEnv = pb.environment();
            Map<String, String> safeEnv = sanitizer.buildSanitizedEnvironment(currentEnv);
            currentEnv.clear();
            currentEnv.putAll(safeEnv);

            try {
                Process process = pb.start();

                // 3. Drain stdout and stderr asynchronously so the process never deadlocks
                CompletableFuture<String> stdoutFuture = drainStreamAsync(process.getInputStream());
                CompletableFuture<String> stderrFuture = drainStreamAsync(process.getErrorStream());

                // 4. Non-blocking wait for process exit via Java 9+ onExit()
                CompletableFuture<ProcessExecutionResult> completionFuture = process.onExit().thenCombine(
                        stdoutFuture.thenCombine(stderrFuture, (stdout, stderr) -> new String[]{stdout, stderr}),
                        (proc, outputs) -> {
                            long duration = System.currentTimeMillis() - startTime;
                            int exitCode = proc.exitValue();
                            return new ProcessExecutionResult(exitCode, outputs[0], outputs[1], duration);
                        }
                );

                Duration effectiveTimeout = (timeout != null) ? timeout : DEFAULT_TIMEOUT;

                return Mono.fromFuture(completionFuture)
                        .timeout(effectiveTimeout)
                        .doOnError(e -> {
                            log.warn("[SecureProcessExecutor] Process execution failed or timed out. Forcibly terminating process PID={}",
                                    process.pid(), e);
                            if (process.isAlive()) {
                                process.destroyForcibly();
                            }
                        })
                        .doOnCancel(() -> {
                            log.info("[SecureProcessExecutor] Reactive pipeline cancelled. Destroying process PID={}", process.pid());
                            if (process.isAlive()) {
                                process.destroyForcibly();
                            }
                        });

            } catch (Exception e) {
                log.error("[SecureProcessExecutor] Failed to spawn process for script: {}", safeScript, e);
                return Mono.error(new ProcessExecutionException("Failed to launch process: " + safeScript, e));
            }
        });
    }

    public Mono<ProcessExecutionResult> executePythonScript(String scriptPath, List<String> arguments) {
        return executePythonScript(scriptPath, arguments, DEFAULT_TIMEOUT);
    }

    public Mono<ProcessExecutionResult> executePythonScript(String scriptPath) {
        return executePythonScript(scriptPath, List.of(), DEFAULT_TIMEOUT);
    }

    /**
     * Drains an InputStream asynchronously to prevent standard output/error buffer blockage.
     */
    private CompletableFuture<String> drainStreamAsync(InputStream inputStream) {
        return CompletableFuture.supplyAsync(() -> {
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(inputStream, StandardCharsets.UTF_8))) {
                return reader.lines().collect(Collectors.joining(System.lineSeparator()));
            } catch (Exception e) {
                log.warn("[SecureProcessExecutor] Error reading process output stream", e);
                return "";
            }
        }, Schedulers.boundedElastic()::schedule);
    }
}
